# main.py
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyDqX8nExVyBu-R0-Fvqonyt7wQl2pyVNA0"

# main.py
import sys
from agents.researcher import create_researcher_agent
from agents.coder import create_coder_agent
from agents.debugger import create_debugger_agent
from utils import inspector

def extract(obj):
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "content"):
        return obj.content
    return str(obj)

def strip_fence(code: str) -> str:
    code = code.strip()
    if code.startswith("```") and code.endswith("```"):
        body = code.split("\n", 1)[1]
        return body.rsplit("```", 1)[0].strip()
    return code

def save_code(text: str, path="generated_code.py"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved code to {path}")

def main():
    researcher = create_researcher_agent()
    coder = create_coder_agent()
    debugger = create_debugger_agent()

    user_prompt = (
        "Explain transformers briefly and include a tiny coding task: "
        "write a Python function to count tokens using whitespace."
    )

    # 1. Researcher
    r = extract(researcher.run(user_prompt))
    print("\n--- Researcher Output ---\n")
    print(r)

    # 2. Coder
    coder_prompt = (
        "Based on this spec, produce ONLY runnable python code:\n\n" + r
    )
    c = extract(coder.run(coder_prompt))
    c = strip_fence(c)
    print("\n--- Coder Output (cleaned) ---\n")
    print(c)

    save_code(c)

    # 3. Static + runtime checks
    syn_ok, syn_msg = inspector.run_syntax_check("generated_code.py")
    _, rt_out, rt_err = inspector.run_file("generated_code.py", timeout=10)

    # 4. Debugger agent
    dbg_prompt = (
        "Here is code to analyze.\n\n"
        f"CODE:\n{c}\n\n"
        f"SYNTAX CHECK:\n{syn_msg}\n\n"
        f"RUNTIME STDOUT:\n{rt_out}\n\n"
        f"RUNTIME STDERR:\n{rt_err}\n\n"
        "Please list issues and produce a corrected full file under ```PATCH``` fenced block."
    )

    d = extract(debugger.run(dbg_prompt))
    print("\n--- Debugger Output ---\n")
    print(d)

    # 5. Patch detection
    if "```PATCH" in d:
        print("\nA PATCH was suggested.")
        apply = input("Apply the patch? (y/n): ").strip().lower()
        if apply == "y":
            patch_text = d.split("```PATCH", 1)[1].split("```", 1)[0].strip()
            inspector.apply_patch("generated_code.py", patch_text)
            print("Patch applied to generated_code.py")
        else:
            print("Patch skipped.")

if __name__ == "__main__":
    main()
