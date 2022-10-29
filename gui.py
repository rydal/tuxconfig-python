import os
import subprocess
import threading
import time
from os.path import join
from urllib.parse import urlparse

import gi
import gtk

from gi.repository.GLib import Thread


gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38 (gnome-3.4)
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Vte, GLib, GObject
try:
    from . import tuxconfig
except:
    import tuxconfig            # "__main__" case


import urllib.request  # python < 3.0

global current_device



def can_i_haz_internet(host='https://google.com'):
    global  web_connected
    try:
        urllib.request.urlopen(host) #Python 3.x
        web_connected = True
    except:
        web_connected = False


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

    notebook = Gtk.Notebook()

    def __init__(self):
        super().__init__(title="Tuxconfig")
        scrolled_window = Gtk.ScrolledWindow()
        self.set_border_width(3)
        self.notebook = MyWindow.notebook
        self.notebook.set_scrollable(True)
        scrolled_window.add(self.notebook)
        self.add(scrolled_window)
        self.about_page = self.AboutPage()
        self.device_page = self.DevicePage()
        self.install_page = self.InstallPage()
        self.creator_page = self.CreatorPage()
        self.request_page = self.RequestPage()
        self.notebook.append_page(self.about_page.box, Gtk.Label(label="About tuxconfig"))
        self.notebook.append_page(self.device_page.box, Gtk.Label(label="Device list"))
        self.notebook.append_page(self.install_page.box,Gtk.Label(label="Install device driver"))
        self.notebook.append_page(self.creator_page.box,Gtk.Label(label="About module creator"))
        
    
    def set_about_page(self):
        self.notebook.set_current_page(2)



    device_map = []



    class DevicePage:
        def __init__(self):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            spinner = Gtk.Spinner()
            spinner.set_halign(align=Gtk.Align.CENTER)
            spinner.set_valign(align=Gtk.Align.CENTER)
            spinner.start()
            self.box.pack_start(spinner,False,False,6)
            devices = []
            pci_devices = tuxconfig.find_device_ids("pci")
            devices.append(pci_devices)
            usb_devices = tuxconfig.find_device_ids("usb")
            devices.append(usb_devices)
            listbox = Gtk.ListBox()

            for device_available in devices:
                print (device_available)
                for a in device_available.values():
                    label = Gtk.Label(label=a.getString())
                    a.get_repository_details()
                    row = Gtk.Box()
                    if a.available:
                        label = Gtk.Label(label="Device: %s".format(a.getString()))
                        button = Gtk.Button.new_with_label("install options")
                        button.connect("clicked", self.set_install_page, a)
                    else:
                        label = Gtk.Label(label="Device: {}".format(a.device_id))
                        request_url = urlparse("http://www.tuxconfig.com/request/{}".format(a.device_id))
                        button = Gtk.LinkButton(request_url, label="Request deriver support")
                    if tuxconfig.get_device_installed_list(a.device_name):
                        installed_label = Gtk.Label(label="Installed")
                    else:
                        installed_label = Gtk.Label(label="Not Installed")
                    row.pack_start(label,True,True,0)
                    row.pack_start(installed_label,True,True,0)
                    row.pack_end(button,True,True,0)

                    listbox.add(row)
            self.box.remove(spinner)
            self.box.pack_start(listbox, True, True, 0)
            self.box.show_all()
        def set_install_page(self,a):
            current_device = a
            MyWindow.notebook.set_current_page(3)


    class AboutPage:
        def __init__(self):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            webView = WebKit2.WebView()
            if can_i_haz_internet():
                webView.load_uri("https://www.tuxconfig.com/landing")
            else:
                data_file = join("file://",os.getcwd(),"/landing.html")
                webView.load_uri(data_file)
            self.box.pack_end(webView,True,True,2)
            self.box.show_all()


    class RequestPage:
        def __init__(self,device):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            webView = WebKit2.WebView()
            if can_i_haz_internet():
                webView.load_uri(join("https://www.tuxconfig.com/request/",device.device_id))
            else:
                data_file = join("file://",os.getcwd(),"/landing.html")
                webView.load_uri(data_file)
            self.box.pack_end(webView,True,True,2)
            self.box.show_all()


    class CreatorPage:
        def __init__(self):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            self.box.add(Gtk.Label(label="About Creator"))
            webView = WebKit2.WebView()
            webView.load_uri("https://www.tuxconfig.com/user/get_contributor/" + str(current_device.pk))
            self.box.add(webView)
            self.box.show_all()


    class InstallPage():

        def __init__(self):
            self.result = 0
            self.install_success = None
            self.install_failed = None
            self.box = Gtk.Box()
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
                button.connect("clicked", tuxconfig.run_install, current_device)
                self.grid.attach(button, 0, 3, 1, 1)
                button = Gtk.Button.new_with_label("remove driver")
                button.connect("clicked", tuxconfig.run_install, current_device)
                self.grid.attach(button, 0, 4, 1, 1)
            else:
                button = Gtk.Button.new_with_label("install driver")
                button.connect("clicked", tuxconfig.run_install, current_device)
                self.grid.attach(button, 0, 3, 1, 1)

            self.grid.show_all()
            self.box.add(self.grid)

        def show_result(self):
            if self.install_success:
                self.result.set_markup("<span color='green'>{} </span>".format("Device installed successfully"))
            elif self.install_failed:
                self.result.set_markup("<span color='red'>{} </span>".format("Device install failed"))


win = MyWindow()
win.set_default_size(800, 600)
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
