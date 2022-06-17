from .globals import *

SPECIAL = set(("name", "desc", "for", "version"))

class PacksWindow:
    def __init__(self):
        with gui.window(label="Packs", tag="packswin", width=500, height=400, show=False):
            pass
    
    def build(self, packs: list[dict]):
        if gui.does_item_exist("packswin"):
            gui.delete_item("packswin", children_only=True)
        
        for pack in packs:
            with gui.collapsing_header(
                label=f'{pack.get("name", "Unnamed")} {pack["version"] if "version" in pack else ""}',
                parent="packswin"
            ):
                # Add pack items if available
                with gui.table(header_row=False):
                    gui.add_table_column(width_fixed=True)
                    gui.add_table_column()

                    for k, v in pack.items():
                        if k not in SPECIAL:
                            with gui.table_row():
                                name = k.replace("_", " ").title()
                                if type(v) == list:
                                    gui.bind_item_theme(
                                        gui.add_button(label=name, indent=0, callback=(lambda x: lambda: webbrowser.open(x))(v[0])),
                                        G.app.hyper_theme
                                    )
                                    gui.add_spacer()
                                else:
                                    gui.add_text(name+":")
                                    gui.add_text(v)

                # Add description if available
                if "desc" in pack:
                    gui.add_text(pack["desc"], wrap=0)
    
    def show(self):
        gui.show_item("packswin")