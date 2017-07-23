import requests, datetime
from xml.etree import ElementTree
import yaml
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)

all_books = {}
config = yaml.load(open("config.yml").read())

page = 1
author_id = 8794
author_name = "Charles%20Stross"

def parse_val(val):
    if val == None:
        return 1
    else:
        return int(val)

while True:
    logging.debug("Page %d", 
    page)
    url = "https://www.goodreads.com/search/index.xml?key=%s&q=%s&search=author&page=%s" % (config["goodreads"]["key"], author_name, page)
    following = requests.get(url)
    following.raise_for_status()
    tree = ElementTree.fromstring(following.content)
    books = tree.findall("./search/results/work")

    for book in books:
        title = book.find("best_book/title").text
        for author in book.findall("best_book/author"):
            if int(author.find("id").text) == author_id:
                break
        else:
            logging.debug("Skipping %s", title)
            break

        when = datetime.date(parse_val(book.find("original_publication_year").text), parse_val(book.find("original_publication_month").text), parse_val(book.find("original_publication_day").text))
        if when == datetime.date(1,1,1):
            continue
        if title not in all_books or (when !=None and all_books[title]["when"] > when):
            all_books[title] = {"when": when}
    if len(books) == 20:
        page +=1
    else:
        break

for (name, info) in sorted(all_books.items(), key=lambda x:x[1]["when"]):
    logging.debug("%s: %s", info["when"], name)