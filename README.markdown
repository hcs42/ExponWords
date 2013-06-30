ExponWords is a web application for learning words. It helps learn the word pairs fed by the user using the principle that the more we have already practiced a word, the less we need to practice it in the future. You can read more at http://exponwords.com/help/en/.

ExponWords is used at http://exponwords.com (which is a free service).

Installation
============

This section describes how to set up an ExponWords server on Debian or Ubuntu Linux using the nginx web server and the sqlite database engine. These steps apply only if you want to run no other web service. If you do want that, then you can adjust these steps accordingly.

Install the prerequisites
-------------------------

        $ sudo apt-get install python gettext nginx sqlite3 python-pip
        $ sudo pip install virtualenv
        $ virtualenv $HOME/virtualenv/django13
        $ $HOME/virtualenv/django13/bin/pip install django==1.3 flup

I used the following versions of these programs:

* Python: 2.7
* gettext: 0.18
* nginx: 0.8
* sqlite3: 3.7
* virtualenv: 1.9.1
* Django: 1.3
* flup: 1.0.3.dev-20110405

Set up ExponWords and run it in debug mode
------------------------------------------

1. Create a Django project (this will create a directory called `ExponWords` with some Python files; the `ExponWords` directory will contain all ExponWords-related stuff):

        $ source $HOME/virtualenv/django13/bin/activate
        $ cd $HOME
        $ django-admin.py startproject ExponWords

2. Clone the ExponWords repository as a Django application called `ew`:

        $ cd ExponWords
        $ git clone git://github.com/hcs42/ExponWords.git ew

3. Edit `settings.py` (you will find an example in `ew/setup/settings.py`):

   * `DATABASES`: fill it in according to the database you want to use. I used sqlite.
   * `ADMIN_ROOT`: change it to `'/admin/media/'`
   * `MEDIA_URL`: set it to your site (see the example)
   * `MIDDLEWARE_CLASSES`: insert `'django.middleware.locale.LocaleMiddleware'` after `SessionMiddleware`
   * `INSTALLED_APPS`: append `'django.contrib.admin'` and `'ew'`
   * `LANGUAGES`: copy it from the example
   * `LOGIN_URL`: set it to `'/login/'`
   * `LOGIN_REDIRECT_URL`: set it to `'/'`
   * `DEFAULT_FROM_EMAIL`: set it to your email address
   * Anything else you want to customize (e.g. timezone)
   * Move the `DEBUG` and `TEMPLATE_DEBUG` variables into `debug_settings.py` (see the next step)

4. Create `debug_settings.py` (you will find an example in `ew/setup/debug_settings.py`):

   * `DATABASES`: fill it in
   * Move the `DEBUG` and `TEMPLATE_DEBUG` variables here from `settings.py` (see the previous step)

5. Overwrite `urls.py` with the one in the `setup` directory:

        $ cp ew/setup/urls.py .

6. Set up the database files. When asked about whether to create a superuser, create them.

        $ python manage.py syncdb
        $ python manage.py syncdb --settings=debug_settings

7. Compile the translation files:

        $ cd ew; django-admin.py compilemessages; cd ..

8. Copy the startup script and change the ports in it if you need to:

        $ cp ew/setup/start_production.sh ew/setup/start_debug.sh .
        $ vim start*

9. Start the server in debug mode:

        $ ./start_debug.sh

   Try it from the browser:

        $ google-chrome http://localhost:8002

   Finally close it:

        Kill `start_debug.sh` with CTRL-C

   Don't forget to source the `activate` script each time before starting the
   server.

Set up the nginx web server and run ExponWords in production mode
-----------------------------------------------------------------

1. Copy the startup script and change the ports in it if you need to:

        $ cp ew/setup/start_production.sh ew/setup/start_production.sh .
        $ vim ew/setup/start_production.sh ew/setup/start_production.sh

2. Perform the following steps as root:

   Rename the original nginx configuration file:

        # mv /etc/nginx/nginx.conf{,.old}

   Copy the provided config file instead and modify its content to match your paths:

        # cp ew/setup/nginx.conf /etc/nginx/nginx.conf
        # vim /etc/nginx/nginx.conf

   Restart nginx:

        # /etc/init.d/nginx restart

3. Start the production server, try it and kill it:

        $ ./start_production
        $ google-chrome http://localhost/
        Kill start_production with CTRL-C

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

Set up Google Analytics
-----------------------

If you want to use Google Analytics to track the usage statistics of your site, create a file `ew/templates/ew/custom_head.html` and place the tracking code given by Google in it (with the scripts tags).

Upgrading ExponWords
--------------------

There is a file in this directory called UPGRADE.txt which describes what actions should be performed when Upgrading ExponWords.

Usage
=====

You can read the user documentation at http://exponwords.com/help/en/.
