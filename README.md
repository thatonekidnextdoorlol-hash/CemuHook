# CemuTap
![Hackatime](https://hackatime.hackclub.com/api/v1/badge/U0C4E7F1317/thatonekidnextdoorlol-hash/CemuTap) 

CemuTap is a free and open source alternative to Cheat Engine's memory scanner, designed specifically for the Cemu Wii U Emulator.

## Features
- Set scan byte query size from 1 byte, 2 bytes, and 4 bytes.
- Scan for specific integers in Cemu's memory and returns matching addresses.
- Filter out addresses that don't match a new value after each scan.
- Export and Save found addresses.

## Requirements
- Windows or Linux
- [Cemu](https://cemu.info/), with a game running.

## Usage
1. Set your value to the integer you are searching for. (ex. 1110 Lives -> 1110)
2. Set the "Byte Size To Query" value to the amount of bytes the game uses for that value (1, 2, or 4).
3. Click the "New Scan" button to start a search for said value in Cemu's memory.
4. After the first scan is completed, modify your value in-game (ex. Losing a life and lives dropping to 1109), then change Value to the new value. (ex. 1109 Lives -> 1109)
A simpler, mini tutorial on how to use CemuTap can be found here: https://www.youtube.com/watch?v=_IzkyIbeI9A

## CemuTap Scan Files (.ctms)
You can export found addresses to save for later usage via the "Export Scan" button. Exported addresses are saved as a ctms (CemuTap Scan File) file, including the date and time of your export as its name. If you ever want to recover a saved export, you can use the "Import Scan" button, which asks for a .ctms file. 

## Running from source
Requirements:
- python3 from [python.org](https://www.python.org/downloads/) (Microsoft Store version can block memory reading)

Steps:
1. Clone the repository:
```
    git clone https://github.com/thatonekidnextdoorlol-hash/CemuTap.git
    cd CemuTap
```
2. Install the dependency (pymem):
```
    pip install pymem
```
3. Open a game in Cemu, then run (from the root directory):
```
    python gui.py
```

## Limitations
- Only scans MEM2 (0x10000000 to 0x50000000)

A Tool By GABEWARE
