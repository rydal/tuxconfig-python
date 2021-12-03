import json
import os
import platform
import random
import string
import subprocess
import urllib
import webbrowser
from json import JSONDecodeError



from urllib import request



def run_install(device):

    directory = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    clone_git = subprocess.Popen(["git", "clone", device.clone_url, "/tmp/" + directory], stdout=subprocess.PIPE)
    streamdata = clone_git.communicate()[0]
    if clone_git.returncode > 0:
        print( "Error cloning git repo")
        return


    set_git_commit = subprocess.Popen(["git", "reset", "--hard", device.commit], cwd='/tmp/' + directory,
                                      stdout=subprocess.PIPE)
    streamdata = set_git_commit.communicate()[0]
    if set_git_commit.returncode > 0:
        print( "Error setting Git branch")

    if not os.path.exists("/tmp/" + directory + "/tuxconfig.conf"):
        print( "Tuxconfig file not in directory")
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

    if install_module.returncode > 0:
        print( "Error installing module")
        return

    test_module = subprocess.Popen(["bash",test_command], stdout=subprocess.PIPE,
                                   cwd="/tmp/" + directory)
    streamdata = test_module.communicate()[0]
    if install_module.returncode > 0:
        print( "Error testing module")
        return

    return "Module installed!"


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

    def get_repository_details(self ):
        current_repository = None
        response = request.get(
            'https://www.tuxconfig.com/user/get_device/' + self.vendor_id + ":" + self.device_id + "/" + get_platform())
        if response.status_code >= 400 and response.status_code < 400:
            return "connection error"
        elif response.status_code >= 500:
            return  "server error"
        else:
            try:
                string = response.content.decode('utf-8')
                json_response = json.loads(string)

                if "none" in json_response:
                    self.available = False
                else:
                    if len(json_response) == 0:
                        print(
                            'https://www.tuxconfig.com/user/get_device/' + self.vendor_id + ":" + self.device_id + "/" + get_platform())
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
    def getString(self):
            return self.device_vendor + " " + self.device_name



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


        return self.vendor_id + ":" + self.device_id + " " +  self.device_vendor + " "+ self.device_name + self.installed

    def getAvailable(self):
        return self.available

    def getHardwareID(self):
        return self.vendor_id + ":" + self.device_id + self.device_vendor + self.device_name

def write_to_file(item_to_add):

    f = open("/var/lib/tuxconfig_conf", "w")
    json_string = json.dumps({"vendor_id": item_to_add.vendor_id, "device_id": item_to_add.device_id, "revision": item_to_add.revision,
                              "vendor_name": item_to_add.device_vendor, "device_name": item_to_add.device_name,
                              "driver": item_to_add.driver, "clone_url": item_to_add.clone_url, "stars": item_to_add.stars,
                              "pk": item_to_add.pk, "tried": item_to_add.tried, "success": item_to_add.success})
    f.write(json_string)
    f.close()

def parse_tuxconfig_file():
    devices_list = []
    with open("/var/lib/tuxconfig_conf","wr") as file:
        for line in file:
            devices_list.append(json.loads(line))
    file.close()
    return devices_list

def remove_line(self,item_to_remove):
    device_list = self.parse_tuxconfig_file()
    for i in device_list:
        if i is item_to_remove:
            device_list.remove(i)
    f = open("/var/lib/tuxconfig_conf", "w")
    for i in device_list:
        f.write(json.dumps(i))
    f.close()








if __name__ == '__main__':
    devices = []
    pci_devices = find_device_ids("pci")
    devices.append(pci_devices)
    usb_devices = find_device_ids("usb")
    devices.append(usb_devices)
    index = 0
    device_map = []
    for device in devices:
        for a in device.values():
            a.get_repository_details()
            if a.available:
                device_map.append( a)
                index += 1
                print(str(index) + ") " + a.getString() + "installable from Tuxconfig.com")

    install_number = input("Install device from list: ")   # Python 3
    install_number_int = 1
    try:
        install_number_int = int(install_number)
    except:
        print("Not a valid choice number")
    install_result = False
    device_to_install = None
    if int(install_number) > len(device_map):
        print("Not a valid choice number")
    else:
        device_to_install = device_map[install_number_int -1 ]
        install_result = run_install(device_to_install)
    if install_result is True:
        device_to_install.success = True
        device_to_install.tried = True
        print("https://www.tuxconfig.com/user/get_contiributor/" + device_to_install.pk )
    else:
        device_to_install.success = True
        device_to_install.tried = False
        print ("install failed")

    f = open("/var/lib/tuxconfig_conf", "w")





