# utils/inspector.py
import subprocess
import sys
import py_compile
import os

def run_syntax_check(path: str):
    try:
        py_compile.compile(path, doraise=True)
        return True, "Syntax OK"
    except py_compile.PyCompileError as e:
        return False, str(e)

def run_flake8(path: str):
    try:
        completed = subprocess.run(
            ["flake8", path], capture_output=True, text=True, timeout=10
        )
        if completed.returncode == 0:
            return True, "Flake8: No issues found"
        else:
            return False, completed.stdout + completed.stderr
    except FileNotFoundError:
        return False, "flake8 not installed"

def run_file(path: str, timeout: int = 10):
    try:
        completed = subprocess.run(
            [sys.executable, path], capture_output=True, text=True, timeout=timeout
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Execution timed out"
    except Exception as e:
        return -2, "", f"Runtime error: {e}"

def apply_patch(path: str, patch_text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(patch_text)
    return True
