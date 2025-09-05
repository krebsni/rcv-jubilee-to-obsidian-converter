"""
Main entry point for Bible processing scripts.
"""

import os
import sys
from pathlib import Path
from .constants import BOOK_ABBR, JUBILEE_ABRV_TO_FULL_BOOK
from .parsers import parse_text, pre_process_footnotes, parse_footnotes, parse_outline
from tqdm import tqdm

def process_all_files(folder_path: str, output_dir: str, book_name: str = None):
    """Process all HTML files in a folder and insert footnotes into the database."""
    all_files = [f for f in os.listdir(folder_path) if f.endswith("N.htm")]
    base_files = [os.path.splitext(f)[0][:-1] for f in all_files]  # Remove 'N' before .htm
    print(f"Found {len(base_files)} books to process.")

    # First run: find all footnote references
    all_refs = {}
    for base in tqdm(base_files, desc="Pre-processing footnotes", unit="book"):
        note_file = os.path.join(folder_path, f"{base}N.htm")
        if not os.path.exists(note_file):
            continue
        current_book_long = JUBILEE_ABRV_TO_FULL_BOOK.get(base)
        current_book = BOOK_ABBR.get(current_book_long)
        all_refs[current_book] = pre_process_footnotes(note_file)

    if book_name:
        print(f"Processing only book: {book_name}")
    for base in tqdm(base_files, desc="Processing books", unit="book"):
        note_file = os.path.join(folder_path, f"{base}N.htm")
        outline_file = os.path.join(folder_path, f"{base}O.htm")
        text_file = os.path.join(folder_path, f"{base}.htm")
        if not (os.path.exists(note_file) and os.path.exists(text_file)):
            continue
        current_book_long = JUBILEE_ABRV_TO_FULL_BOOK.get(base)
        current_book = BOOK_ABBR.get(current_book_long)
        if book_name and current_book != book_name:
            continue
        text = parse_text(text_file, current_book, all_refs)
        notes = parse_footnotes(note_file, current_book, all_refs)
        outline = parse_outline(outline_file, current_book)


        chapter_path = os.path.join(output_dir, "Text", f"{current_book}.md")
        chapter_note_path = os.path.join(output_dir, "Footnotes", f"{current_book}N.md")
        outline_path = os.path.join(output_dir, "Outlines", f"{current_book}O.md")
        Path(os.path.dirname(chapter_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(chapter_note_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(outline_path)).mkdir(parents=True, exist_ok=True)
        with open(chapter_path, "w", encoding="utf-8") as f:
            f.write(text)
        with open(chapter_note_path, "w", encoding="utf-8") as f:
            f.write(notes)
        with open(outline_path, "w", encoding="utf-8") as f:
            f.write(outline)

        # Copy Bible.base template into the output base path if it exists
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "Bible.base")
        output_base_path = os.path.join(output_dir, "Bible.base")
        if os.path.exists(template_path) and not os.path.exists(output_base_path):
          Path(os.path.dirname(output_base_path)).mkdir(parents=True, exist_ok=True)
          with open(template_path, "r", encoding="utf-8") as src, open(output_base_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())




def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process Bible HTML files to markdown.")
    parser.add_argument("input_dir", nargs="?", help="Input directory containing HTML files")
    parser.add_argument("output_dir", nargs="?", default="Bible", help="Output directory for markdown files")
    parser.add_argument('--book_name', type=str, help="Name of the book to process (optional)")
    args = parser.parse_args()
    process_all_files(args.input_dir, args.output_dir, args.book_name)

if __name__ == "__main__":
    main()
