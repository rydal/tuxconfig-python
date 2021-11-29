import base64
import io
import json
import os
import platform
import random
import string
import subprocess
import threading
import time
import tkinter as Tk
import urllib
import webbrowser
from functools import partial
from json import JSONDecodeError
from tkinter import ttk, GROOVE, LEFT, W, E
from tkinter.ttk import Label
from urllib.request import Request, urlopen

import requests
from PIL import ImageTk, Image

devices_installable = []
class InstallProgress():
    @staticmethod
    def add_device(device):
        devices_installable.append(device)




def set_device(device,tabControl):
    InstallProgress.device = device
    tabControl.select(2)

def show_devices_page(tabControl):
    myframe = Tk.Frame(tabControl, relief=GROOVE, width=50, height=100, bd=1)

    row_number = 1
    title_label = ttk.Label(myframe, text="PCI devices", font=("Arial", 16))
    title_label.grid()

    for device in find_device_ids("pci").values():

        device_label = ttk.Label(myframe, text=device.getString(), justify=LEFT, anchor="w")
        device_label.grid(row=row_number, column=0, sticky=W)

        selected_device, error = device.get_repository_details(device.vendor_id, device.device_id)
        if selected_device.available:
            InstallProgress.add_device(device)
            button = Tk.Label(myframe, text="installable", justify=LEFT, anchor="w")
            button.grid(row=row_number, column=1, sticky=E)
        row_number += 1

    title_label = ttk.Label(myframe, text="USB devices", font=("Arial", 16))
    title_label.grid()
    row_number += 1
    for device in find_device_ids("usb").values():

        device_label = ttk.Label(myframe, text=device.getString(), justify=LEFT, anchor="w")
        device_label.grid(row=row_number, column=0, sticky=W)
        selected_device, error = device.get_repository_details(device.vendor_id, device.device_id)

        if selected_device.available:
            button = Tk.Label(myframe, text="installable", justify=LEFT, anchor="w")
            InstallProgress.add_device(device)
            button.grid(row=row_number, column=1, sticky=E)
        row_number += 1

    return myframe


def callback(url):
    webbrowser.open_new(url)


class WebImage:
    def __init__(self, url):
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers = {'User-Agent': user_agent, }
        req = urllib.request.Request(url, None, headers)

        self.image = Image.open(req)

    def get(self):
        return self.image





def show_index_page(tabControl):
    tab1 = ttk.Frame(tabControl)

    title_label = ttk.Label(tab1, text="Tuxconfig - linux device installer", font=("Arial", 20))
    title_label.pack()

    link1 = Tk.Label(tab1, text="About Tuxconfig", fg="blue", cursor="hand2", font=("Arial", 20))
    link1.pack()
    link1.bind("<Button-1>", lambda e: callback("https://www.tuxconfig.com/about"))
    link1 = Tk.Label(tab1, text="Developer site for contributing repositories", fg="blue", cursor="hand2",
                     font=("Arial", 20))
    link1.pack()
    link1.bind("<Button-1>", lambda e: callback("https://www.tuxconfig.com/developer"))
    title_label = ttk.Label(tab1,
                            text="Install devices easily using this front end, covers usb and pci devices on x86, i386 and raspberry pi devices",
                            font=("Arial", 16))
    title_label.pack()

    return tab1


import tkinter as tk  ## Python 3.x


