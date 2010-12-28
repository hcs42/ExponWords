#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import random
import datetime
import optparse
import json
import web
import exponwords_ss
import StringIO
import time


##### getch #####

# Original source of this code: http://code.activestate.com/recipes/134892/

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()


##### Utilities #####

def file_to_string(file_name, return_none=False):
    """Reads a file's content into a string.

    Arguments:
    - file_name (str) -- Path to the file.
    - return_none (bool) -- Specifies what to do if the file does not exist.
      If `return_none` is ``True``, ``None`` will be returned. Otherwise an
      `IOError` exception will be raised.

    **Returns:** str | ``None``
    """

    if return_none and not os.path.exists(file_name):
        return None
    with open(file_name, 'r') as f:
        s = f.read()
    return s


def escape_html(text):
    """Escapes the given text so that it will appear correctly when
    inserted into HTML.

    **Argument:**

    - `text` (str)

    **Returns:** str

    **Example:** ::

        >>> escape_html('<text>')
        '&lt;text&gt;'
    """

    def escape_char(matchobject):
        """Escapes one character based on a match."""
        whole = matchobject.group(0)
        if whole == '<':
            return '&lt;'
        elif whole == '>':
            return '&gt;'
        elif whole == '&':
            return '&amp;'

    return re.sub(r'[<>&]', escape_char, text)


##### Word, WordList #####


class Word(object):

    """Represents a word pair.

    Data attributes:
    - langs ([str]) -- langs[0] is the form of the word in the first language;
      langs[1] is the form of the word in the second language.
    - strengths ([int]) -- strengths[i] is the strengths of the word in
      language i (i is either 0 or 1).
    - dates ([date]) -- dates[0] is the date when the user should be ask to
      translate largs[0] to langs[1]. dates[1] is the date for the opposite
      direction.
    - explanation (str) -- The explanation and/or examples that belong to this
      word pair.
    """

    def __repr__(self):
        return ('<%s -- %s, Expl: %s>' %
                (repr(self.langs[0]), repr(self.langs[1]), repr(self.explanation)))


class WordList(object):

    def __init__(self):
        self.list = []
        self.langs = ['', '']


def words_from_file(dict_file_name):
    """Reads a word list from a file.

    Argument:
    - dict_file_name (str)

    Returns: WordList | None
    """

    file = open(dict_file_name, 'r')
    wordlist = WordList()
    i = 0
    for line in file:
        line = line.rstrip()
        if line == '':
            pass
        elif line[0] == ' ':
            if len(wordlist.list) > 0:
                wordlist.list[-1].explanation += line + '\n'
        elif line.startswith('CONFIG:'):
            regexp = '^CONFIG: (.*?)=(.*)$'
            r = re.search(regexp, line)
            if r is None:
                print 'ERROR: Line %s is incorrect: %s' % (i, line)
                return None
            key = r.group(1)
            value = r.group(2)
            if key == 'lang1':
                wordlist.langs[0] = value
            elif key == 'lang2':
                wordlist.langs[1] = value
            else:
                print ('ERROR: Unknown configuration key at line %s: %s' %
                       (i, key))
                return None
        else:
            strength_date_regexp = '<(\d+) +(\d\d\d\d)-(\d\d)-(\d\d)>'
            regexp = ('^(.*?) -- (.*?)' +
                      '( ' + strength_date_regexp * 2 + ')?' +
                      '$')
            r = re.search(regexp, line)
            if r is None:
                print 'ERROR: Line %s is incorrect: %s' % (i, line)
                return None

            word = Word()
            word.langs = [r.group(1), r.group(2)]
            if r.group(3) is not None:
                word.strengths = [int(r.group(4)), int(r.group(8))]
                word.dates = [datetime.date(int(r.group(5)),
                                           int(r.group(6)),
                                           int(r.group(7))),
                              datetime.date(int(r.group(9)),
                                           int(r.group(10)),
                                           int(r.group(11)))]
            else:
                word.strengths = [0, 0]
                word.dates = [datetime.date.today(), datetime.date.today()]
            word.explanation = ''
            wordlist.list.append(word)
        i += 1
    file.close()
    return wordlist


def write_words(wordlist, file):
    """Writes the word list to a file object.

    Arguments:
    - words (WordList)
    - file (file_object())
    """

    file.write('CONFIG: lang1=%s\n' % wordlist.langs[0])
    file.write('CONFIG: lang2=%s\n' % wordlist.langs[1])
    for word in wordlist.list:
        file.write(
            '%s -- %s <%s %s><%s %s>\n%s' %
            (word.langs[0],
             word.langs[1],
             str(word.strengths[0]),
             str(word.dates[0]),
             str(word.strengths[1]),
             str(word.dates[1]),
             word.explanation))

