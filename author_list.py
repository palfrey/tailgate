from typing import cast

import requests
import dateutil

session = requests.session()
session.headers.update({"User-Agent": "Tailgate (palfrey@tevp.net)"})


def get_books(author_obj, Book, db_session):
    all_books = {}

    url = "https://openlibrary.org/authors/%s/works.json?offset=0" % author_obj.id
    while True:        
        print(url)
        author_list = session.get(url)
        author_list.raise_for_status()
        books = author_list.json()["entries"]
        for book in books:
            try:
                for author in book["authors"]:
                    if (author["type"] == "/type/author_role" or author["type"]["key"] == "/type/author_role") and author["author"]["key"] == "/authors/%s" % author_obj.id:
                        break
                else:
                    print("Can't find author", book )
                    continue
            except (KeyError, TypeError):
                raise Exception(book["authors"])

            id = book["key"].split("/")[-1]
            existing_book = Book.query.filter_by(id=id).first()
            if existing_book is not None:
                print("existing", existing_book.__dict__)
                all_books[existing_book.title] = existing_book
                continue

            if "title" not in book:
                continue
            title = book["title"]

            editions = session.get(f"https://openlibrary.org/works/{id}/editions.json")
            editions.raise_for_status()
            dates = []
            for edition in editions.json()["entries"]:
                book_id = edition["key"].split("/")[-1]

                languages = edition.get("languages",[])
                if len(languages) > 0:
                    language_key = languages[0].get("key", "")
                    if language_key.startswith("/languages/") and language_key != "/languages/eng":
                        continue

                book_obj = session.get(f"https://openlibrary.org/books/{book_id}.json")
                book_obj.raise_for_status()
                book_obj = book_obj.json()

                if "publish_date" not in book_obj:
                    continue

                if "audiobook" in book_obj.get("physical_format", "").lower():
                    continue

                dates.append(book_obj["publish_date"])

            if len(dates) == 0:
                continue
            longest_date = sorted(dates, reverse=True, key=lambda d: len(d))[0]
            try:
                when = dateutil.parser.parse(longest_date)
            except Exception:
                raise Exception((longest_date, dates))
            new_book = Book(id=id, title=title, published=when, author_id=author_obj.id)
            print(new_book.__dict__)
            db_session.add(new_book)
            db_session.commit()
            all_books[title] = new_book
        next_page = author_list.json()["links"].get("next")
        if next_page is None:
            break
        url = "https://openlibrary.org" +next_page

    return all_books