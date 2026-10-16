import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from main import WindowsBackend, findbase, primaryscan, nextscan, export, importscan, readunit, backendcreate
import os
from datetime import datetime

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
        try:
            val=readunit(backend,base,addr,scansize)
        except Exception:
            val = "?"
        results.insert("end", f"{hex(addr)} ({val})")

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
    if not 0<=value<256**bytesize:
        scanstatus.config(text=f"Value must be between 0 and {256 ** bytesize -1}.")
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
                if not 0<=value<256**scansize:
                    scanstatus.config(text=f"Value must be between 0 and {256 ** scansize -1}.")
                    return
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

def cleartableevent():
    global found
    if found == []:
        return
    found = []
    showmatches()
    scanstatus.config(text=f"Address Table Cleared.")

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

def exportbuttonevent():
    if not found:
        scanstatus.config(text=f"No addresses found to export.")
        return
    now=datetime.now()
    path = filedialog.asksaveasfilename(defaultextension=".ctms", initialfile=f"scan-{now.strftime('%m-%d-%Y-%H-%M')}", filetypes=[("CemuTap Scan", "*.ctms")])
    if not path:
        scanstatus.config(text=f"Save Canceled.")
        return
    export(path, found, scansize)
    scanstatus.config(text=f"Scan Exported.")

def importbuttonevent():
    global found, scansize
    try:
        path=filedialog.askopenfilename(filetypes=[("CemuTap Scan", "*.ctms")])
        if path=="":
            scanstatus.config(text=f"Import Canceled.")
            return
        found, scansize = importscan(path)
        size.set(str(scansize))
        scanstatus.config(text=f"Successfully imported CemuTap Scan file.")
        showmatches()
    except Exception:
        scanstatus.config(text="!!! Could not read import. Are you sure this is a CemuTap Scan File?")


exportbutton = ttk.Button(root,text="Export Scan", command=exportbuttonevent)
exportbutton.grid(row=5,column=0,padx=8,pady=8)
importbutton = ttk.Button(root,text="Import Scan", command=importbuttonevent)
importbutton.grid(row=5,column=1,padx=8,pady=8)
resettable = ttk.Button(root, text="Clear Address Table", command=cleartableevent)
resettable.grid(row=5,column=2,padx=8,pady=8)

def refloop():
    if 0<len(found)<=12:
        showmatches()
    root.after(1000,refloop)


try:
    backend = backendcreate()
    base = findbase()
    scanstatus.config(text=f"Attached to Cemu: {hex(base)}")
except Exception as e:
    backend = None
    scanstatus.config(text=f"!!! Cemu Attach Failed: {e}")

refloop()
root.mainloop()