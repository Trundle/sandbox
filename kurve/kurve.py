#!/usr/bin/env python
# encoding: utf-8
"""
    Achtung, die Kurve.

    A funny game copied by me (Andreas Stührk) at Schorndorf 2010.
"""

from __future__ import division
import math
import random
import sys

import gobject
import gtk

# Around 25 fps
TIMEOUT = 40


class Player(object):
    SPEED = 1.5
    TURN_SPEED = 0.17
    POSITION, DIRECTION, LENGTH = xrange(3)

    def __init__(self, left_key, right_key, color):
        self.color = color
        self.left_key = left_key
        self.right_key = right_key
        self.reset()

    def reset(self):
        self.alive = True
        self.direction = random.random() * math.pi * 2
        self.position = (random.randint(100, 400), random.randint(100, 400))
        self.speed = self.SPEED
        self.turn_speed = self.TURN_SPEED
        self.paths = [(self.position, self.direction, 0)]
        self.points = 0

class GameView(gtk.DrawingArea):
    __gsignals__ = dict(expose_event=None, realize=None)

    HOLE_PROBABILITY = 0.0001
    SIZE = (500, 500)

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.players = [Player(gtk.keysyms.Left, gtk.keysyms.Right, (1, 0, 0)),
                        #Player(ord('m'), ord(','), (0, 1, 0)),
                        #Player(ord('9'), ord('0'), (1, 1, 0)),
                         Player(ord('1'), ord('2'), (0, 0, 1))]
        self.pressed_keys = set()
        self.running = False

    def calculate_end_of_path(self, path):
        from_, direction, length = path
        return (from_[0] + math.sin(direction) * length,
                from_[1] + math.cos(direction) * length)

    def do_expose_event(self, event):
        context = self.window.cairo_create()
        context.rectangle(event.area)
        context.clip()

        # Draw black background
        #context.set_source_rgb(random.random(), random.random(), random.random())
        context.set_source_rgb(0, 0, 0)
        context.paint()
        context.stroke()

        width, height = self.window.get_geometry()[2:4]
        context.scale(width / self.SIZE[0], height / self.SIZE[1])

        # Handle each player
        dead_players = 0
        for player in self.players:
            # Key handling
            if self.running and player.alive:
                # XXX Handle the case when both keys are pressed
                if player.left_key in self.pressed_keys:
                    player.direction += player.turn_speed
                elif player.right_key in self.pressed_keys:
                    player.direction -= player.turn_speed

                from_, direction, length = player.paths[-1]
                do_hole = (random.random() % self.HOLE_PROBABILITY) < 1e-6
                if abs(direction - player.direction) < 1e-6 and not do_hole:
                    length += player.speed
                    player.paths[-1] = (from_, direction, length)
                elif not do_hole:
                    player.paths.append((player.position, player.direction,
                                         player.speed))
                else:
                    player.paths.append(((0, 0), float('inf'), 0))

                # Update position
                if do_hole:
                    path = (player.position, player.direction, 3 * player.speed)
                    player.position = self.calculate_end_of_path(path)
                else:
                    player.position = self.calculate_end_of_path(player.paths[-1])

            # Draw player (except for the last segment)
            context.set_source_rgb(*player.color)
            for path in player.paths[:-1]:
                if path[player.LENGTH] > 0:
                    context.move_to(*path[player.POSITION])
                    end_x, end_y = self.calculate_end_of_path(path)
                    context.line_to(end_x, end_y)

            # Check for collision of curent player (without the last line
            # segment)
            if self.running:
                if player.alive and context.in_stroke(*player.position):
                    player.alive = False
                    dead_players += 1

            # Draw last line segment
            (from_, direction, length) = player.paths[-1]
            if length > 0:
                context.move_to(*from_)
                end_x, end_y = self.calculate_end_of_path((from_, direction,
                                                           length))
                context.line_to(end_x, end_y)

            # Check if the player is out of screen:
            if self.running:
                if player.alive and not (0 <= end_x < self.SIZE[0] and
                                         0 <= end_y < self.SIZE[1]):
                    player.alive = False
                    dead_players += 1

                # Check for colissions of other players
                for other in (p for p in self.players if p is not player):
                    if other.alive and context.in_stroke(*other.position):
                        other.alive = False
                        dead_players += 1
            context.stroke()

        alive_players = 0
        for player in self.players:
            if player.alive:
                alive_players += 1
                player.points += dead_players

        # Anyone alive?
        if alive_players < 2 and dead_players:
            gobject.timeout_add(3000, self.reset)
            self.running = False

    def do_realize(self):
        gtk.DrawingArea.do_realize(self)
        self.running = True
        gobject.timeout_add(TIMEOUT, self.force_redraw)

    def force_redraw(self):
        self.queue_draw()
        # Return True so it can be used with timeout_add
        return True

    def reset(self):
        for player in self.players:
            player.reset()
        self.running = True


def handle_key_press(window, event, view):
    if event.type == gtk.gdk.KEY_RELEASE:
        try:
            view.pressed_keys.remove(event.keyval)
        except KeyError:
            pass
    elif event.type == gtk.gdk.KEY_PRESS:
        view.pressed_keys.add(event.keyval)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    win = gtk.Window()
    view = GameView()
    win.connect('key-press-event', handle_key_press, view)
    win.connect('key-release-event', handle_key_press, view)
    win.add(view)
    win.show_all()
    win.connect('delete-event', gtk.main_quit)
    gtk.main()
    return 0


if __name__ == '__main__':
    sys.exit(main())
