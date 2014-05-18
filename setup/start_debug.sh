#!/bin/bash

EW_ENV=$HOME/virtualenv/python34/django16

"$EW_ENV/bin/python" manage.py runserver 0.0.0.0:8002 --settings=ExponWords.debug_settings
