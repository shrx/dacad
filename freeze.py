"""Package freezing for Windows."""

import os
import re

from cx_Freeze import Executable, setup

with open(os.path.join("dacad", "__init__.py"), "rt") as f:
    version_match = re.search('__version__ = "([^"]+)"', f.read())
assert version_match is not None
version = version_match.group(1)

build_exe_options = {"includes": [], "packages": [], "optimize": 0}

setup(
    name="dacad",
    version=version,
    author="desbma",
    packages=["dacad"],
    options={"build_exe": build_exe_options},
    executables=[
        Executable(os.path.join("dacad", "__main__.py"), target_name="dacad.exe"),
        Executable(os.path.join("dacad", "recurse.py"), target_name="dacad_r.exe"),
    ],
)
