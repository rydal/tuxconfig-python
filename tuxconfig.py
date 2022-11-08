#!/usr/bin/python3
import datetime
import fnmatch
import json
import os
from os.path import join

from cpuinfo import get_cpu_info
import random
import string
import subprocess
import sys
import urllib
import webbrowser
from json import JSONDecodeError
from pathlib import Path

import requests
import socket

from gi.repository import GObject
from shlex import quote as shlex_quote

install_success = False
install_failed = False


class InstallUpdates:
    result = ""
    completed = 0


def find_device_ids(type):
    devices = {}
    for file in os.listdir("/sys/bus/" + type + "/devices/"):

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
                if len(pci_id_array) == 2:
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
    if get_cpu_info()['arch'] == "i386":
        return "i386"
    elif get_cpu_info()['arch'] == "X86_64":
        return "x86_64"
    else:
        with open('/proc/cpuinfo') as f:
            line = f.read()
            if 'Hardware' in line:
                hardware_id = line.split(":")[1]
                hardware_id.strip(" ")
        return hardware_id

import threading

class device_details:

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
        self.already_installed = False
        self.installed_status = 0
        self.install_directory = None
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

    def setCloneUrl(self, clone_url):
        self.subsystem = clone_url

    def setCommit(self, commit):
        self.commit = commit

    def get_repository_details(self):
        response = requests.get(
            'https://www.tuxconfig.com/user/get_device/' + self.vendor_id + ":" + self.device_id + "/" + get_platform())
        if response.status_code >= 400 and response.status_code < 404:
            print("connection error")
            return False
        elif response.status_code >= 500:
            print("server error")
            return False
        else:
            try:
                string = response.content.decode('utf-8')
                json_response = json.loads(string)

                if "none" in json_response:
                    self.available = False
                else:

                    current_repository = json_response[0]
                    drivers_available = 0
                    for repository in current_repository:
                        if repository['stars'] > current_repository['stars']:
                            current_repository = repository

                        self.available = True
                        self.clone_url = current_repository['clone_url']
                        self.commit = current_repository['commit']
                        self.stars = current_repository['stars']
                        self.pk = current_repository['pk']
                        drivers_available += 1
                        self.already_installed = self.already_installed(self)
                        if device.tried:
                            print("Trying next favoured install for " + self.device_vendor + " " + self.device_name)
                    return current_repository, drivers_available
            except JSONDecodeError:
                print("cannot parse server request")
                return False

    def write_to_file(self):
        f = open("/var/lib/tuxconfig.log", "w+")

        now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        json_string = json.dumps({"vendor_id": self.vendor_id, "device_id": self.device_id, "revision": self.revision,
                                  "vendor_name": self.device_vendor, "device_name": self.device_name,
                                  "driver": self.driver, "clone_url": self.clone_url, "stars": self.stars,
                                  "commit": self.commit,
                                  "pk": self.pk, "tried": self.tried, "success": self.success, "time": now})
        f.write(json_string)
        f.close()

    def already_installed(self):
        tuxconfig_file = Path('/var/lib/tuxconfig.log')
        if tuxconfig_file.is_file():
            with open('/var/lib/tuxconfig.log') as file:
                for line in file:
                    checking_device = json.loads(line)
                    if checking_device['clone_url'] == self.clone_url and checking_device['commit'] == self.commit:
                        if checking_device['tried'] is True:
                            self.tried = True
                        if checking_device['success'] is True:
                            self.success = True
                        else:
                            print("Install marked as unsuccessful")

    def uninstall_module(self):
        append_to_logfile(get_module_install_status(3),self.install_directory,self.driver)
        self.installed_status = 3
        uninstall = subprocess.Popen(["dmks", "remove", self.driver + "--all"], cwd='/tmp/' + self.install_directory,
                                     stdout=subprocess.PIPE)
        streamdata = uninstall.communicate()[0]
        append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)

    def install_device(self):
        self.install_directory = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        clone_git = subprocess.Popen(["git", "clone", device.clone_url, "/tmp/" + self.install_directory], stdout=subprocess.PIPE)
        streamdata = clone_git.communicate()[0]

        self.installed_status = 1

        if clone_git.returncode > 0:
            append_to_logfile(get_module_install_status(1),self.install_directory,self.driver)
            append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)
            self.installed_status = -1
            return False

        self.installed_status = 2
        append_to_logfile(get_module_install_status(2),self.install_directory,self.driver)
        set_git_commit = subprocess.Popen(["git", "reset", "--hard", device.commit], cwd='/tmp/' + self.install_directory,
                                          stdout=subprocess.PIPE)
        streamdata = set_git_commit.communicate()[0]
        if set_git_commit.returncode > 0:
            append_to_logfile("Error setting Git branch\n",self.install_directory,self.driver)
            self.installed_status = -2
            return False
        append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)
        if not os.path.exists("/tmp/" +self.install_directory + "/tuxconfig.conf"):
            append_to_logfile("Tuxconfig file not in directory\n",self.install_directory,self.driver)
            self.installed_status = -2
            return False
        install_command = None
        test_command = None
        module_name = None

        with open("/tmp/" + self.install_directory + "/tuxconfig.conf", encoding="UTF-8") as tuxconfig_file:
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
                if "module_id" in line:
                    line.split("=")
                    module_name = line.split("=")[1].strip("\"")
        installed = get_device_installed_list(module_name)
        if installed is True:
            self.uninstall_module()

        append_to_logfile(get_module_install_status(4),self.install_directory,self.driver)
        self.installed_status = 4
        if install_command.startswith("./"):
            install_command = install_command[2:len(install_command)]

        install_module = subprocess.Popen(["/tmp/" + self.install_directory + "/" + install_command], stdout=subprocess.PIPE,
                                          cwd="/tmp/" + self.install_directory)
        streamdata = install_module.communicate()[0]
        if install_module.returncode > 0:
            append_to_logfile(get_module_install_status(-3),self.install_directory,self.driver)
            append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)
            return False

        append_to_logfile(get_module_install_status(5),self.install_directory,self.driver)
        self.installed_status = 5
        test_module = subprocess.Popen(["bash", test_command], stdout=subprocess.PIPE,
                                       cwd="/tmp/" + self.install_directory)
        streamdata = test_module.communicate()[0]

        if test_module.returncode > 0:
            append_to_logfile("Error testing new module install\n",self.install_directory,self.driver)
            append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)
            self.installed_status = -4
            return False
        append_to_logfile(str(streamdata, "utf-8") + "\n",self.install_directory,self.driver)
        append_to_logfile(get_module_install_status(6),self.install_directory,self.driver)
        return True


    def getString(self):
        return self.vendor_id + ":" + self.device_id + " " + self.device_vendor + " " + self.device_name + "\n"

    def getDeviceId(self):
        return self.vendor_id + ":" + self.device_id

    def getAvailable(self):
        return self.available

    def getCommit(self):
        return self.commit

    def getCloneUrl(self):
        return self.clone_url

    def toJson(self):
        return json.dumps({"vendor_id" : self.vendor_id,"device_id" : self.device_id, "revision" : self.revision, "device_name" : self.device_name, "device_vendor" : self.device_vendor, "driver" : self.driver,
                    "subsystem" : self.subsystem, "clone_url" : self.clone_url, "commit" : self.commit, "stars" : self.stars, "pk" : self.pk, "tried" : self.tried, "success" : self.success, "available" : self.available,
                    "already_installed" : self.already_installed, "installed_status" : self.installed_status, "install_directory" : self.install_directory })



