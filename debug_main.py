# debug_main.py
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

# Try to import your agents; if import fails, we still want to see the error
print("DEBUG: Python version:", sys.version)
print("DEBUG: Current working dir:", os.getcwd())
print("DEBUG: Checking Gemini API key env var...")

# check common env var used earlier
print("DEBUG: GOOGLE_API_KEY present?:", bool(os.environ.get("GOOGLE_API_KEY")))

# You can set DEBUG_MOCK=1 to avoid external API calls and use a local mock agent
USE_MOCK = os.environ.get("DEBUG_MOCK", "0") == "1"
print("DEBUG: Using mock agents?:", USE_MOCK)
print("DEBUG: Start imports...")

try:
    from agents.researcher import create_researcher_agent
    from agents.coder import create_coder_agent
    print("DEBUG: Imported agent factories successfully.")
except Exception as e:
    print("ERROR: Failed to import agent factories:", repr(e))
    raise

# Helper to run a callable with a timeout and clear logging
def run_with_timeout(fn, args=(), kwargs=None, timeout=30, label="task"):
    kwargs = kwargs or {}
    print(f"DEBUG: Starting '{label}' with timeout {timeout}s...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn, *args, **kwargs)
        try:
            res = fut.result(timeout=timeout)
            elapsed = time.time() - start
            print(f"DEBUG: '{label}' finished in {elapsed:.2f}s.")
            return res
        except FuturesTimeout:
            print(f"ERROR: '{label}' timed out after {timeout}s.")
            # attempt to cancel (best-effort)
            fut.cancel()
            raise
        except Exception as e:
            elapsed = time.time() - start
            print(f"ERROR: '{label}' raised exception after {elapsed:.2f}s: {repr(e)}")
            raise

# A tiny MockAgent to use if external model calls are failing
class MockAgent:
    def __init__(self, name):
        self.name = name
    def run(self, prompt):
        print(f"MOCK {self.name}: received prompt (truncated): {prompt[:120]!r}")
        # return a deterministic mock based on name
        if self.name == "researcher":
            return "MockResearch: Transformers use attention. #SPEC: Create function tokenized_len(s) -> int."
        if self.name == "coder":
            return (
                "# REQUIRES: none\n"
                "def tokenized_len(s: str) -> int:\n"
                "    # simple whitespace tokenizer\n"
                "    return len(s.split())\n\n"
                "if __name__ == '__main__':\n"
                "    print(tokenized_len('hello world'))\n"
            )
        return "MOCK: default response."

def main():
    print("DEBUG: Creating agents...")

    if USE_MOCK:
        researcher = MockAgent("researcher")
        coder = MockAgent("coder")
    else:
        # create real agents (these may contact Gemini on init or on first run)
        try:
            researcher = create_researcher_agent()
            coder = create_coder_agent()
        except Exception as e:
            print("ERROR: Exception while creating real agents:", repr(e))
            print("DEBUG: Falling back to mock agents for testing.")
            researcher = MockAgent("researcher")
            coder = MockAgent("coder")

    print("DEBUG: Agents created. Now running researcher.run()")

    # Step 1: run researcher with timeout
    try:
        research_output = run_with_timeout(researcher.run, args=("Explain transformers in 3 sentences and add a small code spec.",), timeout=45, label="researcher.run")
        print("\n--- Researcher Output (truncated 1000 chars) ---\n")
        print(research_output[:1000])
    except Exception as e:
        print("ERROR: researcher.run failed:", repr(e))
        return

    # Step 2: feed to coder, run with timeout
    coder_prompt = "Based on the following short spec, write runnable Python code only (no extra explanation):\n\n" + research_output
    try:
        code_output = run_with_timeout(coder.run, args=(coder_prompt,), timeout=60, label="coder.run")
        print("\n--- Coder Output (truncated 2000 chars) ---\n")
        print(code_output[:2000])
    except Exception as e:
        print("ERROR: coder.run failed:", repr(e))
        return

    print("\nDEBUG: debug_main.py finished normally.")

if __name__ == "__main__":
    main()
