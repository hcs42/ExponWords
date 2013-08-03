# Copyright (C) 2011-2013 Csaba Hoch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import math
import random
import re
import sys
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


version = '0.13.6'


##### Constants #####


# The maximum number of characters used to represent a word
WORD_PREFIX = 40;

# The minimum dimness required for a word to be practiced during "early
# practice". The dimness of 0.75 means that:
#
#     actual_interval_len = 0.75 * due_interval
#     due_interval2_len = 2 * actual_interval_len = 1.5 * due_interval_len
#
#     strength1 = 1 + log_2 due_interval_len
#     strength2 = 1 + log_2 due_interval2_len
#
# From these:
#
#     strength2 = 1 + log_2 1.5 * due_interval_len
#     strength2 = 1 + log_2 1.5 + log_2 due_interval_len
#     strength2 = 1 + log_2 due_interval_len + log_2 1.5
#     strength2 = strength1 + log_2 1.5
#     strength2 = strength1 + 0.5850
#
# General equasion:
#
#     log_2 2 * (MIN_DIMNESS_FOR_EARLY_PRACTICE) = strength_increment; i.e.
#     MIN_DIMNESS_FOR_EARLY_PRACTICE = (2 ^ strength_increment) / 2
MIN_DIMNESS_FOR_EARLY_PRACTICE = 0.75;


##### Utility functions #####


def unexpected_value(name, value):
    msg = 'Unexpected value for variable "%s": %s' % (name, value)
    raise EWException(msg)

def remove_trailing_newline(text):
    if (len(text) > 1) and (text[-1] == '\n'):
        text = text[:-1]
    return text

def escape_html(text):
    text = re.sub('&', '&amp;', text)
    text = re.sub('<', '&lt;', text)
    text = re.sub('>', '&gt;', text)
    return text

def indent_html(text, add_space_count):

    def insert_nbps(matchobject):
        """Returns the same number of "&nbsp;":s as the number of matched
        characters."""
        spaces = matchobject.group(1)
        space_count = len(spaces)
        space_count += add_space_count
        return '&nbsp;' * space_count

    regexp = re.compile(r'^( *)', re.MULTILINE)
    text = re.sub(regexp, insert_nbps, text)
    return text


def newline_to_br(text, keepend):
    if keepend:
        return re.sub(r'\n', '<br/>', text)
    else:
        return '<br/>'.join(text.splitlines())

class NotFound():
    pass

class TagNotAccepted():
    pass


def try_match(regexp, s, i):
    r = re.compile(regexp)
    m = r.match(s, i)
    if m:
        try:
            g = m.group(1)
        except IndexError:
            g = ''
        return m.end(0), g
    else:
        raise NotFound()


# List of tags from http://www.w3schools.com/tags/ref_byfunc.asp
ALLOWED_TAGS = [
    # Basic
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'p',
    'br',
    'hr',
    # Formatting
    'abbr',
    'b',
    'blockquote',
    'cite',
    'code',
    'em',
    'i',
    'pre',
    'q',
    'small',
    'strong',
    'sub',
    'sup',
    'u',
    # Images
    'img',
    # Links
    'a',
    # Lists
    'ul',
    'ol',
    'li',
    'dl',
    'dt',
    'dd',
    # Style/Sections
    'style',
    'div',
    'span',
    # Tables
    'table',
    'caption',
    'th',
    'tr',
    'td',
    'thead',
    'tbody',
    'tfoot',
    'col',
    'colgroup',
    ]
ALLOWED_TAGS_SET = set(ALLOWED_TAGS)


ALLOWED_ATTRIBUTES = [

    # Global attributes
    # http://www.w3schools.com/tags/ref_standardattributes.asp
    'class',
    'id',
    'lang',
    'style',
    'title',

    # <a>
    'href',
    'target',

    # <img>
    'alt',
    'height',
    'src',
    'width',

    # <table>
    'border',

    # <td>
    'colspan',
    'rowspan',
    'headers',
    ]

ALLOWED_ATTRIBUTES_SET = set(ALLOWED_ATTRIBUTES)


