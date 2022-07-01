# from dearpygui.demo import show_demo

import ctypes

class App:
    def __init__(self, win):
        G.app = self
        
        self.edit_rows: dict[str, dict[str, Union[edit_row.EditRow, edit_row.MultiEditRow]]] = {}

        # Update thread
        log.debug("Loading update thread")
        self.running = True
        self.updates = 0
        self.animation_updates = 0
        self.updater = threading.Thread(target=self.update)
        self.timer = threading.Thread(target=self.time)
        self.last_time = process_time_ns() // 1000000

        # Themes
        log.debug("Loading themes")
        with gui.theme() as self.theme:
            with gui.theme_component(gui.mvMenuItem, enabled_state=False):
                gui.add_theme_color(gui.mvThemeCol_Text, (128, 128, 128))
            
            gui.bind_theme(self.theme)
        
        with gui.theme() as self.hide_theme:
            with gui.theme_component(gui.mvButton, enabled_state=False):
                gui.add_theme_color(gui.mvThemeCol_Button, BACKGROUND_COLOR, category=gui.mvThemeCat_Core)
                gui.add_theme_color(gui.mvThemeCol_ButtonActive, BACKGROUND_COLOR, category=gui.mvThemeCat_Core)
                gui.add_theme_color(gui.mvThemeCol_ButtonHovered, BACKGROUND_COLOR, category=gui.mvThemeCat_Core)
        
        with gui.theme() as self.invert_theme:
            with gui.theme_component(gui.mvText):
                gui.add_theme_color(gui.mvThemeCol_Text, (0, 0, 0))
            
        with gui.theme() as self.hyper_theme:
            with gui.theme_component(gui.mvButton):
                gui.add_theme_color(gui.mvThemeCol_Button, (0, 0, 0, 0))
                gui.add_theme_color(gui.mvThemeCol_ButtonActive, (0, 0, 0, 0))
                gui.add_theme_color(gui.mvThemeCol_ButtonHovered, (29, 151, 236, 25))
                gui.add_theme_color(gui.mvThemeCol_Text, (29, 151, 236))
        
        # Font and texture
        log.debug("Loading font")
        with gui.font_registry():
            gui.bind_font(gui.add_font("i/Roboto.ttf", 20))
            if SYSTEM == "Windows":
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
        
        gui.add_texture_registry(tag="texreg")
        
        # Window elements
        with win:
            # Helps and packs windwos
            log.debug("Loading help and packs windows")
            self.help = help_win.HelpWindow()
            self.packs = packs_win.PacksWindow()

            # Nonbutton
            self.nonbutton = gui.add_button(label="", show=False)

            # Menu Bar
            log.debug("Creating menu bar")
            self.menu_bar = menu_bar.MenuBar()
            
            # Tabs
            log.debug("Creating tab bar")
            self.tab_bar = tab_bar.TabBar()
            
            # Horizontal splitter
            with gui.table(header_row=False, resizable=True):
                gui.add_table_column()
                gui.add_table_column(width_fixed=True, init_width_or_weight=400)
                
                with gui.table_row():
                    # Image display
                    log.debug("Creating image stacker")
                    self.img_stack = image.ImageStacker()

                    # Choices
                    log.debug("Creating type selector")
                    self.selector = selector.TypeSelector()

            # Load packs, gui, and autosave.
            load_packs.reload()
        
        # show_demo()
        self.updater.start()
        self.timer.start()
    
    def change(self):
        # Tells the side thread to update.
        with UPDATE_LOCK:
            self.updates = 1
            self.animation_updates = 1

        # Mark the active file as "unsaved"
        G.active["saved"] = False
    
    def animation_change(self):
        # Tells the side thread to update the animation
        with UPDATE_LOCK:
            self.animation_updates = 1
    
    def update(self):
        while self.running or self.updates:
            # Delay to give time for the locks to be used by other stuff
            sleep(0.05)
            
            if self.updates > 0:
                # Don't run at the same time as a reload
                with RELOAD_LOCK:
                    # Confirm update
                    with UPDATE_LOCK:
                        self.updates -= 1
                    
                    # Write autosave
                    if gui.get_value("autosave"):
                        try:
                            with AUTOSAVE.open("w", encoding="utf-8") as file:
                                json.dump(G.data, file)
                        except Exception:
                            log.error("Autosave failed, disabling it.", exc_info=True)
                            gui.set_value("autosave", False)
                        
                    # Load image
                    try:
                        self.img_stack.update_image()
                    except Exception:
                        log.error("Failed to update active data.", exc_info=True)
            
            if self.animation_updates > 0:
                with RELOAD_LOCK:
                    with UPDATE_LOCK:
                        self.animation_updates -= 1
                    
                    try:
                        self.img_stack.update()
                    except Exception:
                        log.error("Failed to upload active data.", exc_info=True)
    
    def time(self):
        while self.running:
            sleep(0)
            ntime = process_time_ns() // 1000000
            delta = ntime - self.last_time
            if delta:
                self.img_stack.update_animation(delta)
                self.last_time = ntime
    
    def close(self):
        self.running = False
        self.timer.join()
        self.updater.join()


from .globals import *

from . import menu_bar
from . import tab_bar
from . import load_packs
from . import edit_row
from . import image
from . import selector
from . import help_win
from . import packs_win

from typing import Union