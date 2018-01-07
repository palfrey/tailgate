import requests, datetime
from xml.etree import ElementTree
import logging

def get_books(key, author_obj):
    all_books = {}

    page = 1
    def parse_val(val):
        if val == None:
            return 1
        else:
            return int(val)

    while True:
        logging.debug("Page %d", page)
        url = "https://www.goodreads.com/search/index.xml?q=%s&search=author&page=%s&key=%s" % (author_obj.name, page, key)
        following = requests.get(url)
        following.raise_for_status()
        tree = ElementTree.fromstring(following.content)
        books = tree.findall("./search/results/work")

        for book in books:
            title = book.find("best_book/title").text
            for author in book.findall("best_book/author"):
                if int(author.find("id").text) == author_obj.id:
                    break
            else:
                logging.debug("Skipping %s", title)
                break

            when = datetime.date(parse_val(book.find("original_publication_year").text), parse_val(book.find("original_publication_month").text), parse_val(book.find("original_publication_day").text))
            if when == datetime.date(1,1,1):
                continue
            if title not in all_books or (when !=None and all_books[title]["when"] > when):
                all_books[title] = {"when": when, "id": int(book.find("best_book/id").text)}
        if len(books) == 10:
            page +=1
        else:
            break
    return all_books