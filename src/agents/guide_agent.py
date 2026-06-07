"""Guide Agent - Helps users navigate app, provides tutorials."""
from src.chatbots import GuideBot

agent = GuideBot()

def answer(query: str) -> dict:
    return agent.respond(query)