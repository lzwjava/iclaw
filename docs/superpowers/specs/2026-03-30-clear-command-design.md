# `/clear` Command Design

**Date:** 2026-03-30
**Status:** Approved

## Overview

Add a `/clear` command to the iclaw CLI that empties the conversation history, allowing users to start fresh without restarting the application.

## Requirements

1. Clear the `messages` list (conversation history)
2. Clear the `last_reply` variable (used by `/copy`)
3. Show confirmation message after clearing
4. Start completely empty (no greeting re-displayed)

## User Answers

- **Initial state:** Completely empty (no greeting preserved)
- **Copy buffer:** Clear it (reset `last_reply` to `None`)
- **Feedback:** Show confirmation message

## Implementation Approach

**Simple In-Place Clear** (chosen for minimal code footprint)

### Changes

**File:** `iclaw/main.py`

1. Add to `COMMANDS_HELP` (line ~31):
   ```python
   ("/clear", "Clear conversation history"),
   ```

2. Add handler after `/status` (line ~218):
   ```python
   if user_input == "/clear":
       messages.clear()
       last_reply = None
       print("Conversation history cleared.")
       continue
   ```

### Behavior

- Resets conversation to empty state
- User can immediately send new messages
- `/copy` won't work until next assistant response
- No system messages re-displayed

## Trade-offs

**Pros:**
- Minimal code (4 lines total)
- Follows existing command pattern
- No new files needed

**Cons:**
- None identified

## Alternatives Considered

**Dedicated Command Module:** Create `iclaw/commands/clear.py` — rejected as overkill for 2 lines of logic.
