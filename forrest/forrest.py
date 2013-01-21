#!/usr/bin/env python3

"""
    Like drun, but different.
"""

import io
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from itertools import chain, islice
from functools import wraps

from gi.repository import Gdk, GLib, GObject, Gtk, Pango


### Settings ###################################################################

FONT = "Inconsolata 16"
BG_COLOR = "#000000"
FG_COLOR = "green"
HISTFILE = "~/.config/mrun.history"
HISTSIZE = 100
TERMINAL = (
    "urxvt +sb "
    "-font 'xft:Inconsolata:autohint=true:antialias=true:pixelsize=18' "
    "-colorIT red -e sh -c")


### Helper functions ###########################################################

def color_to_rgba(description):
    "Parses a color description to a `Gdk.RGBA`."
    color = Gdk.color_parse(description)
    max = 2 ** 16
    return Gdk.RGBA(
        red=color.red / max,
        green=color.green / max,
        blue=color.blue / max)


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
    menu.emit("selected", "".join(menu.input), False)

# XXX select2 is a terrible name
def do_select2(menu):
    menu.emit("selected", "".join(menu.input), True)

def do_quit(menu):
    menu.emit("quit")


### The menu itself ############################################################

class Menu(GObject.GObject):
    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_LAST, None, [str, bool]),
        "quit": (GObject.SIGNAL_RUN_LAST, None, [])
    }

    commands = {
        "delete": do_delete,
        "expand": do_expand,
        "expand-or-next": do_expand_or_next,
        "next": do_next,
        "previous": do_previous,
        "select": do_select,
        "select2": do_select2,
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
        (Gdk.ModifierType.CONTROL_MASK, Gdk.KEY_Return): "select2",
        (Gdk.ModifierType.CONTROL_MASK, Gdk.KEY_g): "quit",
        # Shift modifier
        (Gdk.ModifierType.SHIFT_MASK, Gdk.KEY_ISO_Left_Tab): "previous"
    }

    def __init__(self, matcher):
        super(Menu, self).__init__()
        self.input = []
        self.matcher = matcher
        self.matches = []
        self.index = 0
        self._keys_grabbed = False
        self._create_widgets()

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

    def _create_widgets(self):
        self._window = Gtk.Window(Gtk.WindowType.POPUP)
        bg_color = color_to_rgba(BG_COLOR)
        self._window.override_background_color(Gtk.StateFlags.NORMAL, bg_color)
        self._label = Gtk.Label()
        fg_color = color_to_rgba(FG_COLOR)
        self._label.override_color(Gtk.StateFlags.NORMAL, fg_color)
        self._label.override_font(Pango.FontDescription(FONT))
        self._label.set_halign(Gtk.Align.START)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._window.add(self._label)
        self._window.connect("key-press-event", self._on_key_press_event)
        self._window.connect("destroy-event", lambda _: self._ungrab_keys())

    def _format_first_match(self, input, match):
        markup = list(match)
        shift = 0
        for input_match in re.finditer(re.escape(input), match):
            (start, end) = input_match.span()
            start += shift
            shift += 3
            end += shift
            shift += 4
            markup[start:start] = "<b>"
            markup[end:end] = "</b>"
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


### Matchers ###################################################################

class ExecutableMatcher:
    def __init__(self):
        self.executables = set()
        self._fill()

    def get_matches(self, input):
        return sorted(
            set(x for x in self.executables if input in x),
            key=lambda x: (x.index(input), len(x)))

    def _fill(self):
        for path in os.environ["PATH"].split(os.pathsep):
            try:
                for filename in os.listdir(path):
                    if os.access(os.path.join(path, filename), os.X_OK):
                        self.executables.add(filename)
            except EnvironmentError:
                pass


class HistoryMatcher:
    def __init__(self, history_path):
        try:
            with open(history_path, "r") as hist_file:
                self.history = [line.strip("\n") for line in hist_file]
        except EnvironmentError:
            self.history = []
        self.history_path = history_path

    def append(self, entry):
        self.history.append(entry)

    def get_matches(self, input):
        return sorted(
            set(x for x in self.history if input in x),
            key=lambda x: (x.index(input), len(x)))

    def write_history(self, number_of_entries):
        history_dir = os.path.dirname(self.history_path)
        (handle, temp_history_path) = tempfile.mkstemp(dir=history_dir)
        try:
            with io.open(handle, "w") as hist_file:
                hist_file.write("\n".join(self.history[-number_of_entries:]))
            os.rename(temp_history_path, self.history_path)
        except:
            os.unlink(temp_history_path)
            raise


class Matcher:
    def __init__(self, matchers):
        self.matchers = matchers

    def get_matches(self, input):
        return list(chain.from_iterable(m(input) for m in self.matchers))


### Application logic ##########################################################

def on_selected(menu, entry, run_in_terminal, history_matcher):
    on_quit(menu)
    if run_in_terminal:
        cmd = '{} "{}"'.format(TERMINAL, entry)
    else:
        cmd = entry
    subprocess.Popen(cmd, shell=True)
    history_matcher.append(entry)
    history_matcher.write_history(HISTSIZE)

def on_quit(menu):
    menu.hide()
    Gtk.main_quit()

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    history_matcher = HistoryMatcher(os.path.expanduser(HISTFILE))
    matcher = Matcher([
        history_matcher.get_matches,
        ExecutableMatcher().get_matches])
    menu = Menu(matcher.get_matches)
    menu.connect("selected", on_selected, history_matcher)
    menu.connect("quit", on_quit)
    GLib.idle_add(menu.show)
    Gtk.main()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
