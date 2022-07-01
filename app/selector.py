from .globals import *

from . import edit_row

class TypeSelector:
    def __init__(self):
        with gui.child_window(width=-1, height=-2):
            with gui.group(horizontal=True):
                gui.add_text("Type:")
                gui.add_combo([""], tag="type", width=-1, callback=lambda: self.change_type())
                gui.set_value("type", "")
            gui.add_separator()
            gui.add_child_window(tag="parts", autosize_x=True, autosize_y=True, border=False)
    
    def change_type(self):
        otype = G.active_type
        ntype = gui.get_value("type")

        if otype:
            gui.hide_item(f"parts/{G.active_type}")
        
        G.active_type = ntype

        if ntype:
            gui.show_item(f"parts/{ntype}")
            # Load defaults if no type was previously selected
            if not G.active["type"]:
                d = G.types[ntype]["default"]
                merge_dict(G.active["parts"], d.get("parts", {}))
                merge_dict(G.active["checkboxes"], d.get("checkboxes", {}))

            # Parse any data in the "active" section, filling in as many fields as possible
            self.load_data()

            # Load animation selections into the animate bar
            animations: dict[str, dict] = G.types[ntype]["animations"]
            if animations:
                gui.show_item("animatebar")
                items = [""]
                items.extend(k.replace("_", " ").title() for k in animations.keys())
                gui.configure_item(G.app.img_stack.animation, items=items)
            else:
                gui.hide_item("animatebar")
        else:
            gui.hide_item("animatebar")
        
        G.active["type"] = ntype
        
        # Tell the app to redraw stuff
        G.app.change()
    
    def load_data(self):
        # Load checkboxes
        for id in G.types[G.active_type]["checkboxes"].keys():
            gui.set_value("check/"+id, G.active["checkboxes"].get(id, False))

        # Load editable rows
        gparts: dict = G.active["parts"]
        gcolors: dict = G.active["colors"]
        for item, row in G.app.edit_rows[G.active_type].items():
            try:
                # Load choices, without updating data
                row.reset_combo(False)

                # Load values
                if isinstance(row, edit_row.EditRow):
                    # Single edit row, load single value into combo
                    # First ensure that key exists
                    v = gparts.get(item, "").replace("_", " ")
                    vs = row.curr_choices
                    if v not in vs:
                        xv = translate(v, vs)
                        if xv:
                            v = xv
                            gparts[item] = xv

                    # Then set value
                    gui.set_value(row.combo, v)
                    row.change_combo(False)
                else:
                    # Multiple, load list instead into many combos
                    vals = gparts.get(item)
                    old_to_new = False
                    if not vals or type(vals) != list:
                        if type(vals) == str:
                            old_to_new = True
                            vals = [vals]
                        else:
                            vals = [""]
                        gparts[item] = vals
                    
                    colors = gcolors.get(item)
                    if not colors or type(colors) != list:
                        if old_to_new:
                            colors = [colors]
                        else:
                            colors = [[]]
                            
                        gcolors[item] = colors
                    
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
                    vs = row.edit_rows[0].curr_choices
                    for n, r in enumerate(row.edit_rows):
                        # First ensure that key exists
                        v = vals[n].replace("_", " ")
                        if v not in vs:
                            xv = translate(v, vs)
                            if xv:
                                v = xv
                                vals[n] = xv
                        
                        # Then set value
                        gui.set_value(r.combo, v)
                        r.change_combo(False)

            except Exception:
                log.warn(f'Failed to load combo(s) for "{G.active_type}/{row.item}"', exc_info=True)

# Translate names like "{Asset}", "{Asset}_1", and "{Asset}_1A" into each other.
def translate(name: str, items: set):
    # No need to translate if the name exists in options.
    if name in items: return name
    if not name: return ''

    # Acquire number and letter suffix if they exist
    sname = name.split()
    if len(sname) == 1:
        # No suffix, check if one with starting suffix does exist
        if name + "_1"  in items: return name + "_1"
        if name + "_A"  in items: return name + "_A"
        if name + "_1A" in items: return name + "_1A"
    else:
        suffix = sname[-1]
        if suffix[-1].isalpha():
            if len(suffix) == 1:
                # In the form {Asset}_L
                bname = ''.join(sname[:-1])
                l = suffix[-1].upper()

                # Check for {Asset}_1L
                if bname + "_1" + l in items: return bname + "_1" + l
                # If form is {Asset}_A, Check for {Asset}
                if l == 'A' and bname in items: return bname
            elif suffix[:-1].isdigit():
                # In the form {Asset}_#L
                bname = ''.join(sname[:-1])
                num = int(suffix[:-1])
                l = suffix[-1].upper()

                if num == 1:
                    # In the form is {Asset}_1L
                    # If form is {Asset}_1A, Check for {Asset}
                    if l == 'A' and bname in items: return bname
                    # Check for {Asset}_L
                    if bname + "_" + l in items: return bname + "_" + l
                elif l == 'A':
                    # In the form {Asset}_#A
                    # Check for {Asset}_#
                    if bname + "_" + str(num) in items: return bname + "_" + str(num)
            else:
                # No suffix, check if one with starting suffix does exist
                if name + "_1"  in items: return name + "_1"
                if name + "_A"  in items: return name + "_A"
                if name + "_1A" in items: return name + "_1A"
                    
        elif suffix.isdigit():
            # In the form {Asset}_#
            # Check for {Asset}_#A
            if name + "A" in items: return name + "A"

            bname = ''.join(sname[:-1])
            num = int(suffix)

            # If form is {Asset}_1, Check for {Asset}
            if num == 1 and bname in items: return bname
        else:
            # No suffix, check if one with starting suffix does exist
            if name + "_1"  in items: return name + "_1"
            if name + "_A"  in items: return name + "_A"
            if name + "_1A" in items: return name + "_1A"
    
    # If we can't find anything, return give up signal
    return ''