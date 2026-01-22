import os
from epub_properties.epub_builder import EpubBuilder

def create_epub(book_data):
    """Generate EPUB book from scraped data."""
    builder = EpubBuilder(
        book_title=book_data["book_title"],
        author=book_data["author"],
        series=book_data["series"],
        book_type=book_data["book_type"],
        output_folder=book_data["output_folder"]
    )
    
    cover_path = os.path.join(book_data["output_folder"], book_data["cover"])
    builder.add_cover_page(cover_image_path=cover_path)
    builder.add_title_page()
    builder.add_info_page(translator="", additional_info="")
    builder.add_dedication_page(dedication_text="")
    builder.add_main_content_page(main_content=book_data["main_content"])

    toc_lessons = [
        (title, f"lesson_{i+1}.xhtml")
        for i, (title, _) in enumerate(book_data["lessons"])
    ]
    builder.add_toc_page(lessons=toc_lessons)
    builder.add_lesson_pages(book_data["lessons"])

    epub_filename = f"{book_data['book_title']}.epub"
    builder.build_epub(epub_filename)
