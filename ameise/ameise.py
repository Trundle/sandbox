#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""
    Chris Langtons Ameise

    Geschrieben 2007 von Andy S. <andysmuell@hammerhartes.de>
"""

import math
import optparse
import random
import sys

from PIL import Image, ImageChops
from PIL import GifImagePlugin

class AnimatedGif(object):
    """An animiertes Gif (PIL saugt)."""
    def __init__(self, path):
        self.fo = file(path, 'wb')
        self.previous = None
    
    def close(self):
        self.fo.write(';')
        self.fo.close()

    def __iadd__(self, other):
        if self.previous is None:
            # Globaler Header
            header = ''.join(GifImagePlugin.getheader(other))
            header = header.replace('GIF87a', 'GIF89a')
            self.fo.write(header)
            # Graphic Control Extension-Block
            header = [
                    '\x21',     # Signatur für Beginn eines
                                # Extension-Blocks
                    '\xf9',     # Graphic Control Extension-Signatur
                    '\x04\x00', # Größe des Blocks (4 Bytes)
                    '\x0a\x00', # Irgendwas + reservierter Block
                    '\xff\x00', # Pause zwischen Frames (1/100 s)
                ]
            self.fo.write(''.join(header))
            # Application Extension Block
            header = [
                    '\x21',     # Signatur für Beginn eines
                                # Extension-Blocks
                    '\xff',     # Application Extension-Signatur
                    '\x0b',     # Größe des Blocks (11 Bytes)
                    'NETSCAPE2.0',
                    '\x03',     # Größe des Sub-Datenblocks (3 Bytes)
                    '\x01',
                    '\x00\x00', # Anzahl der Schleifen (0 = unendlich)
                    '\x00'      # Ende des Blocks
                ]
            #self.fo.write(''.join(header))
            # Erstes Frame
            for string in GifImagePlugin.getdata(other):
                self.fo.write(string)
        else:
            # Delta-Frame
            delta = ImageChops.subtract_modulo(other, self.previous)
            bbox = delta.getbbox()
            if bbox:
                for string in GifImagePlugin.getdata(other.crop(bbox),
                                                     offset=bbox[:2]):
                    self.fo.write(string)
            else:
                # XXX Was macht man in dem Fall?
                pass
        self.previous = other.copy()
        return self

class Ant(object):
    """Repräsentiert eine Ameise."""
    def __init__(self, location, color=(0,0,0)):
        self.color = color
        self.direction = random.choice((0, 90, 180, 270))
        self.direction = math.radians(self.direction)
        self.location = location
        self.world = None

    def walk(self):
        """Lässt die Ameise einen Schritt laufen."""
        delta_x = int(math.sin(self.direction))
        delta_y = int(math.cos(self.direction))
        self.location = (self.location[0] + delta_x,
                         self.location[1] + delta_y)
        if self.world[self.location] != 0:
            # Gefärbtes Feld, 90 Grad nach links wenden
            self.direction += math.radians(90)
            # Feld weiß färben
            self.world[self.location] = 0
        else:
            # Weißes Feld, 90 Grad nach rechts wenden
            self.direction -= math.radians(90)
            # Feld in eigener Farbe färben
            self.world[self.location] = self.color

class WorldSpace(dict):
    def __init__(self, world, wrapping=True):
        dict.__init__(self)
        self.world = world
        self.wrapping = wrapping

    def __getitem__(self, (x, y)):
        if self.wrapping:
            x %= self.world.size[0]
            y %= self.world.size[1]
        try:
            return dict.__getitem__(self, (x, y))
        except KeyError:
            self[(x, y)] = 0
            return 0

    def __setitem__(self, (x, y), value):
        if self.wrapping:
            x %= self.world.size[0]
            y %= self.world.size[1]
        try:
            self.world.pa[(x, y)] = value
        except IndexError:
            pass
        dict.__setitem__(self, (x, y), value)

class World(object):
    """Repräsentiert eine Welt"""
    def __init__(self, size, wrapping=True):
        self.ants = list()
        self.img = Image.new('P', size, 0)
        self.palette = list((255, 255, 255))
        self.img.putpalette(self.palette)
        self.pa = self.img.load()
        self.size = size
        self.worldspace = WorldSpace(self, wrapping)

    def __getitem__(self, item):
        return self.worldspace[item]

    def __setitem__(self, item, value):
        self.worldspace[item] = value

    def __iadd__(self, other):
        self.ants.append(other)
        self.palette.extend(other.color)
        self.img.putpalette(self.palette)
        other.color = len(self.ants)
        other.world = self
        return self

    def steps(self, steps):
        for i in xrange(steps):
            for ant in self.ants:
                ant.walk()
            yield self.img.copy()

def main():
    # Optionen-Parsing
    usage = '%prog [options] <outfile>'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-z', '--zoom',
                      type='int',
                      dest='zoom',
                      default=0,
                      help='scales image by factor `n\'',
                      metavar='n')
    options, args = parser.parse_args()
    if not len(sys.argv) == 4 or not (sys.argv[1].isdigit() and
                                      sys.argv[2].isdigit()):
        print >> sys.stderr, ('Benutzung: ameise.py <Anzahl der '
                              'Ameisen> <Anzahl der Schritte> '
                              '<Ausgabedatei>')
        raise SystemExit(1)
    # Eine neue Welt erstellen (100x100)
    world = World((100,100), False)

    for i in xrange(int(sys.argv[1])):
        x = random.randint(0, world.size[0])
        y = random.randint(0, world.size[1])
        color = tuple(random.randint(0, 255) for i in xrange(3))
        world += Ant((x, y), color)
    
    # Die ersten `sys.argv[2]` Schritte der Ameise in ein animiertes Gif
    # speichern (jeden 10. Schritt).
    gif = AnimatedGif(sys.argv[3])
    for i, frame in enumerate(world.steps(int(sys.argv[2]))):
        if not i % 10:
            # Frame vergrößern
            frame = frame.resize((frame.size[0] * 4,
                                  frame.size[1] * 4))
            gif += frame
    gif.close()

if __name__ == '__main__':
    main()
