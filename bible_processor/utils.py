# Utility functions for parse_text refactor
import re
from bs4 import BeautifulSoup, NavigableString
from typing import Dict, Any
import re
from .constants import BIBLEHUB_INTERLINEAR, BOOK_ABBR, BOOK_ABBR_INDEX, BOOK_ABBR_REVERSE, JUBILEE_ABRV_TO_FULL_BOOK, JUBILEE_ABRV_TO_FULL_BOOK_REVERSE, OUTLINE_MAP

def replace_tags(soup, tag_name, replace_func):
    """Replace all tags of a given type in soup using replace_func."""
    for tag in soup.find_all(tag_name):
        tag.replace_with(replace_func(tag))

def insert_newlines_before_br(soup):
    """Insert newlines before <br> tags in soup."""
    for br in soup.find_all("br"):
        br.insert_before("\n")
    for div in soup.find_all("div"):
      div.insert_before("\n")

def cleanup_markdown(text, current_book):
    """Apply regex-based markdown cleanup steps."""
    text = re.sub(r'(\]\]\)\*\*)', r']])\n**', text)
    text = text.replace(f"\n**", f"\n\n**")
    text = text.replace(f"]][[Bible", f"]]\n\n[[Bible")
    text = text.replace(f"]]**[[Bible", f"]]\n\n**[[Bible")
    text = text.replace(f"]][[", f"]]\n[[")
    text = text.replace(f"\n\n\n", f"\n\n")
    text = re.sub(r"^Book of [^\[]+\[\[", "\n[[", text)
    text = re.sub(r"^\[\[([^#]*)#\^o", r"\n\[\[\1#^o", text)
    text = re.sub(r"\[\[[^\]]+\]\]Book", "Book", text)
    text = re.sub(r'(^\*\*ch\..*\*\*.*$)', r'\1\n', text, flags=re.MULTILINE)
    text = re.sub(r'(^.*\|Title\]\]\*\*.*$)', r'\n\1', text, flags=re.MULTILINE)
    text = re.sub(r'(\[\[Bible\|Home\]\])', r'\n\1 ^b\n', text)
    text = re.sub(r'^\[\[[^#]*#([^\]|]+)\|Introduction to [^\]]+:\]\]\n?', '', text, flags=re.MULTILINE)

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

    # "[[X|*]]S?YS?" links, where the optional S is special character and the second S may not be there, could be e.g. "_","“", "*", but not whitespace. Change the link to "S?[[X|Y]]S?". If it's surrounded/prefixed/postfixed by special characters, move the special characters outside of link  "[[X|*]]*Y*" -> "[[X||*Y*]]".
    def replace_star_link(m):
      link = m.group(1)
      before = m.group(2) or ""
      display = m.group(3)
      after = m.group(4) or ""
      return f"{before}[[{link}|{display}]]{after}"
    text = re.sub(r'\[\[([^\]\|]+)\|\*\]\]([“”\'"\*\_]?)([A-Za-zäöüÄÖÜß]*)([“”\'"\*\_]?)',
    replace_star_link, text)

    text = text.replace("_ _", " ")

    # print lines with "|*]]"
    for line in text.splitlines():
      if "|*]]" in line:
        print(f"Warning: Book {current_book} has |*]] in line: {line}")


    return text

def merge_multiline_chapter_links(text):
    """Merge lines starting with **ch.** and all following lines containing only chapter links."""
    lines = text.splitlines()
    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("**ch.**") or line.startswith("**vv.**"):
            merged = line.strip()
            j = i + 1
            while j < len(lines) and (
                lines[j].strip() == "" or
                re.fullmatch(r'(\s*.*?\|•]].*\s*)+', lines[j].strip())
            ):
                if lines[j].strip():
                    merged += " " + lines[j].strip() + "\n"
                j += 1
            merged_lines.append(merged)
            if line.startswith("**vv.**"):
                merged_lines.append("\n---\n")
            i = j
        else:
            merged_lines.append(line)
            i += 1
    return "\n".join(merged_lines)

