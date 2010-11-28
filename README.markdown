This program helps practicing word pairs stored in a file.

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

Example invocation (y, n and q are typed by the user):

    $ python exponwords.py -f my_words.txt
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

Example invocation with getch() used instead of readline() and with colors:

    $ python exponwords.py -gcf my_words.txt

This features might not work on all system.
