#!/usr/bin/env python3

"""Given a markdown document and an HTML template:

* Render the markdown into HTML via cmark
* In the resulting HTML text string, substitute text matching [[?]] with
  <kbd>?</kbd>
* Insert the revised HTML text string into the template with a jinja-like
  re.sub hack
* Parse the resulting text with Beautiful Soup
* For each h1 element that is a direct descendant of the body
  * create a new section block beneath it, then move all subsequent siblings
    into the new section until the next h1 element, or the end of the body
  * Then add input and label tags before the first section. The label will
    contain the contents of the h1, which is now removed, and both will
    use a "tab-nn" id/for which maps to the "content-nn" class on the section
* Write the HTML tree out to stdout

"""

# Ubuntu/Debian: apt-get install python3-cmarkgfm python3-bs4

import sys
import os
import argparse
import logging
import re
import cmarkgfm
import bs4
from bs4 import BeautifulSoup


def apply_keyboard_tags(input_html):
    """Substitute [[.+]] with <kbd>$1</kbd>"""
    return re.sub(r'\[\[([^\]]+)\]\]', r'<kbd>\1</kbd>', input_html)


def create_tabs_from_h1(input_html):
    """Parse the html with bs4, then transform h1 tags and siblings into
    sections, with input/label pairs added to the top to act as the tabs.
    """
    soup = BeautifulSoup(input_html, 'html.parser')
    tab_counter = 1
    for heading1 in soup.body.find_all('h1'):
        content_id = f"content-{tab_counter:02d}"
        tab_id = f"tab-{tab_counter:02d}"

        # Make the new section, and insert it after the heading1 we're
        # looking at
        new_section = soup.new_tag('section', id=content_id)
        heading1.insert_after(new_section)

        # Move every sibling to the next heading1 into the section, except
        # the section itself. "next_siblings" is a generator that walks the
        # tree, but as the append is a move operation, if we used it as a
        # live generator, the next sibling from that element would be
        # whatever is next inside the section we moved it to. Hence, we
        # snapshot the siblings of heading1 as a list
        for sibling in list(heading1.next_siblings):
            if isinstance(sibling, bs4.element.Tag):
                if sibling.name == 'section':
                    continue
                if sibling.name == 'h1':
                    break
            new_section.append(sibling)

        # Extract the heading out of the main tree
        saved_heading = heading1.extract()
        # Create the input and label mapped to our section
        new_input = soup.new_tag('input', type="radio", id=tab_id)
        new_input['name'] = "tabs"
        if tab_counter == 1:
            # This is how you create stand alone keyword attributes, apparently
            new_input['checked'] = None
        # Improve output readability with a new line
        soup.section.insert_before(new_input, "\n")
        new_label = soup.new_tag('label')
        new_label['for'] = tab_id
        # stuff the contents of the header into the label; as previously
        # noted, append is a move operation, so we snapshot the contents as
        # a list
        for thing in list(saved_heading.contents):
            new_label.append(thing)
        # Improve output readability with a new line
        soup.section.insert_before(new_label, "\n")
        tab_counter += 1

    # Squashes multiple string elements together as a single element, for
    # a tidier default output
    soup.smooth()
    return soup


def cmdline():
    """Parse the command line switches"""
    parser = argparse.ArgumentParser(
        description='Render markdown into a template'
        ' with CSS based tab sections',
    )
    parser.add_argument("--verbose", dest="verbose",
                        action='store_true', default=False,
                        help="Log INFO as well as WARN or above")
    parser.add_argument("--template", dest="template_file",
                        type=str, default=None, required=True,
                        help='Path to the template file')
    parser.add_argument("--no-kbd", dest="kbd",
                        action='store_false', default=True,
                        help="Don't replace [[?]] with <kbd>?</kbd>")
    parser.add_argument("--no-tabs", dest="tabs",
                        action='store_false', default=True,
                        help="Don't replace h1 tags with tab sections")
    parser.add_argument('input_markdown', nargs='?')

    return parser


def build_logger(verbose=False):
    """Set up a basic log to stderr logger.

    Logs WARN and higher by default, but also INFO in verbose mode.
    """
    if verbose:
        level = logging.INFO
    else:
        level = logging.WARN

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setLevel(level)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def main():
    """Do the thing"""
    parser = cmdline()
    args = parser.parse_args()
    build_logger(args.verbose)

    if not args.input_markdown:
        logging.error("Input file not specified")
        sys.exit(1)
    if not os.path.exists(args.input_markdown):
        logging.error("Can't find the input file %s", args.input_markdown)
        sys.exit(1)
    if not os.access(args.input_markdown, os.R_OK):
        logging.error("Can't read the input file %s", args.input_markdown)
        sys.exit(1)
    with open(args.input_markdown, "r", encoding='utf-8') as markdown_file:
        markdown_text = markdown_file.read()
    # markdown_to_html can't work on a file-like, sadly
    markdown_html = cmarkgfm.markdown_to_html(markdown_text)

    # Make it opt out
    if args.kbd:
        markdown_html = apply_keyboard_tags(markdown_html)

    if not os.path.exists(args.template_file):
        logging.error("Can't find the template file %s", args.template_file)
        sys.exit(1)
    if not os.access(args.template_file, os.R_OK):
        logging.error("Can't read the template file %s", args.template_file)
        sys.exit(1)
    with open(args.template_file, 'r', encoding='utf-8') as template_file:
        template_html = template_file.read()

    if not re.search('{{markdown_html}}', template_html):
        logging.error("The '{{markdown_html}}' tag is"
                      " missing from the template file")
        sys.exit(1)
    # I *could* drag in jinja2 to render this, but a re.sub will do
    rendered_template_html = re.sub('{{markdown_html}}',
                                    markdown_html,
                                    template_html)

    # Make this opt out also
    if args.tabs:
        rendered_template_html = create_tabs_from_h1(rendered_template_html)

    print(rendered_template_html)


if __name__ == "__main__":
    main()
