import tkinter as tk
import sv_ttk
import json
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from main import WindowsBackend, findbase, primaryscan, nextscan, export, importscan, readunit, backendcreate, loadcts, savesettings, PluginAPI, pluginslistbuild,executeplugin, plugininstall, writeu,readvalue, writevalue, snapshot, snapshotscan, findtitleid
settings = loadcts()
import os
from datetime import datetime
# i pray for the sanity of whoever is auditing this scrambled mess... (psst, you'll need ctrl+F a LOT.)
found = []
previous =[]
pinnedtabs = {}
tablerows = {}
backend = None
snapshotpath=None
frozen=None
scanfloat = False
base = 0
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

liveedittab=ttk.Frame(toptab)
toptab.add(liveedittab, text="Live Address Editor")

tabletab=ttk.Frame(toptab)
toptab.add(tabletab,text="Address Table")

pluginstab=ttk.Frame(toptab)
toptab.add(pluginstab,text="Plugins")

settingstab=ttk.Frame(toptab)
toptab.add(settingstab,text="Settings")

icon = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "CemuTap.png"))
root.iconphoto(False,icon)

valuelabel = ttk.Label(scantab,text="Value:")
valuelabel.grid(row=0, column=0, padx=8, pady=8)

valuebox = ttk.Entry(scantab)
valuebox.grid(row=0, column=1, padx=8, pady=8)

size = ttk.Combobox(scantab, values=["1","2","4", "Float"], state="readonly", width=5)
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
            val=readvalue(backend,base,addr,scansize,scanfloat)
            if scanfloat:
                val=round(val,4)
        except Exception:
            val = "?"
        results.insert("end", f"{hex(addr)} ({val})")

def scana():
    global found, scansize, previous, scanfloat, snapshotpath
    if backend is None:
        scanstatus.config(text="Not attached to Cemu.")
        return 
    if unknownvalue.get():
        sizetext=size.get()
        isfloat=sizetext=="Float"
        togglebuttons("disabled")
        try:
            snapshotpath=snapshot(backend,base,progress=totalprogress)
            found=[]
            previous=[]
            scansize=4 if isfloat else int(sizetext)
            scanfloat=isfloat
            showmatches()
            scanstatus.config(text="Snapshot taken! Change the value in game, then use Next Scan.")
        finally:
            togglebuttons("!disabled")
        return
    sizetext=size.get()
    floattoggle= sizetext=="Float"
    try:
        bytesize=4 if floattoggle else int(sizetext)
        value= float(valuebox.get()) if floattoggle else int(valuebox.get())
    except ValueError:
        scanstatus.config(text=f"Please enter a valid number.")
        return
    if not floattoggle and not 0<=value<256**bytesize:
        scanstatus.config(text=f"Value must be between 0 and {256 ** bytesize -1}.")
        return
    togglebuttons("disabled")
    try:
        found,previous = primaryscan(backend, base, value, bytesize, floattoggle=floattoggle, progress=totalprogress)
        scansize=bytesize
        scanfloat = floattoggle
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

unknownvalue=tk.BooleanVar(value=False)
unknownvaluecheckbox=ttk.Checkbutton(scantab,text="Unknown Initial Value",variable=unknownvalue)
unknownvaluecheckbox.grid(row=2,column=1,padx=8,pady=8)

