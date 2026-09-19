from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval

from model import gemini


def run() -> None:
    agent = Agent(
        name="Eval Target",
        model=gemini(),
        instructions="Answer arithmetic questions exactly.",
    )

    evaluation = AccuracyEval(
        name="Basic arithmetic",
        model=gemini(),
        agent=agent,
        input="What is 12 * 12?",
        expected_output="144",
    )

    result = evaluation.run(print_results=True)
    print("Evaluation result:", result)
