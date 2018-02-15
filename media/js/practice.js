// Copyright (C) 2011-2013 Csaba Hoch
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

///// Constants /////

// We try to transfer each word RETRIES_COUNT times.
var RETRIES_COUNT = 100;

// The timeout of the AJAX request when we try to transfer a word the first
// time.
var INITIAL_TIMEOUT = 3 * 1000; // 3 seconds

// The timeoout of the AJAX request will be increased by TIMEOUT_INTERVAL ms
// for each retry.
var TIMEOUT_INTERVAL = 3 * 1000; // 3 second

// The maximum value of the timeout of the AJAX request when a word is
// transferred.
var MAX_TIMEOUT = 20 * 1000; // 20 seconds

// The minimum time for the "Please wait" text to be displayed.
var MIN_PLEASE_WAIT_DISPLAY = 300; // 1 second.

// The maximum number of characters used to represent the question word when
// printing information about how adding a label to the word progresses
var QUESTION_WORD_PREFIX = 40;


///// Global state /////

var todays_word_list;
var all_words_to_practice;
var transferred = 0;
var first_transfer_in_progress = 0;
var retry_transfer_in_progress = 0;
var answered = 0;
var answered_incorrectly = 0;
var operations_are_visible = false;
var fullscreen_on = false;

// The state of the UI. Possible states:
// - init
// - intermediate: the UI is doing some work
// - answer: we are waiting for the "answer" button to be pushed
// - yesno: we are waiting for the "yes" or "no" button to be pushed
// - please_wait_hard: there are no more words to ask and we have been
//   displaying "Please wait" for less then MIN_PLEASE_WAIT_DISPLAY ms ago
// - please_wait_soft: we have been displaying "Please wait" for more then
//   MIN_PLEASE_WAIT_DISPLAY ms ago, but we are still trying to send some
//   updates
// - finished: there are no more updates to send
//
// State transitions:
//
//     init -> answer -> intermediate -> yesno -> please_wait_hard 
//                ^                        |              V
//                +------ intermediate <---+      please_wait_soft
//                                                        V
//                                                    finished
var state = 'init';

// Details of the current word
var word;
var word_index = false;
var direction;
var question_word;
var solution_word;
var word_current_date;
var word_current_strength;
var explanation;

// The word index of the previous word
var prev_word_index = false;

// Translation dictionary
var translations = {}


///// Functions /////

function ew_prefix(s, maxlength) {
    // "short" -> "short"
    // "text longer than maxlength characters" -> "text longer th..."
    if (s.length <= maxlength) {
        return s;
    } else {
        return s.substring(0, maxlength - 3) + '...';
    }
}


function init_translations() {
    $('[id^=translate_]').each(function(index) {
        var key = $(this).attr('id').replace(/^translate_/, '');
        var value = ew_strip($(this).text());
        translations[key] = value;
    });
}

function ask_first_word(todays_word_list_param) {
    // Set the given word list as the word list for today and ask the first
    // word.
    todays_word_list = todays_word_list_param['word_list'];
    words_to_practice_now = todays_word_list.length;
    all_words_to_practice = todays_word_list_param['all_words_to_practice'];

    $('#all-now').text(words_to_practice_now);
    if (words_to_practice_now < all_words_to_practice) {
        $('#all-today').text('[' + translations['all_words_to_practice'] +
                             ': ' + all_words_to_practice + ']');
    }

    $('#transferred').text('0');
    $('#transfer-in-progress').text('0');
    $('#answered').text('0');
    $('#answered-incorrectly').text('0');
    ask_word();
}

function get_todays_word_list(success_fun, word_list_type) {
    // Get the list of today's word from the server and ask the first one.
    // word_list_type = "normal" | "early"
    $.ajax({
        url: GET_WORDS_TO_PRACTICE_TODAY_URL + '?' + Math.random(),
        dataType: 'json',
        data: {'word_list_type': word_list_type},
        type: 'get',
        success: success_fun
    });
}

