---
name: using-niri
description: Use for non-browser desktop automation when on Linux, such as spawning, screenshotting or controlling an app.
---

# Using Niri

- The user is often working on this machine, so don't disturb the host's focused window, workspace, pointer, or clipboard.
- `niri-harness` is the right tool for most operations and generally does better than niri's lower-level commands. It's meant to be improved as you go: when it lacks something that belongs in it, or has friction, fix it there, keeping it scoped to niri.
- Check whether you're on Wayland or X11. Some desktop tools are built for one and generally shouldn't be used on the other.

## Recursion

Recursion is mainly for spawning and testing apps without disrupting the host.

```text
niri -c /dev/null -- <command> [args...]
```

The child inherits a unique nested `WAYLAND_DISPLAY` and `NIRI_SOCKET`, so agents can recurse concurrently without coordinating. Keep control and cleanup in that inherited environment; never use `--session`, scan for sockets, or `pkill niri`. Exit the instance you own with `niri msg action quit --skip-confirmation`. The host window rule maps nested Niri windows unfocused.
