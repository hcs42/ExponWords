// Copyright (C) 2011-2013 Csaba Hoch
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

// 'simple' or 'advanced'
display_mode = 'simple';

// 'basic' when the page is loaded; 'confirmation_needed' when the user pressed
// the "Delete word pair" button
delete_state = 'basic';

function advanced_button_click() {
    $('.advanced').show();
    display_mode = 'advanced';
    $('#id_display_mode').attr('value', display_mode);
    $('#advanced_button').hide();
    $('#simple_button').show();
}

function simple_button_click() {
    $('.advanced').hide();
    display_mode = 'simple';
    $('#id_display_mode').attr('value', display_mode);
    $('#advanced_button').show();
    $('#simple_button').hide();
}

function reset_button_click() {
    var today_str = get_now_date();
    if ($(this).attr('id') == 'reset1_button') {
        $('#id_date1').attr('value', today_str);
        $('#id_strength1').attr('value', '0');
    } else if ($(this).attr('id') == 'reset2_button') {
        $('#id_date2').attr('value', today_str);
        $('#id_strength2').attr('value', '0');
    }
}

function delete_button_1_click() {
    delete_state = 'delete_button_1_clicked';
    $('#delete_button_1').hide();
    $('#delete_confirm').show();
}

function delete_button_yes_click() {
    delete_state = 'delete_button_yes_clicked';
}

function delete_button_cancel_click() {
    delete_state = 'delete_button_cancel_clicked';
    $('#delete_button_1').show();
    $('#delete_confirm').hide();
}

function delete_submit() {
    if (delete_state == 'delete_button_1_clicked') {
        return false;
        delete_state = 'confirmation_needed';
    } else if (delete_state == 'delete_button_cancel_clicked') {
        return false;
        delete_state = 'basic';
    } else if (delete_state == 'delete_button_yes_clicked') {
        return true;
    } else {// delete_state == basic or confirmation_needed
        // The "Save" button was pressed
        return true;
    }
}

$(document).ready(function() {

    $('#advanced_button').click(advanced_button_click);
    $('#simple_button').click(simple_button_click);
    $('#reset1_button').click(reset_button_click);
    $('#reset2_button').click(reset_button_click);
    $('#delete_button_1').click(delete_button_1_click);
    $('#delete_button_yes').click(delete_button_yes_click);
    $('#delete_button_cancel').click(delete_button_cancel_click);
    $('form').submit(delete_submit);
    //$('.advanced').hide();
});
