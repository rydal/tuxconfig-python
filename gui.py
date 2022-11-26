import os
import subprocess
import threading
import time
from os.path import join
from urllib.parse import urlparse

import gi
import gtk
from gi.overrides import Gdk
import librecaptcha
import time
import threading



gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38 (gnome-3.4)
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Vte, GLib, GObject
try:
    from . import tuxconfig
except:
    import tuxconfig            # "__main__" case


import urllib.request  # python < 3.0





def detect_desktop_environment():
    desktop_environment = 'generic'
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        desktop_environment = 'kde'
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        desktop_environment = 'gnome'
    else:
        try:
            info = subprocess.getoutput('xprop -root _DT_SAVE_MODE')
            if ' = "xfce4"' in info:
                desktop_environment = 'xfce'
        except (OSError, RuntimeError):
            pass
    return desktop_environment





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
    current_device = None
    install_page = None
    def __init__(self):
        super().__init__(title="Tuxconfig")
        scrolled_window = Gtk.ScrolledWindow()
        self.set_border_width(3)
        self.notebook = MyWindow.notebook
        self.notebook.set_scrollable(True)
        scrolled_window.add(self.notebook)
        self.add(scrolled_window)
        self.about_page = self.AboutPage()
        self.installable_page = self.ShowInstallableDevices()
        self.creator_page = self.CreatorPage()
        self.install_page = self.InstallDevice()
        self.notebook.append_page(self.about_page.box, Gtk.Label(label="About tuxconfig"))
        self.notebook.append_page(self.installable_page.grid, Gtk.Label(label="Device list"))




    device_map = []





    class AboutPage:
        def __init__(self):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            webView = WebKit2.WebView()
            webView.load_uri("https://www.tuxconfig.com")
            self.box.pack_end(webView,True,True,2)
            self.box.show_all()



    class CreatorPage:
        def __init__(self,device):
            self.box = Gtk.Box()
            self.box.set_border_width(10)
            self.box.add(Gtk.Label(label="About Creator"))
            if device is not None and device.pk is not None:
                webView = WebKit2.WebView()
                webView.load_uri("https://www.tuxconfig.com/user/get_contributor/" + str(device.pk))
                self.box.add(webView)
            self.box.show_all()


    class ShowInstallableDevices:

        def __init__(self):
            self.result = 0
            self.install_success = None
            self.install_failed = None
            self.token = None
            self.grid = Gtk.Grid()
            self.usb_modules_available = tuxconfig.find_device_ids("usb")
            self.pci_modules_available = tuxconfig.find_device_ids("pci")
            self.all_devices_available = self.usb_modules_available.extend(self.pci_modules_available)
            self.consent_label = Gtk.Label(label="Search for available models using this program, this will upload the identifiers of your USB and PCI devices")
            self.grid.attach(self.consent_label,True,True,1,1)
            button = Gtk.Button.new_with_label("remove driver")
            button.connect("clicked", self.get_recaptcha)
            self.grid.attach(button, True,True, 1,1)

        def get_recaptcha(self):
            token = librecaptcha.get_token(api_key="6LcpzzIjAAAAANZRqt762HGss9YRj3spNGkz3K2K",site_url="https://www.tuxconfig.com",gui=True,debug=True)
            tuxconfig.get_modules_available(self.all_devices_available,token)


        def get_device_list(self):

            label = Gtk.Label()
            label.set_markup("<b>USB devices:</b>")
            self.grid.attach(label,0,1,1,1)
            device_index = 1
            for device in self.usb_modules_available:
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
                label = Gtk.Label(label=device.getString())
                label.set_alignment(0.0, 0.0)
                hbox.pack_start(label, True,True, 1)
                if device.tried:
                    button = Gtk.Button.new_with_label("try next driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                    button = Gtk.Button.new_with_label("remove driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                if device.getString() in tuxconfig.InstallUpdates.device_array:
                    button = Gtk.Button.new_with_label("install driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                else:
                    label = Gtk.Label()
                    label.set_markup("Not available")
                    hbox.pack_end(label, True,True, 1)
                self.grid.attach(hbox,0,device_index,1,1)
                device_index = device_index + 1


            label = Gtk.Label()
            label.set_markup("<b>PCI devices:</b>")
            label.set_alignment(0.5, 0.0)
            self.grid.attach(label,0,device_index,1,1)

            for device in self.pci_modules_available:
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
                label = Gtk.Label(label=device.getString())
                label.set_alignment(0.0, 0.0)
                hbox.pack_start(label, True,True, 1)
                if device.tried:
                    button = Gtk.Button.new_with_label("try next driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                    button = Gtk.Button.new_with_label("remove driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                if device.getString() in tuxconfig.InstallUpdates.device_array:
                    button = Gtk.Button.new_with_label("install driver")
                    button.connect("clicked", self.run_install, device)
                    hbox.pack_start(button, True,True, 1)
                else:
                    label = Gtk.Label()
                    label.set_markup("Not available")
                    hbox.pack_end(label, True,True, 1)
                self.grid.attach(hbox,0,device_index,1,1)
                device_index = device_index + 1





        def show_result(self):
            if self.install_success:
                label = Gtk.Label()
                label.set_markup("<style text-color=\"color:greenAccent\">Device installed successfully</style>")
                self.grid.attach(label,0,0,1,1)

            elif self.install_failed:
                label = Gtk.Label()
                label.set_markup("<style text-color=\"color:redAccent\">Device installed failed</style>")
                self.grid.attach(label,0,0,1,1)

        def run_install(self):
            MyWindow.notebook.append_page(MyWindow.install_page, Gtk.Label(label="Install device page"))
            MyWindow.notebook.set_current_page(3)

            
    class InstallDevice:

        def __init__(self,device):
            self.result = 0
            self.install_success = False
            self.install_failed = False
            self.device = device
            self.grid = Gtk.Table()
            self.update_spinner_array = []
            self.array_pointer = 0
            

            if os.geteuid() != 0:
                run_as_root_label  = Gtk.Label(label="This app must be run as root to install devices")
                run_as_root_label.set_hexpand(True)
                self.grid.attach_defaults(run_as_root_label, 0, 0, 1, 1)
            else:
                device_id_label = Gtk.Label(label="Device id: " + self.device.getDeviceId())
                self.grid.attach_defaults(device_id_label, 0, 0, 1, 1)
                revision_label = Gtk.Label(label="Revision: " +  self.device.revision)
                self.grid.attach_defaults(revision_label, 0, 0, 1, 1)
                device_name_label = Gtk.Label(label="Device name: " +  self.device.device_vendor_label)
                self.grid.attach_defaults(device_name_label, 0, 0, 1, 1)
                vendor_name_label = Gtk.Label(label="Device vendor: " +  self.device.vendor_name_label)
                self.grid.attach_defaults(vendor_name_label, 0, 0, 1, 1)
                driver_label = Gtk.Label(label="Module driver name: " +  self.device.driver)
                self.grid.attach_defaults(driver_label, 0, 0, 1, 1)
                if  self.device.subsystem == "usb":
                    subsystem_label = Gtk.Label(label="USB device")
                elif self.device.subsystem == "pci":
                    subsystem_label = Gtk.Label(label="PCI device")
                else:
                    subsystem_label = Gtk.Label(label="Other device")
                self.grid.attach_defaults(subsystem_label, 0, 0, 1, 1)
                github_url_label = Gtk.LinkButton(self.device.clone_url, label="Github repository url")
                self.grid.attach_defaults(github_url_label, 0, 0, 1, 1)
                stars_label = Gtk.Label(label="Github stars awarded: " +  self.device.stars )
                self.grid.attach_defaults(stars_label, 0, 0, 1, 1)
                if self.device.tried:
                    tried_label = Gtk.Label(label="Device tried before on this machine")
                    tried_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 1.0, 0.0, 0.0))
                else:
                    tried_label = Gtk.Label(label="Device not tried on this machine")
                    tried_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 1.0))
                self.grid.attach_defaults(tried_label, 0, 0, 1, 1)
                self.installed_status = Gtk.Label()
                self.grid.attach_defaults(self.installed_status, 0, 0, 1, 1)
                button = Gtk.Button.new_with_label("try next driver")
                button.connect("clicked", self.make_install)
                self.grid.attach(button, True,True, 1)


        def make_install(self):
            self.device.install_module()
            self.t = threading.Timer(1.0, self.add_update_thread)
            self.t.start()
            

        def add_update_thread(self):
                
                while True:
                    if self.device.installed_status > self.array_pointer:
                        box = Gtk.Box()
                        label = Gtk.Label(label= tuxconfig.get_module_install_status(self.device.installed_status))
                        spinner = Gtk.Spinner()
                        spinner.start()
                        self.update_spinner_array.append(spinner)
                        box.pack_start(label,expand=False,padding=1,fill=False)
                        box.pack_end(
                            self.update_spinner_array[self.array_pointer],expand=False,padding=1,fill=False)
                        self.array_pointer += 1
                        self.grid.attach_defaults(box, 0, 0, 1, 1)
                    else:
                        self.t.cancel()       
                    for i in range(len(self.update_spinner_array) -1):
                        self.update_spinner_array[i].stop()
                    if self.device.success is True:
                        success_label = Gtk.Label(label="Device successfully installed on this machine")
                        success_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 1.0, 0.0))
                        self.grid.attach(success_label)
                        self.t.cancel()
                        MyWindow.notebook.append_page(MyWindow.install_page, Gtk.Label(label="About module contributor"))
                        MyWindow.notebook.set_current_page(4)
                    elif self.device.failed is True:
                        failed_label = Gtk.Label(label="Device unsuccessfully installed on this machine")
                        failed_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 1.0, 0.0, 0.0))
                        self.grid.attach(failed_label)
                        self.t.cancel()
                    time.sleep(0.1)

   


if __name__ == "__main__":

    win = MyWindow()
    win.set_default_size(800, 600)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

