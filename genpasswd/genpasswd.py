#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  genpasswd
  ~~~~~~~~~

  Generate passwords with different alphabets.

  :copyright: Copyright (C) 2011 Sebastian Ramacher.
  :license: Modified BSD.
"""

__version__ = "1.0"
__author__ = "Sebastian Ramacher"

from optparse import OptionParser
from random import choice

DIGITS="0123456789"
SPECIAL_CHARS="$_-|=+*-/\!?.:"
HEX_ALPHABET="abcdef0123456789"
LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_LENGTH=10

def add_alphabet_option(parser, shortname, longname, noname, destination, description,
                        default):
  parser.add_option(shortname, longname, dest=destination, help=description,
                    action="store_true", default=default)
  parser.add_option(noname, dest=destination, help=description,
                    action="store_false", default=default)

def generate_password(length, alphabet):
  return "".join(choice(alphabet) for x in xrange(length))

def main(args=None):
  if args is None:
    args = sys.argv[1:]

  usage = 'usage: %prog [options]'
  version = '%prog version ' + __version__

  parser = OptionParser(usage=usage, version=version)
  parser.add_option('--length', dest='length', type='int',
                    default=DEFAULT_LENGTH)
  parser.add_option('--alphabet', dest='alphabet', type='string',
                    default=None)
  parser.add_option('--hex-alphabet', dest='hex_alphabet', action="store_true",
                    default=False)

  options=(
    ('-L', '--uppercase-letters', '--no-uppercase-letters', 'uppercase_letters',
     '', True),
    ('-l', '--lowercase-letters', '--no-lowercase-letters', 'lowercase_letters',
     '', True),
    ('-d', '--digits', '--no-digits', 'digits', '', True),
    ('-s', '--special-chars', '--no-special-chars', 'special', '', False)
  )
  for o in options:
    add_alphabet_option(parser, *o)
        
  opts, args = parser.parse_args(args)
  if opts.length <= 0:
    print "E: length cannot be <= 0"
    return 1

  alphabet = opts.alphabet
  if alphabet is None:
    if opts.hex_alphabet:
      alphabet = HEX_ALPHABET
    else:
      alphabet = ""
      if opts.uppercase_letters:
        alphabet += LETTERS
      if opts.lowercase_letters:
        alphabet += LETTERS.lower()
      if opts.digits:
        alphabet += DIGITS
      if opts.special:
        alphabet += SPECIAL_CHARS

  if len(alphabet) <= 1:
    print "E: an alphabet of size <= 1 is definitely not safe at all"
    return 1
  elif len(alphabet) <= 10:
    print "W: short alphabet"

  print generate_password(opts.length, alphabet)

import sys
if __name__ == "__main__":
  try:
    sys.exit(main(sys.argv[1:]))
  except KeyboardInterrupt:
    pass

# vim: set ts=2 sw=2 sts=2 et:
