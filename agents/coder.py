# agents/coder.py
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
			"produce clean, runnable Python code only (no extra explanation). If helper libraries are needed, "
			"list them in a one-line comment at the top as: # REQUIRES: package1, package2. "
			"When asked to write functions also include a small usage example under `if __name__ == '__main__':`"
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