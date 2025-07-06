import logging
from fake_db import FAKE_DB
from llm_utils import get_llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
import ast
from langchain_core.tools import tool
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
llm = get_llm()

def get_response_chain():
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a shopping assistant. Respond helpfully using the product data."),
        ("human", "Products: {products}")
    ])
    return response_prompt | llm

def get_tag_extractor():
    tag_prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract relevant product-related tags from the user's query as a Python list of strings. Break the tags into granualar words. Only output the Python list, nothing else."),
        ("human", "{input}")
    ])
    def safe_literal_eval(x):
        try:
            return ast.literal_eval(x.content.strip())
        except Exception:
            return []
    return tag_prompt | llm | RunnableLambda(safe_literal_eval)

@tool(description="Extract relevant product-related tags from the user's query as a Python list.")
def extract_tags(user_input: str):
    tags = get_tag_extractor().invoke({"input": user_input})
    logger.info(f"Extracted tags: {tags}")
    return tags

@tool(description="Generate a response based on user input and product summary.")
def generate_response(product_summary: str) -> str:
    response = get_response_chain().invoke({
        "products": product_summary
    })
    return response.content

@tool(description="Fetch products from the fake database based on extracted tags.")
def fetch_from_db(tags):
    matched = []
    # If tags is a string, try to parse it as a Python list
    if isinstance(tags, str):
        try:
            tags = ast.literal_eval(tags)
        except Exception:
            logger.warning("Could not parse tags string to list, got: %s", tags)
            tags = []
    print(f"Fetching products with tags: {tags}")
    print(f"Fake DB contents: {FAKE_DB}")
    if not isinstance(tags, list):
        logger.warning("Input 'tags' is not a list!")
    for item in FAKE_DB:
        logger.info(f"Checking item: {item}")
        if any(tag in item["tags"] for tag in tags):
            logger.info(f"Matched product: {item}")
            matched.append(item)
    logger.info(f"Matched products: {matched}")
    return matched if matched else [{"name": "No products found", "tags": []}]

# @tool(description="Format product list for display.")
# def format_response(products: str) -> str:
#     import ast
#     try:
#         parsed_products = ast.literal_eval(products)
#     except Exception:
#         return "⚠️ Could not parse product list."
    
#     if not parsed_products:
#         return "Sorry, no products match your criteria."
    
#     return "\n".join(
#         f"- **{p['name']}** (${p['price']}))"
#         for p in parsed_products
#     )

@tool(description="Format product list (from stringified list of dicts) into readable markdown.")
def format_response(products: str) -> str:
    import ast
    try:
        parsed_products = ast.literal_eval(products)
        if isinstance(parsed_products, str):
            parsed_products = ast.literal_eval(parsed_products)  # double-encoded
    except Exception:
        return "⚠️ Could not parse product list."

    if not isinstance(parsed_products, list):
        return "⚠️ Product list is not valid."

    try:
        return "\n".join(
            f"- **{p['name']}** (${p['price']}))"
            for p in parsed_products
            if isinstance(p, dict)
        )
    except Exception as e:
        return f"⚠️ Error formatting product list: {e}"

@tool(description="Given a list of products, return the product with the lowest price.")
def select_lowest_price_product(products) -> dict:
    """
    Returns the product with the lowest price from a list of products.
    """
    import ast
    # Handle string input (agent may pass as string)
    if isinstance(products, str):
        try:
            products = ast.literal_eval(products)
        except Exception:
            logger.warning("Could not parse products string to list, got: %s", products)
            return {"name": "No products found", "tags": [], "price": None}
    if not isinstance(products, list) or not products:
        return {"name": "No products found", "tags": [], "price": None}
    # Filter out products without a price
    products_with_price = [p for p in products if "price" in p and isinstance(p["price"], (int, float))]
    if not products_with_price:
        return {"name": "No products found", "tags": [], "price": None}
    lowest = min(products_with_price, key=lambda x: x["price"])
    return lowest

