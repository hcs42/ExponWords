// Copyright (C) 2011- Csaba Hoch
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

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

function operation_selection_changed() {
    var value = $('#operation-selection').val();
    var spans = $('div[id^="span-"]');
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
    $('#operation-selection').change(operation_selection_changed);

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
