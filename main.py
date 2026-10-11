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

backend = WindowsBackend()

print(f"CEMU ProcessID: {backend.pm.process_id}")
base = findbase()
print(hex(base))

try:
     print(readunit(backend, base, 0x10000000, 4))
     chunk = backend.read(base + 0x10000000, 0x100000)
     print(len(chunk))
     target = (1109).to_bytes(2,"big")
     found=[]
     position=chunk.find(target,0)
     while position!=-1:
          found.append(position)
          position = chunk.find(target, position+1)
     print(len(found))

except Exception as e:
     print(f"!!! READ FAILURE. Is Cemu running? If it is, try running Cemu and this script at an administrator level: {e}")
     print(f"ps: this could also mean the script broke. create an issue in the main repository :P")

searchsize = int(input("Byte Size To Query: "))
value = int(input("Value Query: "))
target = value.to_bytes(searchsize, "big")

countsuccess = 0
countfail = 0
found = []

for guest in range(0x10000000, 0x50000000, 0x100000):
     try:
          chunk = backend.read(base+guest,0x100000)
     except Exception:
          countfail += 1
          continue
     countsuccess += 1
     position = chunk.find(target, 0)
     while position != -1:
          found.append(guest + position)
          position = chunk.find(target, position+1)

print(len(found))
print(f"Sucessful Chunk Reads: {countsuccess}")
print(f"Failed Chunk Reads: {countfail}")
print([hex(a) for a in found[:5]])

while True:
     text = input("New Value Query (Or Enter To Quit):")
     if text == "":
          break
     newvalue = int(text)
     survivors = []
     for addr in found:
         if readunit(backend, base, addr, searchsize) == newvalue:
             survivors.append(addr)
     found = survivors
     print(len(found))
     if len(found) <= 25:
        print([hex(a) for a in found[:25]])
     else:
        print(f"Matches Over 25. Showing First 25 Found: {[hex(a) for a in found[:25]]}")
