"""
Interactive chat client for OpenAI Assistants API.
Chat with your custom assistant until you type 'STOP'.
"""

import os
import time
from openai import OpenAI


def wait_for_run_completion(client, thread_id, run_id):
    """Wait for the assistant run to complete and return the status."""
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status in ['completed', 'failed', 'cancelled', 'expired']:
            return run.status
        time.sleep(0.5)


def get_latest_assistant_message(client, thread_id):
    """Retrieve the latest assistant message from the thread."""
    messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
    if messages.data:
        return messages.data[0].content[0].text.value
    return None


def main():
    # Initialize OpenAI client
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your-api-key")
        return
    
    # Set your existing Assistant ID from OpenAI platform
    assistant_id = os.environ.get('ASSISTANT_ID')
    if not assistant_id:
        print("Error: ASSISTANT_ID environment variable not set")
        print("Set it with: export ASSISTANT_ID=asst_...")
        print("Find your Assistant ID at: https://platform.openai.com/assistants")
        return
    
    client = OpenAI(api_key=api_key)
    
    print("🤖 Interactive Assistant Chat\n")
    
    # Load existing Assistant
    try:
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"✓ Connected to: {assistant.name}")
    except Exception as e:
        print(f"Error loading assistant: {e}")
        return
    
    # Create a conversation thread
    thread = client.beta.threads.create()
    print(f"✓ Chat session started (Thread: {thread.id})")
    print("\nType your questions below. Type 'STOP' to exit.\n")
    print("="*60)
    
    # Interactive chat loop
    while True:
        # Get user input
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting chat...")
            break
        
        # Check for exit command
        if user_input.upper() == 'STOP':
            print("\nEnding chat session. Goodbye!")
            break
        
        # Skip empty messages
        if not user_input:
            continue
        
        # Add user message to thread
        try:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )
            
            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            
            # Wait for completion with a simple indicator
            print("\nAssistant: ", end='', flush=True)
            status = wait_for_run_completion(client, thread.id, run.id)
            
            if status == 'completed':
                # Get and display the response
                response = get_latest_assistant_message(client, thread.id)
                if response:
                    print(response)
                else:
                    print("(No response)")
            else:
                print(f"[Error: Run {status}]")
                
        except Exception as e:
            print(f"\n[Error: {e}]")
    
    print("\n" + "="*60)
    print("✅ Chat session ended")


if __name__ == "__main__":
    main()
