$(document).ready(function() {
    get_translation(function() {
        // Translate the UI
        translate_node_text($('#lang1-label'));
        translate_node_text($('#lang2-label'));
        translate_node_text($('#explanation-label'));
    });
});
