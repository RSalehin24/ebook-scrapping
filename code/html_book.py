import os
import re
from html import escape

def make_unique_id(name, existing):
    slug = re.sub(r"\W+", "_", name.lower().strip())
    base = slug
    i = 1
    while slug in existing:
        slug = f"{base}_{i}"
        i += 1
    existing.add(slug)
    return slug

def save_html(book_title, author, series, book_type, cover, main_content, lessons, output_folder):
    existing_ids = set()

    html = f"""<!DOCTYPE html>
<html lang='bn'>
  <head>
    <meta charset="UTF-8">
    <title>{escape(book_title)}</title>
    <style>
      body {{ font-family: Arial; line-height: 1.6; margin: 20px; }}
      img {{ max-width: 300px; }}
      a {{ color: blue; text-decoration: none; }}
    </style>
  </head>
  <body>
    <h1>{escape(book_title)}</h1>
    <h2>{escape(author)}</h2>"""

    if series:
        html += f"\n    <h3>সিরিজ: {escape(series)}</h3>"
    if book_type:
        html += f"\n    <h4>{escape(book_type)}</h4>"

    if cover:
        html += f"\n    <img src='{cover}' alt='Book Cover'><br><br>"

    indented_content = "\n".join(f"    {line}" for line in main_content.splitlines())
    html += f"\n{indented_content}\n"

    html += "\n    <hr>\n    <h2>সূচিপত্র</h2>\n    <ul>"
    lesson_ids = []
    for title, _ in lessons:
        lid = make_unique_id(title, existing_ids)
        lesson_ids.append(lid)
        html += f"\n      <li><a href='#{lid}'>{escape(title)}</a></li>"
    html += "\n    </ul>\n    <hr>"

    for lid, (title, content) in zip(lesson_ids, lessons):
        html += f"\n    <h2 id='{lid}'>{escape(title)}</h2>\n    <div>"
        indented_lesson = "\n".join(f"      {line}" for line in content.splitlines())
        html += f"\n{indented_lesson}\n    </div><br>"

    html += "\n  </body>\n</html>"

    html_file = os.path.join(output_folder, "book.html")
    if os.path.exists(html_file):
        print(f"Replacing existing HTML file: {html_file}")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML saved at {html_file}")

def create_html_book(book_data):
    save_html(
        book_title=book_data["book_title"],
        author=book_data["author"],
        series=book_data["series"],
        book_type=book_data["book_type"],
        cover=book_data["cover"],
        main_content=book_data["main_content"],
        lessons=book_data["lessons"],
        output_folder=book_data["output_folder"]
    )
