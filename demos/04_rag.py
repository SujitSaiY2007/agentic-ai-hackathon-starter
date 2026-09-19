from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType

from config import DB_PATH, ROOT
from model import gemini


DATA_FILE = ROOT / "data" / "knowledge.md"


def build_knowledge() -> Knowledge:
    knowledge = Knowledge(
        name="Hackathon Demo Knowledge",
        vector_db=ChromaDb(
            name="hackathon_demo",
            collection="hackathon_demo",
            path=str(ROOT / "tmp" / "chromadb"),
            persistent_client=True,
            search_type=SearchType.hybrid,
            embedder=GeminiEmbedder(id="gemini-embedding-001"),
        ),
        max_results=5,
        contents_db=SqliteDb(db_file=DB_PATH),
    )
    return knowledge


def run() -> None:
    knowledge = build_knowledge()

    # Re-running insert is intentionally simple for learning. In a real app,
    # manage document IDs / upserts so the corpus is not duplicated.
    knowledge.insert(path=str(DATA_FILE))

    agent = Agent(
        name="RAG Agent",
        model=gemini(),
        knowledge=knowledge,
        search_knowledge=True,
        markdown=True,
        instructions=[
            "Use the knowledge base for policy questions.",
            "If the knowledge base does not contain the answer, say so.",
        ],
    )
    agent.print_response("What happens when a user asks for an external refund?")
