try:
    import nuitka
except ModuleNotFoundError:
    print("Nuitka not found on system; please install nuitka to build this project")
    exit(1)

import subprocess
import platform
import shutil

from pathlib import Path

opts = (
    "asset_builder.py",
    "--standalone", "--onefile",

    "--enable-plugin=numpy",

    "--nofollow-import-to=PySide2",
    "--nofollow-import-to=PySide5",
    "--nofollow-import-to=PySide6",
    "--nofollow-import-to=Qt5",
    "--nofollow-import-to=PyQt5",
    "--nofollow-import-to=curses",

    "--noinclude-custom-mode=PySide2:nofollow",
    "--noinclude-custom-mode=PySide5:nofollow",
    "--noinclude-custom-mode=PySide6:nofollow",
    "--noinclude-custom-mode=Qt5:nofollow",
    "--noinclude-custom-mode=PyQt5:nofollow",
    "--noinclude-custom-mode=curses:nofollow",
)

SYSTEM = platform.system()
if SYSTEM == "Windows":
    subprocess.call((
        "nuitka", *opts,
        "--windows-icon-from-ico=i\\icon-large.ico",
        "--windows-disable-console"
    ), shell=True)
else:
    subprocess.call((
        "nuitka3", *opts, "--clang"
    ), shell=False)