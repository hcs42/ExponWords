import threading

wordlist = None
words_to_do = None
words_to_do_current = 0
options = None
webapp = None
session = None
lock = threading.Lock()
