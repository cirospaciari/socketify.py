import sys

vi = sys.version_info
if vi < (3, 7):
    raise RuntimeError('socketify requires Python 3.7 or greater')

if sys.platform in ('win32', 'cygwin', 'cli'):
    raise RuntimeError('socketify does not support Windows at the moment')

import setuptools
from setuptools.command.sdist import sdist
import pathlib
import os
import shutil
import subprocess

_ROOT = pathlib.Path(__file__).parent
UWS_DIR = str(_ROOT / "uWebSockets")
UWS_CAPI_DIR = str(_ROOT / "build" / "uWebSockets" / "capi")
UWS_LIB_PATH = str(_ROOT / "build" / "uWebSockets" / "capi" / "libuwebsockets.so")
UWS_BUILD_DIR = str(_ROOT / "build"/ "uWebSockets")
UWS_LIB_OUTPUT = str(_ROOT / "src" / "socketify" / "libuwebsockets.so")

class Makefile(sdist):
    def run(self):
        env = os.environ.copy()
        if os.path.exists(UWS_BUILD_DIR):
            shutil.rmtree(UWS_BUILD_DIR)
        shutil.copytree(UWS_DIR, UWS_BUILD_DIR)

        subprocess.run(["make", "shared"], cwd=UWS_CAPI_DIR, env=env, check=True)
        shutil.move(UWS_LIB_PATH, UWS_LIB_OUTPUT)
        super().run()


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="socketify",
    version="0.0.1",
    platforms=['macOS', 'POSIX'],
    author="Ciro Spaciari",
    author_email="ciro.spaciari@gmail.com",
    description="Fast WebSocket and Http/Https server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cirospaciari/socketify.py",
    project_urls={
        "Bug Tracker": "https://github.com/cirospaciari/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    package_data={"": ['./libuwebsockets.so']},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    cmdclass={'sdist': Makefile},
    include_package_data=True,
    install_requires=[]
)