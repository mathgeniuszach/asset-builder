from .globals import *

import subprocess

class MessageBox:
    def __init__(self, text, tag, buttons=["Ok"], callback=None):
        self.callback = callback
        self.tag = tag

        with gui.popup(G.app.nonbutton, modal=True, tag=tag):
            gui.add_text(text)
            with gui.group(horizontal=True):
                for label in buttons:
                    gui.add_button(label=label, tag=f"{tag}-{label}", callback=self.clicked)
        
        self.showing = False
        self.modalsize = [-1, -1]

        # HACK: Visibility handler that is only used twice (that is, until the system is sure what size the modal is)
        with gui.item_handler_registry(tag=tag+"-handler"):
            gui.add_item_visible_handler(callback=self.on_show)
        gui.bind_item_handler_registry(tag, tag+"-handler")

    def on_show(self):
        # HACK: Necessary to have this run twice, because the modal's size isn't determined until the first frame it's drawn.
        if self.showing:
            modalsize = gui.get_item_rect_size(self.tag)
            winsize = gui.get_item_rect_size("root")

            if modalsize == self.modalsize:
                self.showing = False
                gui.set_item_pos(self.tag, ((winsize[0] - modalsize[0]) // 2, (winsize[1] - modalsize[1]) // 2))
            else:
                self.modalsize = modalsize

    def clicked(self, sender: str):
        try:
            if self.callback:
                self.callback(sender[sender.index("-")+1:])
        finally:
            gui.hide_item(self.tag)
    
    def show(self):
        self.showing = True
        gui.show_item(self.tag)

    def hide(self):
        gui.hide_item(self.tag)