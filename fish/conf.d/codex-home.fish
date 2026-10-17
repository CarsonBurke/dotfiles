# Orca injects a per-pane CODEX_HOME under ~/.config/orca/codex-accounts/<uuid>/home.
# That path pushes Codex's app-server control socket past the Unix socket path
# limit (SUN_LEN), so the daemon never starts. Fall back to the real ~/.codex
# while leaving any CODEX_HOME set outside Orca untouched.
if set -q CODEX_HOME; and string match -q -- '*/orca/codex-accounts/*' $CODEX_HOME
    set -e CODEX_HOME
end
