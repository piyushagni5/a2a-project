import requests
import uuid

class WeatherClient:
    def __init__(self, server_url="http://127.0.0.1:5000"):
        self.server_url = server_url
        self.agent_info = None
    
    def discover_agent(self):
        """
        Step 1: Discover the weather agent using A2A discovery flow.
        """
        discovery_url = f"{self.server_url}/.well-known/agent.json"
        
        try:
            response = requests.get(discovery_url)
            response.raise_for_status()
            self.agent_info = response.json()
            return self.agent_info
        except requests.exceptions.RequestException as e:
            raise Exception(f"Could not discover agent: {str(e)}")
    
    def ask_weather(self, location):
        """
        Step 2: Send a weather query to the agent using A2A task format.
        """
        if not self.agent_info:
            raise Exception("Agent not discovered. Call discover_agent() first.")
        
        # Create unique task ID
        task_id = str(uuid.uuid4())
        
        # Build A2A task payload
        task_payload = {
            "id": task_id,
            "message": {
                "role": "user",
                "parts": [{"text": f"weather in {location}"}]
            }
        }
        
        # Send task to server
        task_url = f"{self.server_url}/tasks/send"
        
        try:
            response = requests.post(task_url, json=task_payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract agent's response from A2A message structure
            messages = result.get("messages", [])
            if messages and len(messages) > 1:
                return messages[-1]["parts"][0]["text"]
            else:
                return "No response received"
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Weather request failed: {str(e)}")

def main():
    """
    Demo function showing how to use the A2A weather client.
    """
    client = WeatherClient()
    
    print("A2A Weather Client Demo")
    print("=" * 40)
    
    try:
        # Step 1: Discover the weather agent
        print("Discovering weather agent...")
        agent_info = client.discover_agent()
        print(f"Found: {agent_info['name']} - {agent_info['description']}")
        
        # Step 2: Ask for weather in different cities
        cities = ["London", "Tokyo", "New York"]
        
        for city in cities:
            print(f"\nGetting weather for {city}...")
            weather_response = client.ask_weather(city)
            print(f"Response:\n{weather_response}\n")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()