def words_to_file(wordlist, dict_file_name):
    """Writes the word list to a file.

    Arguments:
    - words (WordList)
    - dict_file_name (str)
    """

    file = open(dict_file_name, 'w')
    write_words(wordlist, file)
    file.close()

def words_to_str(wordlist):
    """Writes the word list to a file.

    Argument:
    - words (WordList)

    Return: str
    """

    sio = StringIO.StringIO()
    write_words(wordlist, sio)
    result = sio.getvalue()
    sio.close()
    return result

def ask_word(word, direction, wordlist, use_getch=False, use_color=False):
    """Asks a word from the user via the console.

    Arguments:
    - word (Word)
    - direction (int) -- 0 or 1.
    - use_getch (bool)

    Returns: bool | 'quit'
    """

    from_lang = wordlist.langs[direction]
    question_word = word.langs[direction]
    solution_word = word.langs[1 - direction]

    sys.stdout.write('Word in %s: %s -- ' % (from_lang, question_word))
    if use_getch:
        ch = getch()
    else:
        ch = sys.stdin.readline().strip()

    if ch == 'q':
        return 'quit'

    if use_color:
        CSI="\x1B["
        print CSI+"1;34m" + solution_word + CSI + "0m"
    else:
        print solution_word

    sys.stdout.write(word.explanation)

    while True:
        sys.stdout.write('Did you know this word? [y/n/q]')
        if use_getch:
            ch = getch()
        else:
            ch = sys.stdin.readline().strip()
        sys.stdout.write('\n\n')

        if ch == 'q':
            return 'quit'
        elif ch == 'y':
            return True
        elif ch == 'n':
            return False


def next_date(strength, date):
    return date + datetime.timedelta(2 ** strength)


def calc_words_to_do(wordlist):
    today = datetime.date.today()
    words_to_do = []
    for word in wordlist.list:
        for direction in [0, 1]:
            if word.dates[direction] <= today:
                words_to_do.append((word, direction))
    random.shuffle(words_to_do)
    return words_to_do


def update_word(word, direction, answer):
    assert(isinstance(answer, bool))
    today = datetime.date.today()
    strength = word.strengths[direction]
    if answer:
        # The user knew the answer
        word.strengths[direction] += 1
        word.dates[direction] = next_date(strength, today)
    else:
        # The user did not know the answer
        word.strengths[direction] = 0
        word.dates[direction] = today


def practice_words(wordlist, use_getch=False, use_color=False):
    """Practice the words that need to be asked.

    Argument:
    - wordlist (WordList)
    - use_getch (bool)
    """

    words_to_do = calc_words_to_do(wordlist)
    print 'Total number of words: %s' % (len(wordlist.list) * 2)
    print 'Words to ask now: %s' % (len(words_to_do))

    i = 0
    for word, direction in words_to_do:
        i += 1
        strength = word.strengths[direction]
        sys.stdout.write('%s/%s <%s>: ' % (len(words_to_do), i, strength))

        answer = ask_word(word, direction, wordlist, use_getch, use_color)
        if answer == 'quit':
            print
            break
        else:
            update_word(word, direction, answer)


# def inc_wd(wd,date,strength,n):
#     if date not in wd:
#         wd[date] = {strength: n}
#     elif strength not in wd[date]:
#         wd[date][strength] = n
#     else:
#         wd[date][strength] += n
#
# def print_future(words,days):
#     wd = {} # word dictionary: {date: {strength: words_count}}
#     for strength,date,eo,hu in words:
#         inc_wd(wd,date,strength,1)
#     date = datetime.date.today()
#     for i in range(days):
#         sys.stdout.write(str(date)+': ')
#         if date in wd:
#             for strength,words_count in wd[date].items():
#                 sys.stdout.write('*'*words_count)
#                 inc_wd(wd,next_date(strength,date),strength+1,words_count)
#             del wd[date]
#         print
#         date += datetime.timedelta(1)


def ask_words(options):
    fname = options.dict_file_name
    wordlist = words_from_file(fname)
    if wordlist is None:
        sys.exit(1)
    sys.stdout.write("%d word pairs read.\n" % len(wordlist.list))
    practice_words(wordlist, use_getch=options.getch, use_color=options.color)
    words_to_file(wordlist, fname)
    if options.backup:
        words_to_file(wordlist, fname + '_' + str(datetime.date.today()))

# def show_future(od):
#     words = words_from_file(od['dict-file-name'])
#     print_future(words,od['future-days'])


##### translation #####

def get_tr_dict(lang=None):
    if lang is None:
        lang = exponwords_ss.options.ui_language
    tr_dict = exponwords_ss.tr_dicts.get(lang)
    if tr_dict is None:
        fname = os.path.join('translations', lang + '.json')
        tr_dict = json.loads(file_to_string(fname))
        exponwords_ss.tr_dicts[lang] = tr_dict
    return tr_dict

