# workflows/ml_coach.py
"""
Autonomous ML Coach workflow:
  - researcher -> coder -> save code -> syntax/run checks -> debugger
  - if debugger proposes a PATCH, optionally apply it and loop
  - stops when no PATCH suggested or max iterations reached

Usage:
  python workflows/ml_coach.py

Optional environment variables:
  AUTO_PATCH=1    # apply patches automatically (no prompt)
  MAX_ITERS=5     # change max self-correction iterations
  RUN_TIMEOUT=8   # seconds to run generated code for runtime checks
"""

import os
import time
import re

from agents.researcher import create_researcher_agent
from agents.coder import create_coder_agent
from agents.debugger import create_debugger_agent
from utils import inspector

# Utilities (similar helpers as earlier)
def extract_content(obj):
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "content"):
        return obj.content
    try:
        if isinstance(obj, dict) and "content" in obj:
            return obj["content"]
    except Exception:
        pass
    return str(obj)

def strip_code_fence(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    if s.startswith("```") and "```" in s[3:]:
        # remove first line fence token then closing fence
        parts = s.split("\n", 1)
        body_and_close = parts[1] if len(parts) > 1 else ""
        body = body_and_close.rsplit("```", 1)[0]
        return body.strip()
    return s

def extract_patch_from_debugger(text: str) -> str | None:
    """
    Extract the corrected file content that the Debugger placed under a fenced block labelled PATCH:
    e.g. ```PATCH\n<file content>\n```
    Returns the inner content string or None if not found.
    """
    if not text:
        return None
    # look for ```PATCH ... ```
    m = re.search(r"```PATCH\\s*(.*?)\\s*```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return None

def save_code(code: str, path="generated_code.py"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"[IO] Saved code -> {path}")

def run_iteration(researcher, coder, debugger, user_prompt, run_timeout):
    """
    Returns tuple:
      (final_decision, diagnostics_dict)
    final_decision: "no_patch" | "patch_applied" | "patch_skipped" | "max_iters_reached" | "error"
    diagnostics_dict contains keys:
      - research_text, code_text, syntax_ok, syntax_msg, run_stdout, run_stderr, debugger_output, patch_text (if any)
    """
    diagnostics = {}
    # 1. Researcher
    print("[STEP] Running Researcher...")
    r_out = researcher.run(user_prompt)
    r_text = extract_content(r_out)
    diagnostics["research_text"] = r_text
    print("[STEP] Researcher produced text (truncated):")
    print(r_text[:1000])

    # 2. Coder
    print("[STEP] Running Coder...")
    coder_prompt = "Based on this spec produce runnable Python code only (no extra explanation):\n\n" + r_text
    c_out = coder.run(coder_prompt)
    c_text = extract_content(c_out)
    c_text = strip_code_fence(c_text)
    diagnostics["code_text"] = c_text
    print("[STEP] Coder produced code (truncated):")
    print(c_text[:1000])

    # 3. Save + static + runtime checks
    save_code(c_text)
    syn_ok, syn_msg = inspector.run_syntax_check("generated_code.py")
    diagnostics["syntax_ok"] = syn_ok
    diagnostics["syntax_msg"] = syn_msg
    print("[CHECK] Syntax:", syn_msg)

    code_run_ret, run_stdout, run_stderr = inspector.run_file("generated_code.py", timeout=run_timeout)
    diagnostics["run_retcode"] = code_run_ret
    diagnostics["run_stdout"] = run_stdout
    diagnostics["run_stderr"] = run_stderr
    print("[RUN] return:", code_run_ret)
    print("[RUN] stdout (truncated):", run_stdout[:500])
    print("[RUN] stderr (truncated):", run_stderr[:500])

    # 4. Debugger analysis
    dbg_prompt = (
        "Analyze this Python file and the diagnostics below. List issues (numbered). "
        "If you propose a corrected full-file, provide it inside a fenced block labeled ```PATCH``` and nothing else inside that block.\n\n"
        f"CODE:\n{c_text}\n\n"
        f"SYNTAX_CHECK:\n{syn_msg}\n\n"
        f"RUNTIME_STDOUT:\n{run_stdout}\n\n"
        f"RUNTIME_STDERR:\n{run_stderr}\n\n"
        "Be concise and precise."
    )
    print("[STEP] Running Debugger (analysis)...")
    dbg_out = debugger.run(dbg_prompt)
    dbg_text = extract_content(dbg_out)
    diagnostics["debugger_output"] = dbg_text
    print("[DEBUGGER] out (truncated):")
    print(dbg_text[:1500])

    # look for patch
    patch_text = extract_patch_from_debugger(dbg_text)
    diagnostics["patch_text"] = patch_text

    return diagnostics

def autonomous_loop(user_prompt: str, max_iters: int = 3, run_timeout: int = 8):
    researcher = create_researcher_agent()
    coder = create_coder_agent()
    debugger = create_debugger_agent()

    auto_patch = os.environ.get("AUTO_PATCH", "") == "1"
    print(f"[CONFIG] AUTO_PATCH={auto_patch}, MAX_ITERS={max_iters}, RUN_TIMEOUT={run_timeout}s")

    for iteration in range(1, max_iters + 1):
        print(f"==== ITERATION {iteration} ====")
        try:
            diag = run_iteration(researcher, coder, debugger, user_prompt, run_timeout)
        except Exception as e:
            print("[ERROR] Exception during iteration:", e)
            return "error", {"exception": str(e)}

        # If no patch suggested, finish successfully
        if not diag.get("patch_text"):
            print("[RESULT] No PATCH suggested by Debugger. Workflow completed.")
            return "no_patch", diag

        # Patch suggested
        print("[RESULT] Debugger suggested a PATCH.")
        patch = diag["patch_text"]
        print("[PATCH preview]\n", patch[:1000])

        if auto_patch:
            print("[AUTO] Applying patch automatically (AUTO_PATCH=1).")
            inspector.apply_patch("generated_code.py", patch)
            print("[AUTO] Patch applied.")
            # loop will continue to next iteration to re-evaluate
            continue

        # Ask user interactively
        ans = input("Apply the suggested patch to generated_code.py? (y/n) ").strip().lower()
        if ans == "y":
            inspector.apply_patch("generated_code.py", patch)
            print("[USER] Patch applied.")
            continue
        else:
            print("[USER] Patch skipped. Ending workflow.")
            return "patch_skipped", diag

    print("[RESULT] Reached max iterations without converging.")
    return "max_iters_reached", {"last_diag": diag}

if __name__ == "__main__":
    # Example prompt — you can edit it or pass similar content from your UI/CLI
    prompt = (
        "Explain, at a high level, how transformer models work and give a short analogy. "
        "Then include a tiny coding task: write a Python function named `get_simple_token_length(text: str) -> int` "
        "that returns the whitespace-token count and a small usage example under `if __name__ == '__main__':`."
    )
    max_iters = int(os.environ.get("MAX_ITERS", "3"))
    run_timeout = int(os.environ.get("RUN_TIMEOUT", "8"))

    start = time.time()
    result_status, diagnostics = autonomous_loop(prompt, max_iters=max_iters, run_timeout=run_timeout)
    dur = time.time() - start
    print("\n==== WORKFLOW FINISHED ====")
    print("status:", result_status)
    print("duration:", f"{dur:.2f}s")
    # print summary keys
    for k in ("research_text", "code_text", "syntax_msg", "run_stdout", "run_stderr", "debugger_output"):
        if k in diagnostics:
            print(f"\n--- {k.upper()} (truncated) ---\n", str(diagnostics[k])[:1000])
    print("\nFinal generated file: generated_code.py")
