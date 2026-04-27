---
name: validate-frontend
description: Use agent-browser directly to validate frontend-affecting changes in real web apps or websites after implementation.
---

# Validate Frontend

Use this skill when the task changes frontend behavior or presentation and the result should be validated in a real browser.

- Use `agent-browser` directly. Do not use repo-specific wrappers like `bun ab` unless the user explicitly asks for them.
- Use this for browser-accessible frontends: local dev servers, staging apps, production websites, or other web UIs.
- Run browser validation after frontend-affecting changes instead of stopping at code inspection. This includes layout, styling, copy, forms, navigation, loading states, interactivity, responsive behavior, and console/runtime health.
- If a more specialized skill exists for the exact environment, prefer that skill. Example: use an Electron-specific skill for Electron UI debugging.

## Browser Workflow

- If the app is already reachable by URL, open it directly with `agent-browser open <url>`.
- If Chrome is already running with remote debugging, connect with `agent-browser --auto-connect ...` or `agent-browser --cdp <port> ...`.
- If the frontend was just edited, reload or reopen before validating. Do not assume prior browser state is still correct after hot reloads or rebuilds.
- Start from the changed surface first, then exercise the nearest adjacent user flow that could regress.

## Minimum Validation Pass

- Load the target page and wait for it to settle.
- Capture structure with `agent-browser snapshot -i`.
- Capture visuals with `agent-browser screenshot` when appearance matters.
- Exercise the changed interaction with `click`, `fill`, `press`, `select`, or `find ...`.
- Check `agent-browser console` and `agent-browser errors` for runtime problems.
- If the change is responsive or stateful, validate the affected variant instead of assuming it works.

## Useful Commands

```bash
agent-browser open http://localhost:3000/settings
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser screenshot
agent-browser click @e5
agent-browser fill @e8 "test@example.com"
agent-browser find text "Save" click
agent-browser console
agent-browser errors
agent-browser --auto-connect snapshot -i
agent-browser --cdp 9222 screenshot
```

## Reporting

- Report what you validated, not just that you "checked it".
- If validation fails, include the exact failing behavior, any visible error text, and whether the failure came from UI behavior, console errors, or page load issues.
- If you could not validate, state the concrete blocker: missing URL, dev server not running, auth wall, broken build, missing browser connection, or similar.