def tr(word, lang=None):
    if lang is None:
        lang = exponwords_ss.options.ui_language
    translated_word = get_tr_dict(lang).get(word, word)
    return translated_word

def translate_html(html_text):
    """Translates the given HTML text.

    The substrings in `html_text` which has the form ##WORD## will be translated
    using the `tr` function.

    **Argument:**

    - `html_text` (str)

    **Returns:** str
    """

    def translate(matchobject):
        """Translates one word."""
        word = matchobject.group(1)
        return tr(word)

    return re.sub(r'%TRANS: ([^%]+)%', translate, html_text)

##### web interface #####

urls = [
    r'/', 'Index',
    r'/(exponwords\.html|help\.html)', 'Fetch',
    r'/([a-zA-Z0-9_-]*\.js)', 'Fetch',
    r'/([a-zA-Z0-9_-]*\.css)', 'Fetch',
    r'/(translations/[a-zA-Z0-9_-]*\.json)', 'Fetch',
    r'/(new-word\.html|login\.html)', 'FetchAuth',
    r'/word-list', 'GetWordList',
    r'/help', 'GetHelp',
    r'/get_todays_wordlist', 'GetTodaysWordList',
    r'/get_translation', 'GetTranslation',
    r'/update_word', 'UpdateWord',
    r'/new-word-post', 'AddNewWord',
    r'/login-post', 'LoginPost',
    ]


class BaseServer(object):
    """Serves the index page."""

    def get_session(self):
        return exponwords_ss.session

    def is_logged_in(self):
        return (exponwords_ss.options.password == '' or
                self.get_session().get('logged_in', False))

    def log_in(self):
        self.get_session().logged_in = True

    def log_out(self):
        self.get_session().logged_in = False

    def create_message_page(self, message):
        template = file_to_string('message.html')
        html_text = re.sub('%MESSAGE%', tr(message), template)
        return translate_html(html_text)

class Index(BaseServer):
    """Serves the index page."""

    def GET(self):
        """Serves a HTTP GET request.

        Returns: str
        """

        exponwords_ss.lock.acquire()

        if self.is_logged_in():
            result = file_to_string('exponwords.html')
        else:
            result = file_to_string('login.html')

        result = translate_html(result)
        exponwords_ss.lock.release()
        return result


