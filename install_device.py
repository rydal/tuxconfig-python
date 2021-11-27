import base64
import io
import os
import string
import urllib
from tkinter import ttk, NW, PhotoImage, Canvas, Frame, Label
import urllib.request
import webbrowser
import requests
from PIL import ImageTk, Image



def callback(url):
    webbrowser.open_new(url)


def install_device_page(tabControl,device):
    tab1 = ttk.Frame()

    title_label = ttk.Label(tab1, text="Tuxconfig - linux device installer", font=("Arial", 20))
    title_label.pack()
    print(device)





    return tab1

completed_amount = 0

import subprocess
import platform
def clone_repo(device):
    global  completed_amount
    import random
    directory = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    clone_git = subprocess.Popen(["git","clone",device.clone_url, "/tmp"  + directory ], stdout=subprocess.PIPE)
    if clone_git.returncode > 0:
        return "Error cloning git repo"
    completed_amount += 1
    if not os.path.exists("/tmp/" + directory + "/tuxconfig.conf"):
        return "Tuxconfig file not in directory"
    packages_to_install = None
    install_command = None
    if platform.linux_distribution()[0] == "Ubuntu":
        with open("/tmp/" + directory + "/tuxconfig.conf") as tuxconfig_file:
            for line in tuxconfig_file:
                # For each line, check if line contains the string
                if "ubuntu_repositories" in line:
                    line.split("=")
                    packages_to_install = line[1].strip("\"")
                if "install_command" in line:
                    line.split("=")
                    install_command = line[1].strip("\"")


    if packages_to_install is None:
        return "cannot find list of packages to install"
    completed_amount += 1
    install_packages = subprocess.Popen(["sudo apt get","install",packages_to_install], stdout=subprocess.PIPE)
    if install_packages.returncode > 0:
        return "Error installing packages"
    completed_amount += 1
    install_module = subprocess.Popen(["bash", directory + "/" + install_command], stdout=subprocess.PIPE)
    if install_module.returncode > 0:
        return "Error installing module"
    return True






