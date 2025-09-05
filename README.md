# Rcv Jubilee to Obsidian

This project converts RCV Jubilee Bible HTML files into clean, well-structured Obsidian Markdown notes, including outlines, footnotes, and navigation links.

## Features

- Converts RCV Jubilee Bible source files to Obsidian-compatible Markdown
- Handles outlines, footnotes, navigation, and verse anchors
- Cleans up and formats links, headings, and special blocks
- Supports robust text processing for edge cases

## Post-Editing (Manual)

- Note links referring to other notes in same verse may be broken
- Exo 40 last two outlines points not correct
- Zech needs post processing (top and bottom)
- Zeph and Phil has extra Zephania/Philippians on books line

## Structure

- `bible_processor/`: Main Python package with all processing logic
  - `main.py`: Entry point for conversion
  - `utils.py`: Utility functions for text and markdown processing
  - `parsers.py`: Parsing and formatting pipeline
  - `constants.py`: Book abbreviation and mapping constants
- `Bible/`: Contains processed output files
  - `Text/`, `Footnotes/`, `Outlines/`: Output folders for different content types

## Usage

1. Install requirements (see below)
2. Run the main script:
   ```sh
   python -m bible_processor.main <input_file> <output_folder>
   ```
3. Output will be in the `Bible/` directory, ready for use in Obsidian.

## Debugging in VSC

- See `launch.json` for configuration to run and debug the `main.py` script directly in Visual Studio Code.

## Requirements

- Python 3.8+
- BeautifulSoup4

Install dependencies:
```sh
pip install -r requirements.txt
```

## TODO

- Use bases and properties (e.g. for footnote and outline files, background etc.)
- Change broken paragraph lines
- Add link to [BibleHub Interlinear](https://biblehub.com/interlinear/john/15-19.htm)?
- Change link to outline in `-` to `<book> (Book)` notes
- Add template `Bible` file and include in Bible folder
- Add error links file in `Errors` (e.g. `*` links or self-referential links in footnotes)
- Subject not working for Matthew/Mark/Luke + Psalms
- Both links in outline points between text now point to X (Book) – one should point to XO, and dashes in verse references should also point to book outline
- Maybe make [[Book]] reference before chapter disappear and use one between next and previous to go to top
- Song of Songs text: ensure empty line before chapter/section headings
- Half verses (a/b) split, e.g. Eph 3:17 not working; need non-a/b reference for links
- Outline hover in X (Book) only shows point itself – change to outline heading link, or use headings per verse
- Reference for title (e.g. Psalm)
- 1 Tim 5:18 footnotes not recognized (likely all references where one side is a quote)
- Deut. 2x 5:4 wrong format (bracket of footnote became part of verse)
- Footnote mapping: ensure correct mapping for a/b/c footnotes, use lexically smallest mapping
- Instead of [[Luke#Luke|Luke]] line, combine in previous/next line
- Psalm 119 aleph, beth, etc. not working
- Put verse line before --- (nicer separation), e.g. Psalms, also has title/verse directly after
- Romans: not all outline points are correct headings (e.g. C is ## not ###)
- Verse links in FN paragraphs are wrong, don't hit FN top – maybe change to verse anyway
- Philippians 2 D/E: verse in same line and verse link is loose (actually many outline points)
- Empty reference (i.e. nothing in display part) – use * instead of nothing
- **[[Luke#^22-30|Luke 22:30^1]]  table**: see also Matt/Rev cross-references and correct N/Book usage
- Gal 3:2-3 and similar: ensure correct mapping for footnotes with a/b/c, use lexically smallest mapping
- New chapter line separation not correct (last verse in chapter)
- Chapter lines not always followed by empty line (e.g. Ecclesiastes)
- a/b become ^3-17a (should be handled for one-chapter books as well)

## Completed

- `*` links: if there is word directly after, change the link in post-processing; for cursive, move the formatting outside the link ("|*]]*X*" → "|*X*]]")
- Cursive formatting
- Last chapter heading for Psalms now works (e.g. Psa 150)
- One-chapter books (e.g. Obadiah) links now work
- a/b verse handling for one-chapter books
- Chapter lines now always followed by empty line
- a/b become ^3-17a

## License

MIT
