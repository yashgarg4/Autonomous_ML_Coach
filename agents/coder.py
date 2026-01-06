from agno.agent import Agent
from agno.models.google import Gemini


def create_coder_agent(model_id: str = "gemini-2.5-flash") -> Agent:
	"""Factory to create and return a code-generation Agent instance."""
	model = Gemini(id=model_id)
	coder = Agent(
		name="coder",
		model=model,
		instructions=(
			"You are a helpful code-generation assistant. Given a short programming specification, "
            "produce clean, runnable Python code ONLY (no extra explanation, no prose before the code). "
            "Do NOT wrap the code inside triple backticks. If you add function docstrings, they MUST be "
            "enclosed in triple quotes like: \"\"\"This is a docstring.\"\"\". If you include a module description, "
            "place it as a single top-level module docstring at the very top of the file. Output must be valid Python source."
		),
	)
	return coder


if __name__ == "__main__":
	c = create_coder_agent()
	spec = "Create a function `add(a, b)` that returns the sum of two numbers and a usage example."
	try:
		out = c.run(spec)
		print("Coder response:\n")
		print(out)
	except Exception as e:
		print("Error running coder agent:", e)
