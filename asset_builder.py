#!/usr/bin/env python3

# A script for building character sprites out of paperdolls.

from app.globals import *
import app

def main():
    try:
        log.info("Initializing")
        gui.create_context()
        
        iapp = app.App(gui.window(tag="root", no_scrollbar=True))
        
        gui.create_viewport(title=TITLE, small_icon=str(SMALL_ICON), large_icon=str(LARGE_ICON))
        gui.setup_dearpygui()
        gui.show_viewport()
        gui.set_primary_window("root", True)

        log.info("Finished initialization")
        try:
            while gui.is_dearpygui_running():
                gui.render_dearpygui_frame()
        finally:
            log.info("Exiting")
            gui.destroy_context()
            iapp.close()
        
        return 0
    except Exception as e:
        log.error("An unknown error occurred.", exc_info=True)
        print(f"An unknown error occurred and the program must exit;\n{e.__class__.__name__}: {str(e)}")
        xdialog.error(message=f"An unknown error occurred and the program must exit;\n{e.__class__.__name__}: {str(e)}")
        return 1
    except KeyboardInterrupt:
        try: iapp.close()
        except NameError: pass

if __name__ == "__main__":
    err = main()
    if err: exit(err)