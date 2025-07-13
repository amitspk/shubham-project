import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

def load_env():
    """Load environment variables from .env file."""
    load_dotenv()

def get_api_key() -> str:
    """Fetch the OpenAI API key from environment."""
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return api_key

def get_llm(model: str = "gpt-4.1-nano", temperature: float = 0):
    """Instantiate a ChatOpenAI LLM."""
    api_key = get_api_key()
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)