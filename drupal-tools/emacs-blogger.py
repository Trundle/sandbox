# encoding: utf-8

"""
    A simple blogging utility for writing blog entries in reStructuredText.

    :copyright: Copyright (C) 2010 by Andreas Stührk.
    :license: Modified BSD.
"""


import sys

import docutils.core
import docutils.writers.html4css1
from docutils import nodes
from docutils.parsers import rst
from Pymacs import lisp

interactions = dict()


class CodeElement(nodes.General, nodes.FixedTextElement):
    pass

class TagsElement(nodes.Sequential, nodes.Element):
    pass

class CodeBlock(rst.Directive):
    """
    Directive for a code block.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    option_spec = dict()

    def run(self):
        code = u'\n'.join(self.content)
        node = CodeElement(code)
        node['lang'] = self.arguments[0]
        return [node]

class TagsDirective(rst.Directive):
    """
    Directive for tagging the blog entry.
    """

    has_content = True
    required_arguments = 0
    option_arguments = 0
    option_spec = 0

    def run(self):
        lines = list(self.content)
        if not lines:
            lines.append('')
        tags = lines[0].split() + lines[1:]
        return [TagsElement(','.join(tags))]


class Translator(docutils.writers.html4css1.HTMLTranslator):
    def visit_CodeElement(self, node):
        self.body.append(self.starttag(node, 'code', lang=node['lang']))
        self.body.append(node.rawsource)

    def depart_CodeElement(self, node):
        self.body.append('</code>')

    def visit_TagsElement(self, node):
        self.body.append('[tags]')
        self.body.append(node.rawsource)

    def depart_TagsElement(self, node):
        self.body.append('[/tags]\n')

class Writer(docutils.writers.html4css1.Writer):
    def __init__(self):
        docutils.writers.html4css1.Writer.__init__(self)
        self.translator_class = Translator


def get_text():
    end = lisp.buffer_size() + 1
    old_min = lisp.point_min()
    old_max = lisp.point_max()
    narrowed = (old_min != 1 or old_max != end)
    if narrowed:
        lisp.narrow_to_region(1, end)
    try:
        return lisp.buffer_string()
    finally:
        if narrowed:
            lisp.narrow_to_region(old_min, old_max)

def from_rest():
    text = get_text()
    parts = docutils.core.publish_parts(text, writer=Writer())

    lisp.weblogger_start_entry()
    lisp.insert(parts['title'])
    lisp.goto_char(lisp.point_max())
    lisp.insert(parts['body'])

interactions[from_rest] = ''

rst.directives.register_directive('code-block', CodeBlock)
rst.directives.register_directive('tags', TagsDirective)
