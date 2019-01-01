#!/bin/bash

EW_ENV=$HOME/virtualenv/ewenv

"$EW_ENV/bin/gunicorn" -b localhost:8001 ExponWords.wsgi:application
