#!/usr/bin/env python3

import io
import os
import subprocess
import sys
import tempfile
from itertools import chain


HISTFILE = "~/.config/forrest.history"
HISTSIZE = 100


def get_all_executables():
    executables = set()
    for path in os.environ["PATH"].split(os.pathsep):
        try:
            for filename in os.listdir(path):
                if os.access(os.path.join(path, filename), os.X_OK):
                    executables.add(filename)
        except EnvironmentError:
            pass
    return executables

def load_history(history_path):
    try:
        with open(history_path, "r") as hist_file:
            history = [line.strip("\n") for line in hist_file]
    except EnvironmentError:
        history = []
    return history

def write_history(history_path, history, number_of_entries):
    history_dir = os.path.dirname(history_path)
    (handle, temp_history_path) = tempfile.mkstemp(dir=history_dir)
    try:
        with io.open(handle, "w") as hist_file:
            hist_file.write("\n".join(history[-number_of_entries:]))
        os.rename(temp_history_path, history_path)
    except:
        os.unlink(temp_history_path)
        raise


def uniquify(iterable):
    already_seen = set()
    for value in iterable:
        if value not in already_seen:
            already_seen.add(value)
            yield value

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    hist_file = os.path.expanduser(HISTFILE)
    history = load_history(hist_file)

    unemd_args = [os.path.join(os.path.dirname(__file__), "unemd.py")]
    unemd_args.extend(args)
    menu = subprocess.Popen(
        unemd_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    executables = sorted(get_all_executables())
    values = uniquify(chain(sorted(history), executables))
    (stdout, _) = menu.communicate("\n".join(values).encode("utf-8"))
    cmd = stdout.strip().decode("utf-8")
    if cmd:
        history.append(cmd)
        write_history(hist_file, history, HISTSIZE)
        subprocess.call(cmd, shell=True)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