def simple_html_to_html(s, add_br, add_space_count):
    i = 0
    html_result = []
    s = remove_trailing_newline(s)
    while True:

        i, substr = try_match('([^<&]*)', s, i)
        text = escape_html(substr)
        if add_br:
            text = indent_html(text, add_space_count)
            text = newline_to_br(text, keepend=True)
        html_result.append(text)

        if i == len(s):
            break

        if s[i] == '&':
            html_result.append('&')
            i += 1
            continue

        # s[i] == '<'
        tag_start = i
        try:

            # Read the opening '<' or '</'
            i, _ = try_match(r'<\s*/?', s, i)

            # Read the tag name
            i, html_tag = try_match(r'\s*([^<>"\'= \t]+)\b', s, i)
            if html_tag not in ALLOWED_TAGS_SET:
                raise TagNotAccepted()

            try:
                while True:
                    i, html_attr = \
                        try_match(r'\s*([^<>"\'= \t]+)'     # src
                                  r'\s*=\s*'                # =
                                  r'(?:[^<>"\'= \t]+\b|'    # pic
                                  r'"[^"]*"|'               # 'pic.jpg'
                                  r'\'[^\']*\')',           # "pic.jpg"
                                  s, i)
                    if html_attr not in ALLOWED_ATTRIBUTES_SET:
                        raise TagNotAccepted()
            except NotFound:
                # We didn't find any more attributes
                pass

            # Read the closing '>' or '/>'
            i, _ = try_match(r'\s*/?>', s, i)

        except NotFound:
            # We didn't find a proper tag
            html_result.append('&lt;')
            i = tag_start + 1
        except TagNotAccepted:
            # We tag we found has a name or attribute that is not allowed
            html_result.append('&lt;')
            i = tag_start + 1
        else:
            html_result.append(s[tag_start:i])

    return ''.join(html_result)


def test_simple_html_to_html():

    def test(input, expected_output):
        actual_output = simple_html_to_html(input,
                                            add_br=False,
                                            add_space_count=0)
        if actual_output != expected_output:
            print 'Expected and actual output do not match:'
            print 'Input:          ', input
            print 'Expected output:', expected_output
            print 'Actual output:  ', actual_output
            print

    # Edge cases
    test('', '')
    test('<', '&lt;')
    test('>', '&gt;')
    test('a<a', 'a&lt;a')
    test('<br>', '<br>')
    test('< br >', '< br >')
    test('<br/>', '<br/>')
    test('<unknown>', '&lt;unknown&gt;')

    # Ampersand
    test('&amp;',
         '&amp;')

    # Different attribute value formats
    test('ab<a href=xy>b</a>',
         'ab<a href=xy>b</a>')
    test('ab<a href="xy \' z">b</a>',
         'ab<a href="xy \' z">b</a>')
    test('ab<a href=\'xy " z\'>b</a>',
         'ab<a href=\'xy " z\'>b</a>')

    # More complex examples
    test('<img src=xy title="hello world">',
         '<img src=xy title="hello world">')
    test('ab<img src=xy title="hello world">b',
         'ab<img src=xy title="hello world">b')
    test('<img src=xy title="hello world"><img src=xy title="hello world">',
         '<img src=xy title="hello world"><img src=xy title="hello world">')


##### Date handling #####


# General concept:
#
# words at DAY shall be asked
# if user_time(utc) >= DAY_00:00
# where user_time = now_utc + timezone - turning_point

# Example (DAY example in backets):
#
# timezone: UTC+2 (CEST) -> 2:00
# turning_point: 3:00
# words at 2011-01-10 shall be asked
# if user_time + 2:00 - 3:00 >= 2011-01-10_00:00
# if user_time >= 2011-01-10_01:00


def get_user_time(user=None, timezone=None, turning_point=None, now=None):

    # set timezone and turning_point
    if user is not None:
        ewuser = get_ewuser(user)
        timezone = ewuser.timezone
        turning_point = ewuser.turning_point
    elif (timezone is None or turning_point is None):
        raise EWException('get_user_time: Either the user or the timezone '
                          'and the turning_point parameter has to be not None')

    # set `now`
    if now is None:
        now = datetime.datetime.utcnow()

    return (now
            + datetime.timedelta(hours=timezone)
            - datetime.timedelta(minutes=turning_point))


def is_word_due(word_date, user_time):
    word_dt_0 = datetime.datetime(year=word_date.year,
                                  month=word_date.month,
                                  day=word_date.day)
    return user_time >= word_dt_0


def get_today(user=None, timezone=None, turning_point=None, now=None):
    user_time = get_user_time(user, timezone, turning_point, now)
    return datetime.date(user_time.year, user_time.month, user_time.day)


##### Word strengthener/weakener algorithms #####


