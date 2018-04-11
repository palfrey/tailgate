import requests, datetime
from xml.etree import ElementTree
import logging

def get_books(key, author_obj):
    all_books = {}

    def parse_val(val):
        if val == None:
            return 1
        else:
            return int(val)

    # Some authors have a good author list
    page = 1
    while True:
        url = "https://www.goodreads.com/author/list/%s?format=xml&key=%s&page=%d" % (author_obj.id, key, page)
        print(url)
        author_list = requests.get(url)
        author_list.raise_for_status()
        tree = ElementTree.fromstring(author_list.content)
        books = tree.findall("./author/books/book")
        for book in books:
            #raise Exception(ElementTree.tostring(book))
            title = book.find("title").text
            when = datetime.date(parse_val(book.find("publication_year").text), parse_val(book.find("publication_month").text), parse_val(book.find("publication_day").text))
            if when == datetime.date(1,1,1):
                continue
            if when == None:
                raise Exception(book)
            if title not in all_books or (when !=None and all_books[title]["when"] > when):
                all_books[title] = {"when": when, "id": int(book.find("id").text)}
        if len(books) == 30:
            page +=1
        else:
            break

    # ... and some you need to search for
    page = 1
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