def add_chapter_anchors(text, current_book):
    """Add chapter anchors and Psalm navigation."""
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
        return f"\n---\n{prefix} [[{current_book}#{BOOK_ABBR_REVERSE.get(current_book)}|{BOOK_ABBR_REVERSE.get(current_book)} {chapter_num}]] | [[{current_book}#^{int(chapter_num)+1 if chapter_anchor != "b" else "b"}|Next ->]] ^{chapter_num}\n\n---"

    # First, handle the original chapter anchor pattern
    text = re.sub(
      r'\n?\[\[[^#]*#\^([^\]|]+)\|Chapter (\d+) of ([^\]]+)\]\]',
      chapter_repl,
      text
    )
    # Then, handle the Psalm pattern: [[Psa#Psalms|Psalm]] [[Psa#^107|106]]
    text = re.sub(
      r'(\[\[[^\]]+#Psalms\|Psalm\]\])\s*\[\[[^\]]+#\^(\d+|b)\|(\d+)\]\]',
      psalm_repl,
      text
    )
    return text

def replace_bible_links(text, current_book):
    """Replace Bible links with standardized format."""
    from .constants import BOOK_ABBR, JUBILEE_ABRV_TO_FULL_BOOK
    def replace_bible_link(match):
        bible_key = match.group(1)
        bible_long_key = match.group(2)
        chapter = match.group(3)
        verse = match.group(4)
        mapped = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(bible_key, bible_key), bible_key)
        return f"**[[Bible|{mapped}]] [[{bible_long_key}|{chapter}]]:[[{current_book}#^{chapter}|{verse}]]**"
    text = re.sub(
        r'^\*\*\[\[Bible\|([^\]]+)\]\] \[\[([^\]]+)\|(\d+)\]\]:\[\[[^\]]+\|(\d+)\]\]\*\*',
        replace_bible_link,
        text,
        flags=re.MULTILINE
    )

    return text

def remove_unwanted_lines_and_separate_verse_outline(text, current_book):
    """Remove lines that start with **vv. or [[#^b|Verses]]."""
    lines = [
        line for line in text.splitlines()
        if not (line.lstrip().startswith("[[#^b|Verses]]") or line.lstrip().startswith(f"[[{current_book}#^b|Verses]]"))
    ]
    for i in range(len(lines)):
      if "**[[Bible|" in lines[i] and not lines[i].startswith("**[[Bible|"):
        lines[i] = lines[i].replace("**[[Bible|", "\n\n**[[Bible|")

    return "\n".join(lines)

def update_front_matter_with_subject(text, front_matter, properties):
    """Extract 'Subject of ...' lines and move to front matter."""
    subject_match = re.search(
      r"\[\[[^#]*#([^\]|]+)\|Subject of ([^\]]+)\]\]:\s*\n((?:.*?\n)*?)(?=^---|\n|\Z)", text, flags=re.MULTILINE
    )
    if subject_match:
        book_anchor = subject_match.group(1)
        book_name = subject_match.group(2)
        subject_line = subject_match.group(3).replace('\n', ' ').strip()
        # Add to front matter
        front_matter += f"**Subject:** {subject_line}\n"
        # Remove the subject line from text (including all lines until ---)
        text = re.sub(
          rf"\[\[[^#]*#({re.escape(book_anchor)})\|Subject of {re.escape(book_name)}\]\]:\s*\n((?:.*?\n)*?)(?=^---|\Z)",
          "",
          text,
          flags=re.MULTILINE
        )
        properties["Subject"] = subject_line
    return front_matter, text, properties


def get_book_abbr(book: str) -> str:
    """Get abbreviation for a book name."""
    return BOOK_ABBR.get(book, book)

def roman_to_int(roman: str) -> int:
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result, prev = 0, 0
    for ch in reversed(roman):
        val = roman_map[ch]
        result += -val if val < prev else val
        prev = val
    return result

def is_roman(label: str) -> bool:
    return re.fullmatch(r'[IVXLCDM]+', label) is not None

def is_alphabetic(label: str) -> bool:
    return re.fullmatch(r'[A-Z]', label) is not None

