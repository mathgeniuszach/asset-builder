from __future__ import annotations
import collections

from app import App

from collections import OrderedDict
import dearpygui.dearpygui as gui
from pathlib import Path
from time import sleep

from sys import stdout

import logging
import platform
import shutil
import py7zr
import threading
import json
import numpy
import xdialog
import webbrowser

from PIL import Image, ImageEnhance
from PIL.PngImagePlugin import PngInfo

# Strings
GITHUB = "https://github.com/xMGZx"
DISCORD = "https://discord.gg/pBFqEcXvW5"

SYSTEM = platform.system()
TITLE = "Asset Builder"
if SYSTEM == "Linux":
    SMALL_ICON = Path("i/icon-small.png")
    LARGE_ICON = Path("i/icon-large.png")
else:
    SMALL_ICON = Path("i/icon-small.ico")
    LARGE_ICON = Path("i/icon-large.ico")

AUTOSAVE = Path("autosave.json")
OPTIONS = Path("options.json")
PACKS = Path("packs")
LOG = Path("log.txt")
LOG_FORMAT = "[{asctime}] {levelname:<8}  {message}"
BACKGROUND_COLOR = (37, 37, 38)
VERSION = 1

SAFETY_LOCK = threading.Lock()
UPDATE_LOCK = threading.Lock()
RELOAD_LOCK = threading.Lock()

class NullWriter:
    def write(self, _): pass

# Create logger
LOG.unlink(True)
logging.basicConfig(
    stream=NullWriter(), # Because PIL logs to every single logger, for some reason.
    format=LOG_FORMAT,
    datefmt="%I:%M:%S",
    style="{",
    level=0
)
log = logging.getLogger("log")

log_formatter = logging.Formatter(
    LOG_FORMAT,
    datefmt="%I:%M:%S",
    style="{"
)

# Log to file
log_handler_file = logging.FileHandler(LOG)
log_handler_file.setLevel(10)
log_handler_file.setFormatter(log_formatter)
log.addHandler(log_handler_file)

# Also log to stdout
log_handler_out = logging.StreamHandler(stdout)
log_handler_out.setLevel(15)
log_handler_out.setFormatter(log_formatter)
log.addHandler(log_handler_out)

# Register 7zip stuff
shutil.register_archive_format("7zip", py7zr.pack_7zarchive, description="7zip archive")
shutil.register_unpack_format("7zip", [".7z"], py7zr.unpack_7zarchive)

# Merge dictionaries without overwriting
def merge_dict(a: dict, b: dict):
    """Adds the values in b whose keys are not in a, into a."""
    for k, v in b.items():
        if k not in a:
            a[k] = dict(v) if type(v) == OrderedDict else v

def merge_dict_lists(a: dict, b: dict):
    """
    Adds the values in b whose keys are not in a, into a.
    Also merges values one level deep of type list.
    """
    for k, v in b.items():
        if k not in a:
            a[k] = v
        elif type(a[k]) == list:
            a[k].extend(v)

def get_dict(d: dict, key, v):
    if key not in d:
        d[key] = v
    return d[key]

def get_abs_pos(w = None):
    w = w or gui.get_active_window()
    x = 0
    y = 0

    while w is not None:
        x2, y2 = gui.get_item_pos(w)
        x += x2
        y += y2
        w = gui.get_item_parent(w)
    
    return x, y

class G:
    # The main app class.
    app: App = None
    # A collection of image types generated by packs.
    types = {}
    # The data of everything loaded.
    data = {}
    # A collection of all loaded images.
    images = {}

    # Active type of the current tab.
    active_type = ""
    # The current data of whatever tab is selected.
    active = {}