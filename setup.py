import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","wx"], "inludes":["wx"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).

base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
		"build_exe": {
			"excludes": ["Tkinter"],
			"append_script_to_exe":False,
			"build_exe":"build/bin",
			"compressed":True,
			"copy_dependent_files":True,
			"create_shared_zip":True,
			"include_in_shared_zip":True
		}
}

executables = [
		Executable(
			script="main.py",
			base=base,
			compress=True,
			copyDependentFiles=True,
			appendScriptToExe=True,
			appendScriptToLibrary=False,
			icon="Logo.ico",
			targetDir="build",
			targetName="SpiderScope.exe")
]

setup(  name = "SpiderScope",
        version = "1.0",
        description = "SpiderScope measurement software",
        options = options,
        executables = executables)