def scanb():
    global found,previous,snapshotpath
    if backend is not None:
        if found or snapshotpath is not None:
            togglebuttons("disabled")
            try:
                mode=scantype.get().lower()
                if mode=="exact":
                    value=float(valuebox.get()) if scanfloat else int(valuebox.get())
                    if not scanfloat and not 0<=value<256**scansize:
                        scanstatus.config(text=f"Value must be between 0 and {256 ** scansize -1}.")
                        return
                else:
                    value=0
                if snapshotpath is not None:
                    found,previous=snapshotscan(backend,base,snapshotpath,scansize,mode,value,scanfloat,progress=totalprogress)
                    try:
                        os.remove(snapshotpath)
                    except OSError:
                        pass
                    snapshotpath=None
                else:
                    found,previous= nextscan(backend,base,found,previous,value,scansize,mode=mode,floattoggle=scanfloat,progress=progress2)
                scanstatus.config(text=f"{len(found)} Address Matches Found")
                showmatches()
                for cb in api.scancallbacks:
                    try:
                        cb(found)
                    except Exception as exc:
                        print(f"A plugin's scan callback failed for reason: {exc}")
            except ValueError:
                scanstatus.config(text="Please enter a valid number.")
                return
            finally:
                togglebuttons("!disabled")   
        else:
            scanstatus.config(text=f"First Scan Not Found")
            return
    else:
        scanstatus.config(text="Not attached to Cemu.")

def cleartableevent():
    global found,previous,snapshotpath
    if not found and snapshotpath is None:
        return
    found = []
    previous=[]
    if snapshotpath is not None:
        try:
            os.remove(snapshotpath)
        except OSError:
            pass
    snapshotpath = None
    showmatches()
    scanstatus.config(text=f"Address Table Cleared.")

bytesizelabel = ttk.Label(scantab, text="Byte Size To Query: ")
bytesizelabel.grid(row=1, column=0, padx=8, pady=8)

nextscanbutton = ttk.Button(scantab, text="Next Scan", command=scanb)
nextscanbutton.grid(row=3,column=0,padx=8,pady=8)

scantype=ttk.Combobox(scantab, values=["Exact", "Increased","Decreased","Changed","Unchanged"], state="readonly")
scantype.grid(row=3,column=1,padx=8,pady=8)
scantype.set("Exact")

results = tk.Listbox(scantab, width=40, height=12, bg="#2c2c2c",fg="#ffffff",borderwidth=0,highlightthickness=1,highlightbackground="#3a3a3a")
results.grid(row=0,column=2,rowspan=5,padx=8,pady=8)

table = ttk.Treeview(tabletab,columns=("name","address","type","value","title"),show="headings")
table.heading("name", text="Name")
table.heading("address",text="Address")
table.heading("type",text="Type")
table.heading("value",text="Value")
table.heading("title",text="Title")

table.column("name",width=120)
table.column("address",width=110)
table.column("type",width=60)
table.column("value",width=90)
table.column("title",width=140)

table.grid(row=0,column=0,padx=8,pady=8,sticky="nsew")
tabletab.rowconfigure(0, weight=1)
tabletab.columnconfigure(0, weight=1)

tablebuttons = ttk.Frame(tabletab)
tablebuttons.grid(row=1,column=0,padx=8,pady=8,sticky="w")

table.tag_configure("frozen",foreground="#78b6f5")

def removetablevalue():
    for iid in table.selection():
        table.delete(iid)
        tablerows.pop(iid,None)
ttk.Button(tablebuttons,text="Remove Row",command=removetablevalue).pack(side="left",padx=(0,8))

def addtotable():
    selection=results.curselection()
    if not selection:
        scanstatus.config(text="Please select a result to add to the address table.")
        return
    address = found[selection[0]]
    title = findtitleid() or "?"
    typetext="Float" if scanfloat else str(scansize)
    iid=table.insert("","end",values=("New Address",hex(address),typetext,"?",title))
    tablerows[iid]={"address":address,"size":scansize,"float":scanfloat}
    scanstatus.config(text=f"Successfully added {hex(address)} to the Address Table!")

def tablefreezeevent():
    for iid in table.selection():
        row=tablerows[iid]
        if row.get("frozen") is not None:
            row["frozen"]=None
            table.item(iid,tags=())
        else:
            try:
                row["frozen"]=readvalue(backend,base,row["address"],row["size"],row["float"])
                table.item(iid,tags=("frozen",))
            except Exception:
                pass
ttk.Button(tablebuttons,text="Toggle Freeze",command=tablefreezeevent).pack(side="left")

