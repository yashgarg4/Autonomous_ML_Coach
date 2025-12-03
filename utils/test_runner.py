# utils/test_runner.py
import subprocess
import sys
import os
import re
from typing import Tuple

def normalize_test_imports(test_content: str, target_module: str = "generated_code") -> str:
    """
    Convert relative imports like:
      from . import foo
      from .module import foo
    into absolute imports referencing `target_module`, such as:
      from generated_code import foo
    This is a conservative heuristic to make tests runnable when the source file is saved as generated_code.py.
    """
    # 1) from . import name1, name2  -> from generated_code import name1, name2
    test_content = re.sub(r"(?m)^from\s+\.\s+import\s+(.+)$",
                          rf"from {target_module} import \1",
                          test_content)

    # 2) from .something import name -> from generated_code import name
    test_content = re.sub(r"(?m)^from\s+\.[\w_]+\s+import\s+(.+)$",
                          rf"from {target_module} import \1",
                          test_content)

    # 3) handle "from .module.sub import name" conservatively (map to target_module)
    test_content = re.sub(r"(?m)^from\s+\.[\w_.]+\s+import\s+(.+)$",
                          rf"from {target_module} import \1",
                          test_content)

    return test_content

def _normalize_test_placeholders(test_content: str, target_module: str = "generated_code") -> str:
    # Replace placeholder module names with the actual module
    test_content = test_content.replace("your_module_name", target_module)
    # Ensure relative imports are converted (already handled earlier)
    return test_content

def save_test_file(test_content: str, path: str = "test_generated.py") -> None:
    # Normalize relative imports to absolute imports for our generated code file
    normalized = normalize_test_imports(test_content, target_module="generated_code")
    normalized = _normalize_test_placeholders(normalized, target_module="generated_code")
    with open(path, "w", encoding="utf-8") as f:
        f.write(normalized)
    return

def run_pytest(test_path: str = "test_generated.py", timeout: int = 10) -> Tuple[int, str, str]:
    """
    Runs pytest on the given test file (in current directory).
    Returns (returncode, stdout, stderr).
    """
    cmd = [sys.executable, "-m", "pytest", "-q", "--disable-warnings", test_path]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "pytest timed out"
    except FileNotFoundError as e:
        return -2, "", f"pytest not found: {e}"
    except Exception as e:
        return -3, "", f"runtime error: {e}"

def make_test_runner_safe(test_content: str) -> str:
    """
    Sanity check to ensure tests won't try to do IO/network. 
    This is a very simple and conservative check scanning for suspicious tokens.
    If suspicious tokens found, prepend a warning header for manual review.
    """
    suspicious = ["requests", "socket", "subprocess", "os.system", "open(", "urllib", "ftplib", "paramiko"]
    lc = test_content.lower()
    for token in suspicious:
        if token in lc:
            header = f"# WARNING: test content contains suspicious token '{token}'. Please review before running.\n"
            return header + test_content
    return test_content
