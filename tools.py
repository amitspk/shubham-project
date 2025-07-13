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
        ("system", "Extract relevant product-related tags from the user's query as a Python list of strings. Break the tags into granular words. Only output the Python list, nothing else. Example: ['laptop', 'gaming', 'RGB']"),
        ("human", "{input}")
    ])
    def safe_literal_eval(x):
        try:
            content = x.content.strip()
            # Handle common formatting issues
            if not content.startswith('['):
                content = '[' + content + ']'
            if content.startswith('```') or content.startswith('`'):
                # Extract list from code block
                lines = content.split('\n')
                for line in lines:
                    if '[' in line and ']' in line:
                        content = line.strip()
                        break
            result = ast.literal_eval(content)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.warning(f"Failed to parse tags: {e}, content: {x.content}")
            # Fallback: extract words manually
            words = x.content.lower().split()
            return [word.strip('[],"\'') for word in words if word.strip('[],"\'')]
    return tag_prompt | llm | RunnableLambda(safe_literal_eval)

@tool(description="Extract relevant product-related tags from the full conversation context (chat history + user input) as a Python list.")
def extract_tags(full_context: str):
    print(f"Extracting tags from full context: {full_context}")
    if not full_context or not full_context.strip():
        logger.warning("Empty input provided to extract_tags")
        return []
    
    # Prevent recursive calls by checking if input looks like it's already tags
    if full_context.strip().startswith('[') and full_context.strip().endswith(']'):
        try:
            result = ast.literal_eval(full_context.strip())
            if isinstance(result, list):
                return result
        except:
            pass
    
    try:
        tags = get_tag_extractor().invoke({"input": full_context})
        logger.info(f"Extracted tags from LLM: {tags}")
        # Ensure we always return a list
        if not isinstance(tags, list):
            logger.warning(f"LLM returned non-list: {type(tags)}, using fallback")
            tags = []
        
        # If LLM returned empty list or failed, use intelligent fallback
        if not tags:
            logger.info("LLM returned empty tags, using intelligent fallback")
            # Extract meaningful words (skip common words)
            stop_words = {'i', 'am', 'a', 'an', 'the', 'is', 'are', 'what', 'shall', 'will', 'for', 'to', 'in', 'on', 'at', 'by', 'with'}
            words = full_context.lower().replace('?', '').replace('.', '').replace(',', '').split()
            meaningful_words = [word for word in words if len(word) > 2 and word not in stop_words]
            tags = meaningful_words[:5]  # Limit to 5 most relevant words
            logger.info(f"Fallback extracted tags: {tags}")
        
        return tags
    except Exception as e:
        logger.error(f"Error in extract_tags: {e}")
        # Enhanced fallback: extract meaningful words
        stop_words = {'i', 'am', 'a', 'an', 'the', 'is', 'are', 'what', 'shall', 'will', 'for', 'to', 'in', 'on', 'at', 'by', 'with'}
        words = full_context.lower().replace('?', '').replace('.', '').replace(',', '').split()
        meaningful_words = [word for word in words if len(word) > 2 and word not in stop_words]
        fallback_tags = meaningful_words[:5]  # Limit to 5 most relevant words
        logger.info(f"Exception fallback tags: {fallback_tags}")
        return fallback_tags

@tool(description="Generate a response based on user input and product summary.")
def generate_response(product_summary: str) -> str:
    response = get_response_chain().invoke({
        "products": product_summary
    })
    return response.content

