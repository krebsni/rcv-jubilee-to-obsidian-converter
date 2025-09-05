"""
Parsing functions for text, footnotes, and outlines.
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from .constants import BOOK_ABBR, JUBILEE_ABRV_TO_FULL_BOOK, BOOK_ABBR_REVERSE, OUTLINE_MAP
from .utils import add_verse_anchors, combine_nav_and_verse_lines, combine_split_verses, convert_to_obsidian_link, ensure_empty_line_before_dashes, extract_properties, extract_verse_spec, insert_frontmatter_and_final_cleanup, map_outline_lines, merge_top_chapters_line, outline_with_spacing
import re
from .utils import (
    replace_tags,
    insert_newlines_before_br,
    cleanup_markdown,
    merge_multiline_chapter_links,
    add_chapter_anchors,
    replace_bible_links,
    remove_unwanted_lines_and_separate_verse_outline,
    update_front_matter_with_subject,
)


def pre_process_footnotes(html_file: str) -> dict:
    """Preprocess footnotes to build anchor mapping."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    all_refs = {}
    for p in soup.find_all('p'):
        anchors = []
        prev = p.previous_sibling
        while prev and getattr(prev, 'name', None) == 'a' and prev.has_attr('name'):
            anchor_name = prev['name']
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
    return all_refs

def parse_footnotes(html_file: str, current_book: str, all_refs: dict) -> str:
    """Parse footnotes HTML to markdown."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['head', 'h3', 'pre']):
        tag.decompose()
    for br in soup.find_all("br"):
        br.insert_before("\n")
        br.unwrap()
    anchor_to_p = {}
    sorted_anchor_list = []
    for p in soup.find_all('p'):
        prev = p.previous_sibling
        while prev and not (getattr(prev, 'name', None) == 'a' and prev.has_attr('name')):
            prev = prev.previous_sibling
        if prev and prev.name == 'a' and prev.has_attr('name'):
            anchor_name = prev['name']
            if anchor_name.startswith('n'):
                anchor_name = anchor_name[1:]
            anchor_name = anchor_name.replace('_', '-')
            anchor_name = re.sub(r'P\d+$', '', anchor_name)
            sorted_anchor_list.append(anchor_name)
            anchor_to_p[anchor_name] = p
    notes_by_anchor = {}
    for anchor, p in anchor_to_p.items():
        for a in p.find_all('a', href=True):
            obsidian_link, _ = convert_to_obsidian_link(a, current_book, all_refs)
            a.replace_with(obsidian_link)
        for b in p.find_all("b"):
            b.replace_with(f"**{b.get_text()}**")
        for u in p.find_all("u"):
            u.replace_with(u.get_text())
        for s in p.find_all("s"):
            s.replace_with(s.get_text())
        text = p.get_text().replace("\xa0", " ").strip()
        text = text.rstrip() + f" ^{anchor}"
        text = re.sub(r'\n\s+', '\n', text)
        notes_by_anchor[anchor] = text
    output = []
    for anchor in sorted_anchor_list:
        output.append(notes_by_anchor[anchor])

    def fix_line(s: str) -> str:
        # If it starts with "[ **par.**" and ends with "]", wrap ends with escaped brackets
        return (r"\[" + s[1:-1] + r"\]") if s.startswith("[ **par.**") and s.endswith("]") else s

    output = [
        "\n".join(fix_line(line) for line in chunk.splitlines())
        for chunk in output
    ]
    return "\n\n".join(output)

def parse_outline(html_file: str, current_book: str) -> str:
    """Parse outline HTML to markdown."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['head', 'h3', 'pre']):
        tag.decompose()
    outline_lines = []
    for tag in soup.find_all(['kbd', 'em', 'h6', 'dfn', 'big', 'samp']):
        label = ''
        label_tag = tag.find('a', href=True)
        if label_tag:
            label = label_tag.get_text().strip()
        else:
            b_tag = tag.find('b')
            if b_tag:
                label = b_tag.get_text().strip()
        anchor_tag = tag.find('a', attrs={'name': True})
        anchor = anchor_tag['name'] if anchor_tag else ''
        main_text = ''
        main_link_tag = None
        for a in tag.find_all('a', href=True):
            if a.get_text().strip() != label:
                main_link_tag = a
                break
        if main_link_tag:
            main_obsidian_link, _ = convert_to_obsidian_link(main_link_tag, current_book, {})
            main_text = main_obsidian_link
        else:
            u_tag = tag.find('u', class_='o')
            if u_tag:
                main_text = u_tag.get_text().strip()

        verse_range = extract_verse_spec(tag, current_book)
        label_str = f"{label}" if label else ''
        main = f"{main_text}".strip()
        if verse_range:
            main += f" ({verse_range})"
        outline_link = f"[[{current_book}#^o{anchor[1:]}|{label_str}]]" if anchor else label_str
        line = f"{outline_link} {main}"
        outline_lines.append(line)

    outline_lines = map_outline_lines(outline_lines, current_book, output_line_separator="\n\n")
    book_heading = f"# {BOOK_ABBR_REVERSE.get(current_book, current_book)} Outline\n"
    return book_heading + "\n\n" + outline_lines + "\n"



def parse_text(html, current_book, all_refs):
    """
    Parse Bible HTML text to Obsidian/Raycast markdown, extracting front matter and cleaning up formatting.
    """
    with open(html, 'r', encoding='utf-8') as f:
        html_content = f.read()
    clean_html = re.sub(r'\s+', ' ', html_content).strip()
    soup = BeautifulSoup(clean_html, 'html.parser')

    # Tag replacements
    # replace italic with _text_ but leave in surrounding tags for further processing
    replace_tags(soup, "i", lambda i: f"_{i.get_text()}_")
    replace_tags(soup, "s", lambda s: "")
    replace_tags(soup, "a", lambda a: convert_to_obsidian_link(a, current_book, all_refs)[0])
    replace_tags(soup, "b", lambda b: f"**{b.get_text()}**")
    replace_tags(soup, "q", lambda q: f"\n   {q.get_text()}\n")

    front_matter, properties = extract_properties(soup)
    insert_newlines_before_br(soup)

    text = soup.get_text().strip().replace("\xa0", " ")
    text = cleanup_markdown(text, current_book)
    text = merge_multiline_chapter_links(text)
    text = add_chapter_anchors(text, current_book)
    text = replace_bible_links(text, current_book)
    text = remove_unwanted_lines_and_separate_verse_outline(text, current_book)
    text = map_outline_lines(text, current_book)
    text = outline_with_spacing(text, current_book)
    text = combine_split_verses(text)
    text = add_verse_anchors(text)
    text = combine_nav_and_verse_lines(text)


    front_matter, text, properties = update_front_matter_with_subject(text, front_matter, properties)
    text = merge_top_chapters_line(text)
    text = re.sub(r'\n{3,}', '\n\n', text) # Remove double new lines
    text = ensure_empty_line_before_dashes(text)
    text = insert_frontmatter_and_final_cleanup(text, front_matter, current_book, properties)
    return text