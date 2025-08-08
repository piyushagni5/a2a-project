#!/usr/bin/env python3

import asyncio
import json
from typing import Any
from uuid import uuid4

import click
import httpx
from rich import print as rich_print
from rich.syntax import Syntax
from rich.console import Console

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import SendMessageRequest, SendStreamingMessageRequest, MessageSendParams, TaskState, SendMessageSuccessResponse, Message, TextPart, Part

console = Console()

def print_json_response(data: Any, title: str = "Response") -> None:
    """Print JSON response with rich formatting."""
    try:
        # Handle different data types
        if hasattr(data, 'model_dump'):
            json_data = data.model_dump()
        elif isinstance(data, (dict, list)):
            json_data = data
        else:
            # For complex objects, convert to string representation
            json_data = {"content": str(data)}
        
        json_str = json.dumps(json_data, indent=2, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(f"\n[bold blue]{title}:[/bold blue]")
        console.print(syntax)
    except Exception as e:
        console.print(f"[red]Error formatting response: {e}[/red]")
        console.print(f"Raw data: {data}")

def extract_content_from_response(update: Any) -> str:
    """Extract meaningful content from streaming updates."""
    try:
        # Handle tuple responses (task, response)
        if isinstance(update, tuple) and len(update) >= 2:
            task, response = update[0], update[1]
            
            # Extract from task artifacts
            if hasattr(task, 'artifacts') and task.artifacts:
                for artifact in task.artifacts:
                    # Try to access parts attribute (this seems to be where content is stored)
                    if hasattr(artifact, 'parts') and artifact.parts:
                        for part in artifact.parts:
                            # Try to get text from part root
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                return part.root.text
                            # Try direct text attribute on part
                            elif hasattr(part, 'text'):
                                return part.text
                    
                    # Try other possible attribute names for content
                    for attr in ['text_content', 'content', 'text', 'data']:
                        if hasattr(artifact, attr):
                            content = getattr(artifact, attr)
                            if content and str(content).strip():
                                return str(content)
                    
                    # Try to access nested content
                    if hasattr(artifact, 'root') and hasattr(artifact.root, 'text'):
                        return artifact.root.text
            
            # Extract from task status messages
            if hasattr(task, 'status') and hasattr(task.status, 'message'):
                msg = task.status.message
                if hasattr(msg, 'parts') and msg.parts:
                    for part in msg.parts:
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            return part.root.text
        
        # Handle direct object responses
        elif hasattr(update, 'root'):
            if hasattr(update.root, 'result'):
                result = update.root.result
                
                # Check for artifacts
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        # Try parts attribute first
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    return part.root.text
                                elif hasattr(part, 'text'):
                                    return part.text
                        
                        # Try other attribute names
                        for attr in ['text_content', 'content', 'text', 'data']:
                            if hasattr(artifact, attr):
                                content = getattr(artifact, attr)
                                if content and str(content).strip():
                                    return str(content)
                        
                        # Try nested content
                        if hasattr(artifact, 'root') and hasattr(artifact.root, 'text'):
                            return artifact.root.text
                
                # Check for status messages
                if hasattr(result, 'status') and hasattr(result.status, 'message'):
                    msg = result.status.message
                    if hasattr(msg, 'parts') and msg.parts:
                        for part in msg.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                return part.root.text
        
        return None
    except Exception as e:
        console.print(f"[yellow]Warning: Error extracting content: {e}[/yellow]")
        return None

def build_message_payload(text: str, task_id: str | None = None, context_id: str | None = None) -> Message:
    """Build message payload for A2A communication."""
    from a2a.types import Role
    return Message(
        kind="message",
        role=Role.user,
        parts=[Part(root=TextPart(kind="text", text=text))],
        message_id=uuid4().hex,
        task_id=task_id,
        context_id=context_id,
    )

async def handle_streaming(client, text: str, task_id: str | None = None, context_id: str | None = None):
    """Handle streaming message with clean output."""
    message = build_message_payload(text, task_id, context_id)
    
    latest_task_id = None
    latest_context_id = None
    input_required = False
    progress_messages = set()  # Track progress messages to avoid duplicates
    has_shown_final_result = False
    
    console.print(f"[cyan]Processing: {text}[/cyan]")
    
    try:
        async for update in client.send_message(message):
            # Extract and display meaningful content (progress updates only)
            content = extract_content_from_response(update)
            if content and content.strip():
                # Only show progress messages (searching, processing), not final results
                if any(keyword in content.lower() for keyword in ['searching', 'processing', 'fetching']):
                    if content not in progress_messages:  # Avoid duplicates
                        console.print(f"[blue]{content}[/blue]")
                        progress_messages.add(content)
            
            # Handle different response formats for continuation
            if isinstance(update, tuple):
                task, _ = update
                if task:
                    if hasattr(task, "context_id"):
                        latest_context_id = task.context_id
                    if hasattr(task, "id"):
                        latest_task_id = task.id
                    if hasattr(task, "status") and hasattr(task.status, "state"):
                        if task.status.state == TaskState.input_required:
                            input_required = True
                        elif task.status.state == TaskState.completed:
                            # Extract and show final weather report
                            if not has_shown_final_result and hasattr(task, 'artifacts') and task.artifacts:
                                for artifact in task.artifacts:
                                    if hasattr(artifact, 'parts') and artifact.parts:
                                        for part in artifact.parts:
                                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                                final_result = part.root.text
                                                console.print(f"\n[bold green]Weather Report:[/bold green]")
                                                console.print(f"[green]{final_result}[/green]")
                                                has_shown_final_result = True
                                                break
                                            elif hasattr(part, 'text'):
                                                final_result = part.text
                                                console.print(f"\n[bold green]Weather Report:[/bold green]")
                                                console.print(f"[green]{final_result}[/green]")
                                                has_shown_final_result = True
                                                break
                                        if has_shown_final_result:
                                            break
                            
                            if not has_shown_final_result:
                                console.print("[yellow]Task completed but no weather data found[/yellow]")
                            return
            elif hasattr(update, "root") and hasattr(update.root, "result"):
                result = update.root.result
                if hasattr(result, "context_id"):
                    latest_context_id = result.context_id
                if hasattr(result, "status") and hasattr(result.status, "state"):
                    if result.status.state == TaskState.input_required:
                        latest_task_id = getattr(result, 'taskId', latest_task_id)
                        input_required = True
                    elif result.status.state == TaskState.completed:
                        return
                        
    except Exception as e:
        console.print(f"[red]Error sending message: {e}[/red]")
        raise

    # Handle multi-turn conversations
    if input_required and latest_task_id and latest_context_id:
        follow_up = console.input("\n[bold yellow]Agent needs more input. Your reply: [/bold yellow]")
        await handle_streaming(client, follow_up, latest_task_id, latest_context_id)

async def handle_non_streaming(client, text: str):
    """Handle non-streaming message with clean output."""
    message = build_message_payload(text)
    
    try:
        result = await client.send_message(message)
        
        # Extract and display content
        content = extract_content_from_response(result)
        if content:
            console.print(f"\n[green]Weather Report:[/green]")
            console.print(f"[green]{content}[/green]")
        else:
            console.print("[yellow]No weather data received[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error sending message: {e}[/red]")
        raise

    # Handle follow-up if needed
    if hasattr(result, 'root') and isinstance(result.root, SendMessageSuccessResponse):
        task = result.root.result
        if hasattr(task, 'status') and task.status.state == TaskState.input_required:
            follow_up = console.input("\n[bold yellow]Agent needs more input. Your reply: [/bold yellow]")
            follow_up_req = SendMessageRequest(
                id=uuid4().hex,
                jsonrpc="2.0",
                method="message/send",
                params=MessageSendParams(message=build_message_payload(follow_up, task.id, task.context_id))
            )
            follow_up_resp = await client.send_message(follow_up_req)
            
            # Extract content from follow-up
            content = extract_content_from_response(follow_up_resp)
            if content:
                console.print(f"\n[green]Follow-up Weather Report:[/green]")
                console.print(f"[green]{content}[/green]")
            else:
                console.print("[yellow]No follow-up weather data received[/yellow]")

async def check_agent_capabilities(agent_url: str) -> bool:
    """Check if the agent supports streaming."""
    try:
        async with httpx.AsyncClient() as http_client:
            # Try new endpoint first, fallback to deprecated one
            for endpoint in ["/.well-known/agent-card.json", "/.well-known/agent.json"]:
                try:
                    response = await http_client.get(f"{agent_url}{endpoint}")
                    if response.status_code == 200:
                        agent_info = response.json()
                        capabilities = agent_info.get("capabilities", {})
                        return capabilities.get("streaming", False)
                except:
                    continue
    except Exception as e:
        console.print(f"[red]Failed to check agent capabilities: {e}[/red]")
    return False

async def main_async(agent_url: str):
    """Main async function for client interaction."""
    console.print(f"[green]Connecting to agent at {agent_url}...[/green]")
    
    # Check agent capabilities
    supports_streaming = await check_agent_capabilities(agent_url)
    console.print(f"[green]Connected. Streaming supported: {supports_streaming}[/green]")
    
    async with httpx.AsyncClient() as http_client:
        try:
            # Get agent card and create client using new API
            card_resolver = A2ACardResolver(http_client, agent_url)
            agent_card = await card_resolver.get_agent_card()
            
            config = ClientConfig(httpx_client=http_client)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            console.print("\n[bold cyan]Weather Agent Client Ready![/bold cyan]")
            console.print("[dim]Enter your weather query below. Type 'exit' to quit.[/dim]\n")
            
            while True:
                try:
                    user_input = console.input("[bold green]Ask about weather: [/bold green]")
                    if user_input.lower().strip() in ['exit', 'quit', 'q']:
                        break
                    
                    if not user_input.strip():
                        console.print("[yellow]Please enter a weather query.[/yellow]")
                        continue
                    
                    console.print()  # Add spacing
                    
                    if supports_streaming:
                        await handle_streaming(client, user_input)
                    else:
                        await handle_non_streaming(client, user_input)
                    
                    console.print()  # Add spacing after response
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Goodbye![/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    console.print("[dim]You can continue with another query...[/dim]")
                    
        except Exception as e:
            console.print(f"[red]Failed to initialize client: {e}[/red]")
            console.print("Please make sure the agent server is running and accessible.")

@click.command()
@click.option('--agent-url', required=True, help='URL of the A2A agent to connect to')
def main(agent_url: str):
    """A2A Client for interacting with weather agents."""
    try:
        asyncio.run(main_async(agent_url))
    except KeyboardInterrupt:
        console.print("\n[yellow]Client terminated by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Client error: {e}[/red]")

if __name__ == "__main__":
    main()