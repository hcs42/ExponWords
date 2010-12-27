$(document).ready(function() {
    get_translation(function() {
        // Translate the UI
        translate_node_text($('#password-label'));
    });
});
