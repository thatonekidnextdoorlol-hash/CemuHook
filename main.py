import pymem
import re
import os

class WindowsBackend:
    def __init__(self):
        self.pm = pymem.Pymem("cemu.exe")

    def read(self, address, size):
        return self.pm.read_bytes(address, size)
        
    
def findbase():
        pattern = r"base: 0x([0-9a-fA-F]+)"
        logpath = os.path.join(os.environ["APPDATA"], "Cemu", "log.txt")
        with open(logpath, errors="ignore") as f:
             lpopt = f.read()
             matches = re.findall(pattern, lpopt)
             return int(matches[-1], 16)
        
def readunit(backend, base, guest, size):
    hostaddress = base + guest
    habo =  backend.read(hostaddress, size)
    return int.from_bytes(habo, "big")

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
     return found

def nextscan(backend, base, found, value, size, progress = None):
     survivors = []
     for i, addr in enumerate(found):
         if readunit(backend, base, addr, size) == value:
             survivors.append(addr)
         if progress is not None and i%10000==0:
             progress(i,len(found))
     return survivors

if __name__ == "__main__": # just to make sure the terminal doesn't open

     backend = WindowsBackend()

     print(f"CEMU ProcessID: {backend.pm.process_id}")
     base = findbase()
     print(hex(base))

     searchsize = int(input("Byte Size To Query: "))
     value = int(input("Value Query: "))



     found = primaryscan(backend, base, value, searchsize)

     print(len(found))
     print([hex(a) for a in found[:5]])

     while True:
         text = input("New Value Query (Or Enter To Quit):")
         if text == "":
             break
         newvalue = int(text)
         found = nextscan(backend, base, found, newvalue, searchsize)
         print(len(found))
         if len(found) <= 25:
             print([hex(a) for a in found[:25]])
         else:
             print(f"Matches Over 25. Showing First 25 Found: {[hex(a) for a in found[:25]]}")

