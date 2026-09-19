
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.openai_like import OpenAILikeEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType

from config import DB_PATH, OPENROUTER_API_KEY, ROOT, require_openrouter_key
from model import openrouter

DATA_FILE = ROOT / "data" / "knowledge.md"


def build_knowledge() -> Knowledge:
    require_openrouter_key()
    knowledge = Knowledge(
        name="Hackathon Demo Knowledge",
        vector_db=ChromaDb(
            name="hackathon_demo",
            collection="hackathon_demo",
            path=str(ROOT / "tmp" / "chromadb"),
            persistent_client=True,
            search_type=SearchType.hybrid,
            embedder=OpenAILikeEmbedder(
                id="text-embedding-3-small",
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                dimensions=1536,
            ),
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
        model=openrouter(),
        knowledge=knowledge,
        search_knowledge=True,
        markdown=True,
        instructions=[
            "Use the knowledge base for policy questions.",
            "If the knowledge base does not contain the answer, say so.",
        ],
    )
    agent.print_response("What happens when a user asks for an external refund?")
