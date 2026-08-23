from agent.llm import llm
from agent.prompts import TRAVEL_AGENT_PROMPT


def travel_agent(user_query):
    prompt = f"""
{TRAVEL_AGENT_PROMPT}

User request:
{user_query}
"""

    response = llm.invoke(prompt)

    return response.content