class LoginPost(BaseServer):
    """Logs in the user."""

    def POST(self):
        """Serves a HTTP POST request.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        password = web.input()['password'].encode('utf-8')

        if password == exponwords_ss.options.password:
            self.log_in()
            result = self.create_message_page('Logged in.')
        else:
            result = self.create_message_page('Incorrect password.')

        exponwords_ss.lock.release()
        return result


class Fetch(BaseServer):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        result = translate_html(file_to_string(name))
        exponwords_ss.lock.release()
        return result

class FetchAuth(BaseServer):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        if not self.is_logged_in():
            return self.create_message_page('Please log in.')

        result = translate_html(file_to_string(name))

        exponwords_ss.lock.release()
        return result

class GetTodaysWordList(BaseServer):
    """Serves the word list of the day."""

    def POST(self):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        if not self.is_logged_in():
            result = self.create_message_page('Please log in.')
            exponwords_ss.lock.release()
            return result

        # reading the word list
        fname = exponwords_ss.options.dict_file_name
        exponwords_ss.wordlist = words_from_file(fname)
        exponwords_ss.words_to_do_current = 0
        if exponwords_ss.wordlist is None:
            sys.stderr.write('File not found: ' + fname + '\n')
            sys.exit(1)
        sys.stdout.write("%d word pairs read.\n" %
                         len(exponwords_ss.wordlist.list))

        # calculating the words to be asked today
        exponwords_ss.words_to_do = \
            calc_words_to_do(exponwords_ss.wordlist)

        result = []
        for word, direction in exponwords_ss.words_to_do:
            result.append([word.langs[0],
                           word.langs[1],
                           direction,
                           word.explanation])

        result = json.dumps(result)
        exponwords_ss.lock.release()
        return result

class GetTranslation(BaseServer):
    """Returns the translation of the user interface."""

    def POST(self):
        """Serves a HTTP POST request.

        Returns: JSON
        """

        exponwords_ss.lock.acquire()
        result = json.dumps(get_tr_dict())
        exponwords_ss.lock.release()
        return result

class GetWordList(BaseServer):
    """Returns the word list."""

    def GET(self):
        """Serves a HTTP GET request.

        Returns: JSON
        """

        exponwords_ss.lock.acquire()
        if not self.is_logged_in():
            result = self.create_message_page('Please log in.')
            exponwords_ss.lock.release()
            return result

        fname = exponwords_ss.options.dict_file_name
        wordlist = words_from_file(fname)
        body = escape_html(words_to_str(wordlist))
        template = file_to_string('word-list.html')
        result = re.sub('%WORDLIST%', body, template)
        exponwords_ss.lock.release()
        return result


class GetHelp(BaseServer):
    """Returns the help."""

    def GET(self):
        """Serves a HTTP GET request.

        Returns: JSON
        """

        exponwords_ss.lock.acquire()
        lang = exponwords_ss.options.ui_language
        fname = os.path.join('help', lang + '.html')
        result = file_to_string(fname)
        exponwords_ss.lock.release()
        return result


class UpdateWord(BaseServer):
    """Serves the word list of the day."""

    def POST(self):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        if not self.is_logged_in():
            result = self.create_message_page('Please log in.')
            exponwords_ss.lock.release()
            return result

        # Updating the word in the word list
        answer = json.loads(web.input()['answer'])
        word, direction = \
            exponwords_ss.words_to_do[exponwords_ss.words_to_do_current]
        exponwords_ss.words_to_do_current += 1
        update_word(word, direction, answer)

        # Writing the word list to the disk
        fname = exponwords_ss.options.dict_file_name
        words_to_file(exponwords_ss.wordlist, fname)

        result = json.dumps('ok')
        exponwords_ss.lock.release()
        return result


class AddNewWord(BaseServer):
    """Adds a new word to the word list"""

    def POST(self):
        """Serves a HTTP POST request.

        Returns: str
        """

        exponwords_ss.lock.acquire()
        if not self.is_logged_in():
            result = self.create_message_page('Please log in.')
            exponwords_ss.lock.release()
            return result

        # Getting the details of the new word
        lang1 = web.input()['lang1'].encode('utf-8')
        lang2 = web.input()['lang2'].encode('utf-8')
        explanation = web.input()['explanation'].encode('utf-8')
        if explanation != '':
            explanation = '    ' + explanation + '\n'

        # Creating the new word
        word = Word()
        word.langs = [lang1, lang2]
        word.strengths = [0, 0]
        word.dates = [datetime.date.today(), datetime.date.today()]
        word.explanation = explanation

        # Reading the word list from the disk
        fname = exponwords_ss.options.dict_file_name
        wordlist = words_from_file(fname)

        # Adding the new word to the word list
        wordlist.list.append(word)

        # Writing the word list to the disk
        words_to_file(wordlist, fname)

        result = self.create_message_page('Word added')
        exponwords_ss.lock.release()
        return result


def start_webserver(options):

    exponwords_ss.options = options
    sys.argv = (None, options.port)
    app = web.application(urls, globals())
    exponwords_ss.webapp = app
    store = web.session.DiskStore('sessions')
    exponwords_ss.session = web.session.Session(app, store)
    app.run()


##### command line interface #####

def parse_args():
    """Parses the given command line options.

    Returns: (optparse.Values, [str])
    """

    parser = optparse.OptionParser()

    parser.add_option('-f', '--dict-file-name', dest='dict_file_name',
                      help='The name of the dictionary file. The default is '
                      'words.txt.',
                      action='store', default='words.txt')
    parser.add_option('-p', '--port', dest='port',
                      help='The port on which the webserver will listen. The '
                      'default is 8080.',
                      action='store', default='8080')
#    parser.add_option('-d', '--future-days', dest='future_days',
#                      help='Set the future days. 10 by default. Commands: '
#                      'show-future',
#                      type='int', action='store', default=10)
    parser.add_option('-g', '--getch', dest='getch',
                      help='Use getch() instead of readline()',
                      action='store_true')
    parser.add_option('-c', '--color', dest='color',
                      help='Use terminal colors',
                      action='store_true')
    parser.add_option('-b', '--backup', dest='backup',
                      help='Create backup files',
                      action='store_true')
    parser.add_option('--lang', dest='ui_language',
                      help='Language of the user interface',
                      action='store', choices=['en', 'hu'],
                      default='en')
    parser.add_option('--password', dest='password',
                      help='Password for the web interface',
                      action='store', default='')
    (options, args) = parser.parse_args()
    return (options, args)


def main(options, args):
    if args in [[], ['ask-words'], ['a']]:
        ask_words(options)
    elif args in [['show-future'], ['f']]:
        show_future(options)
    elif args in [['start-webserver'], ['w']]:
        start_webserver(options)
    else:
        print "Unknown command: '%s'" % args


##### main #####

if __name__ == '__main__':
    exponwords_path = os.path.dirname(sys.argv[0])
    if exponwords_path != '':
        os.chdir(os.path.dirname(sys.argv[0]))
    main(*parse_args())
