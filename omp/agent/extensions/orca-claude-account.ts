import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const CLAUDE_PROVIDER = "anthropic";
const CODEX_PROVIDER = "openai-codex";
const POLL_MS = 2000;
const CODEX_AUTH_CLAIM = "https://api.openai.com/auth";

type OrcaClaudeAccount = {
	id: string;
	email: string;
	managedAuthPath: string;
};

type OrcaClaudeSelection = {
	activeAccountId: string | null;
	accounts: OrcaClaudeAccount[];
};

type OrcaCodexAccount = {
	id: string;
	email: string;
	authJsonPath: string;
};

type OrcaCodexSelection = {
	activeAccountId: string | null;
	accounts: OrcaCodexAccount[];
};

export type OrcaAccountSyncResult = {
	email?: string;
	pinned: boolean;
	imported: string[];
};

export type OrcaClaudeSyncResult = OrcaAccountSyncResult;

type OAuthCredential = {
	type: "oauth";
	access: string;
	refresh: string;
	expires: number;
	email?: string;
	accountId?: string;
	orgId?: string;
	orgName?: string;
	authorizedAt?: number;
};

type AuthStorageLike = {
	listOAuthAccounts: (
		provider: string,
		sessionId?: string,
	) => Array<{ credentialId: number; email?: string; accountId?: string; orgId?: string; active?: boolean }>;
	listStoredCredentials?: (
		provider?: string,
	) => Array<{ credential: { type: string; refresh?: string; expires?: number; email?: string } }>;
	upsertCredential: (provider: string, credential: OAuthCredential) => Array<{ id: number }>;
	pinSessionOAuthAccount: (provider: string, sessionId: string, credentialId: number) => boolean;
};

type OrcaSettings = {
	activeClaudeManagedAccountId?: string | null;
	claudeManagedAccounts?: Array<{ id?: string; email?: string; managedAuthPath?: string }>;
	activeCodexManagedAccountId?: string | null;
	codexManagedAccounts?: Array<{ id?: string; email?: string; managedHomePath?: string }>;
};

function orcaConfigDir(): string {
	return process.env.ORCA_CONFIG_DIR?.trim() || path.join(os.homedir(), ".config", "orca");
}

function emailsEqual(a: string | undefined, b: string | undefined): boolean {
	return Boolean(a && b && a.trim().toLowerCase() === b.trim().toLowerCase());
}

