from langchain.agents import initialize_agent, AgentType
from llm_utils import get_llm
from tools import extract_tags, fetch_from_db, format_response, generate_response, select_lowest_price_product

tools = [
    extract_tags,
    fetch_from_db,
    format_response,
    generate_response,
    select_lowest_price_product
]

llm = get_llm()

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    system_message=(
            "You are a helpful shopping assistant. "
            "Answer user queries directly and concisely. "
            "Do not ask the user questions or provide examples. "
            "Only provide helpful, informative responses based on the user's input and available product data."
        )
)

def process_query(user_input: str) -> str:
    """Let the agent decide which tools to use to answer the user's question."""
    return agent.run(user_input)