from scraper import scrape_book_data
from html_book import create_html_book
from epub_book import create_epub
from config import BOOK_URL

def main():
    data = scrape_book_data(BOOK_URL)
    if not data:
        exit(1)

    create_html_book(data)
    create_epub(data)

    print("Book generation complete!")

if __name__ == "__main__":
    main()
    