@tool(description="Fetch products from the fake database based on extracted tags.")
def fetch_from_db(tags):
    matched = []
    
    # Robust input handling
    if tags is None:
        logger.warning("None input provided to fetch_from_db")
        return [{"name": "No products found", "tags": []}]
    
    # If tags is a string, try to parse it as a Python list
    if isinstance(tags, str):
        tags = tags.strip()
        # Handle empty string
        if not tags:
            return [{"name": "No products found", "tags": []}]
        
        try:
            # Try to parse as list first
            if tags.startswith('[') and tags.endswith(']'):
                tags = ast.literal_eval(tags)
            else:
                # Split string into words as fallback
                tags = [word.strip('.,!?"\'') for word in tags.split() if word.strip('.,!?"\'')]
        except Exception as e:
            logger.warning(f"Could not parse tags string to list, got: {tags}, error: {e}")
            # Fallback to word splitting
            tags = [word.strip('.,!?"\'') for word in tags.split() if word.strip('.,!?"\'')]
    
    # Ensure tags is a list
    if not isinstance(tags, list):
        logger.warning(f"Input 'tags' is not a list! Got: {type(tags)}, value: {tags}")
        return [{"name": "No products found", "tags": []}]
    
    # Filter out empty tags
    tags = [tag for tag in tags if tag and isinstance(tag, str) and tag.strip()]
    
    if not tags:
        logger.info("No valid tags provided")
        return [{"name": "No products found", "tags": []}]
    
    for item in FAKE_DB:
        # Ensure item has tags field
        if "tags" not in item or not isinstance(item["tags"], list):
            continue
        
        # Count tag matches using substring matching
        match_count = 0
        matched_tags = []
        
        for tag in tags:
            if isinstance(tag, str):
                for item_tag in item["tags"]:
                    if isinstance(item_tag, str):
                        if tag.lower() in item_tag.lower() or item_tag.lower() in tag.lower():
                            match_count += 1
                            matched_tags.append(item_tag)
                            break  # Avoid counting same item_tag multiple times
        
        # Only include items with at least one tag match
        if match_count > 0:
            # Create a copy of the item with match information
            matched_item = item.copy()
            matched_item['match_count'] = match_count
            matched_item['matched_tags'] = matched_tags
            matched.append(matched_item)
    
    # Sort by match count (descending order - highest matches first)
    matched.sort(key=lambda x: x['match_count'], reverse=True)
    
    for item in matched:
        logger.info(f"Product: {item['name']}, Matches: {item['match_count']}, Tags: {item['matched_tags']}")
    
    return matched if matched else [{"name": "No products found", "tags": []}]

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

# @tool(description="Return the top 5 products from a list of products.")
# def get_top_5_products(products) -> list:
#     """
#     Returns the top 5 products from the provided list.
#     """
#     import ast
#     # Handle string input (agent may pass as string)
#     if isinstance(products, str):
#         try:
#             products = ast.literal_eval(products)
#         except Exception:
#             return []
#     if not isinstance(products, list):
#         return []
#     return products[:5]

@tool(description="Extract budget amount from user's query. Use when user mentions price, budget, or cost anywhere in the query.")
def extract_budget(user_query: str) -> float:
    """
    Extract budget amount from user query.
    Returns the budget as a float or 0 if no budget found.
    """
    import re
    
    # Look for patterns like $20, 20 dollars, 20$, within 20
    patterns = [
        r'\$(\d+(?:\.\d{2})?)',  # $20 or $20.99
        r'(\d+(?:\.\d{2})?)\s*dollars?',  # 20 dollars
        r'(\d+(?:\.\d{2})?)\$',  # 20$
        r'within\s+(\d+(?:\.\d{2})?)',  # within 20
        r'under\s+(\d+(?:\.\d{2})?)',  # under 20
        r'below\s+(\d+(?:\.\d{2})?)',  # below 20
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_query.lower())
        if match:
            try:
                budget = float(match.group(1))
                logger.info(f"Extracted budget: ${budget}")
                return budget
            except ValueError:
                continue
    
    logger.info("No budget found in query")
    return 0.0

