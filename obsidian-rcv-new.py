import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

# First category "verse/chapter":
# "v. <v>", "verse <v>", "verses <v>", "vv. <v>-<v-end>", and the same with first v capitalized.
# "ch. <ch>", "chapter <ch>", "chs. <ch>-<ch-end>", "chapters <ch>-<ch-end>", and the same with first c captitalized.
# Second category "reference string": a reference string is entered with a long Bible book name or abbreviated Bible book name, e.g. "1 Cor. 3:10;  10:23;  14:4, 5;  Rom. 14:19", or "1 Corinthians 3:1..." but it can also start with a "<ch>:<v>[-<v-end>]" string (not just a digit but a ch-v combination (with optional verse range, and optional continuation, e.g. "4:4, 5;  Rom. 14:19". Note that the end of it is determined by a token that is either not a number, comma or semicolon or not a book name (abbreviation or long). Note also that in e.g. "1 Cor. 3:10 1" the last digit is not part of the reference string, since different references inside the reference string must be separated by a comma or semi-colon.

# Third category: only bible book name (either long or abbreviated). In this case no replacement is made (link inserted) but the book is extracted and stored in variable for later use.

# Furthermore, keep track of the last detected book for all categories and if a reference appears without book (in first/second category without bible book), the most recent bible book occurence in the analyzed text is used.

# --- Bible Book Abbreviations and Mappings ---
BOOK_ABBR = {
    "Genesis": "Gen",
    "Exodus": "Exo",
    "Leviticus": "Lev",
    "Numbers": "Num",
    "Deuteronomy": "Deut",
    "Joshua": "Josh",
    "Judges": "Judg",
    "Ruth": "Ruth",
    "1 Samuel": "1 Sam",
    "2 Samuel": "2 Sam",
    "1 Kings": "1 Kings",
    "2 Kings": "2 Kings",
    "1 Chronicles": "1 Chron",
    "2 Chronicles": "2 Chron",
    "Ezra": "Ezra",
    "Nehemiah": "Neh",
    "Esther": "Esth",
    "Job": "Job",
    "Psalms": "Psa",
    "Proverbs": "Prov",
    "Ecclesiastes": "Eccl",
    "Song of Solomon": "SoS",
    "Song of Songs": "SoS",
    "S.S": "SoS",
    "S.S.": "SoS",
    "S. S.": "SoS",
    "S. S": "SoS",
    "SS": "SoS",
    "Isaiah": "Isa",
    "Jeremiah": "Jer",
    "Lamentations": "Lam",
    "Ezekiel": "Ezek",
    "Daniel": "Dan",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obad",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nah",
    "Habakkuk": "Hab",
    "Zephaniah": "Zep",
    "Haggai": "Hag",
    "Zechariah": "Zech",
    "Malachi": "Mal",
    "Matthew": "Matt",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Romans": "Rom",
    "1 Corinthians": "1 Cor",
    "2 Corinthians": "2 Cor",
    "Galatians": "Gal",
    "Ephesians": "Eph",
    "Philippians": "Phil",
    "Colossians": "Col",
    "1 Thessalonians": "1 Thes",
    "2 Thessalonians": "2 Thes",
    "1 Timothy": "1 Tim",
    "2 Timothy": "2 Tim",
    "Titus": "Titus",
    "Philemon": "Philem",
    "Hebrews": "Heb",
    "James": "James",
    "1 Peter": "1 Pet",
    "2 Peter": "2 Pet",
    "1 John": "1 John",
    "2 John": "2 John",
    "3 John": "3 John",
    "Jude": "Jude",
    "Revelation": "Rev"
}

