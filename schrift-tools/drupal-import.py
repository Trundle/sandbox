import collections
import csv
import datetime
import itertools
import re
import sys

import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from lxml import etree, html

import schrift

BLOG_URL = u"http://andy.hammerhartes.de/blog/"

def init_db():
    schrift.db.create_all()

def create_user(name, password, editor):
    user = schrift.User(name, password, editor)
    user.authors.append(user)
    schrift.db.session.add(user)
    return user

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) != 2:
        sys.stderr.write("Usage: import.py <user> <xml dump>\n")
        return 1
    init_db()
    user = create_user(args[0], "V2HfbJqI", True)
    revisions = dict()
    nodes = list()
    tag_names = dict()
    tags = collections.defaultdict(list)
    parent_tags = dict()
    with open(args[1]) as xml_file:
        xml = etree.parse(xml_file)
    # tag data
    for node in xml.findall(".//term_data"):
        name = node.find("name").text.lower()
        tag = schrift.db.session.query(schrift.Tag).filter_by(tag=name).first()
        if tag is None:
            tag = schrift.Tag(name)
            schrift.db.session.add(tag)
        tag_names[node.find("tid").text] = tag
    # tag hierarchy
    for node in xml.findall(".//term_hierarchy"):
        parent_tags[node.find("tid").text] = node.find("parent").text
    # tag nodes
    for node in xml.findall(".//term_node"):
        node_id = node.find("nid").text
        tag_id = node.find("tid").text
        while tag_id != "0":
            tags[node_id].append(tag_names[tag_id])
            tag_id = parent_tags[tag_id]
    # Revisions
    for node in xml.findall(".//node_revisions"):
        revisions[node.find("vid").text] = node
    # Nodes (== blog entries)
    for node in xml.findall(".//node"):
        if node.find("type").text != "blog":
            continue
        post = dict()
        post["nid"] = node.find("nid").text
        post["body"] = revisions[node.find("vid").text].find("body").text
        post["title"] = unicode(node.find("title").text)
        post["created"] = int(node.find("created").text)
        nodes.append(post)
    formatter = HtmlFormatter()
    for entry in nodes:
        body = entry["body"]
        if BLOG_URL in body:
            print "aah", repr(body)
        # Find code blocks
        codes = list()
        index = 0
        while 0 <= index < len(body):
            index = body.find("<code", index)
            if index >= 0:
                end_index = body.find("</code>", index)
                codes.append((index, end_index))
                index = end_index
        # Convert code blocks
        parts = list()
        previous_end = 0
        for (start, end) in codes:
            parts.append(body[previous_end:start])
            code = body[body.index(">", start) + 1:end]
            language = re.search('<code [^>]*lang="?(.*?)[" >]', body[start:end])
            if language is not None:
                language = language.group(1)
            else:
                language = "text"
            language = {"lisp": "common-lisp"}.get(language, language)
            code = pygments.highlight(code, get_lexer_by_name(language), formatter)
            parts.append('<div class="syntax">')
            parts.append(code)
            parts.append("</div>")
            previous_end = end + len("</code>")
        parts.append(body[previous_end:])
        body = ''.join(parts)
        post = schrift.Post(title=entry["title"], content="",
                            summary="", summary_html="",
                            html=body, author=user, private=True)
        post.pub_date = datetime.datetime.fromtimestamp(entry["created"])
        slug = schrift.slugify(entry["title"])
        counter = None
        while schrift.db.session.query(schrift.Post).filter_by(slug=slug).first():
            if counter is None:
                counter = itertools.count(2)
                slug += '-' + str(counter.next())
            else:
                slug = "%s-%i" % (slug.rsplit("-", 1)[0], counter.next())
        post.slug = slug
        post.tags = tags[entry["nid"]]
        schrift.db.session.add(post)
        schrift.db.session.flush()
    schrift.db.session.commit()

if __name__ == "__main__":
    main()