def get_date_info(strength, due_date):
    due_interval = int(round(2 ** (strength - 1)))
    if due_interval > 36500: # ~100 years
        due_interval = 36500
    last_query_date = (due_date - datetime.timedelta(days=due_interval))
    return last_query_date, due_interval


def calc_strengthen_double_due(strength, due_date, today):
    if strength > 16: # 2**16 = ~179 years
        strength = 16
    new_due_interval_len = datetime.timedelta(2 ** max(strength, 0))
    strength2 = strength + 1
    date2 = today + new_due_interval_len
    return strength2, date2


def calc_strengthen_double_actual(strength, due_date, today):

    #######################################################################
    #     Number of days before the word
    #     is asked again (i.e. length of
    #     the next "due interval")
    #                   ^                 x
    #                   |                x
    # 2 ^ strength1     + . . . . . . . X (dimness = 1 at this point)
    #                   |              x.
    #                   |             x .
    #                   |            x  .
    #                   |           x   .
    #                   |          x    .
    #                 0 +---------X-----+----------> Day on which the
    #                             ^     ^            word is practiced
    #                last_query_date  due_date
    #
    #                             <----->
    #               (previous) due_interval =  "2 ^ (strength1 - 1)" days
    #######################################################################

    #######################################################################
    # Original strength-calculating function:
    #
    #       New strength of the
    #       word (strength2)
    #                 ^
    #                 |                                 xxxxxxxxxxxxxxxxxxx
    #  strength1 + 2  +                 xxxxxxxxxxxxxxxx
    #  strength1 + 1  + . . . . Xxxxxxxx
    #      strength1  + . . Xxxx.
    #                 |   xx.   .
    #                 |  x  .   .
    #               0 +-x---+---+----------------------------------------->
    #                   ^   ^   ^                         Day on which the
    #       last_query_date | due_date                    word is practiced
    #       dimness = 0     | dimness = 1
    #                       |
    #          half-way between last_query_date and due_date
    #          dimness = 0.5
    #
    #                   <------->
    #         (previous) due_interval =  "2 ^ (strength1 - 1)" days
    #######################################################################

    #######################################################################
    # Modified strength-calculating function (strength2 should not be
    # smaller than strength1):
    #
    #       New strength of the
    #       word (strength2)
    #                 ^
    #                 |                                 xxxxxxxxxxxxxxxxxxx
    #  strength1 + 2  +                 xxxxxxxxxxxxxxxx
    #  strength1 + 1  + . . . . Xxxxxxxx
    #      strength1  + xxxxXxxx.
    #                 |     .   .
    #                 |     .   .
    #               0 +-+---+---+----------------------------------------->
    #                   ^       ^                         Day on which the
    #       last_query_date   due_date                    word is practiced
    #
    #                   <------->
    #         (previous) due_interval =  "2 ^ (strength1 - 1)" days
    #######################################################################

    #######################################################################
    #
    # Calculating due_interval2_len:
    #
    #     actual_interval_len = day - last_query_date
    #     due_interval2_len = 2 * actual_interval_len
    #
    # Calculating strength2 (original):
    #
    #     due_interval2_len = 2 ^ (strength2 - 1)      // log_2 ^ ()
    #     log_2 due_interval2_len = (strength2 - 1)    // () + 1
    #     1 + log_2 due_interval2_len = strength2
    #     strength2 = 1 + log_2 due_interval2_len
    #
    # Calculating strength2 (modified):
    #
    #     strength2 = max(1 + log_2 due_interval2_len, strength1)
    #
    #######################################################################

    if strength <= 0:
        # if the word is new, ask tomorrow
        strength2 = strength + 1
        date2 = today + datetime.timedelta(days=1)
    else:
        last_query_date, due_interval_len = \
            get_date_info(strength, due_date)
        actual_interval_len = (today - last_query_date).days
        if due_interval_len <= 0:
            # if the word was already strengthened today, don't change
            # anything
            strength2 = strength
            date2 = due_date
        else:
            # otherwise use the nice equasion
            due_interval2_len = 2 * actual_interval_len
            strength2 = max(1 + math.log(due_interval2_len, 2), strength)
            date2 = today + datetime.timedelta(days=due_interval2_len)

    return strength2, date2


def calc_strengthen(strength, due_date, today, strengthener_method):
    if strengthener_method == 'double_due':
        return calc_strengthen_double_due(strength, due_date, today)
    else:
        return calc_strengthen_double_actual(strength, due_date, today)


