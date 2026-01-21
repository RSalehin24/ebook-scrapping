import requests
from bs4 import BeautifulSoup
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

def fetch_page(url):
    """Fetch HTML content of a page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {url}, Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_content(html):
    """Parse title, author, paragraphs, and links from a page."""
    soup = BeautifulSoup(html, "html.parser")
    content_list = []

    # Title
    title_tag = soup.find("h1", class_="entry-title")
    if title_tag:
        content_list.append(("Title", title_tag.get_text(strip=True)))

    # Author
    author_tag = soup.find("span", class_="author-name")
    if author_tag:
        content_list.append(("Author", author_tag.get_text(strip=True)))

    # Main content / description
    desc_tag = soup.find("div", class_="entry-content")
    links = []
    if desc_tag:
        paragraphs = desc_tag.find_all(["p", "li"])
        for idx, para in enumerate(paragraphs, start=1):
            text = para.get_text(strip=True)
            if text:
                content_list.append((f"Paragraph {idx}", text))

        # Collect all URLs in this content
        for a_tag in desc_tag.find_all("a", href=True):
            links.append(a_tag["href"])

    return content_list, links

def save_to_file(filename, page_url, content_list):
    """Append content to the file in a formatted way."""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"==== Content from: {page_url} ====\n\n")
        for label, text in content_list:
            f.write(f"{label}:\n{text}\n\n")
        f.write("\n\n")

def scrape_page_and_links(url, output_file, visited_urls=None):
    """Scrape a page, save content, and recursively scrape links."""
    if visited_urls is None:
        visited_urls = set()

    if url in visited_urls:
        return
    visited_urls.add(url)

    print(f"Scraping: {url}")
    html = fetch_page(url)
    if html is None:
        return

    content_list, links = parse_content(html)
    save_to_file(output_file, url, content_list)

    # Recursively scrape all found links
    for link in links:
        # Only scrape internal links from eBanglalibrary
        if link.startswith("https://www.ebanglalibrary.com"):
            scrape_page_and_links(link, output_file, visited_urls)

if __name__ == "__main__":
    main_url = "https://www.ebanglalibrary.com/books/%E0%A6%B6%E0%A7%8D%E0%A6%B0%E0%A7%87%E0%A6%B7%E0%A7%8D%E0%A6%A0-%E0%A6%95%E0%A6%AC%E0%A6%BF%E0%A6%A4%E0%A6%BE-%E0%A6%9C%E0%A7%80%E0%A6%AC%E0%A6%A8%E0%A6%BE%E0%A6%A8%E0%A6%A8%E0%A7%8D%E0%A6%A6/"
    output_file = "full_scraped_book.txt"

    # Clear file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    # Start scraping main page and its linked pages
    scrape_page_and_links(main_url, output_file)

    print(f"\nAll scraping done. Content saved in '{output_file}'.")
