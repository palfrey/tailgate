from rauth import OAuth1Service, OAuth1Session
from flask import (Flask, render_template, url_for,
                   request, session, redirect, make_response)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from models import build_models
import yaml
import os
from xml.etree import ElementTree
import logging
import sys
import datetime
import re
import icalendar

app = Flask(__name__)
if "DYNO" in os.environ:
    app.logger.info(
        "Found DYNO environment variable, so assuming we're in Heroku")
    config = {
        "app": {
            "database_uri": os.environ["DATABASE_URL"]
        },
        "goodreads": {
            "key": os.environ["KEY"],
            "secret": os.environ["SECRET"]
        },
        "flask": {
            "secret_key": os.environ["FLASK_ENCRYPTION_KEY"]
        }
    }
else:
    config = yaml.safe_load(open('config.yml', 'r'))


@app.before_first_request
def initial_setup():
    with app.app_context():
        upgrade()


@app.before_request
def make_session_permanent():
    session.permanent = True


app.secret_key = config["flask"]["secret_key"]
app.config['SQLALCHEMY_DATABASE_URI'] = config["app"]["database_uri"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('DEBUG', False)
if app.config["DEBUG"]:
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)
    #app.config["SQLALCHEMY_ECHO"] = True
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
models = build_models(db)
for m in models:
    globals()[m.__name__] = m

goodreads = OAuth1Service(
    consumer_key=config["goodreads"]["key"],
    consumer_secret=config["goodreads"]["secret"],
    name='goodreads',
    request_token_url='http://www.goodreads.com/oauth/request_token',
    authorize_url='http://www.goodreads.com/oauth/authorize',
    access_token_url='http://www.goodreads.com/oauth/access_token',
    base_url='http://www.goodreads.com/'
)

@app.route("/")
def index():
    return render_template('index.html', **config)

tokens = {}

@app.route("/oauth/request", methods=["GET"])
def oauth_request():
    request_token, request_token_secret = goodreads.get_request_token(header_auth=True)
    tokens[request_token] = request_token_secret
    authorize_url = goodreads.get_authorize_url(request_token)
    return redirect("%s&oauth_callback=%s" % (authorize_url, url_for("oauth_callback", _external=True)))

@app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    authorize = int(request.args['authorize'])
    if authorize == 0:
        flask("You didn't authorise access on Goodreads")
        return redirect(url_for('index'))
    oauth_token = request.args['oauth_token']
    session = goodreads.get_auth_session(oauth_token, tokens[oauth_token])
    user = session.get("https://www.goodreads.com/api/auth_user")
    user.raise_for_status()
    data = ElementTree.fromstring(user.content)
    id = int(data.find("user").get("id"))
    existing = User.query.filter_by(id=id).first()
    if existing is None:
        user = User(id=id, name=data.find("user/name").text, token=session.access_token, token_secret=session.access_token_secret)
        db.session.add(user)
    else:
        existing.name = data.find("user/name").text
        existing.token = session.access_token
        existing.token_secret = session.access_token_secret

    db.session.commit()
    return redirect(url_for("info", id=id))

def all_books_for_user(user):
    session = OAuth1Session(
        consumer_key = config["goodreads"]["key"],
        consumer_secret = config["goodreads"]["secret"],
        access_token = user.token,
        access_token_secret = user.token_secret
    )
    # following = session.get("https://www.goodreads.com/user/%d/following.xml" % user.id)
    # following.raise_for_status()
    # following = ElementTree.fromstring(following.content)
    # author_user_ids = [int(author_user.find("id").text) for author_user in following.findall("following/user")]

    following = session.get("https://www.goodreads.com/user/%d/following" % user.id)
    following.raise_for_status()
    author_ids = [int(x) for x in re.findall("<a class=\"authorName\" href=\"/author/show/(\d+)", following.text)]

    authors = []
    all_books = []
    for author_id in author_ids:
        author = Author.query.filter_by(id=author_id).first()
        if author is None:
            author_data = session.get("https://www.goodreads.com/author/show/%d?format=xml" % author_id)
            author_data.raise_for_status()
            author_data = ElementTree.fromstring(author_data.content)
            name = author_data.find("author/name").text
            author = Author(id=author_id, name=name)
            db.session.add(author)
            db.session.commit()
        authors.append(author)
        author.update_books(session)
        all_books.extend(author.books)
    return (authors, all_books)

@app.route("/info/<int:id>")
def info(id):
    user = User.query.filter_by(id=id).first()
    (authors, all_books) = all_books_for_user(user)
    next_books = sorted([x for x in all_books if x.published>datetime.datetime.today()], key=lambda x:x.published)
    prev_books = sorted([x for x in all_books if x.published<datetime.datetime.today()], key=lambda x:x.published, reverse=True)
    return render_template('info.html', user=user, authors=sorted(authors, key=lambda x:x.name), next_books=next_books[:5], prev_books=prev_books[:5])

@app.route("/calendar/<int:id>")
def calendar(id):
    user = User.query.filter_by(id=id).first()
    (_, all_books) = all_books_for_user(user)
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Book calendar//')
    cal.add('version','2.0')
    cal.add('X-WR-CALNAME', "Book calendar for %s" % user.name)
    for book in all_books:
        event = icalendar.Event()
        event.add('uid', book.id)
        event.add('dtstart', book.published.date())
        event.add('dtend', (book.published + datetime.timedelta(days=1)).date())
        event.add('summary', "%s - %s" % (book.author.name, book.title))
        cal.add_component(event)
    resp = make_response(cal.to_ical())
    resp.headers["Content-Type"] = "text/Calendar"
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    resp.headers["Expires"] = "Sat, 26 Jul 1997 05:00:00 GMT"
    return resp