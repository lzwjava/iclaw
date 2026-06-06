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

BROWSER_NAVIGATE_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_navigate",
        "description": "Navigate the browser to a URL and return a snapshot of the page with interactive elements.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to.",
                },
            },
            "required": ["url"],
        },
    },
}

BROWSER_SNAPSHOT_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_snapshot",
        "description": "Get a text snapshot of the current browser page with ref IDs for interactive elements (buttons, links, inputs). Use this to see what's on the page before interacting.",
        "parameters": {
            "type": "object",
            "properties": {
                "full": {
                    "type": "boolean",
                    "description": "If true, also include the full page text content.",
                    "default": False,
                },
            },
        },
    },
}

BROWSER_CLICK_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_click",
        "description": "Click a browser element by its ref ID (e.g. @e1, @e2). Get ref IDs from browser_snapshot.",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "The element ref ID to click (e.g. @e1).",
                },
            },
            "required": ["ref"],
        },
    },
}

BROWSER_TYPE_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_type",
        "description": "Type text into a browser input/textarea by its ref ID. Optionally press Enter to submit.",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "The element ref ID to type into (e.g. @e3).",
                },
                "text": {
                    "type": "string",
                    "description": "The text to type.",
                },
                "submit": {
                    "type": "boolean",
                    "description": "If true, press Enter after typing.",
                    "default": False,
                },
            },
            "required": ["ref", "text"],
        },
    },
}

BROWSER_PRESS_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_press",
        "description": "Press a keyboard key in the browser (Enter, Tab, Escape, ArrowDown, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Key to press (e.g. Enter, Tab, Escape, ArrowDown).",
                },
            },
            "required": ["key"],
        },
    },
}

BROWSER_SCROLL_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_scroll",
        "description": "Scroll the browser page up or down.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Direction to scroll.",
                    "default": "down",
                },
            },
        },
    },
}

BROWSER_SCREENSHOT_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}

BROWSER_CONSOLE_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_console",
        "description": "Get browser console output (log, warn, error messages).",
        "parameters": {
            "type": "object",
            "properties": {
                "clear": {
                    "type": "boolean",
                    "description": "If true, clear the console buffer after reading.",
                    "default": False,
                },
            },
        },
    },
}

BROWSER_BACK_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_back",
        "description": "Navigate back in browser history.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}

BROWSER_CLOSE_TOOL = {
    "type": "function",
    "function": {
        "name": "browser_close",
        "description": "Close the browser and free resources.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}

TOOLS = [
    WEB_SEARCH_TOOL,
    EXEC_COMMAND_TOOL,
    EDIT_TOOL,
    BROWSER_NAVIGATE_TOOL,
    BROWSER_SNAPSHOT_TOOL,
    BROWSER_CLICK_TOOL,
    BROWSER_TYPE_TOOL,
    BROWSER_PRESS_TOOL,
    BROWSER_SCROLL_TOOL,
    BROWSER_SCREENSHOT_TOOL,
    BROWSER_CONSOLE_TOOL,
    BROWSER_BACK_TOOL,
    BROWSER_CLOSE_TOOL,
]
