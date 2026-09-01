#!/usr/bin/env bash
set -euo pipefail

readonly source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly libexec_dir="${HOME}/.local/libexec"
readonly unit_dir="${HOME}/.config/systemd/user"
readonly proxy_binary="${libexec_dir}/ivpn-optin-proxy"

tmp_file=""
cleanup() {
  if [[ -n "$tmp_file" ]]; then
    rm -f -- "$tmp_file"
  fi
}
trap cleanup EXIT

atomic_install() {
  local source=$1
  local destination=$2
  local mode=$3

  tmp_file="$(mktemp --tmpdir="$(dirname -- "$destination")" ".$(basename -- "$destination").XXXXXX")"
  install -m "$mode" "$source" "$tmp_file"
  mv -f -- "$tmp_file" "$destination"
  tmp_file=""
}

mkdir -p -- "$libexec_dir" "$unit_dir"
tmp_file="$(mktemp --tmpdir="$libexec_dir" .ivpn-optin-proxy.XXXXXX)"
bun build --compile --minify --outfile "$tmp_file" "$source_dir/ivpn-optin-proxy.mjs"
chmod 0755 -- "$tmp_file"
mv -f -- "$tmp_file" "$proxy_binary"
tmp_file=""

atomic_install "$source_dir/ivpn-optin-proxy-supervisor" "$libexec_dir/ivpn-optin-proxy-supervisor" 0755
atomic_install "$source_dir/ivpn-optin-proxy.mjs" "$libexec_dir/ivpn-optin-proxy.mjs" 0644
atomic_install "$source_dir/ivpn-optin-proxy.service" "$unit_dir/ivpn-optin-proxy.service" 0644

systemctl --user daemon-reload
systemctl --user enable --now ivpn-optin-proxy.service
systemctl --user restart ivpn-optin-proxy.service
