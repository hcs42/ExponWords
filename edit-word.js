var word_index;

$(document).ready(function() {

    word_index = $('#word_index_input').val();
    $.ajax({
        url: '/get_word',
        dataType: 'json',
        data: {'word_index': JSON.stringify(word_index)},
        type: 'post',
        success: function(result) {
            if (result == 'nosuchword') {
                window.alert('No word with such index: ' + word_index);
            } else {
                var lang1 = result[0];
                var lang2 = result[1];
                var explanation = result[2];
                $('#lang1-input').val(lang1);
                $('#lang2-input').val(lang2);
                $('#explanation-input').text(explanation);
            }
        }
    });
});
