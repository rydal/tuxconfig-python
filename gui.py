import threading
import time

import gi

from tuxconfig import find_device_ids, already_installed, run_install

gi.require_version("Gtk", "3.0")
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, GLib
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
        MyWindow.notebook.set_current_page(4)

    @classmethod
    def set_install_page(self,button,device):
        MyWindow.notebook.append_page(self.InstallPage(self.notebook,device), Gtk.Label(label="Developer"))
        MyWindow.notebook.set_current_page(2)



    def AboutPage(self):
        page = Gtk.VBox(homogeneous=False, spacing=0)
        page.set_border_width(10)


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


        if device.tried:
            button = Gtk.Button.new_with_label("try next")
            button.connect("clicked", run_install,device)
            grid.attach(button,0,1,1,1)
            button = Gtk.Button.new_with_label("remove")
            button.connect("clicked", run_install,device)
            grid.attach(button,0,2,1,1)
        else:
            button = Gtk.Button.new_with_label("install")
            button.connect("clicked", run_install,device)
            grid.attach(button,0,1,1,1)
        page.add(grid)

        progress = Gtk.ProgressBar(show_text=True)
        page.add(progress)

        def update_progess(i):
            progress.pulse()
            progress.set_text(str(i))
            return False

        def example_target():
            for i in range(50):
                GLib.idle_add(update_progess, i)
                time.sleep(0.2)

        win.show_all()

        thread = threading.Thread(target=example_target)
        thread.daemon = True
        thread.start()

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