---
name: using-niri
description: Use for non-browser desktop automation when on Linux, such as spawning, screenshotting or controlling an app.
---

# Using Niri

- It's important that you don't disrupt the host's focused window, workspace, pointer, and clipboard as this device is often in use by the user. While still being able to do all the things you need to test, verify and automate.
- `niri-harness` is a self-healing cli you should use for most operations. If it has something that you think belongs in there, or has friction, reasonably resolve with it. Keep it scoped to niri related things.
- Consider `niri-harness` to be a powertool that generally has better solutions and utilities than niri's lower level commands.
- Notice if you are on wayland or X11. Some desktop tools are oriented around one and should generally not be used on the other.

## Recursion

Recursion is generally for when you're spawning and testing apps to limit disruption.

```text
niri -c /dev/null -- <command> [args...]
```

The child inherits a unique nested `WAYLAND_DISPLAY` and `NIRI_SOCKET`, so agents may recurse concurrently without coordination. Keep control and cleanup in that inherited environment; never use `--session`, scan for sockets, or `pkill niri`. Exit the owned instance with `niri msg action quit --skip-confirmation`. The host window rule maps nested Niri windows unfocused.
