from langchain.agents import initialize_agent, AgentType
from llm_utils import get_llm
from tools import extract_tags, fetch_from_db, format_response, generate_response, select_lowest_price_product, select_products_within_budget, select_highest_rated_product, extract_budget

tools = [
    extract_tags,
    fetch_from_db,
    format_response,
    generate_response,
    extract_budget,
    select_products_within_budget,
    select_highest_rated_product,
    select_lowest_price_product
]

llm = get_llm()

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    handle_parsing_errors=True,
    system_message=(
        "If greeted with 'hi', 'hello', just tell 'I am a Shopping Assistant and how can I help you?''. "
        "Always use provided tools to answer user's queries. Do not try to apply your own brain."
        "You are a shopping assistant. Infer the celebration type (e.g., birthday, anniversary, festival) from the user's query. "
        "IMPORTANT: When user mentions a budget (like '$20', '20 dollars', 'within 20'), follow these EXACT steps in order:"
        "1. First, use extract_budget to get the budget amount from user query"
        "2. Then, use extract_tags to get relevant tags from user query"
        "3. Use fetch_from_db with the extracted tags to get products"
        "4. Use select_best_rated_within_budget with BOTH the products AND the extracted budget amount"
        "5. Use generate_response with the filtered result"
        "NEVER call select_best_rated_within_budget without first extracting the budget amount using extract_budget tool."
        "Use budget from tool 'extract_budget' while calling tool select_best_rated_within_budget"
        "Extract relevant tags, fetch the products and apply relevant tools to answer the user's query. "
        "Respond in a friendly, concise, and informative manner. "
        "Do not ask questions or give examples. "
        "Only provide occasion-specific product recommendations."
        "Find the best-rated product within a specified budget. Use this when users mention a budget and want quality recommendations."
        "Identify if it's a fresh conversation or a follow-up based on chat history. if it's fresh conversation, use only the user input to generate response. if it's follow-up conversation, use chat history and user input to generate response."
    )
)

def process_query(user_input: str, chat_history: list = None) -> str:
    """Let the agent decide which tools to use to answer the user's question."""
    
    if chat_history and len(chat_history) > 1:
        print("ENTERING IF CLAUSE")
        # Format chat history for context
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[:-1]])
        full_input = f"Previous conversation:\n{context}\n\nCurrent query: {user_input}"
        print(f"Full input: {full_input}")
        return agent.run(full_input)
    
    print("ENTERING DEFAULT RETURN")
    return agent.run(user_input)