def calc_weaken(strength, today):
    strength2 = min(strength, 0)
    date2 = today
    return strength2, date2


##### Model classes #####


class EWUser(models.Model):

    user = models.OneToOneField(User, primary_key=True)

    # The language of the user interface
    lang = models.CharField(max_length=10, default='en')

    # Time difference with UTC in hours (positive value means east from GMT)
    timezone = models.IntegerField(default=0)

    # How many minutes after midnight should we ask the words of the new day
    # (may be negative)
    turning_point = models.IntegerField(default=0)

    # Word order on practice page
    practice_word_order = models.CharField(default='random', max_length=20)
    strengthener_method = models.CharField(default='double_actual',
                                           max_length=20)

    # Practice page arrangement
    practice_arrangement = models.CharField(default='normal', max_length=20)
    pgupdown_behavior = models.CharField(default='normal', max_length=20)
    quick_labels = models.CharField(default='quick', max_length=255, blank=True)

    # Font sizes on the practice page
    button_size = models.IntegerField(default=35)
    question_size = models.IntegerField(default=20)
    answer_size = models.IntegerField(default=20)
    explanation_size = models.IntegerField(default=20)

    # List of available extra features
    extras = models.CharField(default='', max_length=255, blank=True)

    # Whether the user wants to receive emails about new ExponWords features
    release_emails = models.BooleanField(default=True)

    def __unicode__(self):
        return self.user.username

    def get_turning_point_str(self):
        sign = '-' if self.turning_point < 0 else ''
        tpa = abs(self.turning_point)
        return '%s%02d:%02d' % (sign, tpa / 60, tpa % 60)

    def set_turning_point_str(self, s):
        s = s.strip()
        r = re.match(r'^([+-]?)(\d+):(\d\d)$', s)
        if r is None:
            raise EWException('Invalid turning point string')
        sign, hours, minutes = r.group(1), int(r.group(2)), int(r.group(3))
        self.turning_point = ((-1 if sign == '-' else 1) *
                              (hours * 60 + minutes))

    def get_quick_labels(self):
        return unicode(self.quick_labels).split()

    @staticmethod
    def get_email_receiver_users():
        return [user
                for user in
                   (User.objects.filter(ewuser__release_emails=True).
                                 exclude(email='') |
                    User.objects.filter(ewuser=None).
                                 exclude(email=''))]


def get_ewuser(user):
    try:
        return EWUser.objects.get(pk=user)
    except EWUser.DoesNotExist, e:
        ewuser = EWUser(pk=user.pk)
        ewuser.save()
        return EWUser.objects.get(pk=user)


