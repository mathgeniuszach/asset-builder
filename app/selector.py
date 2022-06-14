from .globals import *

from . import edit_row

class TypeSelector:
    def __init__(self):
        with gui.child_window(width=-1, height=-2):
            with gui.group(horizontal=True):
                gui.add_text("Type:")
                gui.add_combo([""], tag="type", width=-1, callback=self.change_type)
                gui.set_value("type", "")
            gui.add_separator()
            gui.add_child_window(tag="parts", autosize_x=True, autosize_y=True, border=False)
    
    def change_type(self):
        otype = G.active_type
        ntype = gui.get_value("type")

        if otype:
            gui.hide_item(f"parts/{G.active_type}")
        
        G.active_type = ntype
        G.active["type"] = ntype

        if ntype:
            gui.show_item(f"parts/{ntype}")
            if not otype:
                # Load defaults if switching from null type
                d = G.types[ntype]["default"]
                merge_dict(G.active["parts"], d.get("parts", {}))
                merge_dict(G.active["checkboxes"], d.get("checkboxes", {}))

            # Parse any data in the "active" section, filling in as many fields as possible
            self.load_data()
        
        # Tell the app to redraw stuff
        G.app.change()
    
    def load_data(self):
        # Load checkboxes
        for id in G.types[G.active_type]["checkboxes"].keys():
            gui.set_value("check/"+id, G.active["checkboxes"].get(id, False))

        # Load editable rows
        for item, row in G.app.edit_rows[G.active_type].items():
            try:
                # Load choices, without updating data
                row.reset_combo(False)

                # Load values
                if isinstance(row, edit_row.EditRow):
                    # Single edit row, load single value into combo
                    gui.set_value(row.combo, G.active["parts"].get(item, "").replace("_", " "))
                    row.change_combo(False)
                else:
                    # Multiple, load list instead into many combos
                    vals = G.active["parts"].get(item)
                    old_to_new = False
                    if not vals or type(vals) != list:
                        if type(vals) == str:
                            old_to_new = True
                            vals = [vals]
                        else:
                            vals = [""]
                        G.active["parts"][item] = vals
                    
                    colors = G.active["colors"].get(item)
                    if not colors or type(colors) != list:
                        if old_to_new:
                            colors = [colors]
                        else:
                            colors = [[]]
                            
                        G.active["colors"][item] = colors
                    
                    # Ensure that active length and current row count is the same
                    nl = len(vals)
                    ol = len(row.edit_rows)

                    if ol < nl:
                        # Need to add more edit rows
                        for i in range(ol, nl):
                            row.add_row(False)
                    elif ol > nl:
                        # Need to remove some edit rows
                        for i in range(nl, ol):
                            row.edit_rows[1].remove(False)
                    
                    # Load the value and color into every edit row
                    for n, r in enumerate(row.edit_rows):
                        # Value
                        gui.set_value(r.combo, vals[n].replace("_", " "))
                        r.change_combo(False)

            except Exception:
                log.warn(f'Failed to load combo(s) for "{G.active_type}/{row.item}"', exc_info=True)
