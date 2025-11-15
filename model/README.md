# OpenAI Assistants API Interactive Chat Client

An interactive Python client for chatting with your custom OpenAI Assistants in real-time.

## Features

- 💬 **Interactive chat mode** - Have natural conversations with your assistant
- 📚 **Uses your custom assistant** - Works with assistants you've configured on the OpenAI platform
- 📄 **Document-aware** - Leverages any files you've uploaded to your assistant
- 🔄 **Conversation context** - Maintains context throughout the chat session
- 🛑 **Easy exit** - Type 'STOP' to end the conversation

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Get your Assistant ID:**
   - Go to [OpenAI Platform - Assistants](https://platform.openai.com/assistants)
   - Find or create your assistant with uploaded documents
   - Copy the Assistant ID (starts with `asst_...`)

3. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY=sk-proj-your-key-here
   export ASSISTANT_ID=asst_your-assistant-id-here
   ```

   **Tip:** Add these to your `~/.zshrc` or `~/.bashrc` to make them permanent:
   ```bash
   echo 'export OPENAI_API_KEY=sk-proj-your-key' >> ~/.zshrc
   echo 'export ASSISTANT_ID=asst_your-id' >> ~/.zshrc
   source ~/.zshrc
   ```

## Usage

Run the interactive chat:
```bash
python test_assistant.py
```

### Example Session

```
🤖 Interactive Assistant Chat

✓ Connected to: My Custom Assistant
✓ Chat session started (Thread: thread_abc123)

Type your questions below. Type 'STOP' to exit.

============================================================

You: What information do you have about my project?
