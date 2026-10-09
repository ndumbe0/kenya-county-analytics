"""Data Agent - Answers queries about county data, statistics, trends."""
from src.chatbots import DataExplorerBot

agent = DataExplorerBot()

def answer(query: str) -> dict:
    return agent.respond(query)