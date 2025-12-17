from agno.agent import Agent
from agno.models.google import Gemini

def create_debugger_agent(model_id: str = "gemini-2.5-flash") -> Agent:
    model = Gemini(id=model_id)

    debugger = Agent(
        name="debugger",
        model=model,
        instructions=(
            "You are a professional Python debugging assistant.\n"
            "You will receive:\n"
            "1. Python code content.\n"
            "2. Syntax checker output.\n"
            "3. Runtime stdout/stderr.\n\n"
            "Your task:\n"
            "- Analyze all signals.\n"
            "- Identify syntax errors, logical errors, style issues, or crashes.\n"
            "- Provide a numbered list of issues.\n"
            "- Then provide a corrected full-file patch under a fenced block labeled ```PATCH```.\n"
            "- The patch must contain ONLY the corrected Python file content."
        ),
    )

    return debugger

if __name__ == "__main__":
    d = create_debugger_agent()
    print(d.run("Test debugger agent: say hello"))
