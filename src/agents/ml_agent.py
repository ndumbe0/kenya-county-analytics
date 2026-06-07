"""ML Agent - Explains ML predictions, forecasts, model insights."""
from src.chatbots import PredictionBot

agent = PredictionBot()

def answer(query: str) -> dict:
    return agent.respond(query)