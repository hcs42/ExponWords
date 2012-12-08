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
