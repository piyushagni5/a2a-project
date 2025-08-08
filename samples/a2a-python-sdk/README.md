# A2A Python SDK - Weather Agent

This is an educational project that demonstrates how to build and interact with **Agent-to-Agent (A2A)** protocol agents using Python. The project includes a weather agent that provides real-time weather information using **Google Gemini** and **Tavily Search**, along with a client for interacting with the agent.

---

## Features

- **A2A Protocol Implementation**: Full implementation of the Agent-to-Agent protocol
- **Weather Agent**: Real-time weather information for any location worldwide
- **Streaming Support**: Real-time streaming responses with progress updates
- **Multi-turn Conversations**: Support for follow-up questions and clarifications
- **Rich CLI Interface**: Beautiful terminal interface with color-coded output
- **Agent Discovery**: Automatic agent capability detection and negotiation

---

## Installation and Setup (Using `uv`)

### 1. Create a virtual environment from the project directory

```bash
cd samples/a2a-python-sdk
uv venv
source .venv/bin/activate
```

### 2. Install all dependencies

```bash
uv pip install -r requirements.txt
```

### 3. Set required environment variables

Create a `.env` file in the project directory:

```env
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
```

**Required API Keys:**
- **Google API Key**: Get from [Google AI Studio](https://aistudio.google.com)
- **Tavily API Key**: Get from [Tavily](https://tavily.com)

---

## Project Structure

```
a2a-python-sdk/
├── agents/
│   └── weather_agent/
│       ├── agent.py              # Weather agent implementation
│       ├── agent_executor.py     # A2A protocol executor
│       └── __main__.py           # Server entry point
├── client/
│   └── client.py                 # Interactive client
├── pyproject.toml                # Project configuration
├── requirements.txt
└── README.md                     # This file
```

---

## Running the Weather Agent Server

Start the weather agent server on port 10003:

```bash
uv run python -m agents.weather_agent --host localhost --port 10003
```

The server will:
- Start on `http://localhost:10003`
- Provide agent metadata at `http://localhost:10003/.well-known/agent-card.json`
- Support streaming responses
- Handle weather queries for any location

---

## Running the Client

Connect to the weather agent using the interactive client:

```bash
uv run python -m client.client --agent-url http://127.0.0.1:10003
```

### Example Usage

```
Connecting to agent at http://127.0.0.1:10003...
Connected. Streaming supported: True

Weather Agent Client Ready!
Enter your weather query below. Type 'exit' to quit.

Ask about weather: Get me a weather of tokyo

Processing: Get me a weather of tokyo
Searching for current weather in tokyo...
Processing weather data and formatting response...

Weather Report:
Here's the weather for Tokyo, Japan:

*   **Temperature:** 27.1°C (80.8°F), but feels like 29.0°C (84.2°F) 🌡️
*   **Condition:** Partly cloudy 🌤️
*   **Humidity:** 70% 💧
*   **Wind:** From the North at 12.6 km/h 💨

Looks like it might be a bit muggy! Consider wearing light, breathable clothing. Since it's partly cloudy, maybe a good time for an evening 
stroll! 🚶‍♀️🚶‍♂️

```

---

## Resources

- [A2A Protocol](https://a2a-protocol.org/latest/)
- [A2A Github](https://github.com/a2aproject/a2a-samples)
- [Google AI Studio](https://aistudio.google.com)
- [Tavily API Documentation](https://docs.tavily.com)
- [LangChain Documentation](https://python.langchain.com/)