function start_practice() {
    // Start the practice. If WORDS_TO_PRACTICE_TODAY is undefined, get the
    // words from the server.
    if (WORDS_TO_PRACTICE_TODAY == 'normal') {
        get_todays_word_list(ask_first_word, 'normal');
    } else if (WORDS_TO_PRACTICE_TODAY == 'early') {
        get_todays_word_list(ask_first_word, 'early');
    } else {
        ask_first_word(WORDS_TO_PRACTICE_TODAY);
    }
}
    
function update_edit_word(button, curr_word_index) {
    // Sets the given "Edit ... word" link. If there is no word, it will remove
    // the "href" part and make the class of the link "nonlink", which will
    // make it gray.
    if (curr_word_index == false) {
        $(button).removeAttr('href');
        $(button).attr('class', 'nonlink');
    } else {
        var edit_url = EDIT_WORD_PAIR_URL.replace('999', curr_word_index);
        $(button).attr('href', edit_url);
        $(button).removeAttr('class');
    }
}

function update_edit_words(button, curr_word_index) {
    // Sets the "Edit current word" and "Edit previous word" links

    update_edit_word('#edit-word-button', word_index);
    update_edit_word('#edit-prev-word-button', prev_word_index);
}

function ask_word() {

    if (todays_word_list.length == 0) {

        state = 'please_wait_hard';
        prev_word_index = word_index;
        word_index = false;

        $('#buttons').hide();
        $('#question').hide();
        $('#answer').hide();
        $('#explanation').hide();

        update_transfer_in_progress();
        update_edit_words();

        // We display "Please wait" for at least MIN_PLEASE_WAIT_DISPLAY
        // ms so that the user has the time to read it. Then we move to
        // 'please_wait_soft' state and remove the "Please wait" text when the
        // acknowledgement about the last word arrives from the server.
        setTimeout(
            function() {
                state = 'please_wait_soft';
                update_transfer_in_progress();
            }, MIN_PLEASE_WAIT_DISPLAY);

    } else {

        show_answer_button();
        word = todays_word_list[0];
        direction = word[2];
        question_word = word[direction - 1];
        solution_word = word[2 - direction];
        prev_word_index = word_index;
        word_index = word[3];
        word_current_date = word[4];
        word_current_strength = word[5];
        explanation = word[6];

        question = $('#question');
        question.html(question_word);
        if (direction == 1) {
            question.append(" &rarr;");
        } else {
            question.prepend("&larr; ");
        }

        $('#answer').html('');
        $('#explanation').html('');
        update_edit_words();

        todays_word_list.shift();
        state = 'answer';
    }
}

function show_answer_button() {
    $('#ok-button').show();
    $('#yes-button').hide();
    $('#no-button').hide();
}

function show_yesno_buttons() {
    $('#ok-button').hide();
    $('#yes-button').show();
    $('#no-button').show();
}

function answer_button() {
    state = 'intermediate';
    $('#answer').html(solution_word);
    $('#explanation').html(explanation);
    show_yesno_buttons();
    state = 'yesno';
}

function next_timeout(timeout) {
    // Calculates the value of the next timeout based on the last timeout
    var maybe_next_timeout = timeout + TIMEOUT_INTERVAL;
    if (maybe_next_timeout > MAX_TIMEOUT) {
        return timeout;
    } else {
        return maybe_next_timeout;
    }
}

function update_transfer_in_progress() {
    // - Update the value of the "transfer is progress" field
    // - Change the state and show the "please wait" text if needed

    // Display the number of words whose transfer is in progress
    $('#transfer-in-progress').text(retry_transfer_in_progress);

    // If "Please wait" has been displayed for MIN_PLEASE_WAIT_DISPLAY seconds
    // and all words has been transferred, we move to 'finished' state
    if (state == 'please_wait_soft' &&
        first_transfer_in_progress + retry_transfer_in_progress == 0) {
        state = 'finished';
    }

    // Maybe display the "Please wait" text
    if (state == 'please_wait_hard' || state == 'please_wait_soft')
        $('#final_sentence').text(translations['please_wait']);
    else if (state == 'finished') {
        // The page should be reloaded if there are still words today or there
        // were incorrect answers
        if (words_to_practice_now < all_words_to_practice ||
            answered_incorrectly > 0) {
            location.reload();
        } else {
            $('#final_sentence').text(translations['finished']);
        }
    }
}

