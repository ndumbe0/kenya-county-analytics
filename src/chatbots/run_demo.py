"""Convenience entrypoint to test all chatbots."""
from src.chatbots import route_query, auto_route, AGENTS

if __name__ == "__main__":
    samples = [
        ("data", "Population of Nairobi?"),
        ("data", "Compare Mombasa and Kisumu"),
        ("prediction", "What will Makueni population be in 2030?"),
        ("prediction", "Which counties will grow fastest?"),
        ("guide", "How do I download data?"),
        ("guide", "Tell me about the map"),
    ]
    for agent, q in samples:
        result = route_query(agent, q)
        print(f"[{result['agent']}] Q: {q}")
        print(f"  A: {result['answer'][:120]}...")
        print()
