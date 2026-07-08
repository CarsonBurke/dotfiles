function bw-redact --description 'Run Bitwarden CLI with the Redact account profile'
    set -lx BITWARDENCLI_APPDATA_DIR "$HOME/.config/Bitwarden CLI Redact"
    bw $argv
end
