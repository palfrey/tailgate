import datetime
import author_list
import logging
import humanize

log = logging.getLogger("models")

def build_models(db):
    class User(db.Model):
        id = db.Column(db.String, primary_key=True)
    
    class Follows(db.Model):
        user_id = db.Column(db.String, db.ForeignKey('user.id'), primary_key=True)
        follows = db.Column(db.String, db.ForeignKey('author.id'), primary_key=True)

    class Author(db.Model):
        id = db.Column(db.String, primary_key=True)
        name = db.Column(db.String, nullable=False)
        last_updated = db.Column(db.DateTime, nullable=True)
        books = db.relationship('Book', backref='author', lazy='dynamic')

        def pretty_update(self):
            if self.last_updated is None:
                return "never"
            return humanize.naturaltime(
                datetime.datetime.now() - self.last_updated)

        def update_books(self):
            log.info("Updating %s" % self.name)
            books = author_list.get_books(self, Book, db.session)
            self.last_updated = datetime.datetime.now()
            db.session.commit()

    class Book(db.Model):
        id = db.Column(db.String, primary_key=True)
        title = db.Column(db.String, nullable=False)
        published = db.Column(db.DateTime, nullable=False)
        author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    return (User, Follows, Author, Book)