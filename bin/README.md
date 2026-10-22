# `bin/` scripts

## Model launchers

These scripts set a model and effort level, then pass command-line arguments to
the underlying CLI. Keep this table in sync when changing a launcher.

| Script | CLI | Model | Effort / thinking | Purpose |
| --- | --- | --- | --- | --- |
| `claudeopus` | Claude | `claude-opus-5-5` | medium | Opus shorthand |
| `claudefable` | Claude | `claude-fable-5-1` | high | Fable shorthand |
| `codexsol` | Codex | `gpt-6-sol` | medium | Sol shorthand |
| `codexluna` | Codex | `gpt-6-luna` | high | Luna shorthand |
| `codexastra` | Codex | `gpt-6-astra` | medium | Astra shorthand |
| `codexcheap`, `codex-cheap` | Codex | `gpt-6-luna` | high | Luna aliases |
| `commits-push` | Codex | `gpt-6-luna` | high | Run `/commits-push` |
| `ompclaude` | OMP | `claude-opus-5-5` | medium | Opus alias |
| `ompfable` | OMP | `claude-fable-5-1` | high | Fable alias |
| `ompcodex`, `ompastra` | OMP | `gpt-6-astra` | medium | Astra aliases |
| `ompcheap` | OMP | `gpt-6-luna` | high | Luna alias |
| `ompgrok` | OMP | `grok-4.6` | high | Grok alias |

`commits-push` launches a fixed slash command; the other model launchers pass
through their arguments with `"$@"`.

## Other scripts

| Script | Purpose |
| --- | --- |
| `browser-harness` | Run browser-harness against a dedicated Brave profile on macOS. |
| `browser-harness-import-helium-auth` | Copy allowlisted GitHub and Vercel cookies from Helium into that profile. |
| `bw-redact` | Use a separate Bitwarden CLI profile for Redact. |
| `codex-config-filter` | Keep machine-local Codex state out of tracked config. |
| `link-bin` | Link the typed-by-hand commands into `~/.local/bin`. |
| `link-codex-skills` | Link each shared skill into `~/.agents/skills`. |
| `muse` | Launch the local Muse installation with its configured flags. |
| `niri-duplicate-window` | Duplicate the focused window. |
| `niri-ide-from-terminal` | Open the IDE at the focused terminal's directory. |
| `niri-open-ide` | Open the configured IDE. |
| `niri-park-codex-voice-overlay` | Keep the Codex voice overlay off the visible workspaces. |
| `niri-terminal-at-editor` | Open a terminal at the focused editor's project. |
| `orca-import-helium-cookies` | Import Helium cookies into Orca's browser profile. |
| `remove-codex-base-plugins` | Remove the bundled Codex marketplace and its default plugins. |
