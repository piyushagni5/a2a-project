import asyncio
from typing import AsyncIterable, Any, Literal
from uuid import uuid4

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Initialize persistent memory for multi-turn conversations
memory = MemorySaver()

# Initialize Tavily search for weather data
try:
    tavily_search = TavilySearch(max_results=3)
except Exception as e:
    print(f"Warning: Could not initialize Tavily search: {e}")
    print("Please set TAVILY_API_KEY environment variable for real weather data.")
    tavily_search = None

@tool
def search_weather(location: str) -> dict[str, str]:
    """
    Search for current weather information for a specific location.
    
    Args:
        location: The city, state/country for weather lookup (e.g., "New York, NY" or "London, UK")
    
    Returns:
        Dictionary containing weather search results
    """
    if tavily_search is None:
        return {
            "error": "Weather search service not available. Please set TAVILY_API_KEY environment variable.",
            "location": location,
            "mock_data": f"Mock weather for {location}: 72°F, Sunny, Light breeze"
        }
    
    try:
        # Search for current weather using Tavily
        query = f"current weather {location} today temperature conditions humidity wind"
        search_results = tavily_search.invoke({"query": query})
        return {"weather_data": search_results, "location": location}
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}", "location": location}

class ResponseFormat(BaseModel):
    status: Literal["completed", "input_required", "error"]
    message: str

class WeatherAgent:
    RESPONSE_FORMAT_INSTRUCTION = """
    You MUST format your final response as a JSON object with exactly these fields:
    {
        "status": "completed" | "input_required" | "error",
        "message": "your response message here"
    }
    
    Use "completed" when you have successfully provided weather information.
    Use "input_required" when you need a specific location from the user.
    Use "error" when you cannot complete the request due to an error.
    """
    
    SYSTEM_INSTRUCTION = (
        "You are a specialized weather assistant powered by real-time search capabilities. "
        "When users ask for weather information, use the 'search_weather' tool to get current data. "
        "If no location is specified, ask the user to provide one. "
        "Format weather information in a friendly, readable way with emojis and clear details. "
        "Include temperature, conditions, humidity, wind if available. "
        "Make your responses engaging and visually appealing with appropriate emojis. "
        "Always provide actionable information like what to wear or activities to consider."
    )

    SUPPORTED_CONTENT_TYPES = ["text/plain"]

    def __init__(self):
        # Initialize Gemini model with the latest variant
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
        self.tools = [search_weather]
        
        # Create ReAct agent with memory and structured responses
        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
        )

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        # Configure session management for multi-turn conversations
        config: RunnableConfig = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        inputs = {"messages": [("user", query)]}
        
        # Stream through agent reasoning steps
        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            
            # Detect tool usage phase
            if isinstance(message, AIMessage) and message.tool_calls:
                # Extract location from tool call for better UX
                tool_call = message.tool_calls[0]
                location = tool_call.get('args', {}).get('location', 'the specified location')
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Searching for current weather in {location}...",
                }
            # Detect tool result processing phase
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing weather data and formatting response...",
                }
        
        # Provide final structured response
        yield self._final_response(config)

    def _final_response(self, config: RunnableConfig) -> dict[str, Any]:
        # Extract structured response from agent memory
        state = self.graph.get_state(config)
        structured = state.values.get("structured_response")
        
        if isinstance(structured, ResponseFormat):
            if structured.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured.message,
                }
            if structured.status in ("input_required", "error"):
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured.message,
                }
        
        # Graceful fallback for edge cases
        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to process your weather request at the moment. Please try again.",
        }