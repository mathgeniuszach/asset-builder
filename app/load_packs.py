from .globals import *

from . import edit_row

import yaml
import tempfile

nonbutton = None

def find_pack(path: Path):
    if (path / "meta.yaml").is_file():
        return path
    
    for p in path.iterdir():
        if p.is_dir():
            return find_pack(p)
    
    return None

def acquire_pack(packs: list, path: Path, name):
    log.info(f'Loading pack "{name}"')
    try:
        # Locate the pack's meta file, and use that as the root directory
        # (Since windows likes to archive a pack folder into a zip with an extra directory)
        f: Path = find_pack(path)
        if f is None: raise ValueError('could not find "meta.yaml" in pack.')

        # Do not load packs made for newer versions.
        meta = f / "meta.yaml"
        with meta.open() as metafile:
            ver = yaml.safe_load(metafile).get("for", VERSION)
            if ver > VERSION:
                raise ValueError(f'pack is made for newer version of tool (pack: {ver} > tool: {VERSION})')

        # Iterate over types and collect type packs
        for typ in f.iterdir():
            if typ.is_dir() and (typ / "meta.yaml").is_file():
                # Load meta.yaml
                with (typ / "meta.yaml").open("r", encoding="utf-8") as file:
                    ndata: dict = dict(yaml.safe_load(file))
                packs.append((ndata.get("priority", 0), typ, ndata, name))
    except Exception as e:
        log.warn(f'Failed to load pack "{name}"', exc_info=True)
        xdialog.warning(message=f'Failed to load pack "{name}";\n{e.__class__.__name__}: {e}')

def reload():
    log.info("Loading packs")
    gui.disable_item("reload")

    with RELOAD_LOCK:
        # Clear any existing items
        gui.delete_item("parts", children_only=True)
        types = G.types
        types.clear()

        packs: list[tuple[float, Path, bool, dict]] = []

        try:
            # Ensure that packs folder exists
            if not PACKS.is_dir():
                PACKS.unlink(missing_ok=True)
                PACKS.mkdir(parents=True)
            
            tmps = []
            try:
                # Load content into packs to be processed.
                for f in PACKS.iterdir():
                    if f.is_dir():
                        # If the pack is a directory, get it directly
                        log.debug(f'Discovered unzipped pack {f.name}')
                        acquire_pack(packs, f, f.name)
                    elif f.is_file():
                        # The pack is a file, it must be an archive of some kind.
                        # We'll extract it using shutil temporarily. use acquire_pack on it, then delete it.
                        try:
                            tmp = tempfile.mkdtemp()
                            tmps.append(tmp)
                            shutil.unpack_archive(str(f.absolute()), tmp)
                            log.debug(f'Discovered zipped pack {f.name}')
                            acquire_pack(packs, Path(tmp), f.name)
                        except Exception:
                            log.warn(f'Unknown pack "{f.name}"', exc_info=True)
                
                # Process packs
                # Sort it so high priority loads first
                # (nothing will be able to overwrite previous values, so this is faster)
                log.info("Merging packs")
                packs.sort(key=lambda v: v[0], reverse=True)

                # First pass for metadata.
                for _, typ, tdata, packname in packs:
                    try:
                        tname = str(typ.name).replace("_", " ")
                        old = get_dict(types, tname, {"draw_order": {}, "default": {}, "checkboxes": {}, "groups": {}, "parts": {}, "filters": []})

                        # Process metadata
                        for k in ("draw_order", "checkboxes"):
                            if k in tdata:
                                merge_dict(old[k], tdata[k])
                        
                        if "default" in tdata:
                            odef = old["default"]
                            ndef = tdata["default"]

                            for k in ndef.keys():
                                if k in odef:
                                    merge_dict(odef[k], ndef[k])
                                else:
                                    odef[k] = ndef[k]
                        
                        if "filters" in tdata:
                            old["filters"].extend(tdata["filters"])
                        
                        if "groups" in tdata:
                            merge_dict_lists(old["groups"], tdata["groups"])
                        
                        if "size" not in old:
                            if "size" in tdata and type(tdata["size"]) == list and len(tdata["size"]) == 2:
                                old["size"] = tuple(tdata["size"])
                    except Exception:
                        log.error(f'Failed to load metadata for type "{tname}" in pack {packname}', exc_info=True)
                
                # Second pass for parts.
                for _, typ, tdata, packname in packs:
                    try:
                        tname = str(typ.name).replace("_", " ")
                        old = types[tname]
                        if "size" not in old:
                            old["size"] = (256, 256)

                        # Process parts
                        for part in typ.iterdir():
                            if part.is_dir():
                                load_part(part, get_dict(old["parts"], str(part.name), {}), old["size"])
                    except Exception:
                        log.error(f'Failed to load parts for type "{tname}" in pack {packname}', exc_info=True)

                # Third pass for part dependent values.
                for typ, tdata in types.items():
                    dependents = {}

                    parts: dict = tdata["parts"]
                    for part, pdata in parts.items():
                        l = get_dict(pdata, "/depends", [])
                        get_dependencies(part, pdata, dependents, l)
                    
                    for part, pdata in parts.items():
                        pdata["/dependents"] = dependents.get(part, [])

            finally:
                # Delete all temporarily extracted packs
                if tmps: log.debug("Deleting archive for pack")
                for tmp in tmps:
                    shutil.rmtree(tmp)
        
        except Exception as e:
            log.error("Failed to load packs.", exc_info=True)
            xdialog.error(message=f"Failed to load packs;\n{e.__class__.__name__}: {str(e)}")
        
        # Build gui
        build_gui(G.app.edit_rows)

        # Load auto-save data
        if AUTOSAVE.is_file():
            log.info("Loading autosave")
            with AUTOSAVE.open("r", encoding="utf-8") as file:
                G.data = json.load(file)

        # Load the tab bar
        log.debug("Loading tab bar")
        G.app.tab_bar.load_tabs()

        log.info("Finished loading packs")