class WDict(models.Model):

    # WDict = word dictionary (as opposed to the dictionary data type which is
    # an "object dictionary")

    user = models.ForeignKey(User)
    name = models.CharField(max_length=255) # the name of the dictionary
    lang1 = models.CharField(max_length=255)
    lang2 = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)
    practice_word_order = models.CharField(default='default', max_length=20)
    strengthener_method = models.CharField(default='default', max_length=20)
    text_format = models.CharField(default='text', max_length=20)
    css = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    def get_words_to_practice_today(self, word_list_type='normal'):
        assert(word_list_type in ('normal', 'early'))
        user_time = get_user_time(user=self.user)
        today = get_today(self.user)
        result = []
        for wp in self.wordpair_set.filter(deleted=False):
            for direction in (1, 2):
                is_due = is_word_due(wp.get_date(direction), user_time)
                if word_list_type == 'normal':
                    is_needed = is_due
                else:
                    is_needed = (is_due or
                                 (wp.get_strength(direction) > 0 and
                                  wp.get_dimness(direction, today) >=
                                  MIN_DIMNESS_FOR_EARLY_PRACTICE))
                if is_needed:
                    result.append((wp, direction))
        return result

    def sort_words(self, words, order=None, word_list_type='normal'):
        # order = 'random' | 'zero_first' |
        #         ('dimness', dimness_day, dimness_direction)
        # dimness_day = 'today' | 'tomorrow'
        # dimness_direction = 'dimmer_first' | 'dimmer_last'

        # Converting `order` to the format given above
        if order is None:
            if word_list_type == 'normal':
                order = self.get_practice_word_order()
                if order in ('dimmer_first', 'dimmer_last'):
                    order = ('dimness', 'tomorrow', order)
            elif word_list_type == 'early':
                order = ('dimness', 'today', 'dimmer_first')
            else:
                unexpected_value('word_list_type', word_list_type)

        # Converting `order` to a string and possibly setting up other
        # variables
        if order in ('random', 'zero_first'):
            pass
        elif order[0] == 'dimness':
            order, dimness_day, dimness_direction = order
        else:
            unexpected_value('order', order)

        random.shuffle(words)
        if order == 'random':
            pass
        elif order in ('zero_first', 'dimness'):

            # Separating weak words (which should come first) and strong words
            # (which should come last)
            weak_words = [] # words with zero or negative strength
            strong_words = [] # words with positive strength
            for (wp, direction) in words:
                if wp.get_strength(direction) > 0:
                    strong_words.append((wp, direction))
                else:
                    weak_words.append((wp, direction))

            # Ordering the strong words by dimness
            if order == 'dimness':

                # First sort by strength
                def strength_key_fun((wp, direction)):
                    return wp.get_strength(direction)
                strong_words.sort(key=strength_key_fun)

                # Then sort by dimness
                if dimness_day == 'today':
                    dimness_day = get_today(self.user)
                elif dimness_day == 'tomorrow':
                    dimness_day = get_today(self.user) + \
                                      datetime.timedelta(days=1)
                else:
                    unexpected_value('dimness_day', dimness_day)

                def dimness_key_fun((wp, direction)):
                    return wp.get_dimness(direction, dimness_day)
                reverse = (dimness_direction == 'dimmer_first')
                strong_words.sort(key=dimness_key_fun, reverse=reverse)

            words[:] = weak_words + strong_words
        else:
            unexpected_value('order', order)

    def get_practice_word_order(self):
        if self.practice_word_order == 'default':
            return get_ewuser(self.user).practice_word_order
        else:
            return self.practice_word_order

    def get_strengthener_method(self):
        if self.strengthener_method == 'default':
            return get_ewuser(self.user).strengthener_method
        else:
            return self.strengthener_method

    def get_duplicates(self, wp):
        f = WordPair.objects.filter
        lang1_same = set(f(wdict=self,
                           word_in_lang1=wp.word_in_lang1,
                           deleted=False))
        lang1_same.discard(wp)
        lang2_same = set(f(wdict=self,
                           word_in_lang2=wp.word_in_lang2,
                           deleted=False))
        lang2_same.discard(wp)
        same_word_pairs = lang1_same & lang2_same
        similar_word_pairs = (lang1_same | lang2_same) - same_word_pairs
        return sorted(same_word_pairs), sorted(similar_word_pairs)

    def get_css(self):

        if self.css == 'text':
            return None
        else:
            # Replace <, otherwise the user could run any code in the browser with
            # the following CSS:
            #
            #     </style>
            #     CODE
            #     <style>
            #
            # On the other hand, > cannot be replaced, because then this would not
            # work:
            #     </style>
            #     .class1 > .class2
            #     <style>

            return re.sub('<', '&lt;', self.css)



