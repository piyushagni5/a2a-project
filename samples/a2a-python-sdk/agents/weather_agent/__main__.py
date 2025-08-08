import os
import sys
import click
import httpx
from dotenv import load_dotenv

from .agent import WeatherAgent
from .agent_executor import WeatherAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import BasePushNotificationSender, InMemoryPushNotificationConfigStore, InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

load_dotenv()  # Load environment variables from .env file

def build_agent_card(host: str, port: int) -> AgentCard:
    """Build comprehensive agent metadata for discovery and capability negotiation."""
    return AgentCard(
        name="Weather Agent",
        description="Provides real-time weather information for any location using advanced search capabilities. Get current conditions, temperature, humidity, wind speed, and personalized recommendations.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True, 
            pushNotifications=True
        ),
        defaultInputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
        skills=[
            AgentSkill(
                id="get_weather",
                name="Get Current Weather",
                description="Get real-time weather information including temperature, conditions, humidity, and wind for any location worldwide. Provides personalized recommendations based on current conditions.",
                tags=["weather", "temperature", "forecast", "conditions", "climate", "humidity", "wind", "realtime"],
                examples=[
                    "What's the weather like in New York?",
                    "Current weather in London, UK",
                    "Tell me about the weather in Tokyo",
                    "How's the weather in San Francisco today?",
                    "Weather conditions in Mumbai, India",
                    "What should I wear in Chicago today?",
                ],
            )
        ],
    )

@click.command()
@click.option('--host', 'host', default='localhost', help='Host to bind the server to')
@click.option('--port', 'port', default=10003, help='Port to bind the server to') 
def main(host: str, port: int):
    """Start the WeatherAgent A2A server."""
    # Validate required environment variables
    required_vars = ['GOOGLE_API_KEY', 'TAVILY_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file.")
        print("\nRequired:")
        print("- GOOGLE_API_KEY: Get from https://aistudio.google.com")
        print("- TAVILY_API_KEY: Get from https://tavily.com")
        sys.exit(1)
    
    # Setup HTTP client for push notifications
    client = httpx.AsyncClient()
    
    # Configure request handler with all components
    handler = DefaultRequestHandler(
        agent_executor=WeatherAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_sender=BasePushNotificationSender(client, InMemoryPushNotificationConfigStore()),
    )
    
    # Create A2A server application
    server = A2AStarletteApplication(
        agent_card=build_agent_card(host, port),
        http_handler=handler,
    )
    
    print(f"Starting WeatherAgent server on http://{host}:{port}")
    print(f"Agent metadata available at: http://{host}:{port}/.well-known/agent.json")
    
    # Launch server with uvicorn
    import uvicorn
    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()