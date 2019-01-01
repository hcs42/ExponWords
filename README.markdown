ExponWords is a web application for learning words. It helps learn the word
pairs fed by the user using the principle that the more we have already
practiced a word, the less we need to practice it in the future. You can read
more at http://exponwords.com/help/en/.

ExponWords is used at http://exponwords.com (which is a free service).

Installation
============

This section describes how to set up an ExponWords server on Debian or Ubuntu
Linux using the nginx web server and the sqlite database engine. These steps
apply only if you want to run no other web service. If you do want that, then
you can adjust these steps accordingly.

Install the prerequisites
-------------------------

    $ sudo apt-get install python3 python3-pip python3-dev sqlite3 gettext nginx
    $ pip3 install virtualenv
    $ export EW_ENV=$HOME/virtualenv/ewenv
    $ virtualenv "$EW_ENV"
    $ "$EW_ENV/bin/pip" install django==2.1 gunicorn==19.9.0

I used the following versions of these programs:

* Python: 3.6.7
* gettext: 0.19.8.1
* nginx: 0.8
* sqlite3: 3.22.0
* virtualenv: 16.2.0
* Django: 2.1
* gunicorn: 19.9.0

Set up ExponWords and run it in debug mode
------------------------------------------

1. Create a Django project (this will create a directory called `ExponWords`
   with some Python files; the `ExponWords` directory will contain all
   ExponWords-related stuff):

        $ source "$EW_ENV/bin/activate"
        $ cd "$HOME"  # The directory that will contain the ExponWords dir
        $ django-admin.py startproject ExponWords

2. Clone the ExponWords repository as a Django application called `ew`:

        $ cd ExponWords
        $ git clone git://github.com/hcs42/ExponWords.git ew
        $ ls
        ExponWords  ew  manage.py

3. Edit `settings.py` (you will find an example in `ew/setup/settings.py`):

   * `DEBUG`,
     `TEMPLATE_DEBUG`: comment these out
   * `ALLOWED_HOST`: add `['localhost']`
   * `INSTALLED_APPS`: append `'ew'`
   * `MIDDLEWARE_CLASSES`: insert `'django.middleware.locale.LocaleMiddleware'`
     after `CommonMiddleware`
   * `DATABASES`: fill it in according to the database you want to use. I used
     sqlite.
   * `LANGUAGES`: copy it from the example
   * `USE_L10N`,
     `USE_TZ`: update according to `ew/setup/settings.py`
   * `EMAIL_BACKEND`,
     `DEFAULT_FROM_EMAIL`,
     `LOGIN_URL`,
     `LOGIN_REDIRECT_URL`: add according to `ew/setup/settings.py`
   * `STATIC_URL`: update according to `ew/setup/settings.py`
   * `LOGGING`: add according to `ew/setup/settings.py`

5. Overwrite `urls.py` with the one in the `setup` directory:

        $ rm urls.py
        $ ln -s /path/to/ew/setup/urls.py

6. Set up the database files. When asked about whether to create a superuser,
   create them.

        $ cd ..
        $ python manage.py migrate

7. Compile the translation files:

        $ cd ew
        $ django-admin.py compilemessages
        $ cd ..

8. Copy the debug startup script and change the ports and `EW_ENV` value in it
   if you need to:

        $ cp ew/setup/start_debug.sh .
        $ vim start_debug.sh

9. Start the server in debug mode:

        $ ./start_debug.sh

   Try it from the browser by opening `http://localhost:8002`.

   Try the admin page: `http://localhost:8002/admin`.

   Finally close it: kill `start_debug.sh` with CTRL-C.

Set up the nginx web server and run ExponWords in production mode
-----------------------------------------------------------------

1. Copy the startup script and change the ports and `EW_ENV` value in it if you
   need to:

        $ cp ew/setup/start_prod.sh .
        $ vim start_prod.sh

2. Perform the following steps as root:

   Rename the original nginx configuration file:

        # mv /etc/nginx/nginx.conf{,.old}

   Copy the provided config file instead and modify its content to match your
   paths:

        # cp ew/setup/nginx.conf /etc/nginx/nginx.conf
        # vim /etc/nginx/nginx.conf

   Reload NGINX configuration:

        # /etc/init.d/nginx reload

3. Start the production server, try it and kill it:

        $ ./start_prod.sh

   Try it from the browser by opening `http://localhost`.

   Try the admin page: `http://localhost/admin`.

   Finally close it: kill `start_prod.sh` with CTRL-C.

Running ExponWords in production
--------------------------------

1. If you want to run ExponWords in actual production, you should modify
   `settings.py`:

    * Set `DEBUG` to `False`.
    * Set `TEMPLATE_DEBUG` to `False`.
    * Set `ALLOWED_HOST` with the domain of your website (e.g.
      `['myexponwordssite.com']`).
    * Delete the `EMAIL_BACKEND` configuration entry.
    * Set `DEFAULT_FROM_EMAIL` to your real e-mail address.

Set up email sending
--------------------

1. Set up the name of your site:

        $ python manage.py shell
        >>> from django.contrib.sites.models import Site
        >>> s = Site.objects.get(pk=1)
        >>> s.domain = 'mysite.org'
        >>> s.name = 'ExponWords'
        >>> s.save()

2. Set up SMTP server and configure Django to use it. See more information
   here: https://docs.djangoproject.com/en/1.3/topics/email/

Start ExponWords automatically after boot
-----------------------------------------

In Debian or Ubuntu, ExponWords can be set to start up automatically by
performing the following steps as root.

1. Copy the provided init script to the directory of the init scripts:

        # cp ew/setup/exponwords.d /etc/init.d/exponwords

2. Modify the
    
        PYTHON=`which python`

   to

        PYTHON=`/my/path/to/python`

3. Modify the `SITE_PATH` variable in it to `<path to exponwords>/ExponWords`
   and modify `RUN_AS` to your Linux username:

        # vim /etc/init.d/exponwords

4. Try the script:

        # /etc/init.d/exponwords start
        $ google-chrome http://localhost/   # web page is there
        # /etc/init.d/exponwords stop
        $ google-chrome http://localhost/   # web page is not there

5. Run `update-rc.d` to create symbolic links in the `/etc/rc*.d/` directories,
   which will make operating system call `/etc/init.d/exponwords` automatically
   with the `start` parameter after the system has booted, and with the `stop`
   parameter before it shuts down.

        # update-rc.d exponwords defaults

Set up Google Analytics
-----------------------

If you want to use Google Analytics to track the usage statistics of your site,
create a file `ew/templates/ew/custom_head.html` and place the tracking code
given by Google in it (with the scripts tags).

Upgrading ExponWords
--------------------

There is a file in this directory called UPGRADE.txt which describes what
actions should be performed when Upgrading ExponWords.

Usage
=====

You can read the user documentation at http://exponwords.com/help/en/.
