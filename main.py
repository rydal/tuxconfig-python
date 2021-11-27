import tkinter as Tk
########################################################################
from tkinter import ttk

from index import show_index_page
from scan_devices import show_devices_page




def on_closing():
    print('closing')
    root.destroy()

if __name__ == "__main__":
    root = Tk.Tk()
    root.title("Tuxconfig")


    root.protocol('WM_DELETE_WINDOW', on_closing)
    tabControl = ttk.Notebook(root)
    index_tab = show_index_page(tabControl)
    tabControl.add(index_tab, text ='index page')

    devices_tab = show_devices_page(tabControl)
    tabControl.add(devices_tab, text ='Install devices')

# Apparently a common hack to get the window size. Temporarily hide the
    # window to avoid update_idletasks() drawing the window in the wrong
    # position.


    tabControl.grid()


    root.mainloop()