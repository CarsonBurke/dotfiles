#!/bin/sh
# Keep resume remapping in dist/cli.js so bun update cannot restore a
# stock ~/.bun/bin/omp symlink and drop child-ID lookup.
set -eu

DIST="${HOME}/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/dist"
CLI="${DIST}/cli.js"
UPSTREAM="${DIST}/cli.upstream.js"
BUN_BIN="${HOME}/.bun/bin/omp"
MARKER="OMP_RESUME_SHIM"

if [ ! -f "${CLI}" ]; then
	echo "omp resume shim: missing ${CLI}" >&2
	exit 1
fi

if grep -q "${MARKER}" "${CLI}"; then
	if [ ! -f "${UPSTREAM}" ]; then
		echo "omp resume shim: stub present but ${UPSTREAM} missing" >&2
		exit 1
	fi
else
	mv -f "${CLI}" "${UPSTREAM}"
	cat > "${CLI}" <<'EOF'
#!/usr/bin/env bun
// OMP_RESUME_SHIM
import { spawn } from "bun";
import * as path from "node:path";
import { rewriteOmpResumeArgv } from "/home/marvin/.omp/bin/resolve-omp-resume.ts";

const UPSTREAM = path.resolve(import.meta.dir, "cli.upstream.js");

if (process.argv[2] === "--omp-resolve") {
	for (const arg of rewriteOmpResumeArgv(process.argv.slice(3))) {
		process.stdout.write(`${arg}\n`);
	}
	process.exit(0);
}

const args = rewriteOmpResumeArgv(process.argv.slice(2));
const proc = spawn(["bun", UPSTREAM, ...args], {
	stdin: "inherit",
	stdout: "inherit",
	stderr: "inherit",
});
process.exitCode = await proc.exited;
EOF
	chmod +x "${CLI}"
fi

mkdir -p "$(dirname "${BUN_BIN}")"
ln -sfn "${CLI}" "${BUN_BIN}"
echo "omp resume shim: ${CLI} -> ${UPSTREAM}"
