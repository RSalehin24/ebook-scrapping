import requests
import time
import json
import re
import os
import shutil
from bs4 import BeautifulSoup
from config import HEADERS

def get_soup(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    print(f"Failed to fetch {url} ({response.status_code})")
    return None

def clean_buttons(soup):
    for button in soup.find_all("button"):
        button.decompose()
    return soup

def sanitize_folder_name(name):
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name

def create_output_folder(book_title):
    parent_dir = os.path.dirname(os.path.abspath(__file__))

    base_folder = os.path.join(os.path.dirname(parent_dir), "outputs")
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        print(f"Created base folder: {base_folder}")

    folder_name = sanitize_folder_name(book_title)
    full_path = os.path.join(base_folder, folder_name)

    if not os.path.exists(full_path):
        os.makedirs(full_path)
        print(f"Created folder: {full_path}")
    else:
        print(f"Folder already exists: {full_path}")

    return full_path

def extract_title_and_author(soup):
    title_tag = soup.find("title")
    if not title_tag:
        return "Book Title", ""

    full_title = title_tag.get_text(strip=True)
    for sep in ["–", "-"]:
        if sep in full_title:
            return map(str.strip, full_title.split(sep, 1))
    return full_title, ""

def scrape_book_meta(soup):
    author = series = book_type = ""

    meta = soup.find("div", class_="entry-meta entry-meta-after-content")
    if not meta:
        return author, series, book_type

    def get_text(cls):
        span = meta.find("span", class_=cls)
        return span.find("a").get_text(strip=True) if span and span.find("a") else ""

    author = get_text("entry-terms-authors")
    series = get_text("entry-terms-series")
    book_type = get_text("entry-terms-ld_course_category")

    return author, series, book_type

def download_cover_image(soup, output_folder):
    figure = soup.find("figure", class_="entry-image-link entry-image-single")
    if not figure:
        return None

    img = figure.find("img")
    img_url = img.get("data-src") or img.get("src") if img else None

    if not img_url:
        source = figure.find("source")
        img_url = source.get("srcset").split()[0] if source else None

    if not img_url:
        return None

    response = requests.get(img_url, headers=HEADERS)
    if response.status_code != 200:
        return None

    ext = ".webp" if ".webp" in img_url else ".jpg"
    filename = f"book_cover{ext}"
    
    with open(os.path.join(output_folder, filename), "wb") as f:
        f.write(response.content)

    return filename

def scrape_main_content(soup):
    div = soup.find("div", class_="ld-tab-content ld-visible entry-content")
    if div:
        div = clean_buttons(div)
        return div.decode_contents()
    return ""

def get_total_pages(soup):
    pager = soup.find("div", class_="ld-pagination ld-pagination-page-course_content_shortcode")
    if pager and pager.has_attr("data-pager-results"):
        try:
            data = json.loads(pager["data-pager-results"].replace("&quot;", '"'))
            return int(data.get("total_pages", 1))
        except Exception:
            pass
    return 1

def scrape_lesson_list(soup):
    lessons = []
    items = soup.find_all(
        "div",
        class_=lambda c: c and "ld-item-lesson-item" in c
    )

    for item in items:
        a = item.find("a", class_="ld-item-name")
        if not a:
            continue
        title_div = a.find("div", class_="ld-item-title")
        title = title_div.get_text(strip=True) if title_div else "Lesson"
        lessons.append((title, a["href"]))

    return lessons

def scrape_all_lessons(book_url):
    lessons = []
    page = 1

    while True:
        soup = get_soup(f"{book_url}?ld-courseinfo-lesson-page={page}")
        if not soup:
            break

        lessons.extend(scrape_lesson_list(soup))
        if page >= get_total_pages(soup):
            break

        page += 1
        time.sleep(1)

    return lessons

def scrape_lesson_content(url):
    soup = get_soup(url)
    if not soup:
        return ""

    div = soup.find("div", class_="ld-tab-content ld-visible entry-content")
    if div:
        div = clean_buttons(div)
        return div.decode_contents()
    return ""

def scrape_book_data(book_url):
    soup = get_soup(book_url)
    if not soup:
        print("Failed to fetch the book page.")
        return None

    book_title, title_author = extract_title_and_author(soup)
    meta_author, series, book_type = scrape_book_meta(soup)
    author = meta_author or title_author
    output_folder = create_output_folder(book_title)

    cover = download_cover_image(soup, output_folder)
    main_content = scrape_main_content(soup)

    lessons = []
    all_lessons = scrape_all_lessons(book_url)
    for title, url in all_lessons:
        print(f"Scraping lesson: {title}")
        content = scrape_lesson_content(url)
        lessons.append((title, content))
        time.sleep(1)

    return {
        "book_title": book_title,
        "author": author,
        "series": series,
        "book_type": book_type,
        "cover": cover,
        "main_content": main_content,
        "lessons": lessons,
        "output_folder": output_folder
    }