JUBILEE_ABRV_TO_FULL_BOOK = {
    'Jon': 'Jonah',
    '2Pe': '2 Peter',
    '2Th': '2 Thessalonians',
    '2Jo': '2 John',
    'SoS': 'Song of Solomon',
    'Jud': 'Jude',
    'Jam': 'James',
    'Job': 'Job',
    '2Ki': '2 Kings',
    '1Co': '1 Corinthians',
    '2Ti': '2 Timothy',
    'Phi': 'Philippians',
    'Jdg': 'Judges',
    'Prv': 'Proverbs',
    'Isa': 'Isaiah',
    'Col': 'Colossians',
    'Deu': 'Deuteronomy',
    'Est': 'Esther',
    'Lam': 'Lamentations',
    'Mrk': 'Mark',
    '1Ch': '1 Chronicles',
    'Gen': 'Genesis',
    'Joh': 'John',
    'Exo': 'Exodus',
    'Jer': 'Jeremiah',
    'Hag': 'Haggai',
    'Joe': 'Joel',
    '1Sa': '1 Samuel',
    'Ecc': 'Ecclesiastes',
    '3Jo': '3 John',
    '2Co': '2 Corinthians',
    '1Ti': '1 Timothy',
    'Jos': 'Joshua',
    'Tit': 'Titus',
    'Zec': 'Zechariah',
    '1Pe': '1 Peter',
    'Luk': 'Luke',
    'Psa': 'Psalms',
    'Lev': 'Leviticus',
    'Oba': 'Obadiah',
    '1Ki': '1 Kings',
    '1Jo': '1 John',
    '1Th': '1 Thessalonians',
    'Phm': 'Philemon',
    'Rut': 'Ruth',
    'Hos': 'Hosea',
    'Gal': 'Galatians',
    'Mat': 'Matthew',
    'Zep': 'Zephaniah',
    'Num': 'Numbers',
    'Mic': 'Micah',
    'Hab': 'Habakkuk',
    'Eph': 'Ephesians',
    'Nah': 'Nahum',
    '2Sa': '2 Samuel',
    'Act': 'Acts',
    'Dan': 'Daniel',
    'Mal': 'Malachi',
    'Ezk': 'Ezekiel',
    '2Ch': '2 Chronicles',
    'Amo': 'Amos',
    'Neh': 'Nehemiah',
    'Heb': 'Hebrews',
    'Rom': 'Romans',
    'Rev': 'Revelation',
    'Ezr': 'Ezra'
}

BOOK_ABBR_REVERSE = {v: (k if k != "SS" else "Song of Songs") for k, v in BOOK_ABBR.items()}
JUBILEE_ABRV_TO_FULL_BOOK_REVERSE = {v: k for k, v in JUBILEE_ABRV_TO_FULL_BOOK.items()}

# --- Utility Functions ---
def get_book_abbr(book):
    return BOOK_ABBR.get(book, book)

# --- Markdown Outline Mapping ---
OUTLINE_MAP = {
    "h1": "#",
    "tt": "##",
    "h5": "###",
    "del": "####",
    "var": "#####",
    "code": "######"
}

def map_outline(line, current_book):
    m = re.match(r'^\(?\[\[[^#]*#\^o([^\|]+)\|([^\]]+)\]\](.*)', line)
    if not m:
        return line
    num, label, rest = m.groups()
    label = label.strip()
    line = re.sub(
        r'\[\[[^#]*#\^o',
        f'[[{BOOK_ABBR_REVERSE.get(current_book)} (Book)#^o',
        line,
        count=1
    )
    line = line + f" ^o{num}"
    if re.match(r'^[IVXLCDM]+\.$', label):
        return f"## {line}"
    elif re.match(r'^[A-Z]\.$', label):
        return f"### {line}"
    elif re.match(r'^\d+\.$', label):
        return f"#### {line}"
    elif re.match(r'^[a-z]\.$', label):
        return f"##### {line}"
    elif re.match(r'^\(\d+\)$', label):
        return f"###### {line}"
    elif re.match(r'^\([a-z]\)$', label):
        return f"*{line}*"
    else:
        return f"*{line}*"

# --- HTML to Obsidian Link Conversion ---
def convert_to_obsidian_link(tag, current_book, all_refs):
    href = tag.get("href", "")
    name = tag.get("name", "")
    # If <s> tag exists within, insert ^ between main text and <s> text
    if tag.find('s'):
      s = tag.find('s')
      s.replace_with(f"^{s.get_text()}")
    text = tag.get_text()

    # Replace any occurrence of a Jubilee abbreviation (key) in the text with its mapped BOOK_ABBR value
    for jubilee_abbr, full_book in JUBILEE_ABRV_TO_FULL_BOOK.items():
      abbr = BOOK_ABBR.get(full_book, full_book)
      # Replace only whole word matches (case-sensitive)
      text = re.sub(rf'\b{re.escape(jubilee_abbr)}\b', abbr, text)

    match = re.match(r'(?:([\w]+)\.htm)?(?:#([^"]+))?', href)
    if match:
        file, anchor = match.groups()

        # if anchor and "Title" in anchor:
        #    print("Here")

        # Determine Obsidian file that is linked
        is_note, is_outline = False, False
        if file and file.endswith("N"):
            file = file[:-1]
            is_note = True
        elif file and file.endswith("O"):
            file = file[:-1]
            is_outline = True
        book = ""

        if file == "a":
            book = "Bible" # Overview of all books
        elif is_outline:
            book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) + 'O'
        elif file:
            book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) + ('N' if is_note else '')

        chapter = None
        if anchor and (anchor.startswith("v") or anchor.startswith("n")):
          m = re.match(r'n(?:(\d+)_)?(\d+|Title)(?:x([^P]+)(?:P(\d+))?)', anchor)
          if m:
             # footnote link
            chapter = m.group(1)
            verse = m.group(2)
            note = m.group(3)
            tmp_book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) if file else ""
            if not tmp_book:
               # might be reference to other footnote in same fn document
               tmp_book = current_book
            # get long tag
            if chapter:
              anchor = all_refs[tmp_book][f"{chapter}{(f'-{verse}x{note}' if note else f'-{verse}') if verse else ""}"]
            else:
              anchor = all_refs[tmp_book][f"{(f'{verse}x{note}' if note else f'{verse}') if verse else ""}"]

          m = re.match(r'v(\d+)_?(\d*)', anchor)
          if m:
            chapter = m.group(1)
            verse = m.group(2)
            anchor = f"{chapter}-{verse}" if verse else chapter

        if not book and not anchor:
            book = f"{current_book}#{BOOK_ABBR_REVERSE.get(current_book)}"
        if anchor:
            return f"[[{book if book else current_book}#^{anchor}|{text}]]", name
        else:
            return f"[[{book}|{text}]]", name
    return text, name  # fallback if format unexpected

