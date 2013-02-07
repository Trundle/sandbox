# encoding: utf-8

import os
import sys

from gi.repository import Gio, Gtk, Notify

def on_changed(monitor, file, file2, event, remote):
    if event in [Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CREATED]:
        basename = file.get_basename()
        remote_file = remote.get_child(basename)
        if remote_file.query_exists(None):
            print "Copying", file.get_uri(), "to", remote_file.get_uri()
            file.copy(
                remote_file, Gio.FileCopyFlags.OVERWRITE, None,
                lambda *_: None, None)
            msg = "Copied %s to %s" % (file.get_uri(), remote_file.get_uri())
            notification = Notify.Notification.new(
                "Copy operation finished", msg, "dialog-information")
            notification.show()

monitors = list()

def watch(base, remote_base):
    local = Gio.file_new_for_path(base)
    monitor = local.monitor_directory(Gio.FileMonitorFlags.NONE, None)
    monitor.connect("changed", on_changed, remote_base)
    # Keep reference (important)
    monitors.append(monitor)
    for (root, dirs, files) in os.walk(base):
        prefix = os.path.commonprefix([base, root])
        remote_root = remote_base
        for segment in root[len(prefix):].split(os.path.sep):
            remote_root = remote_root.get_child(segment)
        for name in dirs:
            local = Gio.file_new_for_path(os.path.join(root, name))
            remote = remote_root.get_child(name)
            monitor = local.monitor_directory(Gio.FileMonitorFlags.NONE, None)
            monitor.connect("changed", on_changed, remote)
            # Pff, seems like you have to keep a reference to the monitor
            monitors.append(monitor)
            print "Watching", local.get_uri()

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    local, remote = args

    Notify.init("dirsync")

    remote = Gio.file_new_for_uri(remote)

    def mount_done(*args):
        watch(local, remote)

    mount_op = Gio.MountOperation()
    remote.mount_enclosing_volume(
        Gio.MountMountFlags.NONE, mount_op, None, mount_done, None)

    while True:
        Gtk.main_iteration()

if __name__ == "__main__":
    main()
