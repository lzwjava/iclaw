import json
from datetime import datetime


def handle_export_command(messages, tool_logs):
    if not messages:
        print("No conversation history to export.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"iclaw_session_{timestamp}.json"

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "messages": messages,
        "tool_logs": tool_logs,
    }

    with open(filename, "w") as f:
        json.dump(export_data, f, indent=2)

    print(
        f"Exported {len(messages)} messages and {len(tool_logs)} tool logs to {filename}"
    )