# --- Outline Conversion ---
def convert_outline(tag):
    level = OUTLINE_MAP.get(tag.name, None)
    # Only remove the outer tag, keep inner HTML/text as-is
    text = ''.join(str(child) for child in tag.contents).strip()
    if not text:
        return ""
    if level:
        return f"{level} {text}"
    else:
        return f"*{text}*"

# --- YAML Frontmatter Extraction ---
def extract_properties(soup):
    # Add properties
    table = soup.find("table", {"align": "center"})
    if not table:
      return ""
    # Extract <ins> entries
    ins_tags = table.find_all("ins")

    properties = {}
    for ins in ins_tags:
      text = ins.decode_contents().strip()

      # Split into key and value (only at the first colon)
      if ':' in text:
        key_part, value_part = text.split(':', 1)

        # Normalize key: lowercase, underscores
        key = key_part.strip() #.lower().replace(" ", "_").replace("-", "_")

        # If value contains a link ([[...]]), split into list of text and links
        link_pattern = r'(\[\[.*?\]\])'
        if re.search(link_pattern, value_part):
            parts = [f'{p}' if re.match(link_pattern, p) else p for p in re.split(link_pattern, value_part) if p]
            properties[key] = parts
        else:
          properties[key] = value_part.strip()
    table.replace_with("")
    yaml_frontmatter = '---\n'
    for key, value in properties.items():
      if key == "Authors" or key == "Author":
        yaml_frontmatter += "Author:\n"
        if isinstance(value, list):
          for v in value:
            yaml_frontmatter += f'  - "{v.strip()}"\n'
        else:
          yaml_frontmatter += f'  - "{value}"\n'
      else:
        if isinstance(value, list):
          yaml_frontmatter += f"{key}:\n"
          for v in value:
            yaml_frontmatter += f'  - "{v.strip()}"\n'
        else:
          yaml_frontmatter += f'{key}: "{value}"\n'
    return yaml_frontmatter

# --- Newline Adjustment ---
def adjust_newlines(text):
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|Chapter" in line:
            # Insert blank line before (if not already)
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")  # blank line

            # Join with next line (remove newline after)
            if i + 1 < len(lines):
                line = line + " " + lines[i + 1].lstrip()
                i += 1  # Skip next line since we've merged it
        new_lines.append(line)
        i += 1

    return "\n".join(new_lines)

# --- Verse Anchor Addition ---
def add_verse_anchors(text):
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for pattern: "**[[Bible|X]] [[#X|Y]]:[[#X|Z]]**" at start of line
        m = re.match(r'^\*\*\[\[Bible\|[^\]]+\]\] \[\[[^\]]+\|(\d+)\]\]:\[\[[^\]]+\|(\d+)\]\]\*\*', line)
        if m:
          Y, Z = m.group(1), m.group(2)
          # Find index of next empty line
          j = i + 1
          while j < len(lines) and lines[j].strip() != "":
            j += 1
          if j > 0:
            # Append " ^Y-Z" at end of the line before the empty line
            lines[j - 1] = lines[j - 1].rstrip() + f" ^{Y}-{Z}"

        new_lines.append(lines[i])
        i = i+1

    return "\n".join(new_lines)

# --- Outline Spacing ---
def outline_with_spacing(lines, current_book):
    result = []
    n = len(lines)
    for i, line in enumerate(lines):
        mapped = map_outline(line, current_book)
        is_outline = bool(re.match(r'^(#|\*|##|###|####|#####|######)', mapped.strip()))
        # Only add empty line before if previous line is not empty
        if is_outline:
            if i == 0 or lines[i-1].strip() != "":
                result.append("")
            result.append(mapped)
            # Only add empty line after if next line is not empty
            if i == n-1 or lines[i+1].strip() != "":
                result.append("")
        else:
            result.append(mapped)
    return '\n'.join(result)

