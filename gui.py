import tkinter as tk
import sv_ttk
import json
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from main import WindowsBackend, findbase, primaryscan, nextscan, export, importscan, readunit, backendcreate, loadcts, savesettings, PluginAPI, pluginslistbuild,executeplugin, plugininstall
settings = loadcts()
import os
from datetime import datetime

found = []
pinnedtabs = {}
scansize = 2
buttonstate = "!disabled"

root = tk.Tk()
root.title("CemuTap")
root.geometry("800x400")
sv_ttk.set_theme(settings["theme"])

toptab=ttk.Notebook(root)
toptab.pack(fill="both",expand=True)

scantab=ttk.Frame(toptab)
toptab.add(scantab,text="Scan")

pluginstab=ttk.Frame(toptab)
toptab.add(pluginstab,text="Plugins")

settingstab=ttk.Frame(toptab)
toptab.add(settingstab,text="Settings")

icon = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "GABEWARE.png"))
root.iconphoto(False,icon)

valuelabel = ttk.Label(scantab,text="Value:")
valuelabel.grid(row=0, column=0, padx=8, pady=8)

valuebox = ttk.Entry(scantab)
valuebox.grid(row=0, column=1, padx=8, pady=8)

size = ttk.Combobox(scantab, values=["1","2","4"], state="readonly", width=5)
size.grid(row=1, column=1, padx=8, pady=8)
size.set("2")

pluginlist=tk.Listbox(pluginstab,width=25,borderwidth=0,highlightthickness=1)
pluginlist.grid(row=0,sticky="ns",column=0,pady=8,padx=8)

pluginpanel=ttk.Frame(pluginstab)
pluginpanel.grid(row=0,sticky="nsew",column=1,pady=8,padx=8)

pluginstab.rowconfigure(0,weight=1)
pluginstab.columnconfigure(1,weight=1)


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
        for cb in api.scancallbacks:
            try:
                cb(found)
            except Exception as exc:
                print(f"A plugin's scan callback failed for reason: {exc}")
    finally:
        togglebuttons("!disabled")

    

def totalprogress(scanned):
    scanstatus.config(text=f"Scanned {scanned // 0x100000} of 1024 MB")
    root.update()

def progress2(checked,total):
    scanstatus.config(text=f"Scanned {checked} of {total} Addresses")
    root.update()

primaryscanbutton = ttk.Button(scantab, text="New Scan", command=scana)
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
                for cb in api.scancallbacks:
                    try:
                        cb(found)
                    except Exception as exc:
                        print(f"A plugin's scan callback failed for reason: {exc}")
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

bytesizelabel = ttk.Label(scantab, text="Byte Size To Query: ")
bytesizelabel.grid(row=1, column=0, padx=8, pady=8)

nextscanbutton = ttk.Button(scantab, text="Next Scan", command=scanb)
nextscanbutton.grid(row=3,column=0,padx=8,pady=8)

results = tk.Listbox(scantab, width=40, height=12, bg="#2c2c2c",fg="#ffffff",borderwidth=0,highlightthickness=1,highlightbackground="#3a3a3a")
results.grid(row=0,column=2,rowspan=5,padx=8,pady=8)

def addrtablecolors():
    if sv_ttk.get_theme()=="dark":
        results.config(bg="#2c2c2c",fg="#ffffff",highlightbackground="#3a3a3a")
        pluginlist.config(bg="#2c2c2c",fg="#ffffff",highlightbackground="#3a3a3a")
    else:
        results.config(bg="#ffffff",fg="#000000", highlightbackground="#cccccc")
        pluginlist.config(bg="#ffffff",fg="#000000", highlightbackground="#cccccc")
addrtablecolors()
def theme():
    sv_ttk.toggle_theme()
    addrtablecolors()
    settings["theme"] = sv_ttk.get_theme()
    savesettings(settings)

themebutton = ttk.Button(settingstab, text="Toggle Light/Dark Theme",command=theme)
themebutton.grid(row=0,column=0,pady=8,padx=8)
scanstatus = ttk.Label(scantab, text="Ready")
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


exportbutton = ttk.Button(scantab,text="Export Scan", command=exportbuttonevent)
exportbutton.grid(row=5,column=0,padx=8,pady=8)
importbutton = ttk.Button(scantab,text="Import Scan", command=importbuttonevent)
importbutton.grid(row=5,column=1,padx=8,pady=8)
resettable = ttk.Button(scantab, text="Clear Address Table", command=cleartableevent)
resettable.grid(row=5,column=2,padx=8,pady=8)

