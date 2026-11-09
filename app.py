from flask import (Flask, render_template, url_for,
                   request, redirect, make_response)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
import requests
from models import build_models
import yaml
import os
import logging
import sys
import datetime
import icalendar
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
if "DYNO" in os.environ:
    app.logger.info(
        "Found DYNO environment variable, so assuming we're in Heroku")
    config = {
        "app": {
            "database_uri": os.environ["DATABASE_URL"]
        },
        "flask": {
            "secret_key": os.environ["FLASK_ENCRYPTION_KEY"]
        }
    }
else:
    config = yaml.safe_load(open('config.yml', 'r'))

print("Config", config)


app.secret_key = config["flask"]["secret_key"]
app.config['SQLALCHEMY_DATABASE_URI'] = config["app"]["database_uri"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', False)
if type(app.config['DEBUG']) == str:
    app.config['DEBUG'] = app.config['DEBUG'].lower() == "true"
if app.config["DEBUG"]:
    app.debug = True
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
log = app.logger
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
models = build_models(db)
for m in models:
    globals()[m.__name__] = m

print("Initial upgrade")
with app.app_context():
    upgrade()

session = requests.session()
session.headers.update({"User-Agent": "Tailgate (palfrey@tevp.net)"})

@app.route("/")
def index():
    return render_template('index.html', **config)

@app.route("/lists", methods=["GET"])
def lists_for_user():
    account = request.args["account"]
    lists_raw = session.get(f"https://openlibrary.org/people/{account}/lists.json")
    lists_raw.raise_for_status()    
    user = User.query.filter_by(id=account).first()
    if user is None:
        user = User(id=account)
        db.session.add(user)
        db.session.commit()

    lists = []
    for entry in lists_raw.json()["entries"]:
        lists.append({"name": entry["name"], "id": entry["url"].split("/")[-1]})
    
    return render_template('lists.html', user=user, lists=lists, account=account)

def all_books_for_user_list(account, list_id):
    log.debug("Get following list for %s" % account)
    following = session.get(f"https://openlibrary.org/people/{account}/lists/{list_id}/seeds.json")
    following.raise_for_status()
    authors = []
    all_books = []
    for entry in following.json()["entries"]:
        if entry["type"] != "author":
            continue
        id = entry["url"].split("/")[-1]
        name = entry["title"]
        author = Author.query.filter_by(id=id).first()
        if author is None:
            author = Author(id=id, name=name)
            db.session.add(author)
            db.session.commit()
        authors.append(author)
        all_books.extend(author.books)
    return (authors, all_books)

@app.route("/info/<string:account>/<string:list_id>")
def info(account, list_id):
    user = User.query.filter_by(id=account).first()
    (authors, all_books) = all_books_for_user_list(account, list_id)
    next_books = sorted([x for x in all_books if x.published>datetime.datetime.today()], key=lambda x:x.published)
    prev_books = sorted([x for x in all_books if x.published<datetime.datetime.today()], key=lambda x:x.published, reverse=True)
    return render_template('info.html', account=account, list_id=list_id, authors=sorted(authors, key=lambda x:x.name), next_books=next_books[:5], prev_books=prev_books[:5])

@app.route("/calendar/<string:account>/<string:list_id>")
def calendar(account, list_id):
    user = User.query.filter_by(id=account).first()
    (_, all_books) = all_books_for_user_list(account, list_id)
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Book calendar//')
    cal.add('version','2.0')
    cal.add('X-WR-CALNAME', "Book calendar for %s / %s" % (account, list_id))
    for book in all_books:
        event = icalendar.Event()
        event.add('uid', f"{book.id}-{book.published:%Y%m%d}")
        event.add('dtstart', book.published.date())
        event.add('dtend', (book.published + datetime.timedelta(days=1)).date())
        event.add('dtstamp', datetime.datetime.now())
        event.add('summary', "%s - %s" % (book.author.name, book.title))
        event.add('url', 'https://openlibrary.org/works/%s' % book.id)
        event.add('description', 'hhttps://openlibrary.org/works/%s' % book.id)
        cal.add_component(event)
    resp = make_response(cal.to_ical())
    resp.headers["Content-Type"] = "text/Calendar"
    resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    resp.headers["Expires"] = "Sat, 26 Jul 1997 05:00:00 GMT"
    return resp

@app.route("/author/<string:account>/<string:author_id>/<string:list_id>", methods=["POST"])
def author(account, author_id, list_id):
    author = Author.query.filter_by(id=author_id).first()
    author.update_books()
    return redirect(url_for("info", account=account, list_id=list_id))

def update_authors():
    print("Updating authors")
    order = Author.last_updated.asc()
    if db.session.bind is not None and db.session.bind.dialect.name != "sqlite": # Due to https://bitbucket.org/zzzeek/sqlalchemy/issues/3231/nullsfirst-nullslast-broken-with-sqlite
        order = order.nullsfirst()
    for author in Author.query.order_by(order).all():
        print("Updating %s" % author.name)
        author.update_books()


if __name__ == "__main__":
    with app.app_context():
        update_authors()


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
scheduler = BackgroundScheduler()
job = scheduler.add_job(update_authors, 'cron', hour=9, minute=30)
scheduler.start()