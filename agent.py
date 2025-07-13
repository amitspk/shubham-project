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
        "You are a helpful shopping assistant specializing in understanding the occasion, event, or party the user is planning or celebrating. "
        "Your primary goal is to infer the type of celebration (such as birthdays, anniversaries, festivals, housewarmings, baby showers, etc.) from the user's query. "
        "Based on the occasion or event, extract relevant tags from the user's input and use them to suggest a curated list of products that would be suitable or necessary for that celebration. "
        "Always select products by matching the extracted tags with available product data. "
        "Respond in a friendly, concise, and informative manner. "
        "When greeted with 'hi' or 'hello', respond with a warm greeting. "
        "Do not ask the user questions or provide examples. "
        "Only provide helpful, occasion-specific product recommendations based on the user's input and available product data."
    )
)

def process_query(user_input: str) -> str:
    """Let the agent decide which tools to use to answer the user's question."""
    return agent.run(user_input)