class show_install_page(ttk.Frame):

    def __init__(self,tabControl):
        super().__init__()

        self.labelA = ttk.Label(self, text="Tuxconfig - install device")
        self.labelA.grid(column=1, row=1)
        button = Tk.Button(self, command=lambda: self.run_install(),
                           text="install device")
        button.grid(column=1,row=2 )
        for device in devices_installable:
            link1 = Tk.Label(self, text="Install " + device.getString() , fg="blue", cursor="hand2", font=("Arial", 20))
            link1.grid()




    def run_install(self,device):
        self.clone_url = device.clone_url
        self.commit = device.commit
        directory = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        clone_git = subprocess.Popen(["git", "clone", self.clone_url, "/tmp/" + directory], stdout=subprocess.PIPE)
        streamdata = clone_git.communicate()[0]
        if clone_git.returncode > 0:
            InstallProgress.error = "Error cloning git repo"
            return

        set_git_commit = subprocess.Popen(["git", "reset", "--hard", self.commit], cwd='/tmp/' + directory,
                                          stdout=subprocess.PIPE)
        streamdata = set_git_commit.communicate()[0]
        if set_git_commit.returncode > 0:
            InstallProgress.error = "Error setting Git branch"
            return

        if not os.path.exists("/tmp/" + directory + "/tuxconfig.conf"):
            InstallProgress.error = "Tuxconfig file not in directory"
            return
        install_command = None
        test_command = None

        with open("/tmp/" + directory + "/tuxconfig.conf", encoding="UTF-8") as tuxconfig_file:
            lines = tuxconfig_file.readlines()
            for index, line in enumerate(lines):
                line = line.replace("\n", "")
                line = line.replace("\"", "")
                if "install_command" in line:
                    line.split("=")
                    install_command = line.split("=")[1].strip("\"")
                if "test_command" in line:
                    line.split("=")
                    test_command = line.split("=")[1].strip("\"")

        if install_command.startswith("./"):
            install_command = install_command[2:len(install_command)]
        install_module = subprocess.Popen(["sudo", "/tmp/" + directory + "/" + install_command], stdout=subprocess.PIPE,
                                          cwd="/tmp/" + directory)
        streamdata = install_module.communicate()[0]

        print(install_module.returncode)
        if install_module.returncode > 0:
            InstallProgress.error = "Error installing module"
            return

        test_module = subprocess.Popen(["/tmp/" + directory + "/" + test_command], stdout=subprocess.PIPE,
                                       cwd="/tmp/" + directory)
        streamdata = test_module.communicate()[0]
        if install_module.returncode > 0:
            InstallProgress.error = "Error testing module"
            return
        InstallProgress.status = "Test command run, module marked as working"
        return True


def find_device_ids(type):
    devices = {}
    for file in os.listdir("/sys/bus/" + type + "/devices"):

        result = subprocess.check_output(
            ["udevadm", "info", os.path.join("/sys/bus/" + type + "/devices/", file)]).decode(
            "utf-8").split("\n")
        device_id = None
        vendor_id = None
        revision = None
        model_vendor = None
        model_name_id = None
        model_name = None
        driver = None
        subsystem = None
        for line in result:
            line = line[3:len(line)]
            if line.startswith("DRIVER="):
                driver = line[7:len(line)]
            if line.startswith("PRODUCT="):
                product = line[12:len(line)]
            if line.startswith("PCI_ID=") and type == "pci":
                pci_id = line[7:len(line)]
                pci_id_array = pci_id.split(":")
                if len(pci_id_array) >= 2:
                    device_id = pad_ids(pci_id_array[0])
                    vendor_id = pad_ids(pci_id_array[1])
                if len(pci_id_array) == 3:
                    revision = pad_ids(pci_id_array[2])
            if line.startswith("PRODUCT=") and type == "usb":
                pci_id = line[8:len(line)]
                pci_id_array = pci_id.split("/")
                if len(pci_id_array) >= 2:
                    device_id = pad_ids(pci_id_array[0])
                    vendor_id = pad_ids(pci_id_array[1])
                if len(pci_id_array) == 3:
                    revision = pad_ids(pci_id_array[2])
            if line.startswith("ID_MODEL="):
                model_name_id = line[9:len(line)]
            if line.startswith("ID_MODEL_FROM_DATABASE="):
                model_name = line[23:len(line)]
            if line.startswith("ID_VENDOR_FROM_DATABASE="):
                model_vendor = line[24:len(line)]
            if line.startswith("SUBSYSTEM="):
                subsystem = line[10:len(line)]
        if device_id is not None and vendor_id is not None:
            device = device_details()
            device.setDeviceId(device_id)
            device.setVendorId(vendor_id)
            device.setVendor(model_vendor)
            if model_name_id is None and model_name is None:
                continue
            elif model_name_id is not None and model_name is None:
                device.setName(model_name_id)
            elif model_name is not None and model_name_id is None:
                device.setName(model_name)
            elif model_name is not None and model_name_id is not None:
                device.setName(model_name)
            device.setRevision(revision)
            device.setDriver(driver)
            device.setSubsystem(subsystem)
            devices[str(device_id + ":" + vendor_id)] = device

    return devices