def map_outline_line(line: str, current_book: str, previous_rom: str = None, previous_arabic: str = None):
    m = re.match(r'^\(?\[\[[^#]*#\^o([^|]+)\|([^\]]+)\]\](.*)', line)
    if not m:
        line = line.strip()
        return line, previous_rom, previous_arabic

    num, label, rest = m.groups()
    label = label.strip().rstrip('.')
    line = re.sub(
        r'\[\[[^#]*#\^o',
        f'[[{BOOK_ABBR_REVERSE.get(current_book)} (Book)#^o',
        line,
        count=1
    )
    if not "cont'd" in line:
        line = line + f" ^o{num}"
    level = None

    # Handle digit-based label (e.g., 1.)
    if re.fullmatch(r'\d+', label):
        level = 4
        previous_arabic = label
    # Roman numeral (could be ambiguous with letter)
    elif is_roman(label):
        rom_val = roman_to_int(label)
        fits_roman = previous_rom is None or rom_val == roman_to_int(previous_rom) + 1
        alpha_val = ord(label) - ord('A') + 1 if is_alphabetic(label) else None
        fits_alpha = previous_arabic is None or (alpha_val is not None and previous_arabic.isdigit() and alpha_val == int(previous_arabic) + 1)

        if fits_roman and not fits_alpha:
            level = 2
            previous_rom = label
        elif fits_alpha and not fits_roman:
            level = 3
            previous_arabic = str(alpha_val)
        elif fits_roman and fits_alpha:
            # Both fit: prefer alphabetic as deeper level
            level = 3
            previous_arabic = str(alpha_val)
        else:
            # If neither fits: guess roman as default
            level = 2
            previous_rom = label

    # Pure uppercase letter (e.g., A., B.)
    elif is_alphabetic(label):
        level = 3
        previous_arabic = str(ord(label) - ord('A') + 1)
    # Lowercase letter
    elif re.fullmatch(r'[a-z]', label):
        level = 5
    # (1), (2)
    elif re.fullmatch(r'\(\d+\)', label):
        level = 6
    # (a), (b)
    elif re.fullmatch(r'\([a-z]+\)', label):
        level = 'bullet'
    else:
        level = 'bullet'

    if level == 2:
        line = f"## {line}"
    elif level == 3:
        line = f"### {line}"
    elif level == 4:
        line = f"#### {line}"
    elif level == 5:
        line = f"##### {line}"
    elif level == 6:
        line = f"###### {line}"
    else:
        # Insert * before the ^oX tag at the end of the line
        if re.search(r'\s*\^o\w+\s*$', line):
            line = re.sub(r'(\s*\^o\w+\s*$)', r'*\1', line)
        else:
            line = line.rstrip() + '*'
        line = f"###### *{line}"

    return line, previous_rom, previous_arabic

def map_outline_lines(text_or_lines: str | list[str], current_book: str, previous_rom: str = None, previous_arabic: str = None, output_line_separator: str = "\n") -> str:
    """Map outline line to markdown heading based on label, tracking previous roman and arabic labels."""
    new_lines = []
    if isinstance(text_or_lines, list):
        lines = text_or_lines
    else:
        lines = text_or_lines.splitlines()


    for i in range(len(lines)):
        line = lines[i].strip()
        # If the line contains multiple outline points in parentheses, split them out
        outline_point_pattern = r'(\(\[\[[^#]*#\^o[^\|]+\|[^\]]+\]\](?: [^\)]*)?\))'
        outline_points = re.findall(outline_point_pattern, line)
        if outline_points and len(outline_points) >= 1:
          # Remove all found outline points from the line
          rest = line
          for op in outline_points:
            rest = rest.replace(op, '')
          # Add each outline point as its own line
          for op in outline_points:
            new_lines.append("\n" + op.strip())
          # If anything remains, add it as a separate line
          if rest.strip():
            new_lines.append("\n" + rest.strip())
          continue
        # Otherwise, process the line normally
        new_lines.append(line)

    lines = new_lines
    new_lines = []

    for i, line in enumerate(lines):
        line, previous_rom, previous_arabic = map_outline_line(line, current_book, previous_rom, previous_arabic)
        new_lines.append(line)
    return output_line_separator.join(new_lines)


