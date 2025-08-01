# A2A Weather System

A hands-on implementation of the Agent-to-Agent (A2A) protocol featuring a weather information service. This project demonstrates how autonomous agents can discover and communicate with each other using standardized endpoints and message formats.

## Overview

The Agent-to-Agent (A2A) protocol revolutionizes how autonomous agents discover and communicate. Instead of complex integration setups, A2A provides a standardized way for agents to find each other and exchange information seamlessly.

This project includes:
- **Weather Server Agent**: Provides weather information using Tavily API for real-time data and Google Gemini for AI-enhanced responses
- **Weather Client Agent**: Discovers and communicates with the server using the A2A protocol

## Features

- 🔍 **Agent Discovery**: Automatic agent discovery through standardized endpoints  
- 🌤️ **Real-time Weather Data**: Powered by Tavily API for current weather information
- 🤖 **AI-Enhanced Responses**: Google Gemini provides concise, well-formatted weather summaries
- 📡 **Standardized Communication**: Full A2A protocol compliance with structured message formats
- 🔄 **Task Management**: Unique task IDs and proper response handling

## Project Structure

```
a2a-weather/
├── server/
│   └── weather_server.py    # A2A server agent
├── client/
│   └── weather_client.py    # A2A client agent
├── requirements.txt         # Python dependencies
├── .env                    # API keys (create this)
└── README.md              # This file
```

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- API Keys:
  - [Tavily API Key](https://tavily.com) (free tier available)
  - [Google Gemini API Key](https://aistudio.google.com) (free tier available)

## Setup

### 1. Clone and Setup Environment

```bash
# Create project directory
mkdir a2a-weather
cd a2a-weather

# Initialize with uv (recommended)
uv init
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or with standard Python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

Create `requirements.txt`:
```
flask==3.0.0
requests==2.31.0
tavily-python>=0.3.0
python-dotenv==1.0.0
tiktoken>=0.7.0
langchain-google-genai==1.0.10
```

Install packages:
```bash
# With uv
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file in the project root:
```env
TAVILY_API_KEY=your_tavily_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

#### Getting API Keys:

**Tavily API Key:**
1. Visit [tavily.com](https://tavily.com)
2. Sign up for a free account
3. Get your API key from the dashboard

**Google Gemini API Key:**
1. Visit [AI Studio](https://aistudio.google.com)
2. Log in with your Google account
3. Click "Get API Key"
4. Create a new API key and copy it

## Usage

### 1. Start the Weather Server

```bash
cd a2a-weather
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv run python server/weather_server.py
```

The server will start on `http://127.0.0.1:5000`

### 2. Run the Client (in another terminal)

```bash
cd a2a-weather
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv run python client/weather_client.py
```

### Expected Output

```
A2A Weather Client Demo
========================================
Discovering weather agent...
Found: WeatherBot - Get current weather information for any city using real-time data with AI-enhanced summaries

Getting weather for London...
Response:
Here's the London weather summary for August 1st, 2025, at 6:00 PM:

The current temperature in London is 18.4°C (65.1°F) with partly cloudy skies. 
Humidity is at 68%. Wind is blowing from the north at 8.1 mph (13.0 kph), 
with gusts up to 11.1 mph (17.9 kph). Pressure is 1016.0 mb.

----------------------------------------
```

## A2A Protocol Flow

1. **Discovery**: Client calls `/.well-known/agent.json` to discover agent capabilities
2. **Task Creation**: Client generates unique UUID and wraps query in A2A message structure  
3. **Task Sending**: Client sends POST to `/tasks/send` with JSON payload
4. **Processing**: Server extracts query, searches Tavily, and processes with Gemini
5. **Response**: Server returns A2A-compliant JSON with enhanced weather information
6. **Extraction**: Client processes response and displays formatted weather data

## API Endpoints

### Server Endpoints

#### `GET /.well-known/agent.json`
Agent discovery endpoint returning capabilities:
```json
{
  "name": "WeatherBot",
  "description": "Get current weather information for any city using real-time data with AI-enhanced summaries",
  "url": "http://127.0.0.1:5000",
  "version": "1.0",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  }
}
```

#### `POST /tasks/send`
Main task handling endpoint accepting A2A message format:
```json
{
  "id": "unique-task-id",
  "message": {
    "role": "user",
    "parts": [{"text": "weather in London"}]
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Next Steps

This implementation covers the foundational A2A protocol mechanics. Future enhancements could include:

- **Multi-agent systems**: Multiple agents discovering and communicating with each other
- **Streaming responses**: Real-time data streaming for live weather updates  
- **Push notifications**: Weather alerts and updates pushed to clients
- **Google Agent Development Kit (ADK)**: Integration with Google's official A2A tools
- **Model Context Protocol (MCP)**: Enhanced context sharing between agents

## Resources

- [A2A Protocol](https://a2a-protocol.org/latest/)
- [A2A Github](https://github.com/a2aproject/a2a-samples)
- [Tavily API Documentation](https://docs.tavily.com)
- [Google AI Studio](https://aistudio.google.com)
- [Flask Documentation](https://flask.palletsprojects.com)

## Support

For questions and support:
- Check the troubleshooting section above
- Review the API documentation for Tavily and Google Gemini
- Open an issue in this repository for bugs or feature requests