class WordPair(models.Model):

    # each word pair belongs to a dictionary
    wdict = models.ForeignKey(WDict)

    # the word in the first/second language and notes:
    word_in_lang1 = models.TextField()
    word_in_lang2 = models.TextField()
    explanation = models.TextField(blank=True)

    # strengths of the word
    strength1 = models.FloatField(default=0)
    strength2 = models.FloatField(default=0)

    # dates of the next practice
    date_added = models.DateField()
    date1 = models.DateField()
    date2 = models.DateField()

    # labels
    labels = models.CharField(max_length=255, blank=True)

    # whether the word pair is deleted or not
    deleted = models.BooleanField(default=False)

    def save(self):
        self.normalize()
        return models.Model.save(self)

    def normalize(self):
        self.word_in_lang1 = self.word_in_lang1.strip()
        self.word_in_lang2 = self.word_in_lang2.strip()
        self.explanation = self.explanation.rstrip()
        self.normalize_labels()

    def get_html(self, field):

        add_space_count = (4 if field == 'explanation' else 0)

        if self.wdict.text_format == 'text':
            text = getattr(self, field)
            #text = remove_trailing_newline(text)
            text = escape_html(text)
            text = indent_html(text, add_space_count=add_space_count)
            text = newline_to_br(text, keepend=False)
            return text

        elif self.wdict.text_format == 'html':
            return simple_html_to_html(getattr(self, field),
                                       add_br=False,
                                       add_space_count=0)

        elif self.wdict.text_format == 'html_ws':
            return simple_html_to_html(getattr(self, field),
                                       add_br=True,
                                       add_space_count=0)

    def __unicode__(self):
        return ('<%s -- %s>' %
                (repr(self.word_in_lang1), repr(self.word_in_lang2)))

    def get_strength(self, direction):
        if direction == 1:
            return self.strength1
        else:
            return self.strength2

    def set_strength(self, direction, value):
        if direction == 1:
            self.strength1 = value
        else:
            self.strength2 = value

    def get_date(self, direction):
        if direction == 1:
            return self.date1
        else:
            return self.date2

    def set_date(self, direction, value):
        if direction == 1:
            self.date1 = value
        else:
            self.date2 = value

    def strengthen(self, direction, dry_run=False, day=None):
        if day is None:
            day = get_today(self.wdict.user)
        method = self.wdict.get_strengthener_method()
        date = self.get_date(direction)
        strength = self.get_strength(direction)

        strength2, date2 = calc_strengthen(strength, date, day, method)

        if not dry_run:
            self.set_strength(direction, strength2)
            self.set_date(direction, date2)

        return strength2, date2

    def weaken(self, direction, dry_run=False, day=None):
        if day is None:
            day = get_today(self.wdict.user)
        strength = self.get_strength(direction)
        strength2, date2 = calc_weaken(strength, day)

        if not dry_run:
            self.set_strength(direction, strength2)
            self.set_date(direction, date2)

        return strength2, date2

    def get_date_info(self, direction):
        due_date = self.get_date(direction)
        last_query_date, due_interval = \
            get_date_info(self.get_strength(direction), due_date)
        return last_query_date, due_date, due_interval

    def get_dimness(self, direction, day, silent=False):

        # The dimness function does not have a value when strength = 0.
        # (Mathematically, it would have the value of 0, but in ExponWords,
        # strength = 0 means is a special value meaning that the word
        # definitely needs practice, and 0 dimness would mean that it does not
        # need a practice.)
        #
        # The dimness function looks like this when strength > 0:
        #
        # dimness
        #   ^                 x
        #   |                x
        # 1 + . . . . . . . X
        #   |              x.
        #   |             x .
        #   |            x  .
        #   |           x   .
        #   |          x    .
        # 0 +---------X-----+----------> day
        #             ^     ^
        # last_query_date  due_date
        #
        #             <----->
        #          due_interval =  "2 ^ (strength - 1)" days

        strength = self.get_strength(direction)
        if silent and strength == 0:
            return None
        assert(strength > 0)

        last_query_date, due_date, due_interval = self.get_date_info(direction)
        return float((day - last_query_date).days) / due_interval

    @staticmethod
    def get_label_set_from_str(s):
        return set(unicode(s).split())

    def get_label_set(self):
        return self.get_label_set_from_str(self.labels)

    def set_label_set(self, label_set):
        self.labels = ' '.join(sorted(label_set))

    def normalize_labels(self):
        self.set_label_set(self.get_label_set())

    def add_labels(self, labels):
        self.set_label_set(self.get_label_set() |
                           self.get_label_set_from_str(labels))

    def remove_labels(self, labels):
        self.set_label_set(self.get_label_set() -
                           self.get_label_set_from_str(labels))

    def set_labels(self, labels):
        self.set_label_set(self.get_label_set_from_str(labels))

    @staticmethod
    def get_simple_fields():
        return ('word_in_lang1',
                'word_in_lang2',
                'explanation')

    @staticmethod
    def get_advanced_fields():
        return ('labels',
                'date_added',
                'date1',
                'date2',
                'strength1',
                'strength2')

    @staticmethod
    # fields_to_be_edited = simple_fields + advanced_fields
    def get_fields_to_be_edited():
        return ('word_in_lang1',
                'word_in_lang2',
                'explanation',
                'labels',
                'date_added',
                'date1',
                'date2',
                'strength1',
                'strength2')

    @staticmethod
    # Get the list of fields whose value should be saved when adding a word
    # pair, and reused when another word pair is added
    def get_fields_to_be_saved():
        return ('labels',
                'date1',
                'date2',
                'strength1',
                'strength2')

    def get_saved_fields(self):
        saved_fields = {}
        for field in self.get_fields_to_be_saved():
            saved_fields[field] = getattr(self, field)
        return saved_fields

    @staticmethod
    def prefix(s, max_length):
        if len(s) <= max_length:
            return s
        else:
            return s[:max_length - 3] + '...'

    def get_short_repr(self):
        return (self.prefix(self.word_in_lang1, WORD_PREFIX) +
                ' / ' +
                self.prefix(self.word_in_lang2, WORD_PREFIX))


