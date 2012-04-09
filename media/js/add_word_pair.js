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

display_mode = 'simple'; // simple or advanced

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

$(document).ready(function() {

    $('#advanced_button').click(advanced_button_click);
    $('#simple_button').click(simple_button_click);
    $('#reset1_button').click(reset_button_click);
    $('#reset2_button').click(reset_button_click);
    //$('.advanced').hide();
});
