// Constants
RETRIES_COUNT = 24;
RETRY_DELAY_TIME = 10 * 1000; // 10 seconds

// Global state
var todays_wordlist;
var transferred = 0;
var transfer_in_progress = 0;
var answered = 0;
var answered_incorrectly = 0;

// Details of the current word
var word;
var word_index;
var direction;
var question_word;
var solution_word;
var explanation;

function get_todays_wordlist() {
    // Get the list of today's word from the server and ask the first one.
    $.ajax({
        url: '../words-to-practice-today/',
        dataType: 'json',
        data: {'csrfmiddlewaretoken': csrf_token},
        type: 'post',
        success: function(result) {
            todays_wordlist = result;
            $('#all').text(todays_wordlist.length);
            $('#transferred').text('0');
            $('#transfer-in-progress').text('0');
            $('#answered').text('0');
            $('#answered-incorrectly').text('0');
            ask_word();
        }
    });
}

function ask_word() {
    if (todays_wordlist.length == 0) {
        $('#main').text('NO_MORE_FOR_TODAY');
    } else {
        show_ok_button();
        word = todays_wordlist[0];
        direction = word[2];
        question_word = word[direction - 1];
        solution_word = word[2 - direction];
        word_index = word[3];
        explanation = word[4];
        $('#question').text(question_word);
        $('#answer').text('');
        $('#explanation').text('');
        var edit_link = '/edit-word?word_index=' + word_index;
        $('#edit-word-button').attr('href', edit_link);
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

function update_error(data, result, retries)
{
    if (retries == RETRIES_COUNT) {
        transfer_in_progress++;
        $('#transfer-in-progress').text(transfer_in_progress);
    };
    setTimeout(
        function() {
            update_word(data, retries - 1);
        }, RETRY_DELAY_TIME);
}

function update_word(data, retries)
{
    if (retries != 0) {
        $.ajax({
            url: '../update-word/',
            dataType: 'json',
            data: data,
            type: 'post',
            timeout: 2000,
            success: function(result) {
                if (result == 'ok') {
                    transferred++;
                    $('#transferred').text(transferred);
                    if (retries != RETRIES_COUNT) {
                        transfer_in_progress--;
                        $('#transfer-in-progress').text(transfer_in_progress);
                    }
                } else {
                    update_error(data, result, retries);
                }
            },
            error: function(result) {
                update_error(data, result, retries);
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
    update_word(data, RETRIES_COUNT);
}

$(document).ready(function() {

    // Event handlers
    $('#yes-button').click(function() { yesno_button(true); });
    $('#no-button').click(function() { yesno_button(false); });
    $('#ok-button').click(ok_button);

    // The first word
    get_todays_wordlist();
});