def edittable(event):
    iid=table.identify_row(event.y)
    column=table.identify_column(event.x)
    if not iid:
        return
    row = tablerows[iid]
    if column in ("#1","#5"):
        key="name" if column == "#1" else "title"
        text=simpledialog.askstring("Edit",f"New {key}:",initialvalue=table.set(iid,key),parent=root)#parent=root fixed the crash for some reason, don't remove it
        if text is not None:
            table.set(iid,key,text)
    elif column == "#4":
        text = simpledialog.askstring("Edit", "New Value:",parent=root)
        if text is None: return
        try:
            if row["float"]:
                value=float(text)
            else:
                value=int(text)
            if not row["float"] and not 0<=value<256**row["size"]:
                raise ValueError
            writevalue(backend,base,row["address"],row["size"],value,row["float"])
        except ValueError:
            messagebox.showerror("Edit", "Please enter a valid number for the current byte size.",parent=root)
        except Exception as exc:
            messagebox.showerror("Edit", f"Write Failed For Reason: {exc}",parent=root)
table.bind("<Double-Button-1>",edittable)

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
    export(path, found, scansize,scanfloat)
    scanstatus.config(text=f"Scan Exported.")

def importbuttonevent():
    global found, scansize, previous, scanfloat
    try:
        path=filedialog.askopenfilename(filetypes=[("CemuTap Scan", "*.ctms")])
        if path=="":
            scanstatus.config(text=f"Import Canceled.")
            return
        found, scansize, scanfloat = importscan(path)
        previous=[]
        for addr in found:
            try:
                previous.append(readvalue(backend,base,addr,scansize,scanfloat))
            except Exception:
                previous.append(0)
        size.set("Float" if scanfloat else str(scansize))
        scanstatus.config(text=f"Successfully imported CemuTap Scan file.")
        showmatches()
    except Exception:
        scanstatus.config(text="!!! Could not read import. Are you sure this is a CemuTap Scan File?")

#row0
ttk.Label(liveedittab,text="Address:").grid(row=0,column=0,pady=8,padx=8)
editoraddr=ttk.Entry(liveedittab)
editoraddr.grid(row=0,column=1,padx=8,pady=8)
#row1
sizelabel=ttk.Label(liveedittab,text="Byte Size To Modify:")
sizelabel.grid(row=1, column=0, padx=8, pady=8)
editorsize=ttk.Combobox(liveedittab, values=["1","2","4","Float"], state="readonly", width=5)
editorsize.grid(row=1, column=1, padx=8, pady=8)
editorsize.set("2")
#row2
currentvaluelabel=ttk.Label(liveedittab,text="Current Value:")
currentvaluelabel.grid(row=2,column=0,pady=8,padx=8)
currentedit=ttk.Label(liveedittab,text="?")
currentedit.grid(row=2,column=1,pady=8,padx=8)
#row3
nvlabel=ttk.Label(liveedittab,text="New Value:").grid(row=3,column=0,padx=8,pady=8)
newvalue=ttk.Entry(liveedittab)
newvalue.grid(row=3,column=1,padx=8,pady=8)
#row4
writebutton=ttk.Button(liveedittab,text="Write")
writebutton.grid(column=0,row=4,padx=8,pady=8)
freezebutton=ttk.Button(liveedittab,text="Freeze Value")
freezebutton.grid(column=1,row=4,padx=8,pady=8)
editorstatus=ttk.Label(liveedittab,text="Ready.")
editorstatus.grid(column=1,row=5,padx=8,pady=8)

exportbutton = ttk.Button(scantab,text="Export Scan", command=exportbuttonevent)
exportbutton.grid(row=5,column=0,padx=8,pady=8)
importbutton = ttk.Button(scantab,text="Import Scan", command=importbuttonevent)
importbutton.grid(row=5,column=1,padx=8,pady=8)

tablecontrols = ttk.Frame(scantab)
tablecontrols.grid(row=5,column=2,padx=8,pady=8)

