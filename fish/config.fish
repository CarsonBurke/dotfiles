# opencode
fish_add_path /home/marvin/.opencode/bin

# >>> grok installer >>>
fish_add_path $HOME/.grok/bin
# <<< grok installer <<<

# CachyOS-style listings (eza). Install: `sudo pacman -S eza` or `cargo install eza`
if command -q eza
    alias ls 'eza -al --color=always --group-directories-first --icons=always'
    alias la 'eza -a --color=always --group-directories-first --icons=always'
    alias ll 'eza -l --color=always --group-directories-first --icons=always'
    alias lt 'eza -aT --color=always --group-directories-first --icons=always'
    alias l. "eza -a | string match -r '^\\.'"
end
