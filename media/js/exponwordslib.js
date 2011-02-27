// Translation of the user interface
var tr_dict;

function tr(original) {
    if (original in tr_dict) {
        return tr_dict[original];
    } else {
        return original;
    }
}

function translate_node_text(node)
{
    node.text(tr(node.text()));
}

function get_translation(callback) {

    // Get the translation and call the callback function that will translate
    // the UI
    $.ajax({
        url: '/get_translation',
        dataType: 'json',
        data: {},
        type: 'post',
        success: function(result) {
            tr_dict = result;
            callback();
        }
    });
}
