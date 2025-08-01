from flask import Flask, request, jsonify
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app, Tavily client, and Gemini LLM
app = Flask(__name__)
tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=os.getenv('GOOGLE_API_KEY'))

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """
    A2A Discovery endpoint - tells other agents what we can do.
    This is the first endpoint any A2A client will call.
    """
    return jsonify({
        "name": "WeatherBot",
        "description": "Get current weather information for any city using real-time data with AI-enhanced summaries",
        "url": "http://127.0.0.1:5000",
        "version": "1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False
        }
    })

@app.route("/tasks/send", methods=["POST"])
def handle_task():
    """
    Main A2A endpoint where clients send tasks.
    This is where the actual work happens.
    """
    try:
        # Get the task data from the A2A client
        task_data = request.get_json()
        task_id = task_data.get("id")
        
        # Extract the user's message text
        user_message = task_data["message"]["parts"][0]["text"]
        
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "Invalid A2A task format"}), 400

    try:
        # Use Tavily to search for weather information
        search_query = f"current weather {user_message}"
        search_results = tavily.search(
            query=search_query,
            search_depth="basic",
            max_results=3
        )
        
        # Combine search results for processing
        raw_weather_data = []
        for result in search_results.get('results', []):
            raw_weather_data.append(f"{result['title']}: {result['content']}")
        
        if raw_weather_data:
            # Use Gemini to create a concise, well-formatted weather summary
            combined_data = "\n\n".join(raw_weather_data)
            
            prompt = f"""
            Based on the following weather search results, provide a concise and well-formatted weather summary for {user_message}.
            
            Raw weather data:
            {combined_data}
            
            Please provide:
            1. Current temperature and conditions
            2. Key weather details (humidity, wind, etc.)
            3. Any relevant weather alerts or notable information
            
            Keep the response under 150 words and make it clear and easy to read.
            """
            
            response = llm.invoke(prompt)
            response_text = response.content
        else:
            response_text = "Sorry, I couldn't find current weather information for that location."
            
    except Exception as e:
        response_text = f"I encountered an error getting weather data: {str(e)}"

    # Return properly formatted A2A response
    return jsonify({
        "id": task_id,
        "status": {"state": "completed"},
        "messages": [
            task_data["message"],  # Echo back original message
            {
                "role": "agent",
                "parts": [{"text": response_text}]
            }
        ]
    })

if __name__ == "__main__":
    print("Starting WeatherBot A2A Agent on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)