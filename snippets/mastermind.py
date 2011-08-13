#!/usr/bin/env python3
# encoding: utf-8
#
# Mastermind solver
#
# The code is based on Robin Wellner's work at https://gist.github.com/975276.
#
# Copyright 2011 Sebastian Ramacher

import sys
from itertools import product

class Solver(object):
  def __init__(self, numpositions, alphabet='123456'):
    self.numpositions = numpositions
    self.alphabet = alphabet

    self.possible = [''.join(p) for p in product(self.alphabet,
                                                 repeat=self.numpositions)]
    self.S = set(self.possible)
    self.results = [(right, wrong) for right in range(numpositions + 1) for wrong in 
               range(numpositions + 1 - right)]  # if not (right == numpositions - 1 and wrong == 1)]

  def solve(self, scorefn):
    r = self.numpositions // 2
    l = r + self.numpositions % 2
    guess = ''.join([self.alphabet[0]] * l + [self.alphabet[1]] * r)
    return self._solve(guess, scorefn)

  def _solve(self, guess, scorefn):
    sc = scorefn(guess)
    if sc == (self.numpositions, 0):
      return sc

    self.S.difference_update(set(p for p in self.S if self.score(p, guess) !=
                                 sc))
    if len(self.S) == 1:
      return self._solve(self.S.pop(), scorefn)
    guess = max(self.possible, key=lambda x: min(sum(1 for p in self.S if
                                                     self.score(p, x) != res)
                                                 for res in self.results))
    return self._solve(guess, scorefn)
    
  def score(self, guess, other):
    first = len([speg for speg, opeg in zip(guess, other) if speg == opeg])
    return (first, sum([min(guess.count(j), other.count(j)) for j in
                        self.alphabet]) - first)

def scorefn(guess):
  print('Guess', guess)
  return (int(input('Right: ')), int(input('Wrong position: ')))

def main(args=None):
  from optparse import OptionParser

  if args is None:
    args = sys.argv[1:]

  parser = OptionParser()
  parser.add_option('-p', dest='positions', type='int', default=4,
                    help='# of positions')
  parser.add_option('-a', dest='alphabet', type='string', default='123456',
                  help='List of colors')
  options, args = parser.parse_args(args)
  if args:
    parser.print_usage()
    return 1

  s = Solver(options.positions, options.alphabet)
  print('The solutions is', s.solve(scorefn), '.')
  return 0

if __name__ == '__main__':
  sys.exit(main())
