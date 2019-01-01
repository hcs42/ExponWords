#!/bin/bash

EW_ENV=$HOME/virtualenv/ewenv

"$EW_ENV/bin/python" manage.py runserver 0.0.0.0:8002
# If you create a debug_settings.py file, add the following option:
# --settings=ExponWords.debug_settings