# --- Split Verse Combination ---
def combine_split_verses(text):
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match lines like: **[[Bible|SoS]] [[SoS#Song of Songs|1]]:[[SoS#^1|4a]]** [[SoSO#^o0|-]] ...
        m = re.match(
          r'(\*\*\[\[Bible\|([^\]]+)\]\] \[\[([^\]]+)\|(\d+)\]\]:\[\[([^\]]+)\|(\d+)([a])\]\]\*\*) (\[\[[^\]]+\|-\]\]) (.*)',
          line
        )

        verse_lines = []
        if m:
            # Remove the a/b from the verse reference (e.g., [[SoS#^1|4a]] -> [[SoS#^1|4]])
          verse_lines.append(re.sub(r'(\[\[[^\]|]+\|)(\d+)[ab](\]\])', r'\1\2\3', line))
          j = i+1
          while j < len(lines) and lines[j]:
            # lines before outline line
            verse_lines.append(lines[j])
            j = j+1

          # Collect all consecutive outline lines (separated by empty lines), each ending with ^oX
          outline_lines = []
          k = j + 1
          while k < len(lines):
            outline_candidate = lines[k]
            if outline_candidate.strip() == "":
              k += 1
              continue
            if re.search(r"\^o\d+\s*$", outline_candidate):
              outline_lines.append(outline_candidate)
              k += 1
              # After outline line, there may be more outline lines separated by empty lines
              continue
            else:
              break
          j = k
          while j < len(lines) and lines[j]:
            # lines after outline line
            # Remove the verse reference at the beginning of the first line after the outline line
            if j < len(lines):
              # Remove pattern like: **[[Bible|...]] [[...|...]]:[[...|...]]** at the start
              # Remove verse reference and outline point at the start of the line
              # Only insert [b] in the first verse line after the outline lines
              if j == k:
                new_line = re.sub(
                  r'^(?:\*\*\[\[Bible\|[^\]]+\]\] \[\[[^\]]+\|[^\]]+\]\]:\[\[[^\]]+\|[^\]]+\]\]\*\*\s*)?(?:\[\[[^\]]+#\^o[^\|]+\|-\]\]\s*)',
                  '[b] ',
                  lines[j]
                )
              else:
                new_line = re.sub(
                  r'^(?:\*\*\[\[Bible\|[^\]]+\]\] \[\[[^\]]+\|[^\]]+\]\]:\[\[[^\]]+\|[^\]]+\]\]\*\*\s*)?(?:\[\[[^\]]+#\^o[^\|]+\|-\]\]\s*)',
                  '',
                  lines[j]
                )
              verse_lines.append(new_line)
            j = j+1
          new_lines.extend(verse_lines)
          if verse_lines:
            chapter_num = m.group(4)
            verse_num = m.group(6)  # (\d+) from the verse reference
            new_lines[-1] = new_lines[-1].rstrip() + f" ^{chapter_num}-{verse_num}"
          new_lines.append("")
          for outline_line in outline_lines:
            # Add outline lines after the verse lines
            if outline_line.strip():
              new_lines.append(outline_line.strip())
              new_lines.append("")

          i = j
        else:
          new_lines.append(line)
        i += 1
      return "\n".join(new_lines)

# --- Main Text Parsing ---
def parse_text(html, current_book, all_refs):
    with open(html, 'r', encoding='utf-8') as f:
        html_content = f.read()
    clean_html = re.sub(r'\s+', ' ', html_content).strip()
    soup = BeautifulSoup(clean_html, 'html.parser')

    # Convert outline points to markdown headings
    # for tagname in OUTLINE_MAP.keys():
    #     for tag in soup.find_all(tagname):
    #         if tag.find("u", {"class": "o"}):
    #             heading = convert_outline(tag)
    #             tag.replace_with(f"\n\n{heading}\n")

    # Convert all anchor tags to obsidian links
    for s in soup.find_all("s"):
        s.replace_with("")
    for a in soup.find_all("a"):
        obsidian_link, name = convert_to_obsidian_link(a, current_book, all_refs)
        a.replace_with(obsidian_link)

    # Replace bold <b> with **...**
    for b in soup.find_all("b"):
        b.replace_with(f"**{b.get_text()}**")

    for q in soup.find_all("q"):
        q.replace_with(f"\n   {q.get_text()}\n")


    front_matter = extract_properties(soup)

    for br in soup.find_all("br"):
        br.insert_before("\n")

    # Clean remaining tags (optional: remove all other HTML tags)
    text = soup.get_text().strip().replace("\xa0", " ")
    # Insert new lines between ]])** -> ]])\n**
    text = re.sub(r'(\]\]\)\*\*)', r']])\n**', text)
    text = text.replace(f"\n**", f"\n\n**")
    text = text.replace(f"]][[Bible", f"]]\n\n[[Bible")
    text = text.replace(f"]]**[[Bible", f"]]\n\n**[[Bible")
    text = text.replace(f"[ [[{current_book}#^intro|Introduction]] | [[{current_book}#^subject|Subject]] ]", f"")
    text = re.sub(r"(---)?\n+\[\[[^#]*#\^b\|Chapters\]\]\n*", f"\n\n[[{current_book}#^b|Chapters]]\n", text)
    # Insert newlines before outline points, even if preceded by '('
    text = text.replace(f"]][[", f"]]\n[[")
    text = re.sub(
      rf"(\(?)(\[\[{current_book}#\^o)",
      lambda m: f"\n\n{m.group(1)}{m.group(2)}",
      text
    )
    text = text.replace(f"\n\n\n", f"\n\n")
    text = re.sub(r"^Book of [^\[]+\[\[", "\n[[", text)
    text = re.sub(r"^\[\[([^#]*)#\^o", r"\n\[\[\1#^o", text)
    text = re.sub(r"\[\[[^\]]+\]\]Book", "Book", text)
    # Insert new line after line starting with **ch.**
    text = re.sub(r'(^\*\*ch\..*\*\*.*$)', r'\1\n', text, flags=re.MULTILINE)
    text = re.sub(r'(^.*\|Title\]\]\*\*.*$)', r'\n\1', text, flags=re.MULTILINE)
    # Merge multi-line chapter links (e.g., "**ch.** ...\n [[Matt#^15|15]] ...")
    def merge_multiline_chapter_links(text):
      # Merge lines starting with "**ch.**" and all following lines containing only chapter links (possibly with spaces or empty lines)
      lines = text.splitlines()
      merged_lines = []
      i = 0
      while i < len(lines):
        line = lines[i]
        if line.startswith("**ch.**") or line.startswith("**vv.**"):
          merged = line.strip()
          j = i + 1
          # Collect all subsequent lines that only contain chapter links (possibly with spaces or empty lines)
          while j < len(lines) and (
            lines[j].strip() == "" or
            re.fullmatch(r'(\s*.*?\|•]].*\s*)+', lines[j].strip())
          ):
            if lines[j].strip():
              merged += " " + lines[j].strip() + "\n"
            j += 1
          merged_lines.append(merged)
          i = j
        else:
          merged_lines.append(line)
          i += 1
      return "\n".join(merged_lines)

    text = merge_multiline_chapter_links(text)

    # Insert newlines before any "[[#Book|Book]]" style links only if the end of group 2 and group 3 match (e.g., [[#1 John|First John]]) and remove this line (will become part of Chapter of)
    def same_book_end(g2, g3):
      # Compare last word (case-insensitive, ignoring whitespace)
      if "Subject" in g3:
        return False
      return g2.strip().split()[-1].lower() == g3.strip().split()[-1].lower()
    text = re.sub(
      r"(\[\[[^#]*#([^\]|]+)\|([^\]]+)\]\])",
      lambda m: f"\n---" if same_book_end(m.group(2), m.group(3)) else m.group(1),
      text
    )

    # text = adjust_newlines(text)
    text = text.replace(f"[[{current_book}#^b|Verses]]\n", f"[[{current_book}#^b|Verses]]")

    # Add ^Y at end of lines like [[#^X|Chapter Y of Z]]
    def add_chapter_anchors(text):
      def chapter_repl(match):
        anchor = match.group(1)
        chapter_num = match.group(2)
        rest = match.group(3)
        line = match.group(0)
        prefix = ""
        if chapter_num and int(chapter_num) > 1:
          prefix = f"[[{current_book}#^{int(chapter_num) - 1}|<- Previous]] | "
        if f"^{chapter_num}" not in line:
          return f"\n{prefix}[[{current_book}#{BOOK_ABBR_REVERSE.get(current_book)}|{BOOK_ABBR_REVERSE.get(current_book)} {chapter_num} of {rest}]] | [[{current_book}#^{anchor}|Next ->]] ^{chapter_num}\n\n---"
        else:
          return prefix + line

      def psalm_repl(match):
        book_link = match.group(1)
        chapter_anchor = match.group(2)
        chapter_num = match.group(3)
        # Only add previous if chapter_num > 1
        prefix = ""
        if int(chapter_num) > 1:
          prefix = f"[[{current_book}#^{int(chapter_num) - 1}|<- Previous]] | "
        # Compose: [[Book#^prev|<- Previous]] | [[Book#Book|Psalm N]] | [[Book#^next|Next ->]]
        return f"\n---\n{prefix} [[{current_book}#{BOOK_ABBR_REVERSE.get(current_book)}|{BOOK_ABBR_REVERSE.get(current_book)} {chapter_num}]] | [[{current_book}#^{int(chapter_num)+1}|Next ->]] ^{chapter_num}\n\n---"

      # First, handle the original chapter anchor pattern
      text = re.sub(
        r'\n?\[\[[^#]*#\^([^\]|]+)\|Chapter (\d+) of ([^\]]+)\]\]',
        chapter_repl,
        text
      )
      # Then, handle the Psalm pattern: [[Psa#Psalms|Psalm]] [[Psa#^107|106]]
      text = re.sub(
        r'(\[\[[^\]]+#Psalms\|Psalm\]\])\s*\[\[[^\]]+#\^(\d+)\|(\d+)\]\]',
        psalm_repl,
        text
      )
      return text

    text = add_chapter_anchors(text)

    # Add ^b at end of lines like [[#X|Book of X]]
    text = re.sub(r'(\[\[[^#]*#([^\]|]+)\|Book of \2\]\])', r'\1 ^b\n', text)
    # Remove lines like [[#Jonah|Introduction to Jonah:]]
    text = re.sub(r'^\[\[[^#]*#([^\]|]+)\|Introduction to [^\]]+:\]\]\n?', '', text, flags=re.MULTILINE)

    # Find the second to last newline and replace it with two newlines
    newline_indices = [m.start() for m in re.finditer(r'\n', text)]
    if len(newline_indices) >= 2:
      idx = newline_indices[-2]
      text = text[:idx] + '\n\n' + text[idx+1:]

    # Extract "Subject of ..." lines and move to front matter
    subject_match = re.search(
      r"\[\[[^#]*#([^\]|]+)\|Subject of ([^\]]+)\]\]:\s*\n((?:.*?\n)*?)(?=^---|\Z)", text, flags=re.MULTILINE
    )
    if subject_match:
      book_anchor = subject_match.group(1)
      book_name = subject_match.group(2)
      subject_line = subject_match.group(3).replace('\n', ' ').strip()
      # Add to front matter
      front_matter += f"Subject: {subject_line}\n"
      # Remove the subject line from text (including all lines until ---)
      text = re.sub(
        rf"\[\[[^#]*#({re.escape(book_anchor)})\|Subject of {re.escape(book_name)}\]\]:\s*\n((?:.*?\n)*?)(?=^---|\Z)",
        "",
        text,
        flags=re.MULTILINE
      )
    front_matter += '---\n\n'
    front_matter += f"# {BOOK_ABBR_REVERSE.get(current_book)}\n"


    text = add_verse_anchors(text)
    # e.g. **[[Bible|Jon]] [[#Jonah|1]]:[[#Jonah|17]]**  -> **[[Bible|Jon]] [[#Jonah|1]]:[[#1|17]]**
    def replace_bible_link(match):
      bible_key = match.group(1)
      bible_long_key = match.group(2)
      chapter = match.group(3)
      verse = match.group(4)
      # Try to map abbreviation to full book name, then to standard abbreviation
      mapped = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(bible_key, bible_key), bible_key)
      return f"**[[Bible|{mapped}]] [[{bible_long_key}|{chapter}]]:[[{current_book}#^{chapter}|{verse}]]**"

    text = re.sub(
      r'^\*\*\[\[Bible\|([^\]]+)\]\] \[\[([^\]]+)\|(\d+)\]\]:\[\[[^\]]+\|(\d+)\]\]\*\*',
      replace_bible_link,
      text,
      flags=re.MULTILINE
    )

    # Remove lines that start with "**vv." or "[[#^b|Verses]]"
    text = "\n".join(
      line for line in text.splitlines()
      if not (line.lstrip().startswith("[[#^b|Verses]]") or line.lstrip().startswith(f"[[{current_book}#^b|Verses]]")) # and not line.lstrip().startswith("**vv.") # TODO?
    )
    text = outline_with_spacing(text.splitlines(), current_book)
    text = combine_split_verses(text)
    return front_matter + text

# --- Footnote Preprocessing ---
def pre_process_footnotes(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
      html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Map short anchors to combined anchors for postprocessing
    all_refs = {}

    # Build mapping from each <a> name to the last <a> name before <p>
    all_refs = {}
    for p in soup.find_all('p'):
      # Find all <a> tags immediately preceding this <p>
      anchors = []
      prev = p.previous_sibling
      # Walk backwards through siblings to collect <a> tags
      while prev and getattr(prev, 'name', None) == 'a' and prev.has_attr('name'):
        anchor_name = prev['name']
        # Remove "n" at beginning if present
        if anchor_name.startswith('n'):
          anchor_name = anchor_name[1:]
        anchor_name = anchor_name.replace('_', '-')
        anchor_name = re.sub(r'P\d+$', '', anchor_name)
        anchors.insert(0, anchor_name)
        prev = prev.previous_sibling
      if anchors:
        last_anchor = anchors[-1]
        for anchor in anchors:
          all_refs[anchor] = last_anchor
    return all_refs # TODO: [(f"{key} -> {value}") for key, value in all_refs.items() if value.endswith('b')]

# --- Footnote Parsing ---
def parse_footnotes(html_file, current_book, all_refs):
    with open(html_file, 'r', encoding='utf-8') as f:
      html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove navigation and headers
    for tag in soup(['head', 'h3', 'pre']):
      tag.decompose()
    for br in soup.find_all("br"):
      br.insert_before("\n")
      br.unwrap()

    # Build a mapping from anchor name to the next <p> element (footnote text)
    anchor_to_p = {}
    sorted_anchor_list = []
    # Only use the <a> tag immediately before each <p> tag
    for p in soup.find_all('p'):
      prev = p.previous_sibling
      # Walk backwards to skip non-tag siblings (like NavigableString)
      while prev and not (getattr(prev, 'name', None) == 'a' and prev.has_attr('name')):
        prev = prev.previous_sibling
      if prev and prev.name == 'a' and prev.has_attr('name'):
        anchor_name = prev['name']
        # Remove "n" at beginning if present
        if anchor_name.startswith('n'):
          anchor_name = anchor_name[1:]
        anchor_name = anchor_name.replace('_', '-')
        # Remove "P\d+" at end if present
        anchor_name = re.sub(r'P\d+$', '', anchor_name)
        sorted_anchor_list.append(anchor_name)
        anchor_to_p[anchor_name] = p

    notes_by_anchor = {}
    for anchor, p in anchor_to_p.items():
      # Replace all links in the paragraph
      for a in p.find_all('a', href=True):
        obsidian_link, _ = convert_to_obsidian_link(a, current_book, all_refs)
        a.replace_with(obsidian_link)
      # Replace bold <b> with **...**
      for b in p.find_all("b"):
        b.replace_with(f"**{b.get_text()}**")
      # Replace <u> with just text
      for u in p.find_all("u"):
        u.replace_with(u.get_text())
      # Replace <s> with just text
      for s in p.find_all("s"):
        s.replace_with(s.get_text())
      # Remove any remaining HTML tags
      text = p.get_text().replace("\xa0", " ").strip()
      # Append obsidian anchor link at end
      text = text.rstrip() + f" ^{anchor}"
      # Remove whitespace after newlines
      text = re.sub(r'\n\s+', '\n', text)
      notes_by_anchor[anchor] = text

    # Output: join all notes in order of appearance
    output = []
    for anchor in sorted_anchor_list:
      output.append(notes_by_anchor[anchor])
    return "\n\n".join(output)


# --- Outline Parsing ---
def parse_outline(html_file, current_book):
  with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()
  soup = BeautifulSoup(html_content, 'html.parser')

  # Remove navigation/header tags
  for tag in soup(['head', 'h3', 'pre']):
    tag.decompose()

  outline_lines = []
  for tag in soup.find_all(['kbd', 'em', 'h6', 'dfn', 'big', 'samp']):
    # Find the label (I., A., 1., etc.)
    label = ''
    label_tag = tag.find('a', href=True)
    if label_tag:
      label = label_tag.get_text().strip()
    else:
      b_tag = tag.find('b')
      if b_tag:
        label = b_tag.get_text().strip()
    # Find the anchor name (o0, o1, etc.)
    anchor_tag = tag.find('a', attrs={'name': True})
    anchor = anchor_tag['name'] if anchor_tag else ''
    # Find the main outline text (which is also a link)
    main_text = ''
    main_link_tag = None
    for a in tag.find_all('a', href=True):
      # skip the first <a> (label), use the next one for main text
      if a.get_text().strip() != label:
        main_link_tag = a
        break
    if main_link_tag:
      # Use convert_to_obsidian_link for the main outline text
      main_obsidian_link, _ = convert_to_obsidian_link(main_link_tag, current_book, {})
      main_text = main_obsidian_link
    else:
      u_tag = tag.find('u', class_='o')
      if u_tag:
        main_text = u_tag.get_text().strip()
    # Find verse range (optional)
    verse_range = ''
    verse_links = tag.find_all('a', href=True)
    verses = []
    for a in verse_links:
      m = re.search(r'#v(\d+)_?(\d*)', a['href'])
      if m:
        # Use convert_to_obsidian_link to generate the Obsidian link for the verse
        obsidian_link, _ = convert_to_obsidian_link(a, current_book, {})
        verses.append(obsidian_link)
    if verses:
      if len(verses) == 1:
        verse_range = f"{verses[0]}"
      else:
        verse_range = f"{verses[0]}-{verses[-1]}"
    # Compose the line
    label_str = f"{label}" if label else ''
    main = f"{main_text}".strip()
    if verse_range:
      main += f" ({verse_range})"
    # Build the obsidian links
    outline_link = f"[[{current_book}#^o{anchor[1:]}|{label_str}]]" if anchor else label_str
    # Compose the line with both links and anchor
    line = f"{outline_link} {main}"
    line = map_outline(line, current_book)
    outline_lines.append(line)

  # Add book heading at the top
  book_heading = f"# {BOOK_ABBR_REVERSE.get(current_book, current_book)} Outline\n"
  return book_heading + "\n\n" + "\n\n".join(outline_lines) + "\n"


# --- File Processing ---
def process_all_files(folder_path, output_dir):
    """Process all HTML files in a folder and insert footnotes into the database."""

    all_files = [f for f in os.listdir(folder_path) if f.endswith("N.htm")]
    base_files = [os.path.splitext(f)[0][:-1] for f in all_files]  # Remove 'N' before .htm
    print(base_files)

    # do first run to find all footnote references
    all_refs = {}
    for base in base_files:
      note_file = os.path.join(folder_path, f"{base}N.htm")
      if not (os.path.exists(note_file)):
          pass

      print(f"Pre-processing '{base}N.htm'")
      current_book_long = JUBILEE_ABRV_TO_FULL_BOOK.get(base)
      current_book = BOOK_ABBR.get(current_book_long)

      all_refs[current_book] = pre_process_footnotes(note_file)

    for base in base_files:
      note_file = os.path.join(folder_path, f"{base}N.htm")
      outline_file = os.path.join(folder_path, f"{base}O.htm")
      text_file = os.path.join(folder_path, f"{base}.htm")
      if not (os.path.exists(note_file) and os.path.exists(text_file)):
          pass

      print(f"Processing '{text_file}.htm' with '{base}N.htm'")
      current_book_long = JUBILEE_ABRV_TO_FULL_BOOK.get(base)
      current_book = BOOK_ABBR.get(current_book_long)
      # if current_book != "Psa":
      #    continue # TODO: remove

      text, notes, outline = parse_text(text_file, current_book, all_refs), parse_footnotes(note_file, current_book, all_refs), parse_outline(outline_file, current_book)

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

# Main entry point
if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     input_path = sys.argv[1]  # Take the first argument as the input path
    # else:
    #     print("Usage: rcv-footnote-extractor.py <input_directory>")
    #     sys.exit(1)
    process_all_files('/Users/nicolaikrebs/Documents/RcvBible_Footnotes/RcvBible_Footnotes/Jubilee Bible copy 2', 'Bible')


    # TODO Subject not working for matthew/mark/luke + psalms
    # TODO psalms not formatted properly
    # TODO Index
    # TODO both links in outline points between text now point to X (Book) -> one of them should point to XO, make the - in verse references also point to book outline
    # TODO maybe make [[Book]] reference before chapter disappear and use one between next and previous to go to top
    # TODO SoS text not proper - no empty line before [[#SS|Song of Songs]]\n[[#^b|Chapter 8 of 8]] -> insert
    # TODO half verses (a/b) split, e.g. Eph 3:17. not working, how to do? need non-a/b reference for links!!! e.g. SoS 7:9 Going down fn link is at end of previous line (part a) -> does not show up!
    # TODO X (Book) outline hover only shows point itself -> change to outline heading link -> would also list notes.. could also use headings per verse (e.g. one of the verse hovers, like "-" would have link [[X (Book)#[[X#^3-11]]|-]]), like my own footnotes on verse basis instead of outline basis. Perhaps do both?
    # TODO: reference for title! (e.g. paslm)
    # TODO: kursiv?
    # TODO: 1 Tim 5:18 footnotes not recognized!, probably all references where one side is quote?
    # TODO: Deut. 2x  5:4 wrong format (braket of footnote became part of verse)
    # TODO: [[Gen#^1-3x1b|note 3^1]]. 1b should be 1a -> order in list (not just length)!, should be GenN!, same in Lev#^6-9x4 -> LevN, See [[Luke#^5-5x1|note 5^1]] in [[Luke#^5|ch. 5]] (in Luke 8:24^1), [[Gal#^3-3x2a|note 3^2]] also should be GalN TODO TODO TODO
    # TODO: Gal 3:2-3 (probably others) have verses where 3-2x3b and 3-2x3c both have footnote content (3c points to 3b, problem is that b and c both have 3 -> ensure that we search for x\d[a-z] mapping and if \d matches take the earliest (i.e. 3b instead of 3c), or even for 3-3x2a the reference would be to 3-3x2 (ah that's tricky -> I need to rebuild my footnote mapping to only use actual footnotes (i.e. **[[Gal#^3-3|Gal 3:3^2]]  Spirit** would be 3-3x2, etc. otherwise no way to reconstruct true mappings, and then find lexically smallest mapping?))
    # TODO: instead of [[Luke#Luke|Luke]] line, combine in previous next line
    # TODO: Psa. 119 aleph, beth, etc. not working???
    # TODO: put verse line before ---, not after (nicer separation), e.g. psalms, also has title / verse directly after!
    # TODO: rom not all outline points are correct headings (e.g. C is ## not ###
    # TODO: Verse links in FN paragraphs are wrong don't hit FN top -> maybe change to verse anyways