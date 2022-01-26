import gi

gi.require_version("Gtk", "3.0")
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk
from gi.repository import WebKit2

def AboutPage():
    page = Gtk.VBox(homogeneous=False, spacing=0)
    page.set_border_width(10)


    webView = WebKit2.WebView()
    webView.load_uri("https://www.tuxconfig.com")
    page.add(webView)
    page.show_all()
    return page

class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Tuxconfig")
        self.set_border_width(3)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)


        self.notebook.append_page(AboutPage(), Gtk.Label(label="Plain Title"))

        self.page2 = Gtk.Box()
        self.page2.set_border_width(10)
        self.page2.add(Gtk.Label(label="A page with an image for a Title."))
        self.notebook.append_page(
            self.page2, Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.MENU)
        )


win = MyWindow()
win.set_default_size(800,600)
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()