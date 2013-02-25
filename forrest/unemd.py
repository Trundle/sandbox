#!/usr/bin/env python3

"""
    Like dmenu, but with real font support.
"""

import argparse
import re
import sys
import time
import unicodedata
from itertools import chain, dropwhile, islice
from functools import wraps

from gi.repository import Gdk, GLib, GObject, Gtk, Pango


### Helper functions ###########################################################

def color_to_rgba(description):
    "Parses a color description to a `Gdk.RGBA`."
    color = Gdk.color_parse(description)
    return Gdk.RGBA(
        red=color.red,
        green=color.green,
        blue=color.blue)

def color_to_hex(color):
    return "#" + ("{:02x}" * 3).format(
        int(color.red * (2 ** 16)),
        int(color.green * (2 ** 16)),
        int(color.blue * (2 ** 16)))


### Menu commands ##############################################################

def matches_required(func):
    @wraps(func)
    def wrapper(menu):
        if menu.matches:
            func(menu)
    return wrapper

def do_delete(menu):
    del menu.input[-1:]
    menu.input_changed()

@matches_required
def do_expand(menu):
    menu.input = list(menu.matches[menu.index])
    menu.input_changed()

@matches_required
def do_expand_or_next(menu):
    current_match = menu.matches[menu.index]
    if "".join(menu.input) != current_match:
        menu.input = list(current_match)
        menu.update()
    else:
        do_next(menu)

@matches_required
def do_next(menu):
    menu.index += 1
    menu.input = list(menu.matches[menu.index])
    menu.update()

@matches_required
def do_previous(menu):
    menu.index -= 1
    menu.input = list(menu.matches[menu.index])
    menu.update()

def do_select(menu):
    """Selects the current input. Automatically expands to the current
    match if there is a current match before selecting.
    """
    if menu.matches:
        match = menu.matches[menu.index]
    else:
        match = "".join(menu.input)
    menu.emit("selected", match)

def do_quit(menu):
    menu.emit("quit")


### The menu itself ############################################################

