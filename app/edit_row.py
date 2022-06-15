from __future__ import annotations

from .globals import *

from copy import deepcopy


class Checkbox:
    def __init__(self, id, text):
        self.id = id
        self.tag = gui.add_checkbox(label=text, tag="check/"+id, callback=lambda: self.change())
    
    def change(self):
        v = gui.get_value(self.tag)
        if v:
            G.active["checkboxes"][self.id] = v
        else:
            del G.active["checkboxes"][self.id]
        
        G.app.change()

class ColorEditPopup:
    zelf: ColorEditPopup = None
    modes = {
        "?": "",
        "x": "Grayscale & Multiply",
        "+": "Grayscale & Grain Merge"
    }
    rmodes = {v: k for k, v in modes.items()}

    @classmethod
    def __new__(cls, *args, **kwargs):
        if ColorEditPopup.zelf is None:
            zelf = super(ColorEditPopup, cls).__new__(*args, **kwargs)
            ColorEditPopup.zelf = zelf

            zelf.copydata = None

            with gui.popup(G.app.nonbutton) as zelf.popup:
                with gui.group(horizontal=True):
                    gui.add_button(label="Copy", callback=lambda: zelf.copy())
                    gui.add_button(label="Copy Color", callback=lambda: zelf.copy_color())
                    gui.add_button(label="Paste", callback=lambda: zelf.paste())
                    gui.add_button(label="Reset", callback=lambda: zelf.reset())
                
                gui.add_text("Adjustments")
                zelf.contrast = gui.add_slider_float(tag="contrast", label="Contrast", min_value=0, default_value=1, max_value=2, callback=lambda s,a: zelf.change_slider(s,a))
                zelf.sharpness = gui.add_slider_float(tag="sharpness", label="Sharpness", min_value=0, default_value=1, max_value=2, callback=lambda s,a: zelf.change_slider(s,a))
                zelf.blur_steps = gui.add_slider_float(tag="blur_steps", label="Max Blur", min_value=1, default_value=1, max_value=20, callback=lambda s,a: zelf.change_slider(s,a))
                zelf.brightness = gui.add_slider_int(tag="brightness", label="Brightness", min_value=-255, max_value=255, clamped=True, callback=lambda s,a: zelf.change_slider(s,a))
                gui.add_text("Color Mode")
                zelf.combo = gui.add_combo(items=list(ColorEditPopup.modes.values()), callback=lambda: zelf.change_mode())
                gui.add_text("Color")
                zelf.color_picker = gui.add_color_picker(no_alpha=True,  callback=lambda: zelf.change_color())
        else:
            zelf = ColorEditPopup.zelf
        
        return zelf
    
    def show(self, pos, typ, item, i, edit4: ColorEdit4):
        self.typ = typ
        self.item = item
        self.i = i

        self.edit4 = edit4
        self.color_edit, self.text = edit4.edits[i]

        # Load data
        self.load()

        # Set position and show
        gui.set_item_pos(self.popup, pos)
        gui.show_item(self.popup)
    
    def copy(self):
        self.copydata = deepcopy(self.get_active())
    
    def copy_color(self):
        active = self.get_active()
        self.copydata = {
            "color": active.get("color", (128, 128, 128)),
            "mode": active.get("mode", "?")
        }
    
    def paste(self):
        if self.copydata:
            self.load(self.copydata)
            self.edit4.load_colors()
            G.app.change()
    
    def reset(self):
        self.edit4.reset_color(i=self.i)
        self.load()
    
    def load(self, exdata=None):
        # Merge extra data
        da = self.get_active()
        if exdata:
            da.update(exdata)

        # Set adjustment values
        gui.set_value(self.brightness, da.get("brightness", 0))
        gui.set_value(self.contrast, da.get("contrast", 1))
        gui.set_value(self.sharpness, da.get("sharpness", 1))
        gui.set_value(self.blur_steps, da.get("blur_steps", 1))

        # Use the color value of the selected color editor
        gui.set_value(self.color_picker, da.get("color", (128, 128, 128)))
        # Use the color mode of the selected color editor text
        gui.set_value(self.combo, ColorEditPopup.modes[da.get("mode", "?")])
    
    def get_active(self):
        n = self.edit4.n
        if n > -1:
            return G.active["colors"][self.item][n][self.i]
        else:
            return G.active["colors"][self.item][self.i]
    
    def change_mode(self):
        mode = ColorEditPopup.rmodes[gui.get_value(self.combo)]
        self.edit4.set_color(self.i, text=mode)
        self.get_active()["mode"] = mode
        G.app.change()
    
    def change_color(self):
        color = gui.get_value(self.color_picker)
        self.edit4.set_color(self.i, color=color)
        self.get_active()["color"] = color
        G.app.change()
    
    def change_slider(self, sender, app_data):
        self.get_active()[sender] = app_data
        G.app.change()

