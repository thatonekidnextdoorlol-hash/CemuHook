# CemuTap
![Hackatime](https://hackatime.hackclub.com/api/v1/badge/U0C4E7F1317/thatonekidnextdoorlol-hash/CemuTap)
<br>
<img src="CemuTap.png" width="300px">

CemuTap is a free and open source alternative to Cheat Engine's memory scanner, designed specifically for the Cemu Wii U Emulator.

## Features
- Set scan byte query size from 1 byte, 2 bytes, 4 bytes, floats, and even unknown initial values.
- Scan for specific integers in Cemu's memory and returns matching addresses.
- Filter out addresses that don't match a new value after each scan or do not meet a certain criteria (ex. "Changed", "Unchanged", "Increased"...).
- Export and Save found addresses.
- Modify address values in-game using the Live Address Editor.
- Freeze in-game addresses at a specific value.
- Create or use community made CemuTap python plugins.
- Address Table: Save addresses with names, watch their live values, edit their live values, and bulk freeze several values at once all from a single page.
- Export and import Address Tables as a ``.ctms`` file to keep or share per game.
- Signed integers, so negative address values can be both read and written correctly.

## Requirements
- Windows or Linux
- [Cemu](https://cemu.info/), with a game running.

## Usage
1. Set your value to the integer you are searching for. (ex. 1110 Lives -> 1110)
2. Set the "Byte Size To Query" value to the amount of bytes the game uses for that value (1, 2, or 4).
3. Click the "New Scan" button to start a search for said value in Cemu's memory.
4. After the first scan is completed, modify your value in-game (ex. Losing a life and lives dropping to 1109), then change Value to the new value. (ex. 1109 Lives -> 1109)
   
A simpler, mini tutorial on how to scan using CemuTap can be found here: https://www.youtube.com/watch?v=_IzkyIbeI9A

## CemuTap Scan Files (.ctms)
You can export found addresses to save for later usage via the "Export Scan" button. Exported addresses are saved as a ctms (CemuTap Scan File) file, including the date and time of your export as its name. If you ever want to recover a saved export, you can use the "Import Scan" button, which asks for a .ctms file. 

# Live Address Editor
CemuTap allows you to edit the live values of addresses in-game using the **Live Address Editor** tab.
1. Enter an address in hex (e.g. `0x36d3ea3a`), then choose it's byte size.
2. Enter a **New Value** then click **Write** to change the in-game value once.
3. Additionally, you can also use the **Freeze Value** button to lock the new value. To unfreeze a value, you can click on the **Unfreeze** button after freezing.

## Address Table
1. Select any address output after a scan in the scan tab's address table, then click "Add Value to Table.".
2. Double-click a row's `Name` or `Title` to rename it, or double click it's `Value` to modify the in-game value.
3. Select rows (Ctrl + Click for several) and click on the "Toggle Freeze" to freeze their current value.
4. Use "Export Table" and "Import Table" to save and load tables as ``.ctmt`` files.

# Plugins
Documentation and information about using and creating CemuTap plugins can be found in [PLUGINS.md](PLUGINS.md).

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

A Tool By GABEWARE<img src="GABEWARE.png" width="16px">