##### Importing and exporting word pairs #####


def create_add_word_pairs(wdict, word_pairs):
    for wp in word_pairs:
        wdict.wordpair_set.add(wp)
        wp.save()
        wdict.save()


def import_textfile(s, wdict):
    """Adds words from a text file to a dictionary.

    Arguments:
    - s (str)
    - wdict (WDict)
    """

    user = wdict.user
    i = 1
    word_pairs = []
    for line in s.splitlines():
        line = line.rstrip()
        if (line == '') or (line[0] == ' '):
            # This line is part of an explanation.
            if len(word_pairs) != 0:
                line = re.sub('^ {1,4}', '', line) # removing prefix spaces
                word_pairs[-1].explanation += line + '\n'
            elif line == '':
                pass
            else:
                msg = (_('Line %(linenumber)s should not have spaces in '
                         'the beginning: %(line)s') %
                       {'linenumber': i, 'line': line})
                raise EWException(msg)
        else:
            # This line contains a word pair.
            strength_date_regexp = '<(-?\d+) +(\d\d\d\d)-(\d\d)-(\d\d)>'
            regexp = (r'^(\{(\d+)\})? *(.*?) -- (.*?)' +
                      '( ' + strength_date_regexp * 2 + ')?' +
                      '$')
            r = re.search(regexp, line)
            if r is None:
                msg = (_('Line %(linenumber)s is incorrect: %(line)s') %
                       {'linenumber': i, 'line': line})
                raise EWException(msg)

            wp = WordPair()
            word_pairs.append(wp)

            wp.word_in_lang1 = r.group(3)
            wp.word_in_lang2 = r.group(4)
            wp.explanation = ''
            if r.group(5) is not None:
                wp.date_added = get_today(user)
                wp.date1 = datetime.date(int(r.group(7)),
                                         int(r.group(8)),
                                         int(r.group(9)))
                wp.date2 = datetime.date(int(r.group(11)),
                                         int(r.group(12)),
                                         int(r.group(13)))
                wp.strength1 = int(r.group(6))
                wp.strength2 = int(r.group(10))
            else:
                wp.date_added = get_today(user)
                wp.date1 = get_today(user)
                wp.date2 = get_today(user)
                wp.strength1 = 0
                wp.strength2 = 0

        i += 1

    create_add_word_pairs(wdict, word_pairs)
    return word_pairs


def import_tsv(s, wdict):
    """Adds words from a text of tab-separeted values to a dictionary.

    Arguments:
    - s (str)
    - wdict (WDict)
    """

    user = wdict.user
    i = 1
    word_pairs = []
    for line in s.splitlines():
        line = line.strip()
        if (line == ''):
            continue

        fields = line.split('\t')
        if len(fields) < 2:
            msg = (_('Not enough fields in line %(linenumber)s: %(line)s') %
                   {'linenumber': i, 'line': line})
            raise EWException(msg)
        elif 2 <= len(fields) <= 3:
            wp = WordPair()
            wp.word_in_lang1 = fields[0]
            wp.word_in_lang2 = fields[1]
            if len(fields) == 3:
                wp.explanation = fields[2]
            wp.date1 = get_today(user)
            wp.date2 = get_today(user)
            wp.date_added = get_today(user)
            word_pairs.append(wp)
        else:
            msg = (_('Too many fields in line %(linenumber)s: %(line)s') %
                   {'linenumber': i, 'line': line})
            raise EWException(msg)

        i += 1

    create_add_word_pairs(wdict, word_pairs)
    return word_pairs


def export_textfile(wdict=None, word_pairs=None):
    """Prints a dictionary in the old text format.

    Arguments:
    - wdict (WDict)

    Returns: str
    """

    if wdict is None and word_pairs is None:
        raise EWException('export_textfile: Either the wdict or the word_pairs '
                          'parameter has to be not None')
    elif wdict is not None:
        word_pairs = wdict.wordpair_set.filter(deleted=False)

    result = []
    for wp in word_pairs:
        result.append(
            '%s -- %s <%s %s><%s %s>\n' %
            (wp.word_in_lang1.replace('\n', ' ').replace('\r', ' '),
             wp.word_in_lang2.replace('\n', ' ').replace('\r', ' '),
             str(wp.strength1),
             str(wp.date1),
             str(wp.strength2),
             str(wp.date2)))
        for expl_line in wp.explanation.splitlines():
            if expl_line != '':
                result.append('    ')
                result.append(expl_line)
            result.append('\n')
    return ''.join(result)