resettable = ttk.Button(tablecontrols, text="Clear Address Table", command=cleartableevent)
resettable.pack(side=tk.LEFT,padx=8)

addtotablebutton=ttk.Button(tablecontrols,text="Add Value to Table",command=addtotable)
addtotablebutton.pack(side=tk.LEFT,padx=8)

def editortype():
    text=editorsize.get()
    floattoggle=text=="Float"
    return (4 if floattoggle else int(text)), floattoggle #returns 4 is floattoggle is valid

def write():
    if backend is None:
        editorstatus.config(text="CemuTap is not currently attached to Cemu. Is Cemu even open?")
        return
    try:
        address=int(editoraddr.get(),16)
        editorbytesize, isfloat =editortype()
        value=float(newvalue.get()) if isfloat else int(newvalue.get())
    except ValueError:
        editorstatus.config(text="Please enter a hex address and a valid number.")
        return
    if not isfloat and not 0 <= value < 256 ** editorbytesize:
        editorstatus.config(text=f"New Value must be between 0 to {256**editorbytesize-1}.")
        return
    try:
        writevalue(backend,base,address,editorbytesize,value,isfloat)
        editorstatus.config(text=f"Wrote {value} to address {hex(address)}.")
    except Exception as exc:
        editorstatus.config(text=f"Write failed for reason: {exc}")

writebutton.config(command=write)

def sendaddresstoeditor(event):
    selection = results.curselection()
    if not selection:
        return
    addr = found[selection[0]]
    editoraddr.delete(0,"end")
    editoraddr.insert(0,hex(addr))
    editorsize.set("Float" if scanfloat else str(scansize))
    toptab.select(liveedittab)
results.bind("<Double-Button-1>",sendaddresstoeditor)



def refloop():
    if 0<len(found)<=12:
        showmatches()
    root.after(1000,refloop)
    for iid,row in tablerows.items():
        try:
            val=readvalue(backend,base,row["address"],row["size"],row["float"])
            text=str(round(val,4) if row["float"] else val)
        except Exception:
            text="?"
        table.set(iid,"value",text)
    try:
        address=int(editoraddr.get(),16)
        editorbytesize,isfloat=editortype()
        value=readvalue(backend,base,address,editorbytesize,isfloat)
        currentedit.config(text=str(round(value,4) if isfloat else value))
    except Exception:
        currentedit.config(text="?")

def togglefreezevalue():
    global frozen
    if frozen is not None:
        frozen = None
        freezebutton.config(text="Freeze Value")
        editorstatus.config(text="Value Unfrozen.")
        return
    if backend is None:
        editorstatus.config(text="CemuTap is not currently attached to Cemu. Is Cemu even open?")
        return
    try:
        address=int(editoraddr.get(),16)
        editorbytesize, isfloat =editortype()
        value=float(newvalue.get()) if isfloat else int(newvalue.get())
    except ValueError:
        editorstatus.config(text="Please enter a hex address and a valid number.")
        return
    if not isfloat and not 0 <= value < 256 ** editorbytesize:
        editorstatus.config(text=f"New Value must be between 0 to {256**editorbytesize-1}.")
        return
    frozen=(address,editorbytesize,value,isfloat)
    freezebutton.config(text="Unfreeze")
    editorstatus.config(text=f"Froze address {hex(address)} at {value}.")

freezebutton.config(command=togglefreezevalue)

def loopfreeze():
    if frozen is not None:
        try:
            writevalue(backend,base,*frozen)#unpack frozen also
        except Exception:
            pass
    for row in tablerows.values():
        if row.get("frozen") is not None:
            try:
                writevalue(backend,base,row["address"],row["size"],row["frozen"],row["float"])
            except Exception:
                pass
    root.after(100,loopfreeze)

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
        messagebox.showerror("Add Plugin", f"Couldn't install plugin for reason: {exc}",parent=root)
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
loopfreeze()
root.mainloop()