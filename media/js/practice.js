// This file is part of ExponWords.
//
// ExponWords is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// ExponWords is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// ExponWords.  If not, see <http://www.gnu.org/licenses/>.

// Copyright (C) 2011 Csaba Hoch


///// Constants /////

var RETRIES_COUNT = 24;
var INITIAL_TIMEOUT = 3 * 1000; // 3 seconds
var TIMEOUT_INTERVAL = 3 * 1000; // 3 second
var MAX_TIMEOUT = 20 * 1000; // 20 seconds

// The minimum time for the "Please wait" text to be displayed.
var MIN_PLEASE_WAIT_DISPLAY = 1000; // 1 second.


///// Global state /////

var todays_wordlist;
var transferred = 0;
var first_transfer_in_progress = 0;
var retry_transfer_in_progress = 0;
var answered = 0;
var answered_incorrectly = 0;

// State of the UI. Possible states:
// - init
// - intermediate: the UI is doing some work
// - answer: we are waiting for the "answer" button to be pushed
// - yesno: we are waiting for the "yes" or "no" button to be pushed
// - please_wait_hard: there are no more words to ask and we have been
//   displaying "Please wait" for less then MIN_PLEASE_WAIT_DISPLAY seconds ago
// - please_wait_soft: we have been displaying "Please wait" for more then
//   MIN_PLEASE_WAIT_DISPLAY seconds ago, but we are still trying to send some
//   updates
// - finished: there are no more updates to send
var state = 'init';

// Details of the current word
var word;
var word_index = false;
var direction;
var question_word;
var solution_word;
var explanation;

var prev_word_index = false;


///// Functions /////

function ask_first_word(result) {
    todays_wordlist = WORDS_TO_PRACTICE_TODAY;
    $('#all').text(todays_wordlist.length);
    $('#transferred').text('0');
    $('#transfer-in-progress').text('0');
    $('#answered').text('0');
    $('#answered-incorrectly').text('0');
    ask_word();
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

    if (todays_wordlist.length == 0) {

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
        // seconds so that the user has the time to read it. Then we move to
        // 'please_wait_soft' state and remove the "Please wait" text when the
        // acknowledgement about the last word arrives from the server.
        setTimeout(
            function() {
                state = 'please_wait_soft';
                update_transfer_in_progress();
            }, MIN_PLEASE_WAIT_DISPLAY);

    } else {

        show_answer_button();
        word = todays_wordlist[0];
        direction = word[2];
        question_word = word[direction - 1];
        solution_word = word[2 - direction];
        prev_word_index = word_index;
        word_index = word[3];
        explanation = word[4];

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

        todays_wordlist.shift();
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
    var maybe_next_timeout = timeout + TIMEOUT_INTERVAL;
    if (maybe_next_timeout > MAX_TIMEOUT) {
        return timeout;
    } else {
        return maybe_next_timeout;
    }
}

function update_transfer_in_progress() {

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
        $('#please_wait').show();
    else if (state == 'finished') {
        $('#please_wait').hide();
        $('#no_more_words').show();
    }

}

function update_error(data, result, retries, timeout)
{
    if (retries == RETRIES_COUNT) {
        // This is the first transfer error regarding this word
        first_transfer_in_progress--;
        retry_transfer_in_progress++;
        update_transfer_in_progress();
    };
    setTimeout(
        function() {
            update_word(data, retries - 1, next_timeout(timeout));
        }, timeout);
}

function update_word(data, retries, timeout)
{
    // first_transfer_in_progress should be incremented by the caller of this
    // function.

    if (retries != 0) {
        $.ajax({
            url: UPDATE_WORD_URL,
            dataType: 'json',
            data: data,
            type: 'post',
            timeout: timeout,
            success: function(result) {
                if (result == 'ok') {
                    // The server updated the word
                    transferred++;
                    $('#transferred').text(transferred);
                    if (retries == RETRIES_COUNT) {
                        first_transfer_in_progress--;
                    } else {
                        retry_transfer_in_progress--;
                    }
                    update_transfer_in_progress();
                } else {
                    // We got an error from the server
                    update_error(data, result, retries, timeout);
                }
            },
            error: function(result) {
                // We got an error; we may not have reached the server
                update_error(data, result, retries, timeout);
            }
        });
    } else {
        // We give up the transfer
        retry_transfer_in_progress--;
        update_transfer_in_progress();
    }
}

function yesno_button(answer) {
    state = 'intermediate';
    var old_word_index = word_index;
    var old_direction = direction;
    var old_answer = answer;
    first_transfer_in_progress++;
    ask_word();
    answered++;
    if (!answer) {
        answered_incorrectly++;
        $('#answered-incorrectly').text(answered_incorrectly);
    }
    $('#answered').text(answered);
    var data = {'answer': JSON.stringify(old_answer),
                'word_index': JSON.stringify(old_word_index),
                'direction': JSON.stringify(old_direction),
                'csrfmiddlewaretoken': csrf_token};
    update_word(data, RETRIES_COUNT, INITIAL_TIMEOUT);
}

function ew_keypress(e) {
    if (state == 'answer') {
        state = 'intermediate';
        answer_button();
    } else if (state == 'yesno') {
        if (e.which == 105 || e.which == 121) { 
            state = 'intermediate';
            yesno_button(true);
        } else if (e.which == 110) {
            state = 'intermediate';
            yesno_button(false);
        }
    }
}

$(document).ready(function() {

    // Event handlers
    $('#yes-button').click(function() { yesno_button(true); });
    $('#no-button').click(function() { yesno_button(false); });
    $('#ok-button').click(answer_button);
    $('body').keypress(ew_keypress);

    // The first word
    ask_first_word();
});
