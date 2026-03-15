WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current, real-time, or recent information to help answer the user's question.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default 20).",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    },
}

EXEC_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "exec",
        "description": "Execute a shell command on the local system and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
            },
            "required": ["command"],
        },
    },
}

EDIT_TOOL = {
    "type": "function",
    "function": {
        "name": "edit",
        "description": "Apply a unified diff edit to a file on the local system.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to edit.",
                },
                "edit_content": {
                    "type": "string",
                    "description": "The unified diff content to apply.",
                },
            },
            "required": ["file_path", "edit_content"],
        },
    },
}

TOOLS = [WEB_SEARCH_TOOL, EXEC_COMMAND_TOOL, EDIT_TOOL]
