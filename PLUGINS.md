# CemuTap Plugins Documentation
CemuTap allows you to add plugins to interact with:
- Reading Values from the game's memory.
- Cemu Memory Writing.
- React whenever the user runs a scan.
- Add their own interface inside of the Plugins tab and optionally a dedicated pinned tab to the top bar.
Plugins are written in Python and can be created by anyone.

## Plugin Hierarchy
Plugins are a folder located inside of either the user's ``%APPDATA%\CemuTap\plugins\`` if they're on Windows, or the user's ``~/.local/share/CemuTap/plugins/`` if they're on Linux. Plugin folders contain both a ``plugin.json`` file that identifies the name, version, entry, and author of the plugin, and at least one python script that connects to CemuTap via the PluginAPI.

## plugin.json
As explained in the Plugin Hierarchy section; the plugin.json file allows a plugin creator to include information of a plugin such as...
- The plugin's name `name`
- The plugin version `version`
- The author of the plugin `author`
- The python script the plugin calls upon. `entry`
Example of a `plugin.json` file:
``{"name": "CemuRPC", "version": "1.0.0", "author": "Gabe", "entry": "main.py"}``

## PluginAPI
All addresses are Wii U (guest) addresses, such as `0x36D3EA3A`

### `api.read(address, size, floattoggle=False)`
Reads the value provided in `address` and returns it as a number.
- `size`: How many bytes the value uses (1, 2, or 4)
- `floattoggle`: Set to `True` to read a float (also use size 4)

### `api.write(address, size, value, floattoggle=False)`
Writes `value` to `address`. Ensure `size` and `floattoggle` matches the method the game uses to store the value, or else you may accidentally overwrite nearby values.

### `api.onscan(function)`
`function` runs whenever the user finishes a scan. The function receives the list of found addresses.

## The Plugin Script
Your entry script **must** define a `setup` function, and can optionally define `buildui` to create an interactive user interface.

### `setup(api)` (Required Function)
Called once, when CemuTap loads the plugin. `api` is your plugin's connection to CemuTap's functions.

### `buildui(frame)` (Optional)
Called when your plugin's interface is shown: either when it's selected in the Plugins tab or when it's pinned to the top bar. `frame` is an empty Tkinter frame that you can use to build your widgets inside of it. It can also be called more than once, so try to build everything inside of this function.

*Note: Plugins without `buildui` run in the background only*

## Installing a Plugin
Installing a plugin in CemuTap is simple. 
1. First, audit the plugin's source code before running or installing it to CemuTap. Plugins can be created by anyone, and its code runs directly on your machine. Only use plugins that you can confirm are risk free, and were created by someone you trust.
2. After auditing the code, open CemuTap and navigate to the "Plugins" page.
3. Click on the "Add Plugin" button to open up the file selection panel.
4. Locate the plugin you would like to install and click "Open"
*NOTE: Plugins must be formatted as a .zip archive before installation*

## Removing a plugin.
To remove a plugin, simply locate and delete the Plugin's folder inside of CemuTap's dedicated plugins folder (``%APPDATA%\CemuTap\plugins\`` if you are on Windows or ``~/.local/share/CemuTap/plugins/`` if you are using Linux). After deleting the plugin, restart CemuTap.

## Example Plugin
This plugin shows your lives in its own tab, refreshing the lives count every second.

Folder Hierarchy:
```
LivesWatcher/
    plugin.json
    main.py
```

`plugin.json`:
```json
{"name": "LivesWatcher", "version": "1.0.0", "author": "Gabe", "entry": "main.py"}
```

`main.py`:
```python
from tkinter import ttk

api = None

def setup(capi):
    global api
    api = capi

def buildui(frame):
    label = ttk.Label(frame, text="Current Lives: ?") 
    label.pack(padx=8, pady=8)
    def update():
        try:
            label.config(text=f"Lives: {api.read(0x36D3EA3A, 2)}") #Change the address (0x36D3EA3A) to the hex address of the value you want to display!
        except Exception:
            label.config(text="Lives: ?") #If the address doesn't read properly.
        label.after(1000, update) #After 1 second, runs the function update again.
    update()
```

To share and use the example plugin, zip the `LivesWatcher` folder. Refer to the **Installing a Plugin** section to install the plugin.
*Note: Make sure to change the hex address included in the example plugin to a value you want to display before installing/zipping!*

## Tips
- **Extra Libraries:** Other CemuTap users may not have pip, so bundle libraries inside of your plugin. Install the libraries into a `lib` folder with ``pip install <library> --target lib``, and add that folder to sys.path before importing.
- **Slow Work:** Try to avoid running long loops or `time.sleep` in `setup` or `buildui`. This can cause CemuTap to freeze in most instances. Use `widget.after()` for repeated UI updates.
- **Packaged Versions:** The CemuTap app only includes python modules CemuTap itself uses. If your plugin requires another python module, test it with the packaged CemuTap app, not just from source.
- **Errors:** If your plugin fails to load, CemuTap will print the crash reason in the terminal when built and run from source.

