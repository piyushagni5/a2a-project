from a2a.server.events import EventQueue
from a2a.server.agent_execution import RequestContext, AgentExecutor
from a2a.types import TaskArtifactUpdateEvent, TaskStatusUpdateEvent, TaskStatus, TaskState
from a2a.utils import new_task, new_text_artifact, new_agent_text_message

from .agent import WeatherAgent

class WeatherAgentExecutor(AgentExecutor):
    """
    Executor that bridges the A2A server infrastructure with the WeatherAgent.
    Handles task lifecycle management, event queue orchestration, and multi-turn conversation state.
    """
    
    def __init__(self):
        self.agent = WeatherAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute weather agent task with streaming updates."""
        query = context.get_user_input()
        task = context.current_task
        
        if not context.message:
            raise Exception('No message provided')
        
        # Create new task for fresh interactions
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        # Stream agent responses and convert to A2A events
        async for event in self.agent.stream(query, task.context_id):
            
            if event['is_task_complete']:
                # Send final weather result artifact
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        taskId=task.id,
                        contextId=task.context_id,
                        artifact=new_text_artifact(
                            name='weather_report',
                            description='Current weather information for the requested location.',
                            text=event['content'],
                        ),
                        append=False,
                        lastChunk=True,
                    )
                )
                # Mark task as completed
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,
                        contextId=task.context_id,
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                    )
                )
            
            elif event['require_user_input']:
                # Request additional input from user (e.g., location)
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,
                        contextId=task.context_id,
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                event['content'],
                                task.context_id,
                                task.id
                            ),
                        ),
                        final=True,
                    )
                )
            
            else:
                # Send progress updates
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,
                        contextId=task.context_id,
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(
                                event['content'],
                                task.context_id,
                                task.id
                            ),
                        ),
                        final=False,
                    )
                )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel operation (not supported in this implementation)."""
        raise Exception('Cancel not supported')