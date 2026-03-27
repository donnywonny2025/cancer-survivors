---
description: How to use the browser for this project — single persistent window, no new tabs
---

# Browser Usage Rules (MANDATORY)

## Layout
- The user runs a SPLIT SCREEN: browser on the LEFT, Antigravity on the RIGHT of the right monitor.
- **NEVER resize the browser window.** Do not maximize. Do not change dimensions. Leave it exactly as the user positioned it.

## Single Tab Policy
- **ONE TAB ONLY.** Never open new tabs. Never create new windows.
- If there are extra tabs, close them immediately before doing anything else.
- Navigate within the existing active tab using URL changes only.

## Persistence
- This browser must NEVER be closed. It is the "God Browser."
- Cookies and session state must be preserved across all interactions.
- If a page doesn't load, retry in the same tab. Do not open a new tab.

## Subagent Rules
- Every `browser_subagent` call MUST include these instructions:
  1. "Do NOT open new tabs or windows."
  2. "Do NOT resize or maximize the browser window."
  3. "Navigate within the current active tab only."
  4. "If there are extra tabs open, close them first."
  5. "Do NOT call browser_resize_window."

## What This Browser Is For
- Showing the user web pages (router admin, GitHub, documentation, etc.)
- The user looks at it on their left screen while working in Antigravity on the right.
- All browsing happens here. No exceptions.
