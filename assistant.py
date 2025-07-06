import logging
from llm_utils import get_llm
from prompts import get_tag_extractor, get_response_chain
from product_utils import format_products
from fake_db import fetch_from_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShoppingAssistant:
    """AI-powered shopping assistant."""

    def __init__(self):
        self.llm = get_llm()
        self.tag_extractor = get_tag_extractor(self.llm)
        self.response_chain = get_response_chain(self.llm)

    def extract_tags(self, user_input: str):
        tags = self.tag_extractor.invoke({"input": user_input})
        logger.info(f"Extracted tags: {tags}")
        return tags

    def generate_response(self, user_input: str, product_summary: str) -> str:
        response = self.response_chain.invoke({
            "query": user_input,
            "products": product_summary
        })
        return response.content

    def process_query(self, user_input: str) -> str:
        logger.info(f"Processing user input: {user_input}")
        tags = self.extract_tags(user_input)
        results = fetch_from_db(tags)
        logger.info(f"Fetched products: {results}")
        product_summary = format_products(results)
        logger.info(f"Formatted product summary: {product_summary}")
        return self.generate_response(user_input, product_summary)

# Singleton for app usage
assistant = ShoppingAssistant()

def process_query(user_input: str) -> str:
    """Entry point for processing user queries."""
    return assistant.process_query(user_input)