from .globals import *

from . import load_packs

class MenuBar:
    def __init__(self):
        # Setup shortcuts
        self.keys = set()
        with gui.handler_registry():
            gui.add_key_press_handler(callback=lambda s, a: self.key_press(a))
            gui.add_key_release_handler(callback=lambda s, a: self.key_release(a))

        # Setup menu bar
        with gui.menu_bar():
            with gui.menu(label="File", tag="file_menu"):
                # Shortcuts
                gui.add_menu_item(label="Open", shortcut='Ctrl+O', tag="open", callback=lambda s: self.file_button(s))
                gui.add_menu_item(label="Save", shortcut='Ctrl+S', tag="save", callback=lambda s: self.file_button(s))
                gui.add_menu_item(label="Save As", shortcut='Ctrl+Shift+S', tag="save_as", callback=lambda s: self.file_button(s))
                gui.add_menu_item(label="Export", shortcut='Ctrl+E', tag="export", callback=lambda s: self.file_button(s))
                gui.add_menu_item(label="Close", shortcut='Ctrl+W', tag="close", callback=lambda s: self.file_button(s))
            
            with gui.menu(label="Options"):
                gui.add_menu_item(label="Prompt on Unsaved Work", tag="unsaved_prompt", check=True, callback=lambda s: self.change_option(s))
                gui.add_menu_item(label="Autobackup Work", tag="autosave", check=True, callback=lambda s: self.change_option(s))
                gui.add_menu_item(label="Nearest Scaling", tag="nearest", check=True, callback=lambda s: self.change_option(s))

            with gui.menu(label="Packs"):
                gui.add_menu_item(label="List Packs", tag="list-packs", callback=lambda: G.app.packs.show())
                gui.add_menu_item(label="Reload", tag="reload", callback=lambda: load_packs.reload())

            gui.add_menu_item(label="Help", callback=lambda: G.app.help.show())

            gui.add_menu_item(label="Discord", callback=lambda: webbrowser.open(DISCORD))

            gui.add_text("  ", tag="message")

            # Load options
            log.info("Loading options")
            try:
                with OPTIONS.open("r", encoding="utf-8") as file:
                    self.opts = json.load(file)
            except FileNotFoundError:
                self.opts = {}
            except Exception:
                log.warn("Failed to load options file, recreating it.", exc_info=True)
                self.opts = {}

            gui.set_value("unsaved_prompt", self.opts.get("unsaved_prompt", True))
            gui.set_value("autosave", self.opts.get("autosave", True))
            gui.set_value("nearest", self.opts.get("nearest", True))
    
    def key_press(self, key):
        if key not in self.keys:
            if gui.is_key_down(gui.mvKey_Control):
                if gui.is_key_down(gui.mvKey_Shift):
                    if key == gui.mvKey_S:
                        self.file_button("save_as")
                else:
                    if key == gui.mvKey_S:
                        self.file_button("save")
                    elif key == gui.mvKey_O:
                        self.file_button("open")
                    elif key == gui.mvKey_E:
                        self.file_button("export")
                    elif key == gui.mvKey_W:
                        self.file_button("close")
            self.keys.add(key)

    def key_release(self, key):
        self.keys.discard(key)
    
    def file_button(self, sender):
        if   sender == "open":      G.app.tab_bar.open()
        elif sender == "save":      G.app.tab_bar.save_tab()
        elif sender == "save_as":   G.app.tab_bar.save_tab(save_as=True)
        elif sender == "export":    G.app.tab_bar.save_tab(save_as=True, no_load=True)
        elif sender == "close":     G.app.tab_bar.close_tab()

        gui.hide_item("file_menu")
        gui.show_item("file_menu")
    
    def change_option(self, sender):
        self.opts[sender] = gui.get_value(sender)
        try:
            with OPTIONS.open("w", encoding="utf-8") as file:
                json.dump(self.opts, file)
        except Exception:
            log.error("Failed to write to options file!", exc_info=True)
            self.opts = {}
        
        G.app.change()
    
    def set_message(self, text):
        gui.set_value("message", "  "+text)