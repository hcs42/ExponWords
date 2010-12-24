#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import random
import datetime
import optparse
import json
import web as webpy
import exponwords_ss

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


def words_to_file(wordlist, dict_file_name):
    """Writes the word list to a file.

    Arguments:
    - words (WordList)
    - dict_file_name (str)
    """

    file = open(dict_file_name, 'w')
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
    file.close()


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


##### web interface #####

urls = [
    r'/()', 'Fetch',
    r'/(exponwords.js|exponwords.html|exponwords.css)', 'Fetch',
    r'/(json2.js|jquery.js)', 'Fetch',
    r'/get_todays_wordlist', 'GetTodaysWordList',
    r'/update_word', 'UpdateWord',
    ]


class Fetch(object):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        if name == '':
            name = 'exponwords.html'
        return file_to_string(name)

class GetTodaysWordList(object):
    """Serves the word list of the day."""

    def POST(self):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

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
            result.append([word.langs[0], word.langs[1], direction,
                           word.explanation])

        return json.dumps(result)

#json.loads(value)
#words_to_file(wordlist, fname)

class UpdateWord(object):
    """Serves the word list of the day."""

    def POST(self):
        """Serves a HTTP GET request.

        Argument:
        - name (unicode) -- The name of the URL that was requested.

        Returns: str
        """

        # Updating the word in the word list
        answer = json.loads(webpy.input()['answer'])
        word, direction = \
            exponwords_ss.words_to_do[exponwords_ss.words_to_do_current]
        exponwords_ss.words_to_do_current += 1
        update_word(word, direction, answer)

        # Writing the word list to the disk
        fname = exponwords_ss.options.dict_file_name
        words_to_file(exponwords_ss.wordlist, fname)

        return json.dumps('ok')


def start_webserver(options):

    exponwords_ss.options = options
    port = '8080'
    sys.argv = (None, port)
    webapp = webpy.application(urls, globals())
    webapp.run()


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
    os.chdir(os.path.dirname(sys.argv[0]))
    main(*parse_args())
