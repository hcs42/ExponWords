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

// Copyright (C) 2011-2012 Csaba Hoch


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

// Returns the current date in yyyy-mm-dd format
function get_now_date() {
    var now = new Date();
    y = now.getFullYear();
    m = now.getMonth() + 1;
    d = now.getDate();
    if (d < 10) { d = '0' + d; }
    if (m < 10) { m = '0' + m; }
    return y + '-' + m + '-' + d;
}
