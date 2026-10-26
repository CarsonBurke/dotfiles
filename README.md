# dotfiles
 my dotfiles for various apps

See [bin/README.md](bin/README.md) for the executable scripts and model aliases.
See [skills/README.md](skills/README.md) for skill sources, composition, and generation.

## Setup on a new machine

The config directories are symlinked straight into place, so the apps write
their runtime state directly into this working tree:

    ~/.claude       -> claude
    ~/.codex        -> codex
    ~/.agents/skills -> skills
    ~/.omp          -> omp
    ~/.config/fish  -> fish
    ~/.config/nvim  -> nvim
    ~/.config/cosmicbar -> cosmicbar

Codex user skills use the standard `~/.agents/skills` location. Do not link
`~/.codex/skills` to this repository: Codex owns `$CODEX_HOME/skills`.
Bundled system skills are disabled in `codex/config.toml`.

When Orca or another installer also manages `~/.agents/skills`, keep it a real
directory and link each shared skill into it instead of linking the whole
directory. Put the model wrappers and other typed commands on PATH through
`~/.local/bin` either way:

    bin/link-codex-skills
    bin/link-bin

Both are idempotent: they add missing links, keep foreign entries in place, and
drop their own links once a skill or command is renamed or removed. Re-run them
after a pull that touches `skills/` or `bin/`.

Remove the bundled Codex marketplace and its default Browser, Chrome, Computer
Use, LaTeX, Record and Replay, Sites, and Visualize plugins:

    bin/remove-codex-base-plugins

The browser skill also needs its runtime:

    uv tool install --python 3.12 browser-harness==0.1.13

On macOS, the browser skill uses `bin/browser-harness` to start Helium, the
default browser, headless on demand and connect through a loopback-only
debugging endpoint. Other platforms retain browser-harness's native browser
discovery. Chromium refuses remote debugging on the normal profile, so each
start rebuilds a dedicated automation profile from the normal profile's cookies
and Local State. Sign-ins made in Helium carry over at the next start; to pick
up a new one, stop the automation browser and run the task again. The launcher
disables browser-harness telemetry so task code and page output remain local,
and gives each invocation its own transient harness daemon control channel.
Tabs remain shared between local invocations while the browser runs.

Loopback limits the debugging endpoint to the local machine, but it does not
authenticate local processes. Any process running as the user can inspect the
automation browser, and every session it holds, while it is running. Stop the dedicated browser after
sensitive work when no other browser task is active:

    bin/browser-harness --stop

Register the codex config filter once per machine, from the repo root:

    git config filter.codex-config.clean  'bin/codex-config-filter clean %f'
    git config filter.codex-config.smudge 'bin/codex-config-filter smudge %f'

Codex writes per-machine project trust and hook trust hashes into
`codex/config.toml`, all keyed by absolute paths that mean nothing on another
host. The filter keeps those sections in the working tree but out of git, so
the shared settings sync and the local state stops causing churn. Without it
registered git treats the filter as a no-op and that state lands in commits
again — nothing breaks, but the noise comes back.

One wrinkle: once codex has written to the file, `git status` shows it as
modified even though there is nothing to commit, and `git pull` will refuse to
touch it. Settle both with

    git add codex/config.toml

which stages nothing, refreshes the stat cache, and writes the sidecar the
filter restores from. Do that before pulling.
