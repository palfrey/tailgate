Tailgate
========
[![Build Status](https://travis-ci.com/palfrey/tailgate.svg?branch=master)](https://travis-ci.com/palfrey/tailgate)

Generates a calendar of all the books for your followed authors on [Goodreads](https://www.goodreads.com). 
This provides you with information on when they're releasing new books.

Online version is at [https://tailgate.herokuapp.com/](https://tailgate.herokuapp.com/)

Local install
-------------
1. Install NodeJS and Python
    * (Possibly also make a [Virtualenv](https://virtualenv.pypa.io/en/stable/userguide/#usage))
2. Copy `config.yml.example` to `config.yml`
3. Get a [Goodreads Developer Key](https://www.goodreads.com/api/keys) and add the key/secret to `config.yml`
4. `yarn install`
5. `pip install -r requirements.txt`
6. `FLASK_DEBUG=true FLASK_APP=app.py flask run -p 8000`
7. Goto [http://localhost:8000/](http://localhost:8000/)

Heroku install
--------------
These steps have already been run to enable [https://tailgate.herokuapp.com/](https://tailgate.herokuapp.com/)

1. Follow the standard [Heroku setup for a Python app](https://devcenter.heroku.com/articles/getting-started-with-python#introduction) but use `https://github.com/palfrey/tailgate.git` instead of their example app
2. Go into the app settings and do the following   
    * Make sure both `heroku/python` and `heroku/nodejs` are in the Buildpacks list
    * Set `FLASK_ENCRYPTION_KEY` to something random
    * Set `KEY` and `SECRET` to your Goodreads key/secret
3. Add "Heroku Postgres" to the addons for this app. "Hobby Dev" level is good enough.
4. Add ["Heroku Scheduler"](https://elements.heroku.com/addons/scheduler) to the addons for this app, and add `python app.py` to run every so often.
5. Click "Open app" and make sure the app comes up ok, as the first request does the initial database migrations.
