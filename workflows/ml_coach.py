"""
Autonomous ML Coach workflow (final):
  - researcher -> coder (with sanitizer + retries) -> save code
  - inspector (syntax + run)
  - test-writer -> save tests -> pytest
  - debugger analyzes diagnostics and may suggest PATCH
  - if syntax failed and debugger provided a PATCH, auto-apply PATCH once (safe)
  - optionally prompt user to apply further PATCHes or use AUTO_PATCH=1
"""

import os
import re
import time
from typing import Tuple

# Agents & utils (ensure your project exposes these modules)
from agents.researcher import create_researcher_agent
from agents.coder import create_coder_agent
from agents.debugger import create_debugger_agent
from agents.test_writer import create_test_writer_agent
from utils import inspector
from utils import test_runner

# ---- Helpers --
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
    # If it's a fenced block, remove fence and return inner content
    fence_match = re.search(r"```(?:python)?\n(.*?)\n```", s, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    # otherwise remove leading/trailing triple-backticks if present
    s = re.sub(r"^```(?:python)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s, flags=re.IGNORECASE)
    return s

def save_code(text: str, path: str = "generated_code.py"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[IO] Saved code -> {path}")

# ---- Sanitizer + coder retry logic ----
MAX_CODER_RETRIES = 2
STRICT_CODER_SUFFIX = (
    "\n\nIMPORTANT: Output ONLY valid Python source. No prose outside of a single top-level module docstring. "
    "Do NOT use triple-backticks. If you include function docstrings they MUST be triple-quoted. End with valid code."
)

def _clean_docstring_noise(code: str) -> str:
    if not code:
        return code
    # Replace multiple adjacent triple-quote sequences with one
    code = re.sub(r'(["\']{3}){2,}', r'\1', code)
    # If starts with single triple quote and not closed, close it
    if code.startswith('"""') and code.count('"""') == 1:
        code = code + '\n"""'
    if code.startswith("'''") and code.count("'''") == 1:
        code = code + "\n'''"
    # Remove stray triple-quote-only lines
    code = re.sub(r'^[ \t]*("{3}|\'{3})[ \t]*$', '', code, flags=re.MULTILINE)
    # Collapse duplicated docstrings
    code = re.sub(r'("""\s*""")+', '"""', code)
    return code.strip()

def sanitize_generated_code(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    # 1) prefer fenced block
    fence_match = re.search(r"```(?:python)?\n(.*?)\n```", s, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        code = fence_match.group(1).strip()
        return _clean_docstring_noise(code)
    # 2) remove lines that are exactly quote sequences
    s = re.sub(r'^[ \t]*("{3,}|\'{3,})[ \t]*$', '', s, flags=re.MULTILINE)
    # 3) accidental '"""def' -> remove leading quotes
    s = re.sub(r'^(?P<q>["\']{3,})\s*(?=(def |class |import |from ))', '', s, count=1)
    # 4) find first python code token
    token_search = re.search(r'\b(def |class |import |from )', s)
    if token_search:
        pos = token_search.start()
        leading = s[:pos].strip()
        code_part = s[pos:].lstrip()
        if leading:
            leading = re.sub(r'(^```(?:python)?\s*|\s*```$)', '', leading, flags=re.IGNORECASE).strip()
            leading = re.sub(r'(^["\']{3,}\s*|\s*["\']{3,}$)', '', leading).strip()
            leading = re.sub(r'\n\s*\n+', '\n\n', leading).strip()
            doc = '"""' + leading + '"""' + "\n\n"
            cleaned = doc + _clean_docstring_noise(code_part)
            return cleaned
        else:
            return _clean_docstring_noise(code_part)
    # 5) no tokens found -> strip fences and return best-effort
    s = re.sub(r'(^```(?:python)?\s*|\s*```$)', '', s, flags=re.IGNORECASE).strip()
    s = _clean_docstring_noise(s)
    return s

def _looks_like_valid_python(code: str) -> bool:
    if not code or len(code.strip()) < 5:
        return False
    if re.search(r'\b(def |class |import |from )', code):
        first_line = next((ln for ln in code.splitlines() if ln.strip()), "")
        if first_line.startswith('"""') or first_line.startswith("'''"):
            return True
        if re.search(r'[^\w\s"#:()\[\],.+*/=<>-]', first_line):
            return True
        if 'def ' in first_line or 'class ' in first_line:
            return True
        return True
    return False

def run_coder_with_retries(coder_agent, base_coder_prompt: str) -> str:
    attempt = 0
    sanitized = ""
    while attempt <= MAX_CODER_RETRIES:
        attempt += 1
        if attempt == 1:
            raw_out = coder_agent.run(base_coder_prompt)
        else:
            raw_out = coder_agent.run(base_coder_prompt + "\n\n" + STRICT_CODER_SUFFIX)
        last_raw = extract_content(raw_out)
        last_raw = strip_code_fence(last_raw)
        sanitized = sanitize_generated_code(last_raw)
        if _looks_like_valid_python(sanitized):
            return sanitized
        time.sleep(0.3)
    return sanitized

# ---- Fix simple unquoted docstrings inside functions ----
def fix_unquoted_docstrings(code: str) -> str:
    if not code:
        return code
    lines = code.splitlines()
    out_lines = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        out_lines.append(line)
        m = re.match(r'^(\s*)def\s+\w+\s*\(.*\)\s*:\s*$', line)
        if m:
            indent = m.group(1) + "    "
            j = i + 1
            while j < n and lines[j].strip() == "":
                out_lines.append(lines[j])
                j += 1
            doc_lines = []
            while j < n:
                nxt = lines[j]
                if not nxt.startswith(indent) and nxt.strip() != "":
                    break
                stripped = nxt[len(indent):] if nxt.startswith(indent) else nxt.lstrip()
                if re.match(r'^(?:return\b|if\b|for\b|while\b|with\b|assert\b|import\b|from\b|def\b|class\b)', stripped):
                    break
                if stripped.startswith('"""') or stripped.startswith("'''") or stripped.startswith('"') or stripped.startswith("'"):
                    break
                doc_lines.append(stripped)
                j += 1
            doc_lines_clean = [dl.rstrip() for dl in doc_lines]
            non_empty = [dl for dl in doc_lines_clean if dl.strip() != ""]
            if len(non_empty) >= 1:
                remove_count = 0
                while remove_count < (j - (i + 1)):
                    out_lines.pop()
                    remove_count += 1
                docstring = '\n'.join(non_empty)
                docstring_lines = [indent + '"""' + (docstring.splitlines()[0] if docstring else "")]
                rem = docstring.splitlines()[1:]
                for l in rem:
                    docstring_lines.append(indent + l)
                docstring_lines.append(indent + '"""')
                for dl in docstring_lines:
                    out_lines.append(dl)
                if j < n and lines[j].strip() != "":
                    out_lines.append(indent.rstrip())
                i = j - 1
        i += 1
    return "\n".join(out_lines)

# ---- Patch extractor utility ----
def extract_patch_from_debugger(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"```PATCH\s*(.*?)\s*```", text, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return None

# ---- One iteration runner ----
def run_iteration(researcher, coder, test_writer, debugger, user_prompt, run_timeout):
    """Runs one full iteration and yields status updates."""
    yield {"message": "[STEP] Running Researcher..."}
    r_out = researcher.run(user_prompt)
    r_text = extract_content(r_out)
    yield {"message": "[STEP] Researcher produced text.", "research_text": r_text}

    # Coder (with retries + sanitizer)
    yield {"message": "[STEP] Running Coder (with sanitizer + retries)..."}
    base_coder_prompt = "Based on this spec produce runnable Python code only (no extra explanation):\n\n" + r_text
    c_text = run_coder_with_retries(coder, base_coder_prompt)
    # additional protective fixes
    c_text = fix_unquoted_docstrings(c_text)
    yield {"message": "[STEP] Coder produced sanitized code.", "code_text": c_text}

    # Save + static + runtime checks
    save_code(c_text)
    syn_ok, syn_msg = inspector.run_syntax_check("generated_code.py")
    yield {"message": f"[CHECK] Syntax: {syn_msg}", "syntax_ok": syn_ok, "syntax_msg": syn_msg}

    code_run_ret, run_stdout, run_stderr = inspector.run_file("generated_code.py", timeout=run_timeout)
    yield {
        "message": f"[RUN] Code executed with return code: {code_run_ret}",
        "run_retcode": code_run_ret, "run_stdout": run_stdout, "run_stderr": run_stderr
    }

    # Test-Writer -> tests -> run pytest
    yield {"message": "[STEP] Running Test-Writer to generate pytest tests..."}
    test_spec = "Write pytest tests that validate the main public functions in the code. Keep tests deterministic and avoid IO or network."
    test_in = f"SPEC:\n{test_spec}\n\nCODE:\n{c_text}\n"
    test_out = test_writer.run(test_in)
    test_text = extract_content(test_out)
    test_text = strip_code_fence(test_text)
    test_text = test_runner.make_test_runner_safe(test_text)
    test_runner.save_test_file(test_text, path="test_generated.py")
    yield {"message": "[TEST] Test file saved as test_generated.py.", "test_text": test_text}

    yield {"message": "[TEST] Running pytest on test_generated.py ..."}
    tcode, tout, terr = test_runner.run_pytest("test_generated.py", timeout=12)
    yield {
        "message": f"[TEST] Pytest finished with return code: {tcode}",
        "pytest_code": tcode, "pytest_stdout": tout, "pytest_stderr": terr
    }

    # Debugger analysis
    yield {"message": "[STEP] Running Debugger (analysis)..."}
    dbg_prompt = (
        "Analyze this Python file and the diagnostics below. List issues (numbered). "
        "If you propose a corrected full-file, provide it inside a fenced block labeled ```PATCH``` and nothing else inside that block.\n\n"
        f"CODE:\n{c_text}\n\n"
        f"SYNTAX_CHECK:\n{syn_msg}\n\n"
        f"RUNTIME_STDOUT:\n{run_stdout}\n\n"
        f"RUNTIME_STDERR:\n{run_stderr}\n\n"
        f"PYTEST_RETURN_CODE:\n{tcode}\n\n"
        f"PYTEST_STDOUT:\n{tout}\n\n"
        f"PYTEST_STDERR:\n{terr}\n\n"
        "Be concise and precise."
    )
    dbg_out = debugger.run(dbg_prompt)
    dbg_text = extract_content(dbg_out)
    yield {"message": "[DEBUGGER] Analysis complete.", "debugger_output": dbg_text}

    # Patch handling: auto-apply if syntax failed and patch present (one-time)
    patch_text = extract_patch_from_debugger(dbg_text)
    if not syn_ok and patch_text:
        yield {"message": "[AUTO] Syntax error detected. Applying Debugger PATCH automatically."}
        inspector.apply_patch("generated_code.py", patch_text)
        # re-check syntax and runtime
        syn_ok, syn_msg = inspector.run_syntax_check("generated_code.py")
        code_run_ret, run_stdout, run_stderr = inspector.run_file("generated_code.py", timeout=run_timeout)
        yield {"message": f"[AUTO] Re-checked syntax: {syn_msg}", "syntax_ok": syn_ok, "syntax_msg": syn_msg}

    # Yield a final summary of this iteration's artifacts
    yield {
        "message": "Iteration complete. Ready for next step.",
        "patch_text": patch_text,
        "final_code": c_text
    }

# ---- Autonomous loop ----
def autonomous_loop(user_prompt: str, max_iters: int = 3, run_timeout: int = 8, auto_patch_enabled: bool = False):
    """Generator that yields status updates for the autonomous workflow."""
    researcher = create_researcher_agent()
    coder = create_coder_agent()
    test_writer = create_test_writer_agent()
    debugger = create_debugger_agent()

    # For CLI mode, check env var. For UI, use passed param.
    auto_patch = auto_patch_enabled or (os.environ.get("AUTO_PATCH", "") == "1")
    yield {"message": f"[CONFIG] AUTO_PATCH={auto_patch}, MAX_ITERS={max_iters}, RUN_TIMEOUT={run_timeout}s"}

    for iteration in range(1, max_iters + 1):
        yield {"message": f"==== ITERATION {iteration} ===="}
        iteration_artifacts = {}
        try:
            # Collect all yielded dictionaries from the iteration run
            for status_update in run_iteration(researcher, coder, test_writer, debugger, user_prompt, run_timeout):
                iteration_artifacts.update(status_update)
                yield status_update # Pass status up to the UI
        except Exception as e:
            yield {"message": f"[ERROR] Exception during iteration: {e}", "exception": str(e)}
            return

        patch = iteration_artifacts.get("patch_text")
        if not patch:
            yield {"message": "[RESULT] No PATCH suggested by Debugger. Workflow completed."}
            return

        yield {"message": "[RESULT] Debugger suggested a PATCH.", "patch_text": patch}

        if auto_patch:
            inspector.apply_patch("generated_code.py", patch)
            yield {"message": "[AUTO] Patch applied."}
            continue

        apply = input("Apply the suggested patch to generated_code.py? (y/n) ").strip().lower()
        if apply == "y":
            inspector.apply_patch("generated_code.py", patch)
            yield {"message": "[USER] Patch applied."}
            continue
        else:
            yield {"message": "[USER] Patch skipped. Ending workflow."}
            return

    yield {"message": "[RESULT] Reached max iterations without converging."}

# ---- Main entry ----
if __name__ == "__main__":
    prompt = (
        "Explain, at a high level, how transformer models work and give a short analogy. "
        "Then include a tiny coding task: write a Python function named `get_simple_token_length(text: str) -> int` "
        "that returns the whitespace-token count and a small usage example under `if __name__ == '__main__':`."
    )
    max_iters = int(os.environ.get("MAX_ITERS", "3"))
    run_timeout = int(os.environ.get("RUN_TIMEOUT", "8"))
    start = time.time()

    # For CLI execution, we just print the yielded messages
    final_artifacts = {}
    for status_update in autonomous_loop(prompt, max_iters=max_iters, run_timeout=run_timeout):
        print(status_update.get("message", ""))
        final_artifacts.update(status_update)

    dur = time.time() - start
    print("\n==== WORKFLOW FINISHED ====")
    print("duration:", f"{dur:.2f}s")

    for k in ("research_text", "code_text", "syntax_msg", "run_stdout", "run_stderr", "pytest_stdout", "pytest_stderr", "debugger_output"):
        if k in final_artifacts:
            print(f"\n--- {k.upper()} (truncated) ---\n", str(final_artifacts[k])[:1000])
    print("\nFinal generated file: generated_code.py")