def adjust_newlines(text: str) -> str:
    """Adjust newlines for chapter headings and spacing."""
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|Chapter" in line:
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")
            if i + 1 < len(lines):
                line = line + " " + lines[i + 1].lstrip()
                i += 1
        new_lines.append(line)
        i += 1
    return "\n".join(new_lines)


def convert_to_obsidian_link(tag, current_book: str, all_refs: Dict[str, Any]) -> str:
    """Convert HTML anchor tag to Obsidian link."""
    href = tag.get("href", "")
    name = tag.get("name", "")
    if tag.find('s'):
        s = tag.find('s')
        s.replace_with(f"^{s.get_text()}")
    text = tag.get_text()
    for jubilee_abbr, full_book in JUBILEE_ABRV_TO_FULL_BOOK.items():
        abbr = BOOK_ABBR.get(full_book, full_book)
        text = re.sub(rf'\b{re.escape(jubilee_abbr)}\b', abbr, text)
    match = re.match(r'(?:([\w]+)\.htm)?(?:#([^"]+))?', href)
    if match:
        file, anchor = match.groups()
        is_note, is_outline = False, False
        if file and file.endswith("N"):
            file = file[:-1]
            is_note = True
        elif file and file.endswith("O"):
            file = file[:-1]
            is_outline = True
        book = ""
        if file == "a":
            book = "Bible"
        elif is_outline:
            book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) + 'O'
        elif file:
            book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) + ('N' if is_note else '')
        chapter = None
        if anchor and (anchor.startswith("v") or anchor.startswith("n")):
            m = re.match(r'n(?:(\d+)_)?(\d+|Title)(?:x([^P]+)(?:P(\d+))?)', anchor)
            if m:
                chapter = m.group(1)
                verse = m.group(2)
                note = m.group(3)
                tmp_book = BOOK_ABBR.get(JUBILEE_ABRV_TO_FULL_BOOK.get(file.strip())) if file else ""
                if not tmp_book:
                    tmp_book = current_book
                if chapter:
                    anchor = all_refs[tmp_book][f"{chapter}{(f'-{verse}x{note}' if note else f'-{verse}') if verse else ''}"]
                else:
                    anchor = all_refs[tmp_book][f"{(f'{verse}x{note}' if note else f'{verse}') if verse else ''}"]
                book = tmp_book + "N"

            # Match v, v3, v3_Title, etc.
            m = re.match(r'v(\d+)(?:_(Title|\d+))?', anchor)
            if m:
                chapter = m.group(1)
                verse = m.group(2)
                anchor = f"{chapter}-{verse}" if verse else chapter
        if not text:
            text = "*"
        if not book and not anchor:
            book = f"{current_book}#{BOOK_ABBR_REVERSE.get(current_book)}"
        res = ""
        if anchor:
            # replace [ and ] with \[ and \] in display part
            text = re.sub(r'\[', r'(', text)
            text = re.sub(r'\]', r')', text)
            res = f"[[{book if book else current_book}#^{anchor}|{text}]]", name
        else:
            # replace [ and ] with \[ and \] in display part
            text = re.sub(r'(\[|\])', r'\\\1', text)
            res = f"[[{book}|{text}]]", name
        return res

    return text, name

def remove_obsidian_links(text: str) -> str:
    """
    Remove Obsidian links ([[X|Y]] or [[X]]) from text, leaving only the display part (Y or X).
    """
    # Replace [[X|Y]] with Y
    text = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', text)
    # Replace [[X]] with X
    text = re.sub(r'\[\[([^\]|]+)\]\]', r'\1', text)
    return text

def extract_properties(soup: BeautifulSoup) -> str:
    """Extract YAML frontmatter from HTML soup."""
    table = soup.find("table", {"align": "center"})
    if not table:
        return ""
    ins_tags = table.find_all("ins")
    properties = {}
    for ins in ins_tags:
        text = ins.decode_contents().strip()
        if ':' in text:
            key_part, value_part = text.split(':', 1)
            key = key_part.strip()
            properties[key] = value_part.strip()
    table.replace_with("")
    yaml_frontmatter = ""
    for key, value in properties.items():
        yaml_frontmatter += f'**{key}**: {value}\n\n'

    # Remove Obsidian links from property values
    for key in properties:
        properties[key] = remove_obsidian_links(properties[key])
    return yaml_frontmatter, properties

