This program helps practicing word pairs stored in a file. It has both a console
interface and a web interface.

Installation
============

1. Install git and virtualenv. On Ubuntu Linux:

         $ sudo apt-get install git
         $ sudo easy_install virtualenv

2. Download and install web.py into a virtual Python environment and download
   ExponWords:

        $ mkdir exponwords
        $ cd exponwords
        $ virtualenv python
        New python executable in python/bin/python
        Installing setuptools............done.
        $ git clone git://github.com/hcs42/webpy.git
        [...]
        $ git clone git://github.com/hcs42/ExponWords.git
        [...]
        $ ls
        ExponWords  python  webpy
        $ cd webpy/
        $ ../python/bin/python setup.py build
        [...]
        $ ../python/bin/python setup.py install
        [...]
        $ cd ..
        $ python/bin/python ExponWords/exponwords.py --help
        Usage: exponwords.py [options]
        [...]


Console interface
=================

See the "Data format" section about how the input file should look like.

Example invocation (`y`, `n` and `q` are typed by the user):

    $ python/bin/python ExponWords/exponwords.py -f my_words.txt
    4 word pairs read.
    Total number of words: 8
    Words to ask now: 8
    8/1 <0>: Word in English: like --
    szeret
        I like you a lot.
        I really don't like this restaurant.
    Did you know this word? [y/n/q]y


    8/2 <0>: Word in Hungarian: kutya --
    dog
    Did you know this word? [y/n/q]n


    8/3 <0>: Word in Hungarian: szeret -- q

Example invocation with `getch()` used instead of `readline()` (`-g` option) and
with colors (`-c` option):

    $ python/bin/python exponwords.py -gcf my_words.txt ask-words

This features might not work on all system.

Web interface
=============

The web interface can be started in the following way:

    $ python/bin/python exponwords.py -f my_words.txt \
          --port 5656 --password mypassword start-webserver

In the web interface, new words can be added and existing words can be
practiced. If the `--password` parameter is specified, the users have to log in
with this password.

Data format
===========

Example word list file:

    CONFIG: lang1=English
    CONFIG: lang2=Hungarian
    dog -- kutya
    cat -- macska
    like -- szeret
        I like you a lot.
        I really don't like this restaurant.
    go -- megy
        I would like to go to the cinema.
