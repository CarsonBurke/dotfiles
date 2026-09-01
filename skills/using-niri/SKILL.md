---
name: using-niri
description: Use for non-browser desktop automation when Niri is the active Linux compositor, including window control, focus-safe capture, and isolated nested sessions.
---

# Using Niri

Preserve the host's focused window, workspace, pointer, and clipboard. Prefer explicit targets and background interfaces; do not make foreground automation acceptable by restoring focus afterward.

## Routing

- Browser or web UI: use `browser-harness`.
- Native app contents: use the computer-use skill and Orca's semantic actions. Do not use `--restore-window`; recurse if the app cannot operate in the background.
- Desktop topology, capture, and window management: use Niri IPC.

## Host-safe IPC

- Discover with `niri msg -j windows`, `workspaces`, `outputs`, and `focused-window`. Niri and Orca window IDs are unrelated.
- Target actions explicitly with `--id` or `--window-id`; inspect action help because flag names differ. Pass `--focus false` when available.
- If an action could affect focus, snapshot the host window/workspace and verify them afterward. Restore only when the action demonstrably focused its own target.
- Avoid interactive selectors, the overview, screenshot UI, synthetic input, and X11-oriented tools such as `wmctrl` and `xdotool`.
- Use a bounded `niri msg -j event-stream` instead of polling for lifecycle changes.

## Capture

Niri's `screenshot`, `screenshot-screen`, and `screenshot-window` actions always replace the clipboard and emit a desktop notification. Keep those actions for user-initiated screenshots; their notification is intentional. Never disable or filter Niri screenshot notifications globally.

For automated capture, do not invoke a Niri screenshot action:

- Native app contents: use Orca's semantic capture.
- Browser contents: use `browser-harness`.
- Exact output or region pixels: use `grim`, which uses the compositor's screencopy protocol without changing the clipboard or sending a notification.
- Repeated isolated UI capture: use `niri-harness`; its transient frames stay in memory and only requested artifacts are encoded.

Do not fall back to a Niri screenshot action when an automated capture backend fails: that turns a background inspection into a clipboard mutation and notification.

## Recursion

```text
niri -c /dev/null -- <command> [args...]
```

The child inherits a unique nested `WAYLAND_DISPLAY` and `NIRI_SOCKET`, so agents may recurse concurrently without coordination. Keep control and cleanup in that inherited environment; never use `--session`, scan for sockets, or `pkill niri`. Exit the owned instance with `niri msg action quit --skip-confirmation`. The host window rule maps nested Niri windows unfocused.