def add_verse_anchors(text: str) -> str:
    """Add verse anchors to lines with Bible references.
       - Normal books: **[[Bible|Book]] [[Book#Book|<chapter>]]:[[...|<verse>]]** → append  ^<chapter>-<verse>
       - One-chapter books: **[[Bible|Book]] [[Book#Book|<verse>]]** → append  ^<verse>
    """
    # Pattern A: chapter:verse inside the bold header
    #   **[[Bible|Book]] [[Book#Book|CH]]:[[...|VV]]**
    pat_ch_verse = re.compile(
        r'^\*\*\[\[Bible\|[^\]]+\]\]\s+\[\[[^\]]+\|(\d+)\]\]:(?:\[\[[^\]]+\|([^\]]+)\]\])?\*\*'
    )


    # Pattern B: one-chapter books → only a single number (the verse) in the bold header, no colon
    #   **[[Bible|Book]] [[Book#Book|VV]]**
    # Accept a digit+optional letter (e.g., 14b) just in case your data uses lettered verses.
    pat_one_chapter = re.compile(
        r'^\*\*\[\[Bible\|[^\]]+\]\]\s+\[\[[^\]]+\|([^\]]+)\]\]\*\*'
    )

    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        m = pat_ch_verse.match(line)
        if m:
            chap, verse = m.group(1), m.group(2)
            j = i + 1
            while j < len(lines) and lines[j].strip() != "":
                j += 1
            if j > 0:
                if verse:  # chapter:verse
                    lines[j - 1] = lines[j - 1].rstrip() + f" ^{chap}-{verse}"
                else:      # rare: chapter only
                    lines[j - 1] = lines[j - 1].rstrip() + f" ^{chap}"
            new_lines.append(lines[i])
            i += 1
            continue

        m2 = pat_one_chapter.match(line)
        if m2:
            verse_only = m2.group(1)
            j = i + 1
            while j < len(lines) and lines[j].strip() != "":
                j += 1
            if j > 0:
                lines[j - 1] = lines[j - 1].rstrip() + f" ^{verse_only}"
            new_lines.append(lines[i])
            i += 1
            continue

        # Default: passthrough
        new_lines.append(line)
        i += 1

    return "\n".join(new_lines)

def outline_with_spacing(text: str, current_book: str) -> str:
    """Add spacing to outlines for markdown rendering."""
    lines = text.splitlines()
    result = []
    n = len(lines)
    previous_rom, previous_arabic = None, None
    for i, line in enumerate(lines):
        mapped, previous_rom, previous_arabic = map_outline_line(line, current_book, previous_rom, previous_arabic)
        is_outline = bool(re.match(r'^(#|\*\s?\[|##|###|####|#####|######)', mapped.strip()))
        if is_outline:
            if i == 0 or lines[i-1].strip() != "":
                result.append("")
            result.append(mapped)
            if i == n-1 or lines[i+1].strip() != "":
                result.append("")
        else:
            result.append(mapped)
    return '\n'.join(result)

