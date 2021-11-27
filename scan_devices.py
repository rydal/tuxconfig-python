import json
import os
import platform
from json import JSONDecodeError
from tkinter import ttk, Button, Canvas, Frame, GROOVE, Scrollbar, LEFT, W, E

import requests

from subprocess import check_output

from install_device import install_device_page


def show_devices_page(tabControl):
    myframe = Frame(tabControl, relief=GROOVE, width=50, height=100, bd=1)

    row_number = 1
    title_label = ttk.Label(myframe, text="PCI devices", font=("Arial", 16))
    title_label.grid()

    for device in find_device_ids("pci").values():

        device_label = ttk.Label(myframe, text=device.getString(), justify=LEFT,anchor="w")
        device_label.grid(row=row_number, column=0,sticky=W)

        device.get_repository_details(device.vendor_id, device.device_id)
        if device.available:
            button  = Button(myframe, command=install_device_page(tabControl,device))
            button.grid(row=row_number,column=1,sticky=E)
        row_number += 1

    title_label = ttk.Label(myframe, text="USB devices", font=("Arial", 16))
    title_label.grid()
    row_number += 1
    for device in find_device_ids("usb").values():

        device_label = ttk.Label(myframe, text=device.getString(), justify=LEFT,anchor="w")
        device_label.grid(row=row_number, column=0,sticky=W)

        if device.available:
            button  = Button(myframe, command=install_device_page(tabControl,device))
            button.grid(row=row_number,column=1,sticky=E)
        row_number += 1

    return myframe


def find_device_ids(type):
    devices = {}
    for file in os.listdir("/sys/bus/" + type + "/devices"):

        result = check_output(["udevadm", "info", os.path.join("/sys/bus/" + type + "/devices/", file)]).decode(
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
            devices[str(device_id + ":" + vendor_id)  ] = device

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
    def setName(self,device_name):
        self.device_name = device_name
    def setDeviceId(self,vendorId):
        self.vendor_id = vendorId
    def setVendorId(self,device_id):
        self.device_id = device_id
    def setVendor(self,device_vendor):
        self.device_vendor = device_vendor
    def setDriver(self,driver):
        self.driver = driver
    def setRevision(self,revision):
        self.revision = revision
    def setSubsystem(self,subsystem):
        self.subsystem = subsystem

    def get_repository_details(self, vendor_id, device_id):
        response = requests.get(
            'https://www.tuxconfig.com/user/get_device/' + vendor_id + ":" + device_id + "/" + get_platform())
        if response.status_code >= 400 and response.status_code < 400:
            return "connection error", None
        elif response.status_code >= 500:
            return "server error", None
        else:
            try:
                json_response = json.loads(response.content)
                if "none" in json_response:
                    self.available = False
                else:
                    self.available = True
                    self.clone_url = json_response['clone_url']
                    self.stars = json_response['stars']
                    self.pk = json_response['pk']
            except JSONDecodeError:
                return "cannot parse server request"

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
