var todays_wordlist;
var transferred = 0;
var answered = 0;

// Details of the current word
var word;
var direction;
var question_word;
var solution_word;
var explanation;

function get_todays_wordlist() {
    // Get the list of today's word from the server and ask the first one.
    $.ajax({
        url: '/get_todays_wordlist',
        dataType: 'json',
        data: {},
        type: 'post',
        success: function(result) {
            todays_wordlist = result;
            $('#all').text(todays_wordlist.length);
            ask_word();
        }
    });
}

function ask_word() {
    if (todays_wordlist.length == 0) {
        $('#main').text('No more words for today. Good job!');
    } else {
        show_ok_button();
        word = todays_wordlist[0];
        direction = word[2];
        question_word = word[direction]
        solution_word = word[1 - direction]
        explanation = word[3];
        $('#question').text(question_word);
        $('#answer').text('');
        $('#explanation').text('');
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
    $('#explanation').text(explanation);
    show_yesno_buttons();
}

function yesno_button(answer) {
    answered++;
    $('#answered').text(answered);
    ask_word();
    $.ajax({
        url: '/update_word',
        dataType: 'json',
        data: {'answer': JSON.stringify(answer)},
        type: 'post',
        success: function(result) {
            if (result == 'ok') {
                transferred++;
                $('#transferred').text(transferred);
            } else {
                // Appending an '!'
                $('#transferred-exc').text($('#transferred-exc').text() + '!');
            }
        }
    });
}

$(document).ready(function() {
    $('#yes-button').click(function() { yesno_button(true); });
    $('#no-button').click(function() { yesno_button(false); });
    $('#ok-button').click(ok_button);
    get_todays_wordlist();
});
