import tkinter as tk
from tkinter import ttk
from main import WindowsBackend, findbase, primaryscan, nextscan
import os

found = []
scansize = 2
buttonstate = "!disabled"

root = tk.Tk()
root.title("CemuTap")
root.geometry("800x400")

icon = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "GABEWARE.png"))
root.iconphoto(False,icon)

valuelabel = ttk.Label(root,text="Value:")
valuelabel.grid(row=0, column=0, padx=8, pady=8)

valuebox = ttk.Entry(root)
valuebox.grid(row=0, column=1, padx=8, pady=8)

size = ttk.Combobox(root, values=["1","2","4"], state="readonly", width=5)
size.grid(row=1, column=1, padx=8, pady=8)
size.set("2")

def showmatches():
    results.delete(0, "end")
    for addr in found[:500]:
        results.insert("end", hex(addr))

def scana():
    global found, scansize
    if backend is None:
        scanstatus.config(text="Not attached to Cemu.")
        return 
    try:
        value = int(valuebox.get())
        bytesize = int(size.get())
    except ValueError:
        scanstatus.config(text="Value must be a whole number and include only numbers.")
        return  
    togglebuttons("disabled")
    try:
        found = primaryscan(backend, base, value, bytesize, progress=totalprogress)
        scansize=bytesize
        scanstatus.config(text=f"{len(found)} Address Matches Found")
        showmatches() 
    finally:
        togglebuttons("!disabled")
    

def totalprogress(scanned):
    scanstatus.config(text=f"Scanned {scanned // 0x100000} of 1024 MB")
    root.update()

def progress2(checked,total):
    scanstatus.config(text=f"Scanned {checked} of {total} Addresses")
    root.update()

primaryscanbutton = ttk.Button(root, text="New Scan", command=scana)
primaryscanbutton.grid(row=2,column=0,padx=8,pady=8)

def scanb():
    global found
    if backend is not None:
        if found:
            togglebuttons("disabled")
            try:
                value = int(valuebox.get())
                found = nextscan(backend,base,found,value,scansize, progress=progress2)
                scanstatus.config(text=f"{len(found)} Address Matches Found")
                showmatches()
            except ValueError:
                scanstatus.config(text="Value must be a whole number and include only numbers.")
                return
            finally:
                togglebuttons("!disabled")   
        else:
            scanstatus.config(text=f"First Scan Not Found")
            return
    else:
        scanstatus.config(text="Not attached to Cemu.")


bytesizelabel = ttk.Label(root, text="Byte Size To Query: ")
bytesizelabel.grid(row=1, column=0, padx=8, pady=8)

nextscanbutton = ttk.Button(root, text="Next Scan", command=scanb)
nextscanbutton.grid(row=3,column=0,padx=8,pady=8)

results = tk.Listbox(root, width=40, height=12)
results.grid(row=0,column=2,rowspan=5,padx=8,pady=8)

scanstatus = ttk.Label(root, text="Ready")
scanstatus.grid(row=4,column=0,columnspan=2,padx=8,pady=8)

def togglebuttons(override):
    global buttonstate
    if buttonstate == "!disabled":
        buttonstate = "disabled"
    elif buttonstate == "disabled":
        buttonstate = "!disabled"
    if override is not None:
        buttonstate = override
    primaryscanbutton.state([buttonstate])
    nextscanbutton.state([buttonstate])

try:
    backend = WindowsBackend()
    base = findbase()
    scanstatus.config(text=f"Attached to Cemu: {hex(base)}")
except Exception as e:
    backend = None
    scanstatus.config(text=f"!!! Cemu Attach Failed: {e}")

root.mainloop()