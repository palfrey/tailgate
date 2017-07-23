import datetime
import author_list

def build_models(db):
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        token = db.Column(db.String, nullable=False)
        token_secret = db.Column(db.String, nullable=False)
    
    class Follows(db.Model):
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
        follows = db.Column(db.Integer, db.ForeignKey('author.id'), primary_key=True)

    class Author(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, nullable=False)
        name = db.Column(db.String, nullable=False)
        last_updated = db.Column(db.DateTime, nullable=True)
        books = db.relationship('Book', backref='author_', lazy='dynamic')

        def update_books(self, session):
            if self.last_updated is None:
                books = author_list.get_books(session, self)
                for book in Book.query.filter_by(author=self.id):
                    db.session.delete(book)
                for title, values in books.items():
                    db.session.add(Book(id=values["id"], title=title, published=values["when"], author=self.id))
                self.last_updated = datetime.datetime.now()
                db.session.commit()

    class Book(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String, nullable=False)
        published = db.Column(db.DateTime, nullable=False)
        author = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    return (User, Follows, Author, Book)