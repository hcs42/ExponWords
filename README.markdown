This web application helps practicing word pairs.

It is used at http://exponwords.zapto.org/, which is yet a private beta. If you want to use it or try it out, please send me an email.

Installation
============

This section describe how to set up an ExponWords server on Debian or Ubuntu Linux using the nginx web server and the sqlite database engine. These steps apply only if you want to run no other web service. If you do want that, then you can adjust these steps accordingly.

Install the prerequisites
-------------------------

        $ sudo apt-get install gettext
        $ sudo apt-get install nginx python-flup
        $ sudo apt-get install python-sqlite sqlite3

Get Django: https://docs.djangoproject.com/en/1.3/topics/install/#installing-an-official-release

I used the following versions of these programs:

* Python: 2.7
* Django: 1.3
* nginx: 0.8
* sqlite3: 3.7
* gettext: 0.18

All of these are the default on the latest Ubuntu except for Django.

Set up ExponWords and run it in debug mode
------------------------------------------

1. Create a Django project (this will create a directory called `ExponWords` with some Python files):

        $ django-admin startproject ExponWords

2. Clone the ExponWords repository as a Django application called `ew`:

        $ cd ExponWords
        $ git clone git://github.com/hcs42/ExponWords.git ew

3. Edit `settings.py` (you will find an example in `ew/setup/settings.py`):

   * `DATABASES`: fill it in according to the database you want to use. I used sqlite.
   * `ADMIN_ROOT`: change it to `'/admin/media/'`
   * `LOGIN_REDIRECT_URL`: set it to `'..'`
   * `MIDDLEWARE_CLASSES`: insert `'django.middleware.locale.LocaleMiddleware'` after `SessionMiddleware`
   * `INSTALLED_APPS`: append `'ew'`
   * `LANGUAGES`: copy it from the example
   * Anything else you want to customize (e.g. timezone)
   * Move the `DEBUG` and `TEMPLATE_DEBUG` variables into `debug_settings.py` (see the next step)

4. Edit `debug_settings.py` (you will find an example in `ew/setup/debug_settings.py`):

   * `DATABASES`: fill it in
   * Move the `DEBUG` and `TEMPLATE_DEBUG` variables here from `settings.py` (see the previous step)

5. Overwrite `urls.py` with the one in the `setup` directory:

        $ cp ew/setup/urls.py .

6. Set up the database files. When asked about whether to create a superuser, create them.

        $ python manage.py syncdb
        $ python manage.py syncdb --settings=debug_settings

7. Compile the translation files:

        $ cd ew; django-admin compilemessages; cd ..

8. Copy the startup scripts and change the ports in them if you need to:

        $ cp ew/setup/start_production.sh ew/setup/start_debug.sh .
        $ vim ew/setup/start_production.sh ew/setup/start_debug.sh

9. Start the server in debug mode:

        $ ./start_debug.sh

   Try it from the browser:

        $ google-chrome http://localhost:8002

   Finally close it:

        Kill `start_debug.sh` with CTRL-C

Set up the nginx web server and run ExponWords in production mode
-----------------------------------------------------------------

1. Perform the following steps as root:

   Rename the original nginx configuration file:

        # mv /etc/nginx/nginx.conf{,.old}

   Copy the provided config file instead and modify its content to match your paths:

        # cp ew/setup/nginx.conf /etc/nginx/nginx.conf
        # vim /etc/nginx/nginx.conf

   Restart nginx:

        # /etc/init.d/nginx restart

2. Start the production server, try it and kill it:

        $ ./start_production
        $ google-chrome http://localhost/
        Kill start_production with CTRL-C

Start ExponWords automatically after boot
-----------------------------------------

In Debian or Ubuntu, ExponWords can be set to start up automatically by performing the following steps as root.

1. Copy the provided init script to the directory of the init scripts:

        # cp ew/setup/exponwords.d /etc/init.d/exponwords

2. Modify the `SITE_PATH` variable in it to `<path to exponwords>/ExponWords` and modify `RUN_AS` to your Linux username:

        # vim /etc/init.d/exponwords

3. Try the script:

        # /etc/init.d/exponwords start
        $ google-chrome http://localhost/   # web page is there
        # /etc/init.d/exponwords stop
        $ google-chrome http://localhost/   # web page is not there

4. Run `update-rc.d` to create symbolic links in the `/etc/rc*.d/` directories, which will make operating system call `/etc/init.d/exponwords` automatically with the `start` parameter after the system has booted, and with the `stop` parameter before it shuts down.

        # update-rc.d exponwords defaults

Upgrading ExponWords
--------------------

There is a file in this directory called UPDATE.txt which describes what actions should be performed when Upgrading ExponWords.

Usage
=====

You can read the user documentation at http://exponwords.zapto.org/help/en/.
