import http from "node:http";
import https from "node:https";
import net from "node:net";
import { pathToFileURL } from "node:url";

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 18080;
const DEFAULT_DOH_URL = "https://1.1.1.1/dns-query";
const DEFAULT_MAX_DNS_ENTRIES = 512;
const MAX_DOH_RESPONSE_BYTES = 64 * 1024;
const SOCKET_TIMEOUT_MS = 30_000;

async function readLimitedText(response, maxBytes) {
  if (!response.body) return "";

  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > maxBytes) {
      await reader.cancel("response too large");
      throw new Error("DNS over HTTPS response exceeded 64 KiB");
    }
    chunks.push(value);
  }

  const body = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(body);
}

export function createResolver({
  fetchImpl = fetch,
  now = Date.now,
  dohUrl = DEFAULT_DOH_URL,
  maxEntries = DEFAULT_MAX_DNS_ENTRIES,
} = {}) {
  if (!Number.isInteger(maxEntries) || maxEntries < 1) {
    throw new RangeError("maxEntries must be a positive integer");
  }

  const cache = new Map();
  const inFlight = new Map();

  function cacheAddress(hostname, address, expiresAt) {
    cache.delete(hostname);
    while (cache.size >= maxEntries) {
      cache.delete(cache.keys().next().value);
    }
    cache.set(hostname, { address, expiresAt });
  }

  async function resolveUncached(hostname) {
    const url = new URL(dohUrl);
    url.searchParams.set("name", hostname);
    url.searchParams.set("type", "A");

    const response = await fetchImpl(url, {
      headers: { accept: "application/dns-json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      throw new Error(`DNS over HTTPS failed: ${response.status}`);
    }

    const text = await readLimitedText(response, MAX_DOH_RESPONSE_BYTES);
    let body;
    try {
      body = JSON.parse(text);
    } catch {
      throw new Error("DNS over HTTPS returned invalid JSON");
    }

    const answers = Array.isArray(body.Answer) ? body.Answer : [];
    const normalizeName = (name) => String(name ?? "").toLowerCase().replace(/\.$/, "");
    let currentName = normalizeName(hostname);
    const ttlValues = [];
    const visited = new Set();
    let answer;

    while (!visited.has(currentName)) {
      visited.add(currentName);
      const alias = answers.find(
        (entry) =>
          entry.type === 5 && normalizeName(entry.name) === currentName,
      );
      if (!alias) break;
      if (Number.isFinite(Number(alias.TTL))) ttlValues.push(Number(alias.TTL));
      currentName = normalizeName(alias.data);
    }

    answer = answers.find(
      (entry) =>
        entry.type === 1 &&
        normalizeName(entry.name) === currentName &&
        net.isIPv4(entry.data),
    );
    answer ??= answers.find(
      (entry) => entry.type === 1 && net.isIPv4(entry.data),
    );
    if (!answer) throw new Error(`No IPv4 address for ${hostname}`);

    if (Number.isFinite(Number(answer.TTL))) ttlValues.push(Number(answer.TTL));
    const reportedTtl = ttlValues.length ? Math.min(...ttlValues) : 30;
    const ttlSeconds = Math.max(1, Math.min(reportedTtl, 300));
    cacheAddress(hostname, answer.data, now() + ttlSeconds * 1_000);
    return answer.data;
  }

  return async function resolveIPv4(hostname) {
    if (net.isIPv4(hostname)) return hostname;

    const key = hostname.toLowerCase();
    const cached = cache.get(key);
    if (cached && cached.expiresAt > now()) {
      cache.delete(key);
      cache.set(key, cached);
      return cached.address;
    }
    if (cached) cache.delete(key);

    const pending = inFlight.get(key);
    if (pending) return pending;

    const resolution = resolveUncached(key);
    inFlight.set(key, resolution);
    try {
      return await resolution;
    } finally {
      if (inFlight.get(key) === resolution) inFlight.delete(key);
    }
  };
}

export function parseAuthority(authority) {
  const parsed = new URL(`tcp://${authority}`);
  const port = Number(parsed.port || 443);
  if (!parsed.hostname || !Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error("Invalid CONNECT authority");
  }
  return { hostname: parsed.hostname, port };
}

function sanitizeProxyHeaders(requestHeaders, host) {
  const headers = { ...requestHeaders, host };
  const connectionHeaders = String(headers.connection ?? "")
    .split(",")
    .map((name) => name.trim().toLowerCase())
    .filter(Boolean);
  for (const name of [
    ...connectionHeaders,
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
  ]) {
    delete headers[name];
  }
  return headers;
}

function endWithBadGateway(response, error) {
  if (response.destroyed || response.writableEnded) return;
  if (!response.headersSent) response.writeHead(502);
  response.end(error instanceof Error ? error.message : String(error));
}

export function createProxy({
  resolveIPv4 = createResolver(),
  host = DEFAULT_HOST,
  port = DEFAULT_PORT,
  maxConnections = 512,
} = {}) {
  const sockets = new Set();

  const server = http.createServer(async (request, response) => {
    let upstream;
    let clientGone = false;

    const stopForwarding = () => {
      clientGone = true;
      upstream?.destroy();
    };
    request.once("aborted", stopForwarding);
    response.once("close", () => {
      if (!response.writableEnded) stopForwarding();
    });

    try {
      const target = new URL(request.url);
      if (target.protocol !== "http:" && target.protocol !== "https:") {
        throw new Error(`Unsupported proxy protocol: ${target.protocol}`);
      }

      const address = await resolveIPv4(target.hostname);
      if (clientGone || request.aborted || response.destroyed) return;

      const transport = target.protocol === "https:" ? https : http;
      upstream = transport.request(
        {
          host: address,
          port: Number(target.port || (target.protocol === "https:" ? 443 : 80)),
          method: request.method,
          path: `${target.pathname}${target.search}`,
          headers: sanitizeProxyHeaders(request.headers, target.host),
          servername: target.hostname,
          agent: false,
        },
        (upstreamResponse) => {
          response.writeHead(
            upstreamResponse.statusCode ?? 502,
            upstreamResponse.headers,
          );
          upstreamResponse.once("aborted", () => response.destroy());
          upstreamResponse.once("error", (error) => response.destroy(error));
          upstreamResponse.pipe(response);
        },
      );

      upstream.setTimeout(SOCKET_TIMEOUT_MS, () => {
        upstream.destroy(new Error("Upstream request timed out"));
      });
      upstream.once("error", (error) => endWithBadGateway(response, error));
      request.pipe(upstream);
    } catch (error) {
      upstream?.destroy();
      endWithBadGateway(response, error);
    }
  });

  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.once("close", () => sockets.delete(socket));
  });

  server.on("connect", async (request, client, head) => {
    let upstream;
    let connected = false;

    const destroyPeer = () => upstream?.destroy();
    client.setTimeout(SOCKET_TIMEOUT_MS, () => client.destroy());
    client.once("error", destroyPeer);
    client.once("close", destroyPeer);

    try {
      const { hostname, port: targetPort } = parseAuthority(request.url);
      const address = await resolveIPv4(hostname);
      if (client.destroyed) return;

      upstream = net.connect({ host: address, port: targetPort });
      upstream.setTimeout(SOCKET_TIMEOUT_MS, () => {
        upstream.destroy(new Error("Upstream tunnel timed out"));
      });
      upstream.once("connect", () => {
        connected = true;
        client.write("HTTP/1.1 200 Connection Established\r\n\r\n");
        if (head.length) upstream.write(head);
        upstream.pipe(client);
        client.pipe(upstream);
      });
      upstream.once("error", () => {
        if (!connected && !client.destroyed) {
          client.end("HTTP/1.1 502 Bad Gateway\r\n\r\n");
        } else {
          client.destroy();
        }
      });
    } catch {
      upstream?.destroy();
      if (!client.destroyed) client.end("HTTP/1.1 502 Bad Gateway\r\n\r\n");
    }
  });

  server.maxConnections = maxConnections;
  server.headersTimeout = 15_000;
  server.requestTimeout = 60_000;
  server.keepAliveTimeout = 5_000;
  server.maxRequestsPerSocket = 100;

  return {
    server,
    listen() {
      return new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(port, host, () => {
          server.off("error", reject);
          resolve(server.address());
        });
      });
    },
    close() {
      for (const socket of sockets) socket.destroy();
      return new Promise((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      });
    },
  };
}

const isMain =
  import.meta.main === true ||
  (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href);

if (isMain) {
  const proxy = createProxy();
  await proxy.listen();
  process.stdout.write(
    `IVPN opt-in proxy ready on http://${DEFAULT_HOST}:${DEFAULT_PORT}\n`,
  );

  let shuttingDown = false;
  const shutdown = async () => {
    if (shuttingDown) return;
    shuttingDown = true;
    try {
      await proxy.close();
    } finally {
      process.exit(0);
    }
  };
  process.once("SIGTERM", shutdown);
  process.once("SIGINT", shutdown);
}