def get_dependencies(part: str, pdata: dict, rdict: dict, l: list):
    depends = pdata.get("/meta", {}).get("depends", "")
    if not depends: return

    if depends not in l:
        l.append(depends)
        get_dict(rdict, depends, []).append(part)

    for v in pdata.values():
        if isinstance(v, dict) and "/meta" in v:
            get_dependencies(part, v, rdict, l)
        

def load_part(path: Path, old: dict, size: list[int]):
    log.debug(f'Loading part data at "{path}"')

    # Load meta file
    if (path / "meta.yaml").is_file():
        with (path / "meta.yaml").open("r", encoding="utf-8") as file:
            meta = dict(yaml.safe_load(file))
            # Store as "/meta" key, since files cannot have slashes in name.
            merge_dict(get_dict(old, "/meta", {}), meta)
    
    # Load content (recursively)
    for f in path.iterdir():
        if f.is_dir():
            # Directories are loaded recursively.
            load_part(f, get_dict(old, str(f.name), {}), size)
        elif f.is_file():
            if f.suffix != ".yaml":
                # Files should normally be images, load it like an image, but also handle layers
                inamez = str(f.stem).split()
                base = old.get(inamez[0])

                try:
                    img: Image.Image = Image.open(str(f))

                    if img.size != size:
                        log.warn(f'Image "{f}" has size {img.width}x{img.height}, expected {size[0]}x{size[1]}; skipping')
                        continue

                    if len(inamez) == 1:
                        # This image is a base image.
                        if type(base) == list:
                            if not base[0]:
                                # If base is a list and 0 is not loaded, overlay loaded first.
                                img.load()
                                base[0] = img
                        elif not base:
                            # Otherwise, only load if base has not been loaded yet.
                            img.load()
                            old[inamez[0]] = img
                    else:
                        # This image is not a base image. Rather, it's an overlay.
                        i = 1 if inamez[1] == "overlay" else int(inamez[1][-1:])
                        if not base:
                            # Base has not been loaded, do the loading
                            img.load()
                            base = [0] * i
                            base.append(img)
                            old[inamez[0]] = base
                        else:
                            if type(base) != list:
                                # Base is not a list, so it must be the base image. turn it into a list.
                                base = [base]
                                old[inamez[0]] = base
                            
                            # Base should now be a list.
                            if len(base) == i:
                                # Base is one less than index, just append
                                img.load()
                                base.append(img)
                            elif len(base) < i:
                                # Base size is less than index, perform list resize
                                for _ in range(i - len(base)):
                                    base.append(0)
                                img.load()
                                base.append(img)
                            elif not base[i]:
                                # Base list has been resized, but this overlay slot has not been loaded yet.
                                img.load()
                                base[i] = img
                            
                            old[inamez[0]] = base
                except Exception:
                    log.error(f'Unknown image "{f}".')


def build_gui(edit_rows):
    log.debug("Building GUI")

    # Insert types into combo box
    stypes = sorted(G.types.keys())
    stypes.insert(0, "")
    gui.configure_item("type", items=stypes)

    # Each type has a separate, hidden child window.
    for typ, tdata in G.types.items():
        with gui.child_window(parent="parts", tag=f"parts/{typ}", autosize_x=True, autosize_y=True, border=False, show=False):
            log.debug(f'Building gui for type "{typ}"')
            parts = tdata.get("parts", {})
            trows = get_dict(edit_rows, typ, {})

            # Create checkboxes
            for id, text in tdata["checkboxes"].items():
                log.debug(f'Building checkbox "{id}"')
                edit_row.Checkbox(id, text)
            
            gui.add_separator()

            loaded = set()
            
            # Going through each group is how things are created
            for g, items in sorted(tdata["groups"].items(), key=lambda x: x[0]):
                if g != "_":
                    log.debug(f'Building group "{g}"')
                    with gui.table(header_row=False, no_pad_innerX=True):
                        gui.add_table_column(init_width_or_weight=110)
                        gui.add_table_column(init_width_or_weight=180)
                        gui.add_table_column(width_fixed=True, init_width_or_weight=108) # 24*4 + 3*4

                        for item in items:
                            try:
                                # Handle duplicates
                                if item in loaded: raise ValueError("Duplicate item in groups")
                                loaded.add(item)

                                # Build edit rows based on items
                                part = parts[item]
                                meta = part.get("/meta", {})
                                if not meta.get("disabled"):
                                    if meta.get("multiple", False):
                                        log.debug(f'Building multi edit "{item}"')
                                        trows[item] = edit_row.MultiEditRow(typ, item, part)
                                    else:
                                        log.debug(f'Building single edit "{item}"')
                                        trows[item] = edit_row.EditRow(typ, item, part)
                            except Exception:
                                log.warn(f'Failed to build GUI for "{typ}/{item}"', exc_info=True)

                    gui.add_separator()

    gui.enable_item("reload")