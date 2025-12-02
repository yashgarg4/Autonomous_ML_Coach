# agents/researcher.py
from agno.agent import Agent
from agno.models.google import Gemini


# A lightweight Researcher agent that returns concise factual answers.
# Edit instructions to control style/length.


def create_researcher_agent(model_id: str = "gemini-2.5-flash") -> Agent:
	"""Factory to create and return a researcher Agent instance."""
	model = Gemini(id=model_id)
	researcher = Agent(
		name="researcher",
		model=model,
		instructions=(
			"You are a concise research assistant. When asked a question, return a short, factual answer "
			"(2-4 sentences). If the user asks for step-by-step instructions, return a numbered list. "
			"If you need to ask for clarification, ask one clarifying question only."
		),
	)
	return researcher


if __name__ == "__main__":
	# quick local test when running this file directly
	r = create_researcher_agent()
	query = "Explain transformers in 3 sentences"
	try:
		out = r.run(query)
		print("Researcher response:\n")
		print(out)
	except Exception as e:
		print("Error running researcher agent:\n", e)