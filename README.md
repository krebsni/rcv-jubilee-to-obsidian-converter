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
- Zeph and Phil has extra Zephania/Philippians on books line and outline in text is wrong
- Psa aleph, beth, etc. not working
- Romans, Gen, etc. — not all outline points are correct headings (e.g. C is ## not ###)

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

## Upcoming Improvements / To-Do
- Add link to Biblehub Interlinear by adding [-](https://biblehub.com/interlinear/zephaniah/1-2.htm) after "|-]]" in verse lines
- Check outline level logic, e.g. Gen, Rom
- Change broken paragraph lines
- Change link to outline in `-` to `<book> (Book)` notes
- Add template `Bible` file and include in Bible folder
- Add error links file in `Errors` (e.g. self-referential links in footnotes)
- Psalm 119 aleph, beth, etc. not working
- Verse links in FN paragraphs are wrong, don't hit FN top – maybe change to verse anyway
- Philippians 2 D/E: verse in same line and verse link is loose (actually many outline points)
- **[[Luke#^22-30|Luke 22:30^1]]  table**: see also Matt/Rev cross-references and correct N/Book usage
- Gal 3:2-3 and similar: ensure correct mapping for footnotes with a/b/c, use lexically smallest mapping? (Not sure how to solve this. Perhaps manually...)


## License

MIT