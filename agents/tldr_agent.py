"""TLDR agent: finance tips or business concepts, for beginner / intermediate / expert."""
from ollama import chat
from config import LEVELS, TOPIC_CHOICES



def get_tldr(
    level: str = "intermediate",
    topic: str = "finance_tips",
    news_context: str = "",
) -> str:
    """Create a TLDR about finance tips or business concepts. level: beginner, intermediate, or expert. topic: finance_tips or business_concepts. Optionally pass news_context from get_business_news to ground the TLDR in recent news."""
    if level not in LEVELS:
        level = "intermediate"
    if topic not in TOPIC_CHOICES:
        topic = "finance_tips"

    prompt = (
        f"Create a clear TLDR about {topic.replace('_', ' ')}, "
        f"for {level} level. Keep it concise and actionable."
    )
    if news_context:
        prompt += f"\n\nOptional context from recent news:\n{news_context[:2000]}"

    response = chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]
