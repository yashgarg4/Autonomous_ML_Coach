# agents/test_writer.py
from agno.agent import Agent
from agno.models.google import Gemini

def create_test_writer_agent(model_id: str = "gemini-2.5-flash") -> Agent:
    """
    Produces pytest-style unit tests for a single Python file that contains one or more functions.
    The agent receives:
      - A short spec (human description)
      - The Python file content (as text)
    The agent MUST output a single pytest test file content only (no extra explanation).
    The tests should:
      - Import the target functions from generated_code (or reference them directly)
      - Cover typical, edge, and empty input cases where applicable
      - Use plain assert statements (pytest friendly)
      - Keep tests deterministic and avoid network/IO
    Output must be valid Python text suitable to save as test_generated.py.
    """
    model = Gemini(id=model_id)
    instructions = (
        "You are a test writer. Input: (1) a short spec, (2) Python file content. "
        "Produce a pytest-compatible test file only (no commentary). "
        "Name test functions with test_ prefix. Do not import anything except from the generated module. "
        "Avoid network, file or PID operations. Keep tests fast and deterministic."
    )
    agent = Agent(
        name="test_writer",
        model=model,
        instructions=instructions,
    )
    return agent

if __name__ == "__main__":
    t = create_test_writer_agent()
    sample_spec = "Write tests for get_simple_token_length(text: str) -> int to check normal, empty and whitespace-only strings."
    sample_code = "def get_simple_token_length(text: str) -> int:\n    if not text.strip():\n        return 0\n    return len(text.split())\n"
    print(t.run(f"SPEC:\n{sample_spec}\n\nCODE:\n{sample_code}"))