def refloop():
    if 0<len(found)<=12:
        showmatches()
    root.after(1000,refloop)

def pluginselectevent(event):
    selection=pluginlist.curselection()
    if not selection:
        return
    info,mod=loaded[selection[0]]
    for child in pluginpanel.winfo_children():
        child.destroy() #remove any previous panel
    if not hasattr(mod,"buildui"):
        ttk.Label(pluginpanel,text=f"{info['name']} has no readable interface.").pack(padx=8,pady=8)
        return
    try:
        mod.buildui(pluginpanel)
    except Exception as exc:
        ttk.Label(pluginpanel,text=f"{info['name']} UI build failed.").pack(padx=8,pady=8)
pluginlist.bind("<<ListboxSelect>>",pluginselectevent)

def pluginadd():
    path=filedialog.askopenfilename(filetypes=[("CemuTap Plugin", "*.zip")])
    if not path:
        return
    try:
        folder=plugininstall(path)
    except Exception as exc:
        messagebox.showerror("Add Plugin", f"Couldn't install plugin for reason: {exc}")
        return
    if api is None:
        messagebox.showinfo("Add Plugin", "Plugin Installed. It will load on CemuTap's next attachment to Cemu.")
        return
    try:
        with open(os.path.join(folder,"plugin.json")) as file:
            info = json.load(file)
        info["folder"]=folder
        module = executeplugin(info)
        module.setup(api)
    except Exception as exc:
        messagebox.showerror("Add Plugin", f"Plugin installed, although it failed to load for reason: {exc}")
        return
    loaded.append((info,module))
    pluginlist.insert("end",f"{info['name']} v{info['version']} by {info['author']}")

addpluginbutton=ttk.Button(pluginstab,text="Add Plugin", command=pluginadd)
addpluginbutton.grid(row=1,sticky="ew",column=0,pady=8,padx=8)

def pluginid(info):
    return os.path.basename(info["folder"])

def pinplugintab(info,module):
    frame=ttk.Frame(toptab)
    toptab.insert(toptab.index(pluginstab), frame, text=info["name"])
    pinnedtabs[pluginid(info)] = frame

    if hasattr(module,"buildui"):
        try:
            module.buildui(frame)
        except Exception as exc:
            ttk.Label(frame,text=f"UI Build Failed for reason: {exc}").pack(padx=8,pady=8)

def unpin(info):
    frame=pinnedtabs.pop(pluginid(info))
    toptab.forget(frame)
    frame.destroy() 

def onpin():
    selection=pluginlist.curselection()#what is currently has selected on the plugin list
    if not selection:
        messagebox.showinfo("Pin", "Please select a plugin before attempting to pin.")
        return
    info,module =loaded[selection[0]]
    pid=pluginid(info)
    if pid in pinnedtabs:
        unpin(info)
        settings["pinned"].remove(pid)
    else:
        if len(pinnedtabs)>=3:
            messagebox.showwarning("Pin", "You may only have at most 3 pinned plugins. Please unpin a plugin before attempting to pin another.")
            return
        pinplugintab(info,module)
        settings["pinned"].append(pid)
    savesettings(settings)

pinpluginbutton=ttk.Button(pluginstab,text="Pin/Unpin Plugin",command=onpin)
pinpluginbutton.grid(row=2,pady=8,padx=8,sticky="ew",column=0)

try:
    backend = backendcreate()
    base = findbase()
    scanstatus.config(text=f"Attached to Cemu: {hex(base)}")
    api=PluginAPI(backend,base)
    loaded=[]
    for info in pluginslistbuild():
        try:
            module=executeplugin(info)
            module.setup(api)
            loaded.append((info,module))
        except Exception as exc:
            print(f"Plugin {info['name']} failed to load for reason: {exc}")
except Exception as e:
    backend = None
    api=None
    loaded=[]
    scanstatus.config(text=f"!!! Cemu Attach Failed: {e}")

for info,module in loaded:
    pluginlist.insert("end",f"{info['name']} v{info['version']} by {info['author']}")

if api is not None: #remove any plugins from the pinned tabs if they were deleted before cemutap ran again
    loadedids=[pluginid(info) for info, module in loaded]
    settings["pinned"] = [pid for pid in settings["pinned"] if pid in loadedids]
    savesettings(settings)

for info,module in loaded:
    if pluginid(info) in settings["pinned"] and len(pinnedtabs) < 3:
        pinplugintab(info,module)

refloop()
root.mainloop()