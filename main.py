import psutil
import re
import os
import json
import sys
import importlib.util
import shutil
import zipfile
import tempfile

class WindowsBackend:
    def __init__(self):
        import pymem
        self.pm = pymem.Pymem("cemu.exe")
    def read(self, address, size):
        return self.pm.read_bytes(address, size)
    def write(self,address,data):
        self.pm.write_bytes(address,data,len(data))

class LinuxBackend:
    def __init__(self,pid):
        self.f = open(f"/proc/{pid}/mem", "r+b", buffering=0)
    def read(self,address,size):
        self.f.seek(address)
        return self.f.read(size)
    def write(self,address,data):
        self.f.seek(address)
        return self.f.write(data)

class PluginAPI:
    def __init__(self,backend,base):
        self.backend=backend
        self.base=base
        self.scancallbacks=[]
    def read(self,guest, size):
        return readunit(self.backend,self.base,guest,size)
    def write(self,guest,size,value ):
        writeu(self.backend,self.base,guest,size,value)
    def onscan(self,function):
        self.scancallbacks.append(function)

def cemupid():
    for process in psutil.process_iter(["name"]):
        name=process.info["name"]
        if name and name.lower() == "cemu":
            return process.pid

def backendcreate():
    if sys.platform=="win32":
        return WindowsBackend()
    # linux seperator
    pid=cemupid()
    if pid is None:
        raise RuntimeError("Cemu Instance Not Detected: Is Cemu even running?")
    return LinuxBackend(pid)

def findlog():
    if sys.platform=="win32":
        return os.path.join(os.environ["APPDATA"],"Cemu","log.txt")
    candidates=["~/.var/app/info.cemu.Cemu/data/Cemu/log.txt","~/.local/share/Cemu/log.txt"]
    for path in candidates:
        fpath=os.path.expanduser(path)
        if os.path.exists(fpath):
            return fpath
    return None

def datadir():
    if sys.platform=="win32":
        dirpath=os.path.join(os.environ["APPDATA"],"CemuTap")
    else:
        dirpath=os.path.expanduser("~/.local/share/CemuTap")
    os.makedirs(dirpath,exist_ok=True)
    return dirpath

def savesettings(settings):
        with open(os.path.join(datadir(), "settings.json"),"w") as folder:
            json.dump(settings,folder)

defaults={"theme":"dark","pinned":[]}

def loadcts():
    settings=dict(defaults)
    try:
        with open(os.path.join(datadir(), "settings.json")) as folder:
            settings.update(json.load(folder))
    except Exception:
        pass
    return settings

def plugindir():
    path=os.path.join(datadir(),"plugins")
    os.makedirs(path,exist_ok=True)
    return path

def pluginslistbuild():
    plugins=[]
    for folder in os.listdir(plugindir()):
        path=os.path.join(plugindir(),folder)
        try:
            with open(os.path.join(path,"plugin.json")) as fd:
                info=json.load(fd)
        except Exception:
            continue
        info["folder"]=path
        plugins.append(info)
    return plugins

def pluginroot(folder):
    if os.path.exists(os.path.join(folder,"plugin.json")):
        return folder
    for name in os.listdir(folder):
        inner = os.path.join(folder,name)
        if os.path.exists(os.path.join(inner,"plugin.json")):
            return inner
    return None

def plugininstall(path):
    with tempfile.TemporaryDirectory() as temp:
        if zipfile.is_zipfile(path):
            zipfile.ZipFile(path).extractall(temp)
            source=pluginroot(temp)
        else:
            source=pluginroot(path)
        if source is None:
            raise ValueError("No plugin.json found in selected archive.")
        destination=os.path.join(plugindir(), os.path.basename(source.rstrip("/\\")))
        if os.path.exists(destination):
            raise ValueError("A CemuTap plugin already exists with this foldername.")
        shutil.copytree(source,destination)
        return destination


def executeplugin(info):
    path=os.path.join(info["folder"],info["entry"])
    spec=importlib.util.spec_from_file_location(info["name"],path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def findbase():
        pattern = r"base: 0x([0-9a-fA-F]+)"
        logpath = findlog()
        with open(logpath, errors="ignore") as f:
             lpopt = f.read()
             matches = re.findall(pattern, lpopt)
             return int(matches[-1], 16)
        
def readunit(backend, base, guest, size):
    hostaddress = base + guest
    habo =  backend.read(hostaddress, size)
    return int.from_bytes(habo, "big")

def writeu(backend,base,guest,size,value):
    backend.write(base+guest,value.to_bytes(size,"big"))

def primaryscan(backend, base, value, size, progress = None):
     target = value.to_bytes(size, "big")
     found = []
     
     for guest in range(0x10000000, 0x50000000, 0x100000):
         try:
             chunk = backend.read(base+guest,0x100000)
         except Exception:
             continue
         position = chunk.find(target, 0)
         while position != -1:
             found.append(guest + position)
             position = chunk.find(target, position+1)
         if progress is not None:
            progress(guest-0x10000000 + 0x100000)
     return found, [value]*len(found)

def keep(mode,current,old,value):
    if mode=="exact":
        return current==value
    if mode=="increased":
        return current> old
    if mode=="decreased":
        return current < old
    if mode== "changed":
        return current != old
    if mode=="unchanged":
        return current == old
    return False #if none pass ofc

def nextscan(backend, base, found, previous, value, size, mode="exact",progress = None):
     survivors = []
     survivingvalues=[]
     start=None
     chunk=None
     for i, addr in enumerate(found):
         chunkbegin = addr // 0x100000 * 0x100000
         offset=addr-chunkbegin
         if chunkbegin!=start:
             try:
                 chunk = backend.read(base+chunkbegin, 0x100000 + size)
             except Exception:
                 try:
                     chunk=backend.read(base+chunkbegin,0x100000)
                 except Exception:
                     chunk=None
             start=chunkbegin
         if chunk is not None:
             raw=chunk[offset:offset+size]
             if len(raw)==size:
                 current = int.from_bytes(raw, "big")
                 if keep(mode,current,previous[i],value):
                     survivors.append(addr)
                     survivingvalues.append(current)
         if progress is not None and i%10000==0:
             progress(i,len(found))
     return survivors,survivingvalues

def export(path, found, size):
    data = {"version": 1, "size": size, "addresses": found}
    with open(path,"w") as f:
        json.dump(data,f)

def importscan(path):
    with open(path) as f:
        data=json.load(f)
        return data["addresses"],data["size"]

if __name__ == "__main__": # just to make sure the terminal doesn't open :P

     backend = WindowsBackend()

     print(f"CEMU ProcessID: {backend.pm.process_id}")
     base = findbase()
     print(hex(base))

     searchsize = int(input("Byte Size To Query: "))
     value = int(input("Value Query: "))



     found,previous = primaryscan(backend, base, value, searchsize)

     print(len(found))
     print([hex(a) for a in found[:5]])

     while True:
         text = input("New Value Query (Or Enter To Quit):")
         if text == "":
             break
         newvalue = int(text)
         found,previous = nextscan(backend, base, found, previous, newvalue, searchsize)
         print(len(found))
         if len(found) <= 25:
             print([hex(a) for a in found[:25]])
         else:
             print(f"Matches Over 25. Showing First 25 Found: {[hex(a) for a in found[:25]]}")