@tool(description="REQUIRED: Use this tool when user mentions budget, price limit, or cost constraints (like '$20', '20 dollars', 'within 20'). Takes a list of products and maximum budget, returns a list of products whose total price sum falls within that budget. Use budget value returned by tool 'extract_budget'")
def select_products_within_budget(products=None, budget: float = None, **kwargs) -> List[Dict]:
    """
    Finds the best combination of products whose total price falls within the specified budget.
    Returns the combination with the highest total rating value.
    Args:
        products: List of product dictionaries or string representation of list
        budget: Maximum budget as a number
    Returns:
        List of product dictionaries that fit within budget
    """
    import ast
    from itertools import combinations
    logger.info(f"select_best_rated_within_budget called with budget: {budget}")

    # Handle case where arguments come as a single dictionary
    if products is not None and isinstance(products, dict) and 'products' in products:
        budget = products.get('budget', budget)
        products = products['products']
    
    # Extract from kwargs if still None
    if products is None:
        products = kwargs.get('products', [])
    if budget is None:
        budget = kwargs.get('budget', 0.0)

    # Handle string input for products
    if isinstance(products, str):
        try:
            products = ast.literal_eval(products)
        except Exception:
            logger.warning("Could not parse products string to list")
            return [{"name": "Invalid products input", "price": None, "ratings": None}]

    # Validate inputs
    if not isinstance(products, list):
        logger.warning(f"Products is not a list: {type(products)}")
        return [{"name": "Invalid products format", "price": None, "ratings": None}]
    print("My budget:" + str(budget))
    if not isinstance(budget, (int, float)) or budget <= 0:
        logger.warning(f"Budget is not a valid number: {type(budget)}, value: {budget}")
        return [{"name": "Invalid or missing budget", "price": None, "ratings": None}]

    # Filter products that have valid price and ratings
    valid_products = [
        p for p in products
        if "price" in p and "ratings" in p 
        and isinstance(p["price"], (int, float)) 
        and isinstance(p["ratings"], (int, float))
        and p["price"] <= budget  # Individual product must be within budget
    ]

    logger.info(f"Found {len(valid_products)} valid products for budget ${budget}")

    if not valid_products:
        return [{"name": "No products found within budget", "price": None, "ratings": None, "budget": budget}]

    best_combination = []
    best_total_rating = 0
    best_total_price = 0

    # Try all possible combinations of products
    for r in range(1, len(valid_products) + 1):
        for combo in combinations(valid_products, r):
            total_price = sum(p["price"] for p in combo)
            total_rating = sum(p["ratings"] for p in combo)
            
            if total_price <= budget:
                # Prefer combinations with higher total ratings, then lower total price as tiebreaker
                if (total_rating > best_total_rating or 
                    (total_rating == best_total_rating and total_price < best_total_price)):
                    best_combination = list(combo)
                    best_total_rating = total_rating
                    best_total_price = total_price

    if not best_combination:
        return [{"name": "No combination found within budget", "price": None, "ratings": None, "budget": budget}]

    logger.info(f"Best combination: {len(best_combination)} products, total price: ${best_total_price}, total rating: {best_total_rating}")
    for product in best_combination:
        logger.info(f"  - {product['name']}: ${product['price']} (Rating: {product['ratings']})")
    
    return best_combination

@tool(description="Given a list of products, return the product with the highest rating.")
def select_highest_rated_product(products) -> dict:
    """
    Returns the product with the highest rating from a list of products.
    """
    import ast
    # Convert string input to list if needed
    if isinstance(products, str):
        try:
            products = ast.literal_eval(products)
        except Exception:
            logger.warning("Could not parse products string to list, got: %s", products)
            return {"name": "No products found", "tags": [], "ratings": None}
    if not isinstance(products, list) or not products:
        return {"name": "No products found", "tags": [], "ratings": None}

    # Filter only products that have a numeric 'ratings' field
    rated_products = [p for p in products if "ratings" in p and isinstance(p["ratings"], (int, float))]
    if not rated_products:
        return {"name": "No rated products found", "tags": [], "ratings": None}

    highest = max(rated_products, key=lambda x: x["ratings"])
    return highest