class Menu(GObject.GObject):
    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_LAST, None, [str]),
        "quit": (GObject.SIGNAL_RUN_LAST, None, [])
    }

    commands = {
        "delete": do_delete,
        "expand": do_expand,
        "expand-or-next": do_expand_or_next,
        "next": do_next,
        "previous": do_previous,
        "select": do_select,
        "quit": do_quit
    }

    keymap = {
        # No modifier
        (0, Gdk.KEY_BackSpace): "delete",
        (0, Gdk.KEY_Escape): "quit",
        (0, Gdk.KEY_Left): "previous",
        (0, Gdk.KEY_Return): "select",
        (0, Gdk.KEY_Right): "next",
        (0, Gdk.KEY_Tab): "expand-or-next",
        # Control modifier
        (Gdk.ModifierType.CONTROL_MASK, Gdk.KEY_g): "quit",
        # Shift modifier
        (Gdk.ModifierType.SHIFT_MASK, Gdk.KEY_ISO_Left_Tab): "previous"
    }

    def __init__(self, matcher, font, bg_color, fg_color):
        super(Menu, self).__init__()
        self.input = []
        self.matcher = matcher
        self.matches = []
        self.index = 0
        self._keys_grabbed = False
        self.bg_color = color_to_rgba(bg_color)
        self.fg_color = color_to_rgba(fg_color)
        self._create_widgets(font=font)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        number_of_matches = len(self.matches)
        if number_of_matches == 0:
            self._index = 0
        else:
            self._index = value % number_of_matches

    def hide(self):
        self._ungrab_keys()
        self._window.hide()

    def show(self):
        self._position()
        self._window.show_all()
        self._grab_keys()

    def update(self):
        "Should be called after the `input` attribute was changed."
        input = "".join(self.input)
        markup = input
        if input:
            if self.matches:
                matches = self.matches
                markup += "{"
                markup += self._format_first_match(input, matches[self.index])
                if len(matches) > 1:
                    remaining_matches = chain(
                        islice(matches, self.index + 1, None),
                        islice(matches, max(self.index, 0)))
                    markup += " | " + " | ".join(remaining_matches)
                markup += "}"
            else:
                markup += "[no matches]"
        self._label.set_markup(markup)

    def _create_widgets(self, font):
        self._window = Gtk.Window(Gtk.WindowType.POPUP)
        self._window.override_background_color(
            Gtk.StateFlags.NORMAL, self.bg_color)
        self._label = Gtk.Label()
        self._label.override_color(Gtk.StateFlags.NORMAL, self.fg_color)
        self._label.override_font(Pango.FontDescription(font))
        self._label.set_halign(Gtk.Align.START)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._window.add(self._label)
        self._window.connect("key-press-event", self._on_key_press_event)
        self._window.connect("destroy-event", lambda _: self._ungrab_keys())

    def _format_first_match(self, input, match):
        markup = list('<span foreground="{}" background="{}">'.format(
            color_to_hex(self.bg_color), color_to_hex(self.fg_color)))
        shift = len(markup)
        markup.extend(match)
        for input_match in re.finditer(re.escape(input), match):
            (start, end) = input_match.span()
            start += shift
            shift += 3
            end += shift
            shift += 4
            markup[start:start] = "<b>"
            markup[end:end] = "</b>"
        markup.extend("</span>")
        return "".join(markup)

    def _grab_keys(self):
        window = self._window.get_window()
        success = [Gdk.GrabStatus.ALREADY_GRABBED, Gdk.GrabStatus.SUCCESS]
        for i in range(10):
            # Deprecated, but `Gdk.DeviceManager` doesn't seem to be
            # usable from Python
            result = Gdk.keyboard_grab(window, False, Gdk.CURRENT_TIME)
            if result in success:
                self._keys_grabbed = True
                break
            time.sleep(0.1)
        else:
            self.hide()
            dialog = Gtk.MessageDialog(
                message_format="Could not grab keyboard.",
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK)
            dialog.run()
            dialog.destroy()
            self.commands["quit"](self)

    def _ungrab_keys(self):
        if self._keys_grabbed:
            Gdk.keyboard_ungrab(Gdk.CURRENT_TIME)
            self._keys_grabbed = False

    def _position(self):
        screen = self._window.get_screen()
        root_window = Gdk.get_default_root_window()
        (_, pointer_x, pointer_y, _) = root_window.get_pointer()
        monitor_number = screen.get_monitor_at_point(pointer_x, pointer_y)
        monitor_rect = screen.get_monitor_geometry(monitor_number)
        (_, natural_height) = self._label.get_preferred_height()
        self._window.move(monitor_rect.x, monitor_rect.y)
        self._window.set_default_size(monitor_rect.width, natural_height)

    def input_changed(self):
        "Should be called after the `input`  attribute was modified."
        self.index = 0
        self.matches = self.matcher("".join(self.input))
        self.update()

    def _on_key_press_event(self, window, event):
        command = self.keymap.get((event.get_state(), event.keyval))
        if command is not None:
            self.commands[command](self)
        else:
            data = event.string
            if len(data) == 1 and unicodedata.category(data) != "Cc":
                self.input.append(data)
                self.input_changed()


### Matcher ####################################################################

class _Marker:
    def __len__(self):
        return sys.maxsize

    def find(self, _):
        return -1

    def lower(self):
        return self

class InsensitiveMatcher:
    def __init__(self, values):
        self._marker = _Marker()
        self.values = values
        self.values.append(self._marker)
        self.values_lower = [x.lower() for x in values]
        self.values_lower.append(self._marker)

    def get_matches(self, input):
        def inner():
            def keyfunc(value):
                (value, lower) = value
                return lower.find(input_lower)
            input_lower = input.lower()
            matches = sorted(zip(self.values, self.values_lower), key=keyfunc)
            matches_iter = dropwhile(lambda x: x[0] is not self._marker, matches)
            for (value, _) in islice(matches_iter, 1, None):
                yield value
        return list(inner())


### Application logic ##########################################################

def on_selected(menu, entry):
    on_quit(menu)
    sys.stdout.write(entry)

def on_quit(menu):
    menu.hide()
    Gtk.main_quit()

def _create_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-bg", "--bg-color", default="#000000")
    parser.add_argument("-fg", "--fg-color", default="green")
    parser.add_argument("-fn", "--font", default="Inconsolata 16")
    return parser

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = _create_argument_parser().parse_args(args)

    menu = Menu(
        InsensitiveMatcher(sys.stdin.read().splitlines()).get_matches,
        font=parsed_args.font,
        bg_color=parsed_args.bg_color,
        fg_color=parsed_args.fg_color)
    menu.connect("selected", on_selected)
    menu.connect("quit", on_quit)
    GLib.idle_add(menu.show)
    Gtk.main()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
