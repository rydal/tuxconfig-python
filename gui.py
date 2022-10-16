import os
import threading
import time

import gi
import tkinter as tk

from gi.repository.GLib import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38 (gnome-3.4)
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Vte, GLib, GObject
from tuxconfig import find_device_ids, run_install, InstallUpdates, write_to_file, device_details, install_success, \
    install_failed
import threading as th
# install_command
# test_command
# module_id

# uninstall_module
# install_module
# test_module
# pkill -sigusr1
# term.watch_child(pid[1])

class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Tuxconfig")
        self.set_border_width(3)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.page1 = Gtk.Box()
        self.page1.set_border_width(10)
        self.page1.add(Gtk.Label(label="Default Page!"))
        self.notebook.append_page(self.page1, Gtk.Label(label="Plain Title"))

        self.page2 = Gtk.Box()
        self.page2.set_border_width(10)
        self.page2.add(Gtk.Label(label="A page with an image for a Title."))

class AboutPage:
    def __init__(self):
        self.page = Gtk.Box()
        self.page.set_border_width(10)
        self.page.add(Gtk.Label(label="About Tuxconfig"))
        if os.geteuid() != 0:
            label = Gtk.Label(label="Must be run as root!")
            label.set_alignment(0.0, 0.0)
            self.page.pack_start(label,True,True,2)
        else:
            webView = WebKit2.WebView()
            webView.load_uri("https://www.tuxconfig.com")
            self.page.pack_end(webView,True,True,2)
            self.page.show_all()

    def get_page(self):
        return self
class CreatorPage:
    def __init__(self):
        self.page = Gtk.Box()
        self.page.set_border_width(10)
        self.page.add(Gtk.Label(label="About Creator"))
        webView = WebKit2.WebView()
        webView.load_uri("https://www.tuxconfig.com/user/get_contributor/" + str(current_device.pk))
        self.page.add(webView)
        self.page.show_all()

    def get_page(self):
        return self

class InstallPage(GObject.GObject):
    __gsignals__ = {
        'my_signal': (GObject.SIGNAL_RUN_FIRST, None,
                      (int,))
    }
    def do_my_signal(self, arg):
        print("method handler for `my_signal' called with argument", arg)

    def run_install_thread(self,device):

        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            ["/bin/sh"],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
        )


    def __init__(self):
        self.page = Gtk.Box()
        self.grid = Gtk.Grid()
        label = Gtk.Label(label=current_device.getString())
        label.set_alignment(0.0, 0.0)
        self.grid.attach(label, 0, 0, 1, 1)
        update = Gtk.Label(label="Install details:")
        update.set_alignment(0.0, 0.0)
        self.grid.attach(update, 0, 1, 1, 1)
        self.terminal = Vte.Terminal()
        result_label = Gtk.Label(label="Result:")
        result_label.set_alignment(0.0, 0.0)
        self.grid.attach(result_label, 0, 2, 1, 1)
        self.result = Gtk.Label(label="")
        self.result.set_alignment(0.0, 0.0)
        self.grid.attach(result_label, 0, 2, 1, 1)

        win.connect('delete-event', Gtk.main_quit)
        self.grid.add(self.terminal)
        if current_device.tried:
            button = Gtk.Button.new_with_label("try next driver")
            button.connect("clicked", self.run_install_thread, current_device)
            self.grid.attach(button, 0, 3, 1, 1)
            button = Gtk.Button.new_with_label("remove driver")
            button.connect("clicked", self.run_install_thread, current_device)
            self.grid.attach(button, 0, 4, 1, 1)
        else:
            button = Gtk.Button.new_with_label("install driver")
            button.connect("clicked", self.run_install_thread, current_device)
            self.grid.attach(button, 0, 3, 1, 1)

        self.grid.show_all()
        self.page.add(self.grid)

    def show_result(self):
        if install_success:
            self.result.set_markup("<span color='green'>{} </span>".format("Device installed successfully"))
        elif install_failed:
            self.result.set_markup("<span color='red'>{} </span>".format("Device install failed"))

    def get_page(self):
        return self


current_device = device_details()
class MyWindow(Gtk.Window):
    notebook = Gtk.Notebook()

    def __init__(self):
        super().__init__(title="Tuxconfig")
        self.set_border_width(3)

        self.add(MyWindow.notebook)

        MyWindow.notebook.append_page(self.AboutPage(), Gtk.Label(label="About"))
        MyWindow.notebook.append_page(self.DevicePage(), Gtk.Label(label="List devices"))

    @classmethod
    def set_about_page(self):
        creator_page = self.CreatorPage()
        MyWindow.notebook.append_page(creator_page, Gtk.Label(label="Contributor"))
        MyWindow.notebook.set_current_page(3)

    @classmethod
    def set_install_page(self):
        MyWindow.notebook.append_page(self.InstallPage(), Gtk.Label(label="Developer"))
        MyWindow.notebook.set_current_page(2)




    device_map = []

    def DevicePage(self):
        page = Gtk.VBox()
        grid = Gtk.Grid()
        devices = []
        pci_devices = find_device_ids("pci")
        devices.append(pci_devices)
        usb_devices = find_device_ids("usb")
        devices.append(usb_devices)
        row = 0

        for device_available in devices:
            for a in device_available.values():
                label = Gtk.Label(label=a.getString())
                label.set_alignment(0.0, 0.0)
                grid.attach(label, 0, row, 1, 1)
                a.get_repository_details()
                if a.available:
                    button = Gtk.Button.new_with_label("install options")
                    button.connect("clicked", self.set_install_page, a)
                    grid.attach(button, 1, row, 1, 1)

                row += 1

        return page


win = MyWindow()
win.set_default_size(800, 600)
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
