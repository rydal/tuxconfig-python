#!/usr/bin/python3
import datetime
import json
import os
import platform
import random
import string
import subprocess
import sys
import urllib
import webbrowser
from json import JSONDecodeError
from pathlib import Path

import requests

class InstallUpdates:
    result = ""

def run_install(button,device):

    directory = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    print ("cloning repository")
    InstallUpdates.result += "cloning repository\n"
    clone_git = subprocess.Popen(["git", "clone", device.clone_url, "/tmp/" + directory], stdout=subprocess.PIPE)
    streamdata = clone_git.communicate()[0]
    if clone_git.returncode > 0:
        return  "Error cloning git repo"


    print ("Reseting git head")
    InstallUpdates.result += "Reseting git head\n"
    set_git_commit = subprocess.Popen(["git", "reset", "--hard", device.commit], cwd='/tmp/' + directory,
                                      stdout=subprocess.PIPE)
    streamdata = set_git_commit.communicate()[0]
    InstallUpdates.result += streamdata
    if set_git_commit.returncode > 0:
        return  "Error setting Git branch"


    if not os.path.exists("/tmp/" + directory + "/tuxconfig.conf"):
        return "Tuxconfig file not in directory"


    install_command = None
    test_command = None
    module_name = None

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
            if "module_id" in line:
                line.split("=")
                module_name = line.split("=")[1].strip("\"")
    installed = get_device_installed_list(module_name)
    if installed is True:
        print ("Uninstalling current module")
        InstallUpdates.result += "Uninstalling current module\n"
        uninstall = subprocess.Popen(["dmks", "remove", installed + "--all"], cwd='/tmp/' + directory,
                                          stdout=subprocess.PIPE)
        streamdata = uninstall.communicate()[0]
        InstallUpdates.result += streamdata
        sys.exit(5)
    print ("installing module, takes some time.")
    if install_command.startswith("./"):
        install_command = install_command[2:len(install_command)]
    
    install_module = subprocess.Popen(["sudo", "/tmp/" + directory + "/" + install_command], stdout=subprocess.PIPE,
                                      cwd="/tmp/" + directory)

    streamdata = install_module.communicate()[0]

    if install_module.returncode > 0:
        return "Error installing module"


    test_module = subprocess.Popen(["bash",test_command], stdout=subprocess.PIPE,
                                   cwd="/tmp/" + directory)
    streamdata = test_module.communicate()[0]
    InstallUpdates.result += streamdata
    if install_module.returncode > 0:
        return "Error testing module"

    print("Module installed!")
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

    def setCloneUrl(self, clone_url):
        self.subsystem = clone_url

    def setCommit(self, commit):
        self.commit = commit

    def get_repository_details(self ):
        response = requests.get(
            'https://www.tuxconfig.com/user/get_device/' + self.vendor_id + ":" + self.device_id + "/" + get_platform())
        if response.status_code >= 400 and response.status_code < 400:
            print ("connection error")
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

                    for repository in json_response:
                        if repository['stars'] > current_repository['stars']:
                            current_repository = repository
                        if already_installed(current_repository['clone_url'],current_repository['commit']):
                            print("Trying next favoured install for " + self.device_vendor + " " + self.device_name)

                        self.available = True
                        self.clone_url = current_repository['clone_url']
                        self.commit = current_repository['commit']
                        self.stars = current_repository['stars']
                        self.pk = current_repository['pk']
                    return current_repository
            except JSONDecodeError:
                print("cannot parse server request")
                return False

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
        return self.vendor_id + ":" + self.device_id + " " +  self.device_vendor + " " + self.device_name + "\n"

    def getAvailable(self):
        return self.available

    def getCommit(self):
        return self.commit

    def getCloneUrl(self):
        return self.clone_url


def write_to_file(device):
    f = open("/var/lib/tuxconfig.log", "w+")

    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    json_string = json.dumps({"vendor_id": device.vendor_id, "device_id": device.device_id, "revision": device.revision,
                              "vendor_name": device.device_vendor, "device_name": device.device_name,
                              "driver": device.driver, "clone_url": device.clone_url, "stars": device.stars,"commit" : device.commit,
                              "pk": device.pk, "tried": device.tried, "success": device.success, "time" : now})

    f.write(json_string)
    f.close()


def get_device_installed_list(module_name):

    get_packages = subprocess.Popen(["dkms status | cut -d\",\" -f 1,2"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = get_packages.communicate()[0].decode("utf-8")
    for package in output.split("\n"):
        package.strip(": added")
        package_details = package.strip().split(",")
        if package_details[0] == module_name:

            return package_details[0] + "/" + package_details[1].strip()
    return False

def already_installed(clone_url,commit):
    tuxconfig_file  = Path('/var/lib/tuxconfig.log')
    if tuxconfig_file.is_file():
        with open('/var/lib/tuxconfig.log') as file:
            for line in file:
                checking_device = json.loads(line)
                if checking_device['clone_url'] == clone_url and checking_device['commit'] == commit:
                    if checking_device['tried'] is True:
                        print("Install attempted and failed")
                    else:
                        print("Install not attempted")
                    if checking_device['success'] is True:
                        print("Install marked as successful")
                    else:
                        print("Install marked as unsuccessful")
                    if checking_device['tried'] is True and  checking_device['success'] is True:
                        return True

    return False




if __name__ == '__main__':

    if os.geteuid() != 0:
        print("Please run as root / using sudo")
        exit(1)
    print ("Getting available drivers")
    devices = []
    pci_devices = find_device_ids("pci")
    devices.append(pci_devices)
    usb_devices = find_device_ids("usb")
    devices.append(usb_devices)
    index = 0
    device_map = []

    empty_list = False
    for device in devices:
        for a in device.values():
            error = a.get_repository_details()
            if a.available:
                empty_list = True
                device_map.append( a)
                index += 1
                print(str(index) + ") " + a.getString() + "\ninstallable from www.tuxconfig.com")
    if empty_list is False:
        print("No more drivers available for this device")
        exit(2)

    install_number = input("Select device from list: ")   # Python 3
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
            try_install = input("Select device driver to try, number between 1 and " +  str(len(device_map)))  + ":"
        else:
            try_install = 1
        device_to_install = device_map[ int(try_install) - 1 ]
        device_to_install.tried= True
        install_result = run_install(None,device_to_install)
        if install_result is True:
            device_to_install.success = True
            set_git_commit = subprocess.Popen(["xdg-open", "https://www.tuxconfig.com/user/get_contributor/" + str(device_to_install.pk) ],stdout=subprocess.PIPE)
        else:
            device_to_install.success = False

            print ("install failed" +  " " + install_result)
            write_to_file(device_to_install)




