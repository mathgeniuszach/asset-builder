from .globals import *

import msgpack

n = 1

class TabBar:
    def __init__(self):
        with gui.tab_bar(tag="tabs", reorderable=True, callback=lambda: self.choose_tab()):
            gui.add_tab_button(label="+", trailing=True, callback=lambda: self.add_tab())
            gui.add_tab_button(label="x", trailing=True, callback=lambda: self.close_tab())
            self.tab_count = 0
            self.add_tab()
    
    def remove_all_tabs(self):
        gui.delete_item("tabs", children_only=True)
        gui.add_tab_button(label="+", trailing=True, parent="tabs", callback=lambda: self.add_tab())
        gui.add_tab_button(label="x", trailing=True, parent="tabs", callback=lambda: self.close_tab())
    
    def add_tab(self, data=None):
        global n
        sn = str(n)
        n += 1

        self.tab_count += 1
        if data:
            G.data[sn] = data
        else:
            G.data[sn] = {"type": "", "checkboxes": {}, "parts": {}, "colors": {}, "save": "", "saved": False}
        G.images[sn] = {}
        
        lbl = "* Untitled"
        if data and data.get("save", ""):
            lbl = ("" if data.get("saved") else "* ") + Path(data.get("save")).stem
        gui.add_tab(label=lbl, tag=sn, parent="tabs")
        gui.set_value("tabs", sn)

        G.app.change()
    
    def _close_tab(self, data=None):
        sn = gui.get_value("tabs")
        gui.delete_item(sn)
        del G.data[sn]
        del G.images[sn]

        self.tab_count -= 1
        if self.tab_count == 0:
            self.add_tab(data=data)

    def close_tab(self):
        if G.active.get("saved") or not gui.get_value("unsaved_prompt"):
            # If we already saved or the user doesn't want to hear it, just close immediately.
            self._close_tab()
        else:
            # If we haven't saved, pop open dialog asking if we want to.
            r = xdialog.yesnocancel(message="Do you want to save this tab?")
            if r == xdialog.YES:
                if self.save_tab():
                    self._close_tab()
            elif r == xdialog.NO:
                self._close_tab()

    def choose_tab(self):
        # Load active data
        active: dict = G.data[gui.get_value("tabs")]
        G.active = active

        # Update type
        gui.set_value("type", active.get("type", ""))
        G.app.selector.change_type()
    
    def save_tab(self, save_as=False, no_load=False):
        # Get the data now before the user does funny switchy tab business
        sn = gui.get_value("tabs")
        active = G.active

        # Get the image to save with
        img = G.app.img_stack.image
        if img is None:
            xdialog.info(message="You cannot save without selecting a type first.")
            return False

        # Get save location
        fname = active.get("save")
        if not fname or save_as:
            fname = xdialog.save_file(filetypes=[("PNG Image", "*.png")])
            if not fname: return False

        # Ensure that location exists to save into
        fpath = Path(fname)
        if not fpath.parent.exists():
            fname = xdialog.save_file(filetypes=[("PNG Image", "*.png")])
            if not fname: return False
            fpath = Path(fname)
        
        if fpath.suffix != ".png":
            fname = str(fpath)+".png"
            fpath = Path(fname)

        # Save image and data
        if no_load:
            img.save(fpath)
        else:
            # I like to call this data being appended to the image a "parasite"
            info = PngInfo()
            active["save"] = fname
            info.add_text("msgp", msgpack.packb(active), True)
            img.save(fpath, pnginfo=info)

            # Mark active as "saved"
            active["saved"] = True
            gui.configure_item(sn, label=fpath.stem)
        
        return True

    def open(self):
        try:
            fname = xdialog.open_file(filetypes=[("PNG Image", "*.png")])
            if not fname: return
            img = Image.open(fname)
            data = msgpack.unpackb(img.text["msgp"].encode("latin-1"))
            
            data["save"] = fname
            data["saved"] = True

            if self.tab_count == 1 and not G.active_type and not G.active["save"]:
                self._close_tab(data=data)
            else:
                self.add_tab(data=data)
        except Exception:
            log.warning("Could not open file", exc_info=True)
            xdialog.warning(message="Could not open file.\nThe file must be a png image saved (not exported) by the tool itself.")

    def load_tabs(self, resetn=True):
        global n
        
        # Delete all tabs
        sn: str = gui.get_value("tabs")
        osn = sn
        self.remove_all_tabs()
        
        # Re-add tabs
        self.tab_count = len(G.data)
        ndata = {}
        for sn, v in G.data.items():
            if sn == osn:
                i = -1
            else:
                i = n
                n += 1
            
            sn = str(i)
            lbl = "* Untitled"
            if v.get("save", ""):
                lbl = ("" if v.get("saved") else "* ") + Path(v.get("save")).stem
            gui.add_tab(label=lbl, tag=sn, parent="tabs")

            ndata[sn] = v
            G.images[sn] = {}
        
        G.data = ndata
        gui.set_value("tabs", "-1" if "-1" in ndata else next(iter(ndata.keys())))

        # Choose the tab that remains
        self.choose_tab()