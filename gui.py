import os
import threading
import time

import gi
import glib

from tuxconfig import find_device_ids, already_installed, run_install, InstallUpdates

gi.require_version("Gtk", "3.0")
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, GLib, GObject
from gi.repository import WebKit2



class MyWindow(Gtk.Window):
    notebook = Gtk.Notebook()
    def __init__(self):
        super().__init__(title="Tuxconfig")
        self.set_border_width(3)
        



        self.add(MyWindow.notebook)


        MyWindow.notebook.append_page(self.AboutPage(), Gtk.Label(label="About"))
        MyWindow.notebook.append_page(self.DevicePage(), Gtk.Label(label="List devices"))


    @classmethod
    def set_about_page(self,device):
        MyWindow.notebook.append_page(self.CreatorPage(self.notebook,device), Gtk.Label(label="Contributor"))
        MyWindow.notebook.set_current_page(3)

    @classmethod
    def set_install_page(self,button,device):
        MyWindow.notebook.append_page(self.InstallPage(self.notebook,device), Gtk.Label(label="Developer"))
        MyWindow.notebook.set_current_page(2)



    def AboutPage(self):
        page = Gtk.VBox(homogeneous=False, spacing=0)
        page.set_border_width(10)
        if os.geteuid() != 0:
            label = Gtk.Label(label="Must be run as root!")
            label.set_alignment(0.0,0.0)
            page.add(label)
        else:
            webView = WebKit2.WebView()
            webView.load_uri("https://www.tuxconfig.com")
            page.add(webView)
        page.show_all()
        return page

    def CreatorPage(self,device):
        page = Gtk.VBox(homogeneous=False, spacing=0)
        page.set_border_width(10)


        webView = WebKit2.WebView()
        webView.load_uri("https://www.tuxconfig.com/user/get_contributor/" + str(device.pk))
        page.add(webView)
        page.show_all()
        return page


    def InstallPage(self, device):
        page = Gtk.VBox(homogeneous=False, spacing=0)
        page.set_border_width(10)
        grid = Gtk.Grid()
        label = Gtk.Label(label=device.getString())
        label.set_alignment(0.0,0.0)
        grid.attach(label,0,0,1,1)
        update = Gtk.Label(label="Install details")
        update.set_alignment(0.0,0.0)
        grid.attach(update,0,1,1,1)
        result_label = Gtk.Label(label="")
        result_label.set_alignment(0.0,0.0)
        grid.attach(result_label,0,2,1,1)


        def run_install_thread(button,device):
            thread = threading.Thread(target=example_target)
            thread.daemon = True
            thread.start()
            result = run_install(None,device)
            if result is True:
                result_label.set_markup("<span color='green'>{} </span>".format("Device installed successfully"))
                MyWindow.set_about_page(device)
            else:
                result_label.set_markup("<span color='red'>{} </span>".format("Device install failed"))



        if device.tried:
            button = Gtk.Button.new_with_label("try next")
            button.connect("clicked", run_install_thread,device)
            grid.attach(button,0,3,1,1)
            button = Gtk.Button.new_with_label("remove")
            button.connect("clicked", run_install_thread,device)
            grid.attach(button,0,4,1,1)
        else:
            button = Gtk.Button.new_with_label("install")
            button.connect("clicked", run_install_thread,device)
            grid.attach(button,0,3,1,1)
        page.add(grid)



        def update_progess():
            GLib.idle_add(update.set_text,InstallUpdates.result + "\n")


            return False

        def example_target():
            while True:
                GLib.idle_add(update_progess)
                time.sleep(0.2)


        win.show_all()


        page.show_all()
        return page

    device_map = []

    def DevicePage(self):
        page = Gtk.VBox(homogeneous=False, spacing=0)
        page.set_border_width(10)
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
                label.set_alignment(0.0,0.0)
                grid.attach(label,0,row,1,1)
                a.get_repository_details()
                if a.available:

                    button = Gtk.Button.new_with_label("install options")
                    button.connect("clicked", self.set_install_page,a)
                    grid.attach(button,1,row,1,1)

                row += 1

        page.add(grid)
        page.show_all()
        return page

win = MyWindow()
win.set_default_size(800,600)
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()