function ew_ajax_error(url, data, result, retries, timeout, success_fun,
                       error_fun, give_up_fun) {

    error_fun(retries);
    setTimeout(
        function() {
            ew_ajax_send(url, data, retries - 1, next_timeout(timeout),
                         success_fun, error_fun, give_up_fun);
        }, timeout);
}

function ew_ajax_send(url, data, retries, timeout, success_fun, error_fun,
                      give_up_fun) {
    if (retries != 0) {
        $.ajax({
            url: url,
            dataType: 'json',
            data: data,
            type: 'post',
            timeout: timeout,
            success: function(result) {
                if (result == 'ok') {
                    // The update was successful
                    success_fun(retries);
                } else {
                    // We got an error from the server
                    ew_ajax_error(url, data, result, retries, timeout,
                                  success_fun, error_fun, give_up_fun);
                }
            },
            error: function(result) {
                // We got an error; we may not have reached the server
                ew_ajax_error(url, data, result, retries, timeout,
                              success_fun, error_fun, give_up_fun);
            }
        });
    } else {
        // We give up the transfer
        give_up_fun();
    }
}

function ajax_update_word_success(retries) {
    // The server updated the word successfully
    transferred++;
    $('#transferred').text(transferred);
    if (retries == RETRIES_COUNT) {
        first_transfer_in_progress--;
    } else {
        retry_transfer_in_progress--;
    }
    update_transfer_in_progress();
}

function ajax_update_word_error(retries) {
    if (retries == RETRIES_COUNT) {
        // This is the first transfer error regarding this word
        first_transfer_in_progress--;
        retry_transfer_in_progress++;
        update_transfer_in_progress();
    };
}

function ajax_update_word_give_up() {
    retry_transfer_in_progress--;
    update_transfer_in_progress();
}

function ajax_update_word(update_data) {
    // Sends an "update word" request to the server.

    // first_transfer_in_progress should be incremented by the caller of this
    // function.

    update_data['csrfmiddlewaretoken'] = csrf_token;
    ew_ajax_send(UPDATE_WORD_URL, update_data, RETRIES_COUNT, INITIAL_TIMEOUT,
                 ajax_update_word_success,
                 ajax_update_word_error,
                 ajax_update_word_give_up);
}

function find_li_with_label(word_index, direction, label) {
    return $.grep($('#operations-list li'),
                  function(node, index) {
                      return $(node).attr('id') ==
                             'ql-' + word_index + '-' + direction + '-' + label;
                  }, false);
}

function ajax_add_label_to_current_word(label) {
    // Sends an "add label" request to the server.

    // If we already have an update with the same input, we ignore the new
    // request
    if (find_li_with_label(word_index, direction, label) > 0) {
        return;
    }

    // Read the translated texts from the HTML file
    var tr_keys = ['start', 'success', 'trying', 'gave_up'];
    var tr_dict = {};
    for (var i=0; i<tr_keys.length; i++) {
        // Example:
        // tr_dict['start'] = "Adding label started: mylabel, 23"
        var trans_label = tr_keys[i];
        tr_dict[trans_label] = 
            translations['add_label_' + trans_label] + ': ' +
            label + ', ' + ew_prefix(question_word, QUESTION_WORD_PREFIX);
    }

    var change_text_gen = function(text) {
        // Generates a function which places the given text in the 'li' item
        // which belongs to this word_index+direction+label
        return function() {
            var li = find_li_with_label(word_index, direction, label);
            $(li).text(text);
        }
    }

    var data = {'word_index': JSON.stringify(word_index),
                'label': JSON.stringify(label),
                'csrfmiddlewaretoken': csrf_token};

    // Show the user that the operation has started
    $('#operations-list').append('<li></li>');
    $('#operations-list li').last().
                             attr('id', 'ql-' + word_index + '-' + direction +
                                        '-' + label).
                             text(tr_dict['start']);

    ew_ajax_send(ADD_LABEL_URL, data, RETRIES_COUNT, INITIAL_TIMEOUT,
                 change_text_gen(tr_dict['success']),
                 change_text_gen(tr_dict['error']),
                 change_text_gen(tr_dict['give_up']));
}

