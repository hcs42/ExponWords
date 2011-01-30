import threading

original_dir = None
wordlist = None
options = None
webapp = None
session = None
lock = threading.Lock()
tr_dicts = {}
