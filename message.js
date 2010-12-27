$(document).ready(function() {
    get_translation(function() {
        // Translate the UI
        translate_node_text($('#message'));
        translate_node_text($('#index-page'));
    });
});