def pad_ids(usb_id):
    while len(usb_id) < 4:
        usb_id = "0" + usb_id
    return usb_id


def get_platform():
    if platform.processor() == "i386":
        return "i386"
    elif platform.processor() == "x86_64":
        return "x86_64"
    else:
        with open('/proc/cpuinfo') as f:
            line = f.read()
            if 'Hardware' in line:
                hardware_id = line.split(":")[1]
                hardware_id.strip(" ")
        return hardware_id


class device_details:
    def setName(self, device_name):
        self.device_name = device_name

    def setDeviceId(self, vendorId):
        self.vendor_id = vendorId

    def setVendorId(self, device_id):
        self.device_id = device_id

    def setVendor(self, device_vendor):
        self.device_vendor = device_vendor

    def setDriver(self, driver):
        self.driver = driver

    def setRevision(self, revision):
        self.revision = revision

    def setSubsystem(self, subsystem):
        self.subsystem = subsystem

    def get_repository_details(self, vendor_id, device_id):
        current_repository = None
        response = requests.get(
            'https://www.tuxconfig.com/user/get_device/' + vendor_id + ":" + device_id + "/" + get_platform())
        if response.status_code >= 400 and response.status_code < 400:
            return None, "connection error"
        elif response.status_code >= 500:
            return None, "server error"
        else:
            try:
                string = response.content.decode('utf-8')
                json_response = json.loads(string)

                if "none" in json_response:
                    self.available = False
                else:
                    if len(json_response) == 0:
                        print(
                            'https://www.tuxconfig.com/user/get_device/' + vendor_id + ":" + device_id + "/" + get_platform())
                        return None, "empty list"
                    current_repository = json_response[0]
                    for repository in json_response:
                        if repository['stars'] > current_repository['stars']:
                            current_repository = repository
                        self.available = True
                        self.clone_url = current_repository['clone_url']
                        self.commit = current_repository['commit']
                        self.stars = current_repository['stars']
                        self.pk = current_repository['pk']
            except JSONDecodeError:
                return "cannot parse server request"
        return self, None

    def write_to_file(self):

        f = open("/var/lib/tuxconfig_conf", "w")
        json_string = json.dumps({"vendor_id": self.vendor_id, "device_id": self.device_id, "revision": self.revision,
                                  "vendor_name": self.device_vendor, "device_name": self.device_name,
                                  "driver": self.driver, "clone_url": self.clone_url, "stars": self.stars,
                                  "pk": self.pk, "tried": self.tried, "success": self.success})
        f.write(json_string)
        f.close()

    def __init__(self):

        self.vendor_id = None
        self.device_id = None
        self.revision = None
        self.device_name = None
        self.device_vendor = None
        self.driver = None
        self.subsystem = None
        self.clone_url = None
        self.commit = None
        self.stars = None
        self.pk = None
        self.tried = False
        self.success = False
        self.available = False

    def getString(self):
        if self.driver:
            self.installed = "installed"
        else:
            self.installed = "not installed"

        return self.vendor_id + ":" + self.device_id + self.device_vendor + self.device_name

    def getAvailable(self):
        return self.available

    def getHardwareID(self):
        return self.vendor_id + ":" + self.device_id + self.device_vendor + self.device_name


notebook = None


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Tuxconfig")

        self.notebook = ttk.Notebook(self)

        self.Frame1 = show_index_page(self.notebook)
        self.Frame2 = show_devices_page(self.notebook)
        self.Frame3 = show_install_page(self.notebook)

        self.notebook.add(self.Frame1, text='Index page')
        self.notebook.add(self.Frame2, text='List devices')
        self.notebook.add(self.Frame3, text='Install devices')

        self.notebook.pack()


if __name__ == '__main__':
    app = MainApplication()
    app.mainloop()