def append_to_logfile(message,directory,module_name):
    with open(join(directory,"_",module_name,".log"), "a") as logfile:
        logfile.write(message)

def poll_update_status(device):
    if device.installed_status > 0:
        print (get_module_install_status(device.installed_status))


class DaemonStoppableThread(threading.Thread):

    def __init__(self,installable_device):
        super(DaemonStoppableThread, self).__init__()
        self.setDaemon(True)
        self.stop_event = threading.Event()
        self.sleep_time = 1000
        self.device = installable_device
        self.target = poll_update_status(self.device)
def get_module_install_status(install_status):
    if install_status == 0:
        return "Waiting to install"
    elif install_status == 1:
        return "Cloning repository"
    elif install_status == 2:
        return "Resetting git head"
    elif install_status == 3:
        return "Uninstalling current module"
    elif install_status == 4:
        return "Installing new module"
    elif install_status == 5:
        return "Running tests on installing module"
    elif install_status == -1:
        return "Error cloning repository"
    elif install_status == -2:
        return "Error removing previous installing module"
    elif install_status == -3:
        return "Error installing module"
    elif install_status == -4:
        return "Error running tests on installing module"

def get_root():
    got_root = 00000000
    if os.geteuid() != 0:
        print("Please run as using sudo")
        text = input("Enter user password")  # Python 3
        sudo_password = 'echo %s|sudo su'.format(text)
        got_root = os.system(shlex_quote(sudo_password))
    if got_root != 00000000:
        print("That failed, trying su with your root password")
        text = input("Enter root password")  # Python 3
        sudo_password = 'echo %s su'.format(text)
        got_root = os.system(shlex_quote(sudo_password))
    if got_root != 00000000:
        print("You need to be super user to install modules, exiting now.")
        exit(1)






