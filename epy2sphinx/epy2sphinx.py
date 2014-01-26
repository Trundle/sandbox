#!/usr/bin/env python3
# encoding: utf-8

"""Converts epydoc to sphinx markup in docstrings. Only support a
very minimal subset of epydoc.


Known limitations:

   * Does not handle module docstrings as well as (epydoc invented)
     variable docstrings.
   * Always uses the same encoding for the output, hence be careful
     when you have source files with different encodings.

:copyright: 2013 Andreas Stührk <andy-python@hammerhartes.de>

"""

import difflib
import re
import os
import sys
from itertools import islice

from pygments import highlight
from pygments.filter import Filter
from pygments.formatters import NullFormatter
from pygments.lexers import Python3Lexer
from pygments.token import Token


_ENCODING_COOKIE = re.compile("coding[:=]\s*([-\w.]+)")


class ConverterFilter(Filter):
    "Converts epydoc markup to sphinx markup."

    REPLACEMENTS = {
        "@param": ":param",
        "@type": ":type",
        "@return": ":returns",
        # Not really part of epydoc markup I think
        "@raise": ":raises"
    }

    def filter(self, lexer, stream):
        for (ttype, value) in stream:
            if ttype is Token.Literal.String.Doc:
                yield (ttype, self._convert_docstring(value))
            else:
                yield (ttype, value)

    def _convert_docstring(self, value):
        for (tag, replacement) in self.REPLACEMENTS.items():
            value = value.replace(tag, replacement)
        return value


class Converter:
    def __init__(self, filter=None):
        self._formatter = NullFormatter()
        self._lexer = Python3Lexer(ensurenl=False, stripnl=False)
        self._lexer.add_filter("tokenmerge")
        if filter is None:
            filter = ConverterFilter()
        self._lexer.add_filter(filter)

    def convert(self, source, filename):
        converted_source = highlight(source, self._lexer, self._formatter)
        return difflib.unified_diff(
            source.splitlines(), converted_source.splitlines(),
            os.path.join("a", filename), os.path.join("b", filename),
            lineterm="")

def load_source(path):
    encoding = encoding = "utf-8"
    with open(path, "r", encoding="ascii") as source_file:
        try:
            match = _ENCODING_COOKIE.match("".join(islice(source_file, 2)))
        except UnicodeDecodeError:
            pass
        else:
            if match is not None:
                encoding = match.group(1)
    with open(path, "r", encoding=encoding) as source_file:
        return source_file.read()

def convert_file(converter, path):
    source = load_source(path)
    for line in converter.convert(source, path):
        sys.stdout.write(line + "\n")


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    converter = Converter()
    for path in args:
        if os.path.isdir(path):
            for (root, dirs, files) in os.walk(path):
                for filename in files:
                    if filename.endswith(".py"):
                        convert_file(converter, os.path.join(root, filename))
        else:
            convert_file(converter, path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