def combine_split_verses(text: str) -> str:
    """Combine split verses and outlines for proper formatting."""
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(
            r'(\*\*\[\[Bible\|([^\]]+)\]\] \[\[([^\]]+)\|((\d+)\]\]:\[\[([^\]]+)\|(\d+)([a])\]\]|(\d+)([a])\]\])\*\*) (\[\[[^\]]+\|-\]\]) (.*)',
            line
        )
        verse_lines = []
        if m:
            verse_lines.append(re.sub(r'(\[\[[^\]|]+\|)(\d+)[ab](\]\])', r'\1\2\3', line))
            j = i+1
            while j < len(lines) and lines[j]:
                verse_lines.append(lines[j])
                j += 1
            outline_lines = []
            k = j + 1
            while k < len(lines):
                outline_candidate = lines[k]
                if outline_candidate.strip() == "":
                    k += 1
                    continue
                if re.search(r"\^o\w+\s*$", outline_candidate):
                  outline_lines.append(outline_candidate)
                  k += 1
                  continue
                else:
                  break
            j = k
            while j < len(lines) and lines[j]:
                if j < len(lines):
                    # Remove pattern like: **[[Bible|...]] [[...|...]]:[[...|...]]** at the start
                    # Remove verse reference and outline point at the start of the line
                    # Only insert [b] in the first verse line after the outline lines
                    if j == k:
                        new_line = re.sub(
                            r'^(?:\*\*\[\[Bible\|[^\]]+\]\] \[\[[^\]]+\|[^\]]+\]\](?::\[\[[^\]]+\|[^\]]+\]\])?\*\*\s*)?(?:\[\[[^\]]+#\^o[^\|]+\|-\]\]\s*)',
                            '\\[b\\] ',
                            lines[j]
                        )
                    else:
                        new_line = re.sub(
                            r'^(?:\*\*\[\[Bible\|[^\]]+\]\] \[\[[^\]]+\|[^\]]+\]\](?::\[\[[^\]]+\|[^\]]+\]\])?\*\*\s*)?(?:\[\[[^\]]+#\^o[^\|]+\|-\]\]\s*)',
                            '',
                            lines[j]
                        )
                    verse_lines.append(new_line)
                j += 1
            new_lines.extend(verse_lines)
            new_lines.append("")
            for outline_line in outline_lines:
                if outline_line.strip():
                    new_lines.append(outline_line.strip())
                    new_lines.append("")
            i = j
        else:
            new_lines.append(line)
        i += 1

    return "\n".join(new_lines)

def extract_verse_spec(tag, current_book):
    """Return a human/markdown string like:
       [[Gen#^25-22|25:22]]-[[Gen#^25-26|26]]; [[Gen#^25-29|29]]-[[Gen#^25-34|34]]; ...
    """
    tokens = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            txt = str(child)
            # keep only separators that matter between verse links
            for ch in txt:
                if ch in ['-', ',', ';']:
                    tokens.append(('sep', ch))
        elif child.name == 'a' and child.has_attr('href'):
            if re.search(r'#v\d+_', child['href']):  # verse anchor
                link, _ = convert_to_obsidian_link(child, current_book, {})
                tokens.append(('link', link))
        # ignore other nodes (e.g., mdash between main text and first verse list)

    # Now rebuild respecting separators into segments and ranges
    pieces = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t[0] == 'link':
            # range pattern: link - link
            if i+2 < len(tokens) and tokens[i+1] == ('sep', '-') and tokens[i+2][0] == 'link':
                pieces.append(f"{tokens[i][1]}-{tokens[i+2][1]}")
                i += 3
            else:
                pieces.append(tokens[i][1])
                i += 1
        elif t == ('sep', ',') or t == ('sep', ';'):
            # normalize list separators to '; ' (use ',' if you prefer)
            # avoid duplicate separators
            if pieces and pieces[-1] not in ['; ']:
                pieces.append('; ')
            i += 1
        else:
            i += 1

    # Clean any trailing separators
    out = ''.join(pieces).strip()
    out = out.rstrip('; ,')

    if not out:
        return ''

    # plural if there is a range or multiple chunks
    # Match exactly: link - link (no other content)
    is_single_range = bool(re.fullmatch(
        r'\s*\[\[[^\]|]+\|\d+\]\]\s*-\s*\[\[[^\]|]+\|\d+\]\]\s*',
        out
    ))

    return f'vv. {out}' if is_single_range else out

