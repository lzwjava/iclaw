"""Handle /compact command to compress conversation history using LLM."""


def handle_compact_command(messages, chat_fn, copilot_token, current_model):
    """Compress conversation history using LLM to summarize context."""
    if not messages:
        print("No conversation history to compact.")
        return messages

    prompt = """Summarize the conversation history below into a concise context summary that preserves:
1. Key decisions and outcomes
2. Important code changes or file references
3. Current task or goal
4. Critical technical details

Be extremely concise. Output only the summary, no preamble.

Conversation history:
"""

    history_text = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if content:
            history_text += f"{role}: {content}\n\n"

    compact_messages = [{"role": "user", "content": prompt + history_text}]

    try:
        response = chat_fn(compact_messages, copilot_token, current_model, tools=None)
        summary = response.get("content", "")

        if summary:
            new_messages = [
                {
                    "role": "system",
                    "content": f"Previous conversation summary:\n{summary}",
                }
            ]
            print(f"Compacted {len(messages)} messages into summary.")
            return new_messages
        else:
            print("Failed to compact: no summary generated.")
            return messages
    except Exception as e:
        print(f"Error compacting history: {e}")
        return messages