function yesno_button(answer) {
    state = 'intermediate';
    var update_data = {'answer': JSON.stringify(answer),
                       'word_index': JSON.stringify(word_index),
                       'direction': JSON.stringify(direction),
                       'old_date': JSON.stringify(word_current_date),
                       'old_strength': JSON.stringify(word_current_strength)};
    first_transfer_in_progress++;
    ask_word();
    answered++;
    if (!answer) {
        answered_incorrectly++;
        $('#answered-incorrectly').text(answered_incorrectly);
    }
    $('#answered').text(answered);
    ajax_update_word(update_data);
}

function ew_practice_button_pressed(button) {
    if (state == 'answer') {
        state = 'intermediate';
        answer_button();
    } else if (state == 'yesno') {
        if (button == 'yes') { 
            state = 'intermediate';
            yesno_button(true);
        } else if (button == 'no') {
            state = 'intermediate';
            yesno_button(false);
        }
    }
}

function ew_pageupdown(e) {
    // Activated only if the user changes the value of the 'pgupdown_behavior'
    // setting
    if (e.originalEvent.key == ew_yes_key) {
        e.preventDefault();
        ew_practice_button_pressed('yes');
    } else if (e.originalEvent.key == ew_no_key) {
        e.preventDefault();
        ew_practice_button_pressed('no');
    }
}

function maybe_activate_ew_pageupdown() {
    if (PGUPDOWN_BEHAVIOR == 'yesno') {
        ew_yes_key = 'PageUp';
        ew_no_key = 'PageDown';
        $('body').bind('keydown', ew_pageupdown);
    } else if (PGUPDOWN_BEHAVIOR == 'noyes') {
        ew_no_key = 'PageUp';
        ew_yes_key = 'PageDown';
        $('body').bind('keydown', ew_pageupdown);
    }
}

function show_hide_operations(action) {
    // action in ['show', 'hide', 'toggle']
    if (action == 'show' ||
        (action == 'toggle' && !operations_are_visible)) {
            $('#show-operations-button').hide();
            $('#operations').show();
            operations_are_visible = true;
    } else {
            $('#show-operations-button').show();
            $('#operations').hide();
            operations_are_visible = false;
    }
}

function fullscreen(action) {
    // action in ['on', 'off', 'toggle']
    if (action == 'on' ||
        (action == 'toggle' && !fullscreen_on)) {
            $('#breadcrumb').hide();
            $('#fullscreen-on-button').hide();
            $('#fullscreen-off-button').show();
            $('#all-today').hide();
            $('body #main #buttons').hide();
            fullscreen_on = true;
    } else {
            $('#breadcrumb').show();
            $('#fullscreen-on-button').show();
            $('#fullscreen-off-button').hide();
            $('#all-today').show();
            $('body #main #buttons').show();
            fullscreen_on = false;
    }
}

function ew_keypress(e) {
    if (e.which == 109) {
        // 'm' (more)
        show_hide_operations('toggle');
    } else if (e.which == 102) {
        // 'f' (fullscreen)
        fullscreen('toggle');
    } else {
        ew_practice_button_pressed(
            (e.which == 105 || e.which == 121) ? 'yes' :
            (e.which == 110) ? 'no' : 'other');
    }
}

$(document).ready(function() {

    // Initializing event handlers
    $('#yes-button').click(function() { yesno_button(true); });
    $('#no-button').click(function() { yesno_button(false); });
    $('#ok-button').click(answer_button);
    $('body').keypress(ew_keypress);

    $('#show-operations-button').click(function() {
        show_hide_operations('show');
    });
    $('#hide-operations-button').click(function() {
        show_hide_operations('hide');
    });

    $('#fullscreen-on-button').click(function() {
        fullscreen('on');
    });
    $('#fullscreen-off-button').click(function() {
        fullscreen('off');
    });

    $('#quick-labels [id^=quick-label-]').click(function() {
        var label = $(this).attr('id').replace(/^quick-label-/, '');
        ajax_add_label_to_current_word(label);
    });

    maybe_activate_ew_pageupdown();

    //Initializing the translation dictionary
    init_translations();

    // Ask the first word
    start_practice();
});
