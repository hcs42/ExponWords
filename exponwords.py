#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import random
import datetime
from hcs_args import args_to_od

def print_help(subject = None):
    print """\
NAME
    Words
USAGE
    Words [options]
DESCRIPTION
    The program can store and ask word pairs.
COMMANDS
    h, help, -h, --help:
        This help.
    a, ask-words
        Ask the words.
    f, show-future
        Show the future.
OPTIONS
    -f, --dict-file-name [file]
        The name of the dictionary file.
        The default is: /a/docs/hcs/esperanto/w.txt
        Commands: ask-words, show-future
    -d, --future-days [days]
        Set the future days.
        10 by default.
        Commands: show-future
AUTHOR
    Csaba Hoch <csaba.hoch@gmail.com>"""

def words_from_file(dict_file_name):
    file = open(dict_file_name,'r')
    words = []
    for line in file:
        line = line.strip()
        if line != '':
            r = re.search(r'<(\d+) +(\d\d\d\d)-(\d\d)-(\d\d)> +([^\|]+)\|(.*)',line)
            if r == None:
                r = re.search('([^\|]+) *\| *(.*)',line)
                strength = 0
                date = datetime.date.today()
                eo = r.group(1).strip()
                hu = r.group(2).strip()
            else:
                strength = int(r.group(1))
                date = datetime.date(int(r.group(2)),int(r.group(3)),int(r.group(4)))
                eo = r.group(5).strip()
                hu = r.group(6).strip()
            words.append((strength,date,eo,hu))
    file.close()
    return words

def words_to_file(words,dict_file_name):
    file = open(dict_file_name,'w')
    for (strength, date, eo, hu) in words:
        file.write('<'+str(strength)+' '+str(date)+'> '+eo+' | '+hu+'\n')
    file.close()

#def new_word():
#    global esp_word, hun_word, esp_to_hun
#    esp_word, hun_word = words[random.randint(0,len(words)-1)]
#    esp_to_hun = True if random.randint(1,2) == 1 else False

def x_to_accent(w):
    i = 1
    while i < len(w):
        if w[i] == 'x':
            if   w[i-1] == 'c': new = 'ĉ'
            elif w[i-1] == 'g': new = 'ĝ'
            elif w[i-1] == 'h': new = 'ĥ'
            elif w[i-1] == 'j': new = 'ĵ'
            elif w[i-1] == 's': new = 'ŝ'
            elif w[i-1] == 'u': new = 'ŭ'
            elif w[i-1] == 'C': new = 'Ĉ'
            elif w[i-1] == 'G': new = 'Ĝ'
            elif w[i-1] == 'H': new = 'Ĥ'
            elif w[i-1] == 'J': new = 'Ĵ'
            elif w[i-1] == 'S': new = 'Ŝ'
            w = w[0:i-1] + new + w[i+1:]
        else:
            i += 1
    return w

def ask_word(eo,hu,dir):
    if dir == 'eh':
        sys.stdout.write('Esperanta vorto: %s = ' % x_to_accent(eo))
        solution = hu
    else:
        sys.stdout.write('Hungara vorto: %s = ' % hu)
        solution = eo
    r = re.search('([^ ,]+).*',solution)
    solution = r.group(1)
    line = sys.stdin.readline().strip()
    if line == 'q':
        return 'q'
    elif line == solution:
        sys.stdout.write('++++++++++++++++++++\n')
        return True
    else:
        sys.stdout.write( \
                '-------------------- '+ \
                ('Malĝusta; ' if solution!='' else '') + \
                'la solvaĝo estas: ' + \
                solution + '\n')
        if line != '':
            return (True if sys.stdin.readline().strip() == 'c' else False)
        else:
            return False

def next_date(strength,date):
    return date + datetime.timedelta(2**strength)

def practice_words(words):
    today = datetime.date.today()
    words_done = []
    words_to_do = []
    for word in words:
        strength,date,eo,hu = word
        if date <= today:
            words_to_do.append((strength,date,eo,hu,'eh'))
            words_to_do.append((strength,date,eo,hu,'he'))
        else:
            words_done.append(word)
    random.shuffle(words_to_do)

    sys.stdout.write("%d vortoj estos demanita.\n" % len(words_to_do))
    sys.stdout.write("Proksimuma tempo en minutoj: %d\n" % (len(words_to_do)/14))

    t = {} # t(eo,hu) = 0: failed; t(eo,hu) = 1: one passed
    finished = False
    i = 0
    for strength,date,eo,hu,dir in words_to_do:
        if finished:
            if (eo,hu) not in s:
                words_done.append((strength,date,eo,hu))
                s.add((eo,hu))
        else:
            i += 1
            sys.stdout.write(str(len(words_to_do))+'/'+str(i)+' <'+str(strength)+'>: ')
            answer_ok = ask_word(eo,hu,dir)
            if answer_ok == 'q':
                s = set()
                s.add((eo,hu))
                words_done.append((strength,date,eo,hu))
                finished = True
            elif not (eo,hu) in t:
                t[(eo,hu)] = answer_ok
            else:
                if t[(eo,hu)] and answer_ok:
                    words_done.append((strength+1,next_date(strength,today),eo,hu))
                else:
                    words_done.append((0,today,eo,hu))
                del t[(eo,hu)]

    return words_done

def inc_wd(wd,date,strength,n):
    if date not in wd:
        wd[date] = {strength: n}
    elif strength not in wd[date]:
        wd[date][strength] = n
    else:
        wd[date][strength] += n

def print_future(words,days):
    wd = {} # word dictionary: {date: {strength: words_count}}
    for strength,date,eo,hu in words:
        inc_wd(wd,date,strength,1)
    date = datetime.date.today()
    for i in range(days):
        sys.stdout.write(str(date)+': ')
        if date in wd:
            for strength,words_count in wd[date].items():
                sys.stdout.write('*'*words_count)
                inc_wd(wd,next_date(strength,date),strength+1,words_count)
            del wd[date]
        print
        date += datetime.timedelta(1)

def ask_words(od):
    dict_file_name = od['dict-file-name']
    words = words_from_file(dict_file_name)
    sys.stdout.write("%d vortparoj entute.\n" % len(words))
    words = practice_words(words)
    words_to_file(words,dict_file_name)
    words_to_file(words,dict_file_name+'_'+str(datetime.date.today()))

def show_future(od):
    words = words_from_file(od['dict-file-name'])
    print_future(words,od['future-days'])

def main(args):
    cmd = ('help' if len(args) == 0 else args.pop(0))
    dict_file_name_option = ['dict-file-name','f', 1, '/a/docs/hcs/esperanto/w.txt']
    if cmd in ['help','h','--help','-h']:
        print_help(None if len(args) == 0 else args.pop(0))
        return
    elif cmd in ['ask-words','a']:
        opt_spec = [dict_file_name_option]
        ask_words(args_to_od(args, opt_spec))
    elif cmd in ['show-future','f']:
        opt_spec = [dict_file_name_option,
                    ['future-days', 'd', 1, 10]]
        od = args_to_od(args, opt_spec)
        try:
            od['future-days'] = int(od['future-days'])
        except ValueError:
            print "Error: integer expected after 'future-days' option, but '%s'" \
                  " is not an integer." % (od['future-days'],)
            return
        show_future(od)
    else:
        raise Exception, "Unknown command: '%s'" % cmd

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception, e:
        print "Error:", e
