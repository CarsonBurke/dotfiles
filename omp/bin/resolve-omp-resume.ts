import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const SESSION_ID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RESUME_FLAGS: Record<string, true> = {
	"--resume": true,
	"-r": true,
	"--session": true,
	"--fork": true,
};

export function getOmpSessionsRoot(): string {
	return path.join(os.homedir(), ".omp", "agent", "sessions");
}

export function looksLikeOmpSessionId(value: string): boolean {
	return SESSION_ID_RE.test(value) && !value.includes("/") && !value.includes("\\");
}

export function resolveInteractiveSessionFile(sessionFile: string): string {
	let current = path.resolve(sessionFile);
	for (let depth = 0; depth < 8; depth++) {
		const parentSessionFile = `${path.dirname(current)}.jsonl`;
		if (!fs.existsSync(parentSessionFile)) return current;
		current = parentSessionFile;
	}
	return current;
}

function headerIdFromPrefix(content: string): string | undefined {
	for (const rawLine of content.split(/\r?\n/)) {
		const line = rawLine.trim();
		if (!line) continue;
		if (line.includes('"type":"title"')) continue;
		const match = line.match(/"type"\s*:\s*"session"[\s\S]*?"id"\s*:\s*"([^"]+)"/);
		if (match?.[1]) return match[1];
		return undefined;
	}
	return undefined;
}

export function findInteractiveSessionFileById(
	sessionArg: string,
	sessionsRoot: string = getOmpSessionsRoot(),
): string | undefined {
	const needle = sessionArg.toLowerCase();
	const stack = [sessionsRoot];
	while (stack.length > 0) {
		const dir = stack.pop();
		if (!dir) continue;
		let entries: fs.Dirent[];
		try {
			entries = fs.readdirSync(dir, { withFileTypes: true });
		} catch {
			continue;
		}
		for (const entry of entries) {
			const full = path.join(dir, entry.name);
			if (entry.isDirectory()) {
				stack.push(full);
				continue;
			}
			if (!entry.isFile() || !entry.name.endsWith(".jsonl")) continue;
			const fileName = entry.name.slice(0, -".jsonl".length).toLowerCase();
			if (fileName === needle || fileName.startsWith(needle) || fileName.endsWith(`_${needle}`)) {
				return resolveInteractiveSessionFile(full);
			}
			try {
				const fd = fs.openSync(full, "r");
				try {
					const buf = Buffer.alloc(4096);
					const n = fs.readSync(fd, buf, 0, buf.length, 0);
					const headerId = headerIdFromPrefix(buf.subarray(0, n).toString("utf8"));
					if (headerId?.toLowerCase().startsWith(needle)) {
						return resolveInteractiveSessionFile(full);
					}
				} finally {
					fs.closeSync(fd);
				}
			} catch {
				// Unreadable session file: keep scanning.
			}
		}
	}
	return undefined;
}

export function rewriteOmpResumeArgv(argv: string[], sessionsRoot?: string): string[] {
	const out = [...argv];
	for (let i = 0; i < out.length; i++) {
		const arg = out[i];
		if (RESUME_FLAGS[arg] && out[i + 1] && looksLikeOmpSessionId(out[i + 1])) {
			const resolved = findInteractiveSessionFileById(out[i + 1], sessionsRoot);
			if (resolved) out[i + 1] = resolved;
			continue;
		}
		if ((arg === "--continue" || arg === "-c") && out[i + 1] && looksLikeOmpSessionId(out[i + 1])) {
			const resolved = findInteractiveSessionFileById(out[i + 1], sessionsRoot);
			if (resolved) {
				out[i] = "--resume";
				out[i + 1] = resolved;
			}
			continue;
		}
		const eq = arg.indexOf("=");
		if (eq <= 0) continue;
		const flag = arg.slice(0, eq);
		const value = arg.slice(eq + 1);
		if (!RESUME_FLAGS[flag] || !looksLikeOmpSessionId(value)) continue;
		const resolved = findInteractiveSessionFileById(value, sessionsRoot);
		if (resolved) out[i] = `${flag}=${resolved}`;
	}
	return out;
}
