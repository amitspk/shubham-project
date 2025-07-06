from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
import ast

# def get_tag_extractor(llm):
#     tag_prompt = ChatPromptTemplate.from_messages([
#         ("system", "Extract key tags from the user message as a Python list of strings."),
#         ("human", "{input}")
#     ])
#     # Use ast.literal_eval for safety
#     return tag_prompt | llm | RunnableLambda(lambda x: ast.literal_eval(x.content.strip()))

# def get_tag_extractor(llm):
#     tag_prompt = ChatPromptTemplate.from_messages([
#         ("system", "Extract key tags from the user message as a Python list of strings. Only output the Python list, nothing else."),
#         ("human", "{input}")
#     ])
#     def safe_literal_eval(x):
#         try:
#             return ast.literal_eval(x.content.strip())
#         except Exception:
#             return []
#     return tag_prompt | llm | RunnableLambda(safe_literal_eval)

# def get_response_chain(llm):
#     response_prompt = ChatPromptTemplate.from_messages([
#         ("system", "You are a shopping assistant. Respond helpfully using the product data."),
#         ("human", "User query: {query}\nProducts: {products}")
#     ])
#     return response_prompt | llm