def get_device_installed_list(module_name):
    get_packages = subprocess.Popen(["dkms status | cut -d\",\" -f 1,2"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
    output = get_packages.communicate()[0].decode("utf-8")
    for package in output.split("\n"):
        package.strip(": added")
        package_details = package.strip().split(",")
        if package_details[0] == module_name:
            return package_details[0] + "/" + package_details[1].strip()
    return False





def check_connected():
    IPaddress = socket.gethostbyname(socket.gethostname())
    if IPaddress == "127.0.0.1":
        print("Internet not connected.")
        return False
    else:
        return True





if __name__ == '__main__':


    print("Getting available drivers")
    devices = []
    pci_devices = find_device_ids("pci")
    devices.append(pci_devices)
    usb_devices = find_device_ids("usb")
    devices.append(usb_devices)
    index = 0
    device_map = []

    empty_list = True
    for device in devices:
        for a in device.values():
            error = a.get_repository_details()
            if a.available:
                empty_list = False
                device_map.append(a)
                index += 1
                print(str(index) + ") " + a.getString() + " installable from www.tuxconfig.com")
    if empty_list is True:
        print("No more drivers available for this device")
        exit(2)

    install_number = input("Select device from list: ")  # Python 3
    install_number_int = 1
    try:
        install_number_int = int(install_number)
    except:
        print("Not a valid choice number")
    install_result = False
    device_to_install = None
    if install_number_int > len(device_map):
        print("Not a valid choice number")
        exit(5)
    else:

        for device in device_map:
            print("Try install with " + device.stars + " github rating?")
        if len(device_map) > 1:
            try_install = input("Select device driver to try, number between 1 and " + str(len(device_map))) + ":"
        else:
            try_install = 1
        device_to_install = device_map[int(try_install) - 1]
        device_to_install.tried = True
        install_result = device_to_install.install_device()
        t = DaemonStoppableThread(device_to_install)
        t.start()
        if install_result is True:
            device_to_install.success = True
            set_git_commit = subprocess.Popen(
                ["xdg-open", "https://www.tuxconfig.com/user/get_contributor/" + str(device_to_install.pk)],
                stdout=subprocess.PIPE)
        else:
            device_to_install.success = False

            print("install failed")
        device_to_install.write_to_file()