def combine_nav_and_verse_lines(text, max_distance=4):
    """
    Flexibly combines navigation and verse lines for Song of Songs markdown formatting.
    Finds nav and vv lines within max_distance lines, merges vv before '| [[...Next ->]]' in nav.
    Output starts with '---\\n', ends with '\\n\\n---', and is surrounded by empty lines.
    """
    lines = text.splitlines()
    result = []
    n = len(lines)
    i = 0
    while i < n:
        # Find nav line
        if lines[i].strip().startswith("---"):
            # Search for nav line within next max_distance lines
            nav_idx = None
            for j in range(i+1, min(i+3, n)):
                nav_line = lines[j].strip()
                if "<- Previous" in nav_line or "Next ->" in nav_line:
                    nav_idx = j
                    break
            if nav_idx is not None:
                # Search for vv line within next max_distance lines after nav
                vv_idx = None
                for k in range(nav_idx+1, min(nav_idx+1+max_distance, n)):
                    vv_line = lines[k].strip()
                    if "**vv.**" in vv_line:
                        vv_idx = k
                        break
                if vv_idx is not None:
                    nav_line = lines[nav_idx].strip()
                    vv_line = lines[vv_idx].strip()
                    if re.search(r'\s*\^\w+\s*$', nav_line):
                        # Insert vv_line before the ^o... anchor at the end of nav_line
                        merged = re.sub(
                          r'(\s*\^\w+\s*$)',
                          f' | {vv_line.strip()}\\1',
                          nav_line
                        ).replace('  ', ' ')
                    else:
                        merged = f"{nav_line} | {vv_line}"
                    result.append("")
                    result.append("---")
                    result.append(merged)
                    result.append("")
                    result.append("---")
                    result.append("")
                    # Skip processed lines
                    i = vv_idx + 1
                    continue
        # If no merge, preserve the line
        result.append(lines[i])
        i += 1
    return "\n".join(result)

def ensure_empty_line_before_dashes(text: str) -> str:
    """
    Ensures that every line containing only '---' has an empty line before it.
    """
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---" and i > 3:
            if result and result[-1].strip() != "":
                result.append("")

            # remove duplicate dashes lines
            for j in range(i+1, len(lines)):
                if lines[j].strip():
                    break
            if lines[j].strip() == "---":
                i = j
        i += 1
        result.append(line)

    return "\n".join(result)

def merge_top_chapters_line(text: str) -> str:
    """
    Removes '[ [[<Book>#^intro|Introduction]] | [[<Book>#^subject|Subject]] ]' and merges
    '[[<Book>#^b|Chapters]]' with the following '**ch.** ...' line, removing '**ch.**'.
    """
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        # Remove intro/subject line
        if re.match(r'^\[\s*\[\[.*#\^intro\|Introduction\]\] \| \[\[.*#\^subject\|Subject\]\]\s*\]', lines[i]):
            i += 1
            continue
        # Merge chapters line with next **ch.** line
        if re.match(r'^\[\[.*#\^b\|Chapters\]\]$', lines[i]):
            chapters_line = lines[i]
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("**ch.**"):
                ch_line = re.sub(r'\*\*ch\.\*\*\s*', '', lines[i + 1]).strip()
                result.append(f"---\n{chapters_line} {ch_line}")
                i += 2
                continue
        if "Book |" in lines[i]:
            # if the line does not start with "Book |", insert two newlines before it
            if not lines[i].startswith("Book |"):
                # append first part of the line
                result.append(lines[i].split("Book |")[0].strip())
                result.append("\n---\n")
                lines[i] = "[[Bible|Book]] | " + lines[i].split("Book |")[1].strip()
            else:
                # Add --- before the book line
                lines[i] = "---\n" + lines[i].replace("Book |", "[[Bible|Book]] | ")
        result.append(lines[i])
        i += 1
    return "\n".join(result)

def generate_property_string(properties: dict, current_book: str) -> dict:
    """Update properties with standardized keys and values."""
    from .constants import BOOK_ABBR_REVERSE, BOOK_ABBR_INDEX
    for key in ["Author", "Authors", "author"]:
      if key in properties:
        properties["Author(s)"] = properties.pop(key)
    time_ministry = properties.pop("Time of His Ministry", None)
    time_writing = properties.pop("Time of Writing", None)
    if time_ministry or time_writing:
      combined = ""
      if time_writing:
        combined += time_writing
      if time_ministry:
        if combined:
          combined += "; "
        combined += time_ministry
      properties["Time of Writing/Ministry"] = combined
    properties["Version"] = '"[[RcV]]"'
    properties["Index"] = BOOK_ABBR_INDEX.get(current_book)
    properties["Book"] = BOOK_ABBR_REVERSE.get(current_book, current_book)
    # Combine Recipient/Recipients
    recipient = properties.pop("Recipient", None)
    recipients = properties.pop("Recipients", None)
    if recipient or recipients:
      combined = ""
      if recipient:
        combined += recipient
      if recipients:
        if combined:
          combined += "; "
        combined += recipients
      properties["Recipient(s)"] = combined

    # Sort properties: Author(s), Time of Writing/Ministry, Place of Writing, Recipients, Subject, Book, Version, Index
    desired_order = ["Author(s)", "Time of Writing/Ministry", "Place of Writing", "Recipients", "Subject", "Book", "Version", "Index"]
    sorted_keys = desired_order + [k for k in properties if k not in desired_order]
    properties = {k: properties[k] for k in sorted_keys if k in properties}

    for key in properties:
      if isinstance(properties[key], str):
        properties[key] = properties[key].replace(": ", " — ")

    return '---\n' + "\n".join([f"{key}: {value}" for key, value in properties.items()]) + '\n---\n'

