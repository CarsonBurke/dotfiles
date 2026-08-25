# dotfiles
 my dotfiles for various apps

## Setup on a new machine

The config directories are symlinked straight into place, so the apps write
their runtime state directly into this working tree:

    ~/.claude       -> claude
    ~/.codex        -> codex
    ~/.omp          -> omp
    ~/.config/fish  -> fish
    ~/.config/nvim  -> nvim
    ~/.config/cosmicbar -> cosmicbar

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