##### Logging #####


class EWLogEntry(models.Model):

    datetime = models.DateTimeField()
    action = models.TextField()
    user = models.ForeignKey(User, blank=True, null=True)
    username = models.TextField(blank=True)
    text = models.TextField(blank=True)
    ipaddress = models.TextField(blank=True)

    def __unicode__(self):
        return ('%s <%s> %s | %s' %
                (self.datetime.strftime('%Y-%m-%d %H-%M-%S'), self.username,
                 self.action, self.text))


def log(request, action, text=''):

    logentry = EWLogEntry()
    logentry.datetime = datetime.datetime.now()
    try:
        logentry.action = action
        logentry.ipaddress = (request.META.get('REMOTE_ADDR' , '') + ', ' +
                              request.META.get('HTTP_X_FORWARDED_FOR', ''))
        if request.user.is_authenticated():
            logentry.user = request.user
            logentry.username = request.user.username

        logentry.text = text
    except Exception, e:
        logentry.action = 'Logging failed'
    logentry.save()


##### Announcing releases #####

class Announcement(models.Model):

    lang = models.CharField(max_length=10, primary_key=True)
    text = models.TextField()

    def __unicode__(self):
        return self.lang + ' | ' + self.text.splitlines()[0]


##### Show the future #####


def incr_wcd(wcd, wdict, strength, due_date, ask_date, count):
    strength_to_word_count = wcd.setdefault((wdict, ask_date), {})
    key = (strength, due_date)
    try:
        strength_to_word_count[key] += count
    except KeyError:
        strength_to_word_count[key] = count

def get_initial_word_counts_dict(user, start_date):
    """
    Returns: wdicts, {(wdict, date): {(strength, due_date): word_count}}
    """

    def add_wp(wcd, wdict, strength, due_date):
        if (start_date is not None) and (due_date < start_date):
            ask_date = start_date
        else:
            ask_date = due_date
        incr_wcd(wcd, wdict, strength, due_date, ask_date, 1)

    wcd = {}
    wdicts = WDict.objects.filter(user=user, deleted=False)
    for wdict in wdicts:
        word_pairs = WordPair.objects.filter(wdict=wdict,
                                             deleted=False)
        for wp in word_pairs:
            add_wp(wcd, wdict, wp.strength1, wp.date1)
            add_wp(wcd, wdict, wp.strength2, wp.date2)
    return wdicts, wcd


def calc_future(user, days_count, start_date):
    """
    Returns: [date], [WDict], {(WDict, date): question_count}
    """

    dates = [start_date + datetime.timedelta(i)
             for i in range(days_count)]

    wdicts, wcd = get_initial_word_counts_dict(user, start_date)

    date_to_question_count = {} # {(wdict, date): question_count}
    for date in dates:
        for wdict in wdicts:
            strength_to_word_count = wcd.pop((wdict, date), {})
            strengthener_method = wdict.get_strengthener_method()
            question_count = 0
            for key, word_count in strength_to_word_count.items():
                (strength, due_date) = key
                question_count += word_count
                strength2, date2 = \
                    calc_strengthen(strength, due_date, date,
                                    strengthener_method)
                incr_wcd(wcd, wdict, strength2, date2, date2, word_count)
            date_to_question_count[(wdict, date)] = question_count

    return dates, wdicts, date_to_question_count


##### Miscellaneous utilities #####


class EWException(Exception):
    """A very simple exception class used."""

    def __init__(self, value):
        """Constructor.

        **Argument:**

        - `value` (object) -- The reason of the error.
        """
        Exception.__init__(self)
        self.value = value

    def __unicode__(self):
        """Returns the string representation of the error reason.

        **Returns:** str
        """

        value = self.value
        if isinstance(value, unicode):
            return value
        elif isinstance(value, str):
            return unicode(value)
        else:
            return repr(value)

    def __str__(self):
        return self.__unicode__()


def get_labels(user):
    all_word_pairs = WordPair.objects.filter(wdict__user=user,
                                             wdict__deleted=False,
                                             deleted=False)
    labels = set()
    for wp in all_word_pairs:
        labels.update(unicode(wp.labels).split())
    return labels


def parse_date(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d')
