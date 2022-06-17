try:
    import nuitka
except ModuleNotFoundError:
    print("Nuitka not found on system; please install nuitka to build this project")
    exit(1)

import subprocess
import platform
import shutil

from pathlib import Path


SYSTEM = platform.system()
if SYSTEM == "Linux":
    subprocess.call((
        "nuitka3", "asset_builder.py",
        "--standalone", "--onefile", "--clang",

        "--enable-plugin=numpy",

        "--nofollow-import-to=PySide2",
        "--nofollow-import-to=PySide5",
        "--nofollow-import-to=PySide6",
        "--nofollow-import-to=Qt5",
        "--nofollow-import-to=PyQt5",
        "--nofollow-import-to=curses",
        "--nofollow-import-to=email",

        "--noinclude-custom-mode=PySide2:nofollow",
        "--noinclude-custom-mode=PySide5:nofollow",
        "--noinclude-custom-mode=PySide6:nofollow",
        "--noinclude-custom-mode=Qt5:nofollow",
        "--noinclude-custom-mode=PyQt5:nofollow",
        "--noinclude-custom-mode=curses:nofollow",
        "--noinclude-custom-mode=email:nofollow",
    ), shell=False)
elif SYSTEM == "Windows":
    ...
else:
    print("Dunno how to build for this system.")