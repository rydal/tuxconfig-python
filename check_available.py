#!/usr/bin/python3
import os
import sys

from tuxconfig import check_connected, pad_ids, device_details, run_install, write_to_file, already_installed
import subprocess


def get_usb_device(udev_string):
    result = subprocess.check_output(
        ["udevadm", "info", os.path.join("/sys", udev_string)]).decode(
        "utf-8").split("\n")
    device_id = None
    vendor_id = None
    revision = None
    model_vendor = None
    model_name_id = None
    model_name = None

    for line in result:
        line = line[3:len(line)]
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

    if device_id is not None and vendor_id is not None:
        inserted_device = device_details()
        inserted_device.setVendorId(vendor_id)
        inserted_device.setDeviceId(device_id)
        inserted_device.setVendor(model_vendor)
        if model_name_id is not None and model_name is None:
            inserted_device.setName(model_name_id)
        elif model_name is not None and model_name_id is None:
            inserted_device.setName(model_name)
        elif model_name is not None and model_name_id is not None:
            inserted_device.setName(model_name)
        inserted_device.setRevision(revision)

        return inserted_device
    else:
        return None


if __name__ == '__main__':

    if os.geteuid() != 0:
        print("Please run as root / using sudo")
        exit(1)
    print ("Getting available drivers")
    if len(sys.argv) != 1:
        print("Please pass udev path.")
        exit(2)
    device_string = sys.argv[1]
    device = get_usb_device(device_string)
    repository, drivers_available = device.get_repository_details()

    if len(drivers_available) == 1:
        input("Try install with " + device.stars + " github rating?")
    elif len(drivers_available) > 1:
        try_install = input("Select device driver to try, number between 1 and " +  str(len(drivers_available)))  + ":"
    else:
        try_install = 1
    device_to_install = drivers_available[ int(try_install) - 1 ]
    device_to_install.tried= True

    install_result = run_install(device)
    if install_result is True:
        device.success = True
        set_git_commit = subprocess.Popen(["xdg-open", "https://www.tuxconfig.com/user/get_contributor/" + str(device.pk) ],stdout=subprocess.PIPE)
    else:
        device.success = False
        print ("install failed" +  " " + install_result)
    write_to_file(device)
