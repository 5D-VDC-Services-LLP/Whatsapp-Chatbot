import os
from agno.agent import Agent
from agno.tools import tool
from agno.models.google import Gemini
from src.core.schemas import Intent, ParametersUnion
from src.core.config import settings

@tool
def parse_api_query(intent: Intent, parameters: ParametersUnion) -> dict:
    """
    Parses the user's natural language query about issues, reviews, or forms
    into a structured JSON object for an API call. Use this tool for any
    request to find or count items in a project.

    You must determine the correct 'intent' ('get_issues', 'get_reviews', or 'get_forms')
    and then populate the corresponding parameter object.
    """
    return {
        "intent": intent,
        "parameters": parameters.model_dump()
    }

intent_parser = Agent(
    model=Gemini(
        id="gemini-2.0-flash-lite",
        api_key=settings.GEMINI_API_KEY,
    ),
    tools=[parse_api_query],
    enable_agentic_knowledge_filters=False,
    instructions="""
    You are an expert NLU (Natural Language Understanding) engine for a project management system.
    Your sole purpose is to analyze user input and translate it into a single, structured JSON object that represents the user's intent and any extracted parameters.
    Your response MUST be ONLY the valid JSON object and nothing else. Do not add explanations, notes, or markdown fences like ```json.

    Follow this logic:
    1.  **Determine the Intent**: Analyze the query to determine one of the following intents: "get_issues", "get_reviews", "get_forms", "greet", or "unsure".
    2.  **Extract Parameters**: Identify and extract all relevant parameters from the query that correspond to the chosen intent. If no parameters are found, use an empty object `{}`.
    3.  **Handle Non-Task Queries**:
        - For simple greetings ("hi", "hello"), the intent is "greet".
        - For anything unrelated to issues, reviews, or forms (e.g., jokes, spam, general questions), the intent is "unsure".
    4.  **Format the Output**: Combine the intent and parameters into a single JSON object.
    ---
    **Examples:**

    User: "show me all open reviews for the S1.S3-Architecture workflow that are due today for me"
    {"intent": "get_reviews", "parameters": {"assignee_name": "current_user","review_status": ["open"], "review_workflow": ["S1.S3-Architecture"], "due_date": "today"},"count_only": true}}
    
    User: "show me all in review WIR forms that are due today for Ashrik"
    {"intent": "get_reviews", "parameters": {"assignee_name": "Ashrik","form_status": ["in_review"], "form_template": ["WIR"], "due_date": "today"},"count_only": false}}

    User: "Mujhe kitne issues assigned hai"
    {"intent": "get_issues", "parameters": {"assignee_name": "current_user", "count_only": true}}
    """,
    debug_mode=False,
    monitoring=False
)