def add_biblehub_link_to_line(line: str, current_book: str) -> str:
    """
    Add BibleHub interlinear link to lines ending with ^N or ^N-M.
    """
    from .constants import BIBLEHUB_INTERLINEAR
    m = re.search(r'(\s\^(\d+(?:-\d+)?))$', line)
    if m:
        chapter_verse = m.group(2)
        url = f"https://biblehub.com/interlinear/" + f"{BIBLEHUB_INTERLINEAR[current_book]}/{chapter_verse}.htm"
        # Insert [ ](url) before the anchor
        line = re.sub(r'(\s\^(\d+)(-\d+)?)$', f' [ ]({url})\\1', line)
    return line


def insert_frontmatter_and_final_cleanup(text: str, front_matter: str, current_book: str, properties: dict) -> str:
    """
    Insert front matter at the beginning of the text.
    """
    book_abbrs = set(BOOK_ABBR.values())
    long_form_abbrs = set(JUBILEE_ABRV_TO_FULL_BOOK.values())
    lines = text.strip().splitlines()
    inserted = False

    result = [generate_property_string(properties, current_book)]

    nav_line = lines[0]
    curr_book_jub_abbr = JUBILEE_ABRV_TO_FULL_BOOK_REVERSE.get(BOOK_ABBR_REVERSE.get(current_book), current_book)
    if not re.search(r"\]\]\s+" + re.escape(curr_book_jub_abbr) + r"\s+\[\[", nav_line):
        print(f"Warning: First line does not contain a navigation link for {current_book}.")

    for i, line in enumerate(lines):
      # [ **par.** [[GenN#^1-1x1a|1]] [[GenN#^1-1x1a|2]] [[GenN#^1-1x1a|3]] [[GenN#^1-1x1a|4]] ] -> \[ **par.** [[GenN#^1-1x1a|1]] [[GenN#^1-1x1a|2]] [[GenN#^1-1x1a|3]] [[GenN#^1-1x1a|4]] \]
      line = line.strip()
      line = add_biblehub_link_to_line(line, current_book)

      if "[[Bible|Book]] | " in line:
        result.append(f"# {BOOK_ABBR_REVERSE.get(current_book)}\n")
        result.append(line)
      elif not inserted and ("**ch.**" in line or "Bk1" in line):
        if "Bk1" in line:
            result.append("")
        result.append(line)
        result.append("\n---\n" + front_matter.rstrip())
        inserted = True

      else:
        # Remove lines that are just a book link (e.g., [[SoS#Song of Songs|*]]) and merge remainder to previous line
        m = re.match(r'^\[\[([A-Za-z0-9]+)#([^\]|]+)\|\*\]\](.*)', line)
        if m and m.group(1) in book_abbrs and m.group(2) in long_form_abbrs:
          remainder = m.group(3).strip()
          if remainder and len(result) > 0:
            result[-1] = result[-1].rstrip() + " " + remainder
          continue
        result.append(line)
    if not inserted:
      for i, line in enumerate(result):
          if line.strip().startswith("**vv.**"):
            result[i] = "\n---\n" + front_matter.rstrip()
            inserted = True
            break

    result.append("\n" + nav_line)
    return "\n".join(result)