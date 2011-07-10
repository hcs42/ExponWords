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


// Constants
var RETRIES_COUNT = 24;
var INITIAL_TIMEOUT = 3 * 1000; // 3 seconds
var TIMEOUT_INTERVAL = 3 * 1000; // 3 second
var MAX_TIMEOUT = 20 * 1000; // 20 seconds

// Global state
var todays_wordlist;
var transferred = 0;
var transfer_in_progress = 0;
var answered = 0;
var answered_incorrectly = 0;

// Details of the current word
var word;
var word_index = false;
var direction;
var question_word;
var solution_word;
var explanation;

var prev_word_index = false;

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

        prev_word_index = word_index;
        word_index = false;

        $('#buttons').text($('#translation_no_more_words').text());
        $('#question').hide();
        $('#answer').hide();
        $('#explanation').hide();

        update_edit_words();

    } else {

        show_ok_button();
        word = todays_wordlist[0];
        direction = word[2];
        question_word = word[direction - 1];
        solution_word = word[2 - direction];
        prev_word_index = word_index;
        word_index = word[3];
        explanation = word[4];
        $('#question').text(question_word);
        $('#answer').text('');
        $('#explanation').text('');
        update_edit_words();

        todays_wordlist.shift();
    }
}

function show_ok_button() {
    $('#ok-button').show();
    $('#yes-button').hide();
    $('#no-button').hide();
}

function show_yesno_buttons() {
    $('#ok-button').hide();
    $('#yes-button').show();
    $('#no-button').show();
}

function ok_button() {
    $('#answer').text(solution_word);
    $('#explanation').html(explanation);
    show_yesno_buttons();
}

function next_timeout(timeout) {
    var maybe_next_timeout = timeout + TIMEOUT_INTERVAL;
    if (maybe_next_timeout > MAX_TIMEOUT) {
        return timeout;
    } else {
        return maybe_next_timeout;
    }
}

function update_error(data, result, retries, timeout)
{
    if (retries == RETRIES_COUNT) {
        transfer_in_progress++;
        $('#transfer-in-progress').text(transfer_in_progress);
    };
    setTimeout(
        function() {
            update_word(data, retries - 1, next_timeout(timeout));
        }, timeout);
}

function update_word(data, retries, timeout)
{
    if (retries != 0) {
        $.ajax({
            url: UPDATE_WORD_URL,
            dataType: 'json',
            data: data,
            type: 'post',
            timeout: timeout,
            success: function(result) {
                if (result == 'ok') {
                    transferred++;
                    $('#transferred').text(transferred);
                    if (retries != RETRIES_COUNT) {
                        transfer_in_progress--;
                        $('#transfer-in-progress').text(transfer_in_progress);
                    }
                } else {
                    update_error(data, result, retries, timeout);
                }
            },
            error: function(result) {
                update_error(data, result, retries, timeout);
            }
        });
    } else {
        transfer_in_progress--;
        $('#transfer-in-progress').text(transfer_in_progress);
    }
}

function yesno_button(answer) {
    var old_word_index = word_index;
    var old_direction = direction;
    var old_answer = answer;
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

$(document).ready(function() {

    // Event handlers
    $('#yes-button').click(function() { yesno_button(true); });
    $('#no-button').click(function() { yesno_button(false); });
    $('#ok-button').click(ok_button);

    // The first word
    ask_first_word();
});
