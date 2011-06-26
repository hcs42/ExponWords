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

var all_selected = false;
var select_all_text;
var select_none_text;

function select_all() {
    var checkboxes = $('#table input[type=checkbox]');
    if (all_selected) {
        // Select none
        checkboxes.attr('checked', false);
        all_selected = false;
        $('#select-all-button').text(select_all_text);
    } else {
        // Select all
        checkboxes.attr('checked', true);
        all_selected = true;
        $('#select-all-button').text(select_none_text);
    }
}

$(document).ready(function() {

    // Event handlers
    $('#select-all-button').click(select_all);

    select_all_text = $("#select-all-button").text();
    select_none_text = $("#translation-select-none").text();
});
