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
    if (all_selected) {
        // Select none
        $('#hits :checkbox').attr('checked', false);
        $('#hits tr').filter(':has(:checkbox)').removeClass('selected');
        $('#select-all-button').text(select_all_text);
        all_selected = false;
    } else {
        // Select all
        $('#hits :checkbox').attr('checked', true);
        $('#hits tr').filter(':has(:checkbox)').addClass('selected');
        $('#select-all-button').text(select_none_text);
        all_selected = true;
    }
}

function action_selection_changed() {
    var value = $('#action-selection').val();
    var spans = $('span[id^="span-"]');
    $.each(spans, function() {
        if ($(this).attr('id') == 'span-' + value) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

$(document).ready(function() {

    // Event handlers
    $('#select-all-button').click(select_all);
    $('#action-selection').change(action_selection_changed);

    select_all_text = $("#select-all-button").text();
    select_none_text = $("#translation-select-none").text();

    // The following code is based on: http://www.learningjquery.com/2008/12/quick-tip-click-table-row-to-trigger-a-checkbox-click
    $('#hits tr')
    .filter(':has(:checkbox:checked)')
    .addClass('selected')
    .end()
    .click(function(e) {
        // Don't do anything if the user clicked on a link a cell.
        if (!$(e.target).is('a')) {
            if (e.target.type === 'checkbox') {
                $(this).toggleClass('selected');
            } else {
                $(':checkbox', this).trigger('click');
            }
        }
    });
});
