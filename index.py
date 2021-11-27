import base64
import io
import urllib
from tkinter import ttk, NW, PhotoImage, Canvas, Frame, Label
import urllib.request
import webbrowser
import requests
from PIL import ImageTk, Image
from urllib3.packages.six import BytesIO

def callback(url):
    webbrowser.open_new(url)

class WebImage:
    def __init__(self,url):
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers={'User-Agent':user_agent,}
        req = urllib.request.Request(url, None, headers)
        response = requests.get(url)
        self.image =  Image.open(requests.get(url, stream=True).raw)


    def get(self):
        return self.image

def show_index_page(tabControl):
    tab1 = ttk.Frame()

    title_label = ttk.Label(tab1, text="Tuxconfig - linux device installer", font=("Arial", 20))
    title_label.pack()


    image=WebImage("https://www.rydalinc.org/RydalIncBanner.png").get()
    photo_image = ImageTk.PhotoImage(image.resize((636,172)))
    label = Label(tab1, image=photo_image)
    label.image = photo_image
    label.pack()


    link1 = Label(tab1, text="About Tuxconfig", fg="blue", cursor="hand2", font=("Arial", 20))
    link1.pack()
    link1.bind("<Button-1>", lambda e: callback("https://www.tuxconfig.com/about"))
    link1 = Label(tab1, text="Developer site for contributing repositories", fg="blue", cursor="hand2", font=("Arial", 20))
    link1.pack()
    link1.bind("<Button-1>", lambda e: callback("https://www.tuxconfig.com/developer"))
    title_label = ttk.Label(tab1, text="Install devices easily using this front end, covers usb and pci devices on x86, i386 and raspberry pi devices", font=("Arial", 16))
    title_label.pack()



    return tab1
