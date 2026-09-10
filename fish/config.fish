# opencode
fish_add_path /home/marvin/.opencode/bin

# >>> grok installer >>>
fish_add_path $HOME/.grok/bin
# <<< grok installer <<<

# Keep local binaries available without letting them shadow mise-managed tools.
fish_add_path --append --move $HOME/.local/bin
# Prefer mise-managed executables when duplicate tools are installed.
fish_add_path --prepend --move $HOME/.local/share/mise/shims

# CachyOS-style listings (eza). Install: `sudo pacman -S eza` or `cargo install eza`
if command -q eza
    alias ls 'eza -al --color=always --group-directories-first --icons=always'
    alias la 'eza -a --color=always --group-directories-first --icons=always'
    alias ll 'eza -l --color=always --group-directories-first --icons=always'
    alias lt 'eza -aT --color=always --group-directories-first --icons=always'
    alias l. "eza -a | string match -r '^\\.'"
end