function readJson(filePath: string): unknown {
	return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function decodeJwtPayload(token: string): Record<string, unknown> | undefined {
	const parts = token.split(".");
	if (parts.length < 2) return undefined;
	let payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
	while (payload.length % 4 !== 0) payload += "=";
	try {
		return JSON.parse(Buffer.from(payload, "base64").toString("utf8")) as Record<string, unknown>;
	} catch {
		return undefined;
	}
}

export function resolveOrcaDataPath(configDir: string = orcaConfigDir()): string {
	const indexPath = path.join(configDir, "orca-profile-index.json");
	let profileId = "local-default";
	try {
		const index = readJson(indexPath) as { activeProfileId?: string };
		if (typeof index.activeProfileId === "string" && index.activeProfileId.trim()) {
			profileId = index.activeProfileId.trim();
		}
	} catch {
		// fall through to default profile
	}
	const profilePath = path.join(configDir, "profiles", profileId, "orca-data.json");
	if (fs.existsSync(profilePath)) return profilePath;
	return path.join(configDir, "orca-data.json");
}

function readOrcaSettings(configDir: string = orcaConfigDir()): OrcaSettings {
	const raw = readJson(resolveOrcaDataPath(configDir)) as { settings?: OrcaSettings };
	return raw.settings ?? {};
}

export function readOrcaClaudeSelection(configDir: string = orcaConfigDir()): OrcaClaudeSelection {
	const settings = readOrcaSettings(configDir);
	const accounts = (settings.claudeManagedAccounts ?? [])
		.map((account) => ({
			id: typeof account.id === "string" ? account.id : "",
			email: typeof account.email === "string" ? account.email.trim().toLowerCase() : "",
			managedAuthPath: typeof account.managedAuthPath === "string" ? account.managedAuthPath : "",
		}))
		.filter((account) => account.id && account.email && account.managedAuthPath);
	const activeAccountId =
		typeof settings.activeClaudeManagedAccountId === "string" && settings.activeClaudeManagedAccountId
			? settings.activeClaudeManagedAccountId
			: null;
	return { activeAccountId, accounts };
}

export function readOrcaCodexSelection(configDir: string = orcaConfigDir()): OrcaCodexSelection {
	const settings = readOrcaSettings(configDir);
	const accounts: OrcaCodexAccount[] = [];
	for (const account of settings.codexManagedAccounts ?? []) {
		const id = typeof account.id === "string" ? account.id : "";
		const email = typeof account.email === "string" ? account.email.trim().toLowerCase() : "";
		const home = typeof account.managedHomePath === "string" ? account.managedHomePath : "";
		if (!id || !email || !home) continue;
		accounts.push({ id, email, authJsonPath: path.join(home, "auth.json") });
	}

	const systemAuth = path.join(os.homedir(), ".codex", "auth.json");
	const systemOauth = readCodexAuthFile(systemAuth);
	if (systemOauth?.email && !accounts.some((account) => emailsEqual(account.email, systemOauth.email))) {
		accounts.push({
			id: "system-default",
			email: systemOauth.email,
			authJsonPath: systemAuth,
		});
	}

	const activeAccountId =
		typeof settings.activeCodexManagedAccountId === "string" && settings.activeCodexManagedAccountId
			? settings.activeCodexManagedAccountId
			: systemOauth?.email
				? "system-default"
				: null;
	return { activeAccountId, accounts };
}

function readManagedClaudeOAuth(account: OrcaClaudeAccount): OAuthCredential | undefined {
	const credPath = path.join(account.managedAuthPath, ".credentials.json");
	const identityPath = path.join(account.managedAuthPath, "oauth-account.json");
	let access: string | undefined;
	let refresh: string | undefined;
	let expires = 0;
	try {
		const creds = readJson(credPath) as {
			claudeAiOauth?: { accessToken?: string; refreshToken?: string; expiresAt?: number };
		};
		access = creds.claudeAiOauth?.accessToken;
		refresh = creds.claudeAiOauth?.refreshToken;
		expires = Number(creds.claudeAiOauth?.expiresAt ?? 0);
	} catch {
		return undefined;
	}
	if (!access || !refresh || !Number.isFinite(expires) || expires <= 0) return undefined;

	let accountId: string | undefined;
	let orgId: string | undefined;
	let orgName: string | undefined;
	try {
		const identity = readJson(identityPath) as {
			accountUuid?: string;
			organizationUuid?: string;
			organizationName?: string;
		};
		accountId = identity.accountUuid;
		orgId = identity.organizationUuid;
		orgName = identity.organizationName;
	} catch {
		// identity is optional; email from the Orca account row is enough to pin
	}

	return {
		type: "oauth",
		access,
		refresh,
		expires,
		email: account.email,
		accountId,
		orgId,
		orgName,
		authorizedAt: Date.now(),
	};
}

function readCodexAuthFile(authJsonPath: string): OAuthCredential | undefined {
	try {
		const raw = readJson(authJsonPath) as {
			tokens?: {
				access_token?: string;
				refresh_token?: string;
				id_token?: string;
				account_id?: string;
			};
		};
		const access = raw.tokens?.access_token;
		const refresh = raw.tokens?.refresh_token;
		if (!access || !refresh) return undefined;
		const accessClaims = decodeJwtPayload(access);
		const idClaims = raw.tokens?.id_token ? decodeJwtPayload(raw.tokens.id_token) : undefined;
		const auth =
			accessClaims && typeof accessClaims[CODEX_AUTH_CLAIM] === "object" && accessClaims[CODEX_AUTH_CLAIM]
				? (accessClaims[CODEX_AUTH_CLAIM] as Record<string, unknown>)
				: undefined;
		const email =
			(typeof idClaims?.email === "string" && idClaims.email.trim().toLowerCase()) ||
			(typeof accessClaims?.email === "string" && accessClaims.email.trim().toLowerCase()) ||
			undefined;
		const accountId =
			(typeof auth?.chatgpt_account_id === "string" && auth.chatgpt_account_id) ||
			raw.tokens?.account_id ||
			undefined;
		const exp = typeof accessClaims?.exp === "number" ? accessClaims.exp * 1000 : 0;
		if (!Number.isFinite(exp) || exp <= 0) return undefined;
		return {
			type: "oauth",
			access,
			refresh,
			expires: exp,
			email,
			accountId,
			orgId: accountId,
			orgName: typeof auth?.chatgpt_plan_type === "string" ? auth.chatgpt_plan_type : undefined,
			authorizedAt: Date.now(),
		};
	} catch {
		return undefined;
	}
}

function upsertProviderAccounts(
	authStorage: AuthStorageLike,
	provider: string,
	incoming: Array<{ email: string; oauth: OAuthCredential }>,
): string[] {
	const imported: string[] = [];
	const stored = authStorage.listStoredCredentials?.(provider) ?? [];
	for (const account of incoming) {
		const existing = stored.find(
			(row) => row.credential.type === "oauth" && emailsEqual(row.credential.email, account.email),
		);
		const unchanged =
			existing?.credential.refresh === account.oauth.refresh &&
			existing.credential.expires === account.oauth.expires;
		if (!unchanged) authStorage.upsertCredential(provider, account.oauth);
		if (!existing) imported.push(account.email);
	}
	return imported;
}

function pinProviderEmail(
	authStorage: AuthStorageLike,
	provider: string,
	sessionId: string,
	email: string | undefined,
	imported: string[],
): OrcaAccountSyncResult {
	if (!email || !sessionId) return { email, pinned: false, imported };
	const accounts = authStorage.listOAuthAccounts(provider, sessionId);
	const match = accounts.find((row) => emailsEqual(row.email, email));
	if (!match) return { email, pinned: false, imported };
	if (match.active) return { email, pinned: true, imported };
	return {
		email,
		pinned: authStorage.pinSessionOAuthAccount(provider, sessionId, match.credentialId),
		imported,
	};
}

export function syncOrcaClaudeAccount(
	authStorage: AuthStorageLike,
	sessionId: string,
	configDir: string = orcaConfigDir(),
): OrcaAccountSyncResult {
	const selection = readOrcaClaudeSelection(configDir);
	const incoming = selection.accounts.flatMap((account) => {
		const oauth = readManagedClaudeOAuth(account);
		return oauth ? [{ email: account.email, oauth }] : [];
	});
	const imported = upsertProviderAccounts(authStorage, CLAUDE_PROVIDER, incoming);
	const active = selection.accounts.find((account) => account.id === selection.activeAccountId);
	return pinProviderEmail(authStorage, CLAUDE_PROVIDER, sessionId, active?.email, imported);
}

export function syncOrcaCodexAccount(
	authStorage: AuthStorageLike,
	sessionId: string,
	configDir: string = orcaConfigDir(),
): OrcaAccountSyncResult {
	const selection = readOrcaCodexSelection(configDir);
	const incoming = selection.accounts.flatMap((account) => {
		const oauth = readCodexAuthFile(account.authJsonPath);
		return oauth?.email ? [{ email: oauth.email, oauth }] : [];
	});
	const imported = upsertProviderAccounts(authStorage, CODEX_PROVIDER, incoming);
	const active = selection.accounts.find((account) => account.id === selection.activeAccountId);
	const activeEmail = active?.email ?? incoming.find((row) => emailsEqual(row.email, active?.email))?.email;
	return pinProviderEmail(authStorage, CODEX_PROVIDER, sessionId, active?.email ?? activeEmail, imported);
}

export default function (pi: {
	on: (event: string, handler: (event: unknown, ctx: unknown) => void) => void;
}): void {
	let lastClaude: string | undefined;
	let lastCodex: string | undefined;
	let watching = false;

	function sync(ctx: unknown, notify: boolean): void {
		const typed = ctx as {
			sessionManager?: { getSessionId?: () => unknown };
			modelRegistry?: { authStorage?: AuthStorageLike };
			ui?: { notify?: (message: string, type?: "info" | "warning" | "error") => void };
			setInterval?: (callback: () => void, ms?: number) => unknown;
		};
		const sessionId = typed.sessionManager?.getSessionId?.();
		const authStorage = typed.modelRegistry?.authStorage;
		if (typeof sessionId !== "string" || !sessionId || !authStorage) return;

		let claude: OrcaAccountSyncResult;
		let codex: OrcaAccountSyncResult;
		try {
			claude = syncOrcaClaudeAccount(authStorage, sessionId);
			codex = syncOrcaCodexAccount(authStorage, sessionId);
		} catch {
			return;
		}

		if (notify) {
			if (claude.pinned && claude.email && claude.email !== lastClaude) {
				typed.ui?.notify?.(`OMP Claude account: ${claude.email}`, "info");
			}
			if (codex.pinned && codex.email && codex.email !== lastCodex) {
				typed.ui?.notify?.(`OMP Codex account: ${codex.email}`, "info");
			}
		}
		if (claude.pinned) lastClaude = claude.email;
		if (codex.pinned) lastCodex = codex.email;

		if (!watching && typeof typed.setInterval === "function") {
			watching = true;
			typed.setInterval(() => sync(ctx, true), POLL_MS);
		}
	}

	pi.on("session_start", (_event, ctx) => sync(ctx, true));
	pi.on("session_switch", (_event, ctx) => sync(ctx, true));
	pi.on("before_agent_start", (_event, ctx) => sync(ctx, false));
	pi.on("before_provider_request", (_event, ctx) => sync(ctx, false));
}
