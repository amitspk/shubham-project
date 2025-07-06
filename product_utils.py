from typing import List, Dict

def format_products(products: List[Dict]) -> str:
    """Format product list for display."""
    if not products:
        return "No matching products found."
    return "\n".join(
        f"- **{item['name']}** (tags: {', '.join(item['tags'])})"
        for item in products
    )