import os
from ebooklib import epub
from jinja2 import Environment, FileSystemLoader

class EpubBuilder:
    def __init__(self, book_title, author, series="", book_type="", output_folder=""):
        self.book_title = book_title
        self.author = author
        self.series = series
        self.book_type = book_type
        self.output_folder = output_folder
        self.env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "page_templates"))
        )
        self.book = epub.EpubBook()
        self.book.set_title(book_title)
        self.book.set_language("bn")
        self.book.add_author(author)
        self.chapters = []

    def render_template(self, template_name, **context):
        template = self.env.get_template(template_name)
        return template.render(**context)

    def add_cover_page(self, cover=None):
        html_content = self.render_template("cover.html", cover=cover)
        c = epub.EpubHtml(title="Cover", file_name="cover.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)

    def add_title_page(self):
        html_content = self.render_template("title_page.html", book_title=self.book_title, author=self.author)
        c = epub.EpubHtml(title="Title Page", file_name="title.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)

    def add_info_page(self, translator="", additional_info=""):
        html_content = self.render_template(
            "info_page.html",
            book_title=self.book_title,
            author=self.author,
            translator=translator,
            series=self.series,
            book_type=self.book_type,
            additional_info=additional_info
        )
        c = epub.EpubHtml(title="Info", file_name="info.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)

    def add_dedication_page(self, dedication_text=""):
        html_content = self.render_template("dedication.html", dedication_text=dedication_text)
        c = epub.EpubHtml(title="Dedication", file_name="dedication.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)
        
    def add_main_content_page(self, main_content):
        html_content = self.render_template("main_content.html", main_content=main_content)
        c = epub.EpubHtml(title="Main Content", file_name="main_content.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)

    def add_toc_page(self, lessons):
        html_content = self.render_template("toc.html", lessons=lessons)
        c = epub.EpubHtml(title="Contents", file_name="toc.xhtml", content=html_content)
        self.book.add_item(c)
        self.chapters.append(c)

    def add_lesson_pages(self, lessons):
        for idx, (title, content) in enumerate(lessons, start=1):
            html_content = self.render_template("lesson.html", lesson_title=title, lesson_content=content)
            file_name = f"lesson_{idx}.xhtml"
            c = epub.EpubHtml(title=title, file_name=file_name, content=html_content)
            self.book.add_item(c)
            self.chapters.append(c)

    def build_epub(self, filename="book.epub"):
        self.book.toc = tuple(self.chapters)
        self.book.spine = ["nav"] + self.chapters
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        epub.write_epub(os.path.join(self.output_folder, filename), self.book)
        print(f"EPUB saved at {os.path.join(self.output_folder, filename)}")
