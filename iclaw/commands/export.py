import pyperclip
from datetime import datetime


def handle_export_command(messages, tool_logs):
    if not messages:
        print("No conversation history to export.")
        return

    lines = [
        "# Conversation Export",
        f"Exported at: {datetime.now().isoformat()}",
        "",
        "=" * 80,
        "",
    ]

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")

        lines.append(f"## {role} (Message {i + 1})")
        lines.append("")

        if content:
            lines.append(content)

        if msg.get("tool_calls"):
            lines.append("")
            lines.append("**Tool Calls:**")
            for tc in msg["tool_calls"]:
                lines.append(
                    f"- {tc['function']['name']}: {tc['function']['arguments']}"
                )

        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    if tool_logs:
        lines.append("")
        lines.append("# Tool Execution Logs")
        lines.append("")
        for log in tool_logs:
            ts = datetime.fromtimestamp(log["timestamp"]).strftime("%H:%M:%S")
            lines.append(f"**[{ts}] {log['function']}**")
            lines.append(f"Args: {log['args']}")
            lines.append(f"Result: {log['result']}")
            lines.append("")
            lines.append("-" * 80)
            lines.append("")

    output = "\n".join(lines)
    pyperclip.copy(output)
    print(
        f"Exported {len(messages)} messages and {len(tool_logs)} tool logs to clipboard"
    )