class ColorEdit4:
    def __init__(self, typ, item, n):
        self.typ = typ
        self.item = item
        self.n = n

        self.popup = ColorEditPopup()

        self.edits = []
        with gui.item_handler_registry() as self.och:
            gui.add_item_clicked_handler(callback=lambda s,a: self.open_color(a), button=0)
            gui.add_item_clicked_handler(callback=lambda s,a: self.reset_color(a), button=1)

        with gui.child_window(width=-1, height=26, border=False) as self.win:
            for i in range(4):
                g = gui.add_color_edit(
                    (128, 128, 128), user_data=i, show=False, pos=(i*27+2, 0),
                    no_tooltip=True, no_picker=True, no_drag_drop=True, no_inputs=True
                )
                t = gui.add_text("?", user_data=i, pos=(i*27+10, 0), show=False)
                gui.bind_item_theme(t, G.app.invert_theme)

                gui.bind_item_handler_registry(g, self.och)
                # gui.bind_item_handler_registry(t, self.och)

                self.edits.append((g, t))

        self.visible = 0
    
    def get_active(self):
        if self.n > -1:
            return G.active["colors"][self.item][self.n]
        else:
            if self.item not in G.active["colors"]:
                l = []
                G.active["colors"][self.item] = l
                return l
            else:
                return G.active["colors"][self.item]

    def set_visible(self, count):
        if count < 0 or count > 4: return

        if count > self.visible:
            # Need to show more color pickers
            for i in range(self.visible, count):
                g, t = self.edits[i]
                gui.show_item(g)
                gui.show_item(t)
            
        elif count < self.visible:
            # Need to show less color pickers
            for i in range(count, self.visible):
                g, t = self.edits[i]
                gui.hide_item(g)
                gui.hide_item(t)
        
        self.visible = count

        self.load_colors()
    
    def load_colors(self):
        c = self.get_active()
        count = len(c)

        if count < 0 or count > 4: return

        if self.visible == 0 and self.n == -1:
            # Special case, no values means we can delete the list entirely
            del G.active["colors"][self.item]
        elif count < self.visible:
            # Need to pull more data into active list
            for _ in range(count, self.visible):
                c.append({})
        elif count > self.visible:
            # Need to delete data from active list
            for _ in range(self.visible, count):
                del c[-1]
        
        for i, cdata in enumerate(c):
            self.set_color(
                i,
                color=cdata.get("color", (128, 128, 128)),
                text=cdata.get("mode", "?")
            )
    
    def set_color(self, i, color=None, text=None):
        g, t = self.edits[i]
        if color:
            gui.set_value(g, color)
            if max(color[:3]) < 128:
                gui.bind_item_theme(t, G.app.theme)
            else:
                gui.bind_item_theme(t, G.app.invert_theme)
        if text: gui.set_value(t, text)
    
    def open_color(self, app_data):
        x, y = get_abs_pos(self.win)
        i = gui.get_item_user_data(app_data[1])
        self.popup.show((x, y+25), self.typ, self.item, i, self)
    
    def reset_color(self, app_data=None, i=None):
        if i is None:
            i = gui.get_item_user_data(app_data[1])
        self.get_active()[i] = {}
        self.set_color(i, (128, 128, 128), "?")
        G.app.change()



def build_choices(part: dict):
    meta = part.get("/meta", {})
    depend = meta.get("depends", "")
    if depend:
        choices = {"": [""]}
        counts = {}
        for k, v in part.items():
            if isinstance(v, dict) and not k[0] == "/":
                choices[k], counts[k] = build_choices(v)
        
        return choices, counts
    else:
        choices = [""]
        counts = {}
        for k, v in part.items():
            if not isinstance(v, dict) and not k[0] == "/":
                choices.append(k.replace("_", " "))
                counts[k] = len(v) if isinstance(v, list) else 1
        
        if meta.get("color"):
            counts = {}
        
        choices.sort()
        return choices, counts


