import requests
from bs4 import BeautifulSoup
import os
import time
import shutil
import base64
import re
import json

# -------------------------------
# CONFIG
# -------------------------------
BASE_URL = "https://www.ebanglalibrary.com"
BOOK_URL = "https://www.ebanglalibrary.com/books/%e0%a6%b9%e0%a7%8d%e0%a6%af%e0%a6%be%e0%a6%b0%e0%a6%bf-%e0%a6%aa%e0%a6%9f%e0%a6%be%e0%a6%b0-%e0%a6%8f%e0%a6%a8%e0%a7%8d%e0%a6%a1-%e0%a6%a6%e0%a6%bf-%e0%a6%ab%e0%a6%bf%e0%a6%b2%e0%a6%b8%e0%a6%ab/"

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

OUTPUT_FOLDER = "scraped_book"
HTML_FILE = os.path.join(OUTPUT_FOLDER, "book.html")
COVER_IMAGE_FILE = os.path.join(OUTPUT_FOLDER, "book_cover.jpg")

# -------------------------------
# UTILITIES
# -------------------------------
def get_soup(url):
  response = requests.get(url, headers=HEADERS)
  if response.status_code == 200:
    return BeautifulSoup(response.text, "html.parser")
  else:
    print(f"Failed to fetch {url} (status {response.status_code})")
    return None

def clean_buttons(soup):
  """Remove all <button> elements from a BeautifulSoup object."""
  for button in soup.find_all("button"):
    button.decompose()
  return soup

def make_unique_id(name, existing_ids):
  """Generate a unique HTML id for a lesson/sub-lesson."""
  slug = re.sub(r'\W+', '_', name.strip().lower())
  orig_slug = slug
  counter = 1
  while slug in existing_ids:
    slug = f"{orig_slug}_{counter}"
    counter += 1
  existing_ids.add(slug)
  return slug

def create_output_folder():
  if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
  os.makedirs(OUTPUT_FOLDER)
  print(f"Created folder: {OUTPUT_FOLDER}")

def extract_title_and_author(soup):
  title_tag = soup.find("title")
  if not title_tag:
    return "Book Title", ""

  full_title = title_tag.get_text(strip=True)

  # Split by en dash or hyphen
  for sep in ["–", "-"]:
    if sep in full_title:
      book_title, author = full_title.split(sep, 1)
      return book_title.strip(), author.strip()

  return full_title.strip(), ""

def download_cover_image(soup):
  figure = soup.find("figure", class_="entry-image-link entry-image-single")
  if not figure:
    print("Cover figure not found")
    return None

  img_url = None

  # 1. Try <img> src or data-src
  img_tag = figure.find("img")
  if img_tag:
    img_url = (
      img_tag.get("data-src")
      or img_tag.get("src")
    )

  # 2. Fallback to <source srcset>
  if not img_url:
    source_tag = figure.find("source")
    if source_tag and source_tag.get("srcset"):
      img_url = source_tag.get("srcset").split()[0]

  if not img_url:
    print("Cover image url not found")
    return None

  # Download
  response = requests.get(img_url, headers=HEADERS)
  if response.status_code != 200:
    print("Failed to download cover image")
    return None

  # detect extension
  ext = ".webp" if ".webp" in img_url else ".jpg"
  cover_path = os.path.join(OUTPUT_FOLDER, f"book_cover{ext}")

  with open(cover_path, "wb") as f:
    f.write(response.content)

  print(f"Downloaded cover image: {cover_path}")
  return os.path.basename(cover_path)

def scrape_book_meta(soup):
  """Extract author, series, and book type from the meta div."""
  author_name = ""
  series_name = ""
  book_type = ""

  meta_div = soup.find("div", class_="entry-meta entry-meta-after-content")
  if not meta_div:
    return author_name, series_name, book_type

  # Author
  author_span = meta_div.find("span", class_="entry-terms-authors")
  if author_span:
    a = author_span.find("a")
    if a:
      author_name = a.get_text(strip=True)

  # Series
  series_span = meta_div.find("span", class_="entry-terms-series")
  if series_span:
    a = series_span.find("a")
    if a:
      series_name = a.get_text(strip=True)

  # Book type / genre
  type_span = meta_div.find("span", class_="entry-terms-ld_course_category")
  if type_span:
    a = type_span.find("a")
    if a:
      book_type = a.get_text(strip=True)

  return author_name, series_name, book_type

def scrape_main_content(soup):
  content_div = soup.find("div", class_="ld-tab-content ld-visible entry-content")
  if content_div:
    content_div = clean_buttons(content_div)
    return str(content_div)
  return ""

def get_total_pages(soup):
  pager_div = soup.find("div", class_="ld-pagination ld-pagination-page-course_content_shortcode")
  if pager_div and pager_div.has_attr("data-pager-results"):
    try:
      data_json = json.loads(pager_div["data-pager-results"].replace("&quot;", '"'))
      return int(data_json.get("total_pages", 1))
    except:
      return 1
  return 1

