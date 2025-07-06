# fake_db.py
FAKE_DB = [
    {"name": "TrailRunner 1000", "tags": ["running", "grip", "affordable"], "price": 79.99},
    {"name": "SpeedX Elite", "tags": ["running", "lightweight"], "price": 129.99},
    {"name": "BudgetFit Pro", "tags": ["affordable", "walking"], "price": 49.99},
    {"name": "GripMax Trek", "tags": ["grip", "hiking" ,"durable"], "price": 109.99},
    {"name": "GripMax Trek V2", "tags": ["grip", "hiking", "durable"], "price": 119.99},
]

# def fetch_from_db(tags):
#     matched = []
#     print(f"Fetching products with tags: {tags}")
#     for item in FAKE_DB:
#         if any(tag in item["tags"] for tag in tags):
#             matched.append(item)
#     return matched if matched else [{"name": "No products found", "tags": []}]