class EditRow:
    CHOICE_CACHE = {}

    def __init__(self, typ: str, item: str, part: dict, n: int = None, multi: MultiEditRow = None):
        self.typ = typ
        self.item = item
        self.n = n
        self.multi = multi

        self.depends = part["/depends"]
        self.dependents = part["/dependents"]
        self.curr_counts = {}

        # Get choices list
        id = (typ, item)
        if id not in EditRow.CHOICE_CACHE:
            EditRow.CHOICE_CACHE[id] = build_choices(part)
        
        self.choices, self.color_counts = EditRow.CHOICE_CACHE[id]

        # If n > 0, this combo was just added from a multi-combo.
        parent = 0
        before = 0
        if n:
            parent = "parts/{G.active_type}"
            before = multi.atr

        self.tr = gui.generate_uuid()
        with gui.table_row(tag=self.tr, parent=parent, before=before):
            if n:
                with gui.group(horizontal=True, horizontal_spacing=0):
                    gui.bind_item_theme(gui.add_button(width=-30, enabled=False), G.app.hide_theme)
                    gui.add_button(label="-", width=25, callback=lambda: self.remove())
            else:
                gui.add_text(item.replace("_", " "))
            
            self.combo = gui.add_combo(width=-1, callback=lambda: self.change_combo())
            self.reset_combo()

            self.color_editor = ColorEdit4(typ, item, -1 if multi is None else n)
    
    def collect_choices(self):
        parts = G.active.get("parts", {})

        # Calculate all the available choices based on dependencies
        c = self.choices
        co = self.color_counts
        # TODO: Make this support branching dependencies
        for d in self.depends:
            if type(c) == list: break
            selp = parts.get(d, "")
            c = c.get(selp, [""])
            co = co.get(selp, {})
        
        return co, c
    
    def set_combo(self, color_counts, choices, update=True):
        self.curr_counts = color_counts
        
        gui.configure_item(self.combo, items=choices)

        # If the selected choice is not longer available, reset the combo.
        if update:
            val = gui.get_value(self.combo)
            if val and val not in choices:
                gui.set_value(self.combo, "")
                self.change_combo(update)
    
    def reset_combo(self, update=True):
        self.set_combo(*self.collect_choices(), update)
    
    def change_combo(self, update=True):
        # Get active value
        val = gui.get_value(self.combo).replace(" ", "_")
        # Update number of colors visible
        self.color_editor.set_visible(0 if not val else self.curr_counts.get(val, 0))

        if self.multi is None:
            # Not part of a multi-combo, so update value outside of list
            if update:
                if val:
                    G.active["parts"][self.item] = val
                else:
                    del G.active["parts"][self.item]
            
            # Then update dependent values
            for d in self.dependents:
                combo = G.app.edit_rows.get(self.typ, {}).get(d)
                if combo is not None:
                    combo.reset_combo(update)
        else:
            # Part of a multi-combo, only update value as part of a list
            if update: G.active["parts"][self.item][self.n] = val
        
        if update: G.app.change()

    def remove(self, update=True):
        if self.multi is None: raise TypeError("Cannot delete a non-multi combo")

        # Delete the row
        gui.delete_item(self.tr)
        self.multi.remove_row(self.n)

        # Delete value from active in normal use
        if update is not False:
            del G.active["parts"][self.item][self.n]
            del G.active["colors"][self.item][self.n]
            G.app.change()


class MultiEditRow:
    def __init__(self, typ: str, item: str, part: dict):
        self.typ = typ
        self.item = item
        self.part = part

        self.edit_rows: list[EditRow] = [
            EditRow(typ, item, part, 0, self)
        ]

        self.atr = gui.generate_uuid()
        with gui.table_row(tag=self.atr):
            gui.add_text("")
            gui.add_button(label="+", callback=lambda: self.add_row(), width=25)
    
    def add_row(self, update=True):
        self.edit_rows.append(
            EditRow(self.typ, self.item, self.part, len(self.edit_rows), self)
        )
        if update:
            G.active["parts"][self.item].append("")
            G.active["colors"][self.item].append([])
            G.app.change()
    
    def remove_row(self, n):
        # Delete row
        del self.edit_rows[n]

        # Update row indexes
        for i in range(n, len(self.edit_rows)):
            self.edit_rows[i].n = i
    
    def reset_combo(self, update=True):
        co, c = self.edit_rows[0].collect_choices()
        for er in self.edit_rows:
            er.set_combo(co, c, update)