def scrape_lesson_list(soup):
  lessons = []
  lesson_divs = soup.find_all(
    "div",
    class_=lambda c: c and "ld-item-list-item" in c.split() and "ld-item-lesson-item" in c.split()
  )
  for div in lesson_divs:
    a_tag = div.find("a", class_="ld-item-name")
    if a_tag and a_tag.get("href"):
      lesson_url = a_tag["href"]
      lesson_title_div = a_tag.find("div", class_="ld-item-title")
      lesson_title = lesson_title_div.get_text(strip=True) if lesson_title_div else "Lesson"
      lessons.append((lesson_title, lesson_url))
  return lessons

def scrape_all_lessons(book_url):
  all_lessons = []
  page_num = 1
  while True:
    url = f"{book_url}?ld-courseinfo-lesson-page={page_num}"
    soup = get_soup(url)
    if not soup:
      break
    lessons = scrape_lesson_list(soup)
    if not lessons:
      break
    all_lessons.extend(lessons)
    total_pages = get_total_pages(soup)
    if page_num >= total_pages:
      break
    page_num += 1
    time.sleep(1)
  return all_lessons

def scrape_lesson_content(url):
  soup = get_soup(url)
  if not soup:
    return ""
  content_div = soup.find("div", class_="ld-tab-content ld-visible entry-content")
  if content_div:
    content_div = clean_buttons(content_div)
    return str(content_div)
  return ""

# -------------------------------
# SAVE HTML
# -------------------------------
def save_html(book_title, author, series_name, book_type, cover_image, main_content, lessons):
  existing_ids = set()
  html_lines = []

  # HTML header
  html_lines.append("<!DOCTYPE html>")
  html_lines.append("<html lang='bn'>")
  html_lines.append("<head>")
  html_lines.append("  <meta charset='UTF-8'>")
  html_lines.append(f"  <title>{book_title}</title>")
  html_lines.append("  <style>")
  html_lines.append("    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }")
  html_lines.append("    img { max-width: 300px; }")
  html_lines.append("    h1, h2, h3, h4 { margin-top: 1em; }")
  html_lines.append("    ul { list-style-type: disc; margin-left: 20px; }")
  html_lines.append("    a { color: blue; text-decoration: none; }")
  html_lines.append("  </style>")
  html_lines.append("</head>")
  html_lines.append("<body>")

  # Book title, author, type
  html_lines.append(f"  <h1>{book_title}</h1>")
  html_lines.append(f"  <h2>{author}</h2>")
  if series_name:
    html_lines.append(f"  <h3>সিরিজ: {series_name}</h3>")
  if book_type:
    html_lines.append(f"  <h4>{book_type}</h4>")

  # Cover image
  if cover_image:
    html_lines.append(f"  <img src='{cover_image}' alt='Book Cover'><br><br>")

  # Main content
  html_lines.append("  <div id='main_content'>")
  html_lines.append(main_content)
  html_lines.append("  </div>")

  # Table of contents
  html_lines.append("  <hr>")
  html_lines.append("  <h2>সূচিপত্র</h2>")
  html_lines.append("  <ul>")
  lesson_ids = []
  for title, _ in lessons:
    lesson_id = make_unique_id(title, existing_ids)
    lesson_ids.append(lesson_id)
    html_lines.append(f"    <li><a href='#{lesson_id}'>{title}</a></li>")
  html_lines.append("  </ul>")
  html_lines.append("  <hr>")

  # Lesson sections
  for lesson_id, (title, content_html) in zip(lesson_ids, lessons):
    html_lines.append(f"  <h2 id='{lesson_id}'>{title}</h2>")
    html_lines.append(f"  {content_html}")
    html_lines.append("  <br>")

  # Footer
  html_lines.append("</body>")
  html_lines.append("</html>")

  # Write to file
  with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(html_lines))

  print(f"HTML saved at {HTML_FILE}")

# -------------------------------
# MAIN SCRIPT
# -------------------------------
def main():
  create_output_folder()

  soup = get_soup(BOOK_URL)
  if not soup:
    return

  book_title, author = extract_title_and_author(soup)
  meta_author, series_name, book_type = scrape_book_meta(soup)

  cover_image = download_cover_image(soup)
  main_content = scrape_main_content(soup)
  lessons_list = scrape_all_lessons(BOOK_URL)

  lesson_contents = []
  for title, url in lessons_list:
    print(f"Scraping lesson: {title}")
    content_html = scrape_lesson_content(url)
    lesson_contents.append((title, content_html))
    time.sleep(1)

  save_html(book_title, author, series_name, book_type, cover_image, main_content, lesson_contents)

if __name__ == "__main__":
  main()
