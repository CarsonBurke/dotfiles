import assert from "node:assert/strict";
import http from "node:http";
import net from "node:net";
import test from "node:test";
import { createProxy, createResolver, parseAuthority } from "./ivpn-optin-proxy.mjs";

function dohResponse(address = "203.0.113.10", ttl = 60) {
  return new Response(
    JSON.stringify({ Answer: [{ type: 1, data: address, TTL: ttl }] }),
    { headers: { "content-type": "application/dns-json" } },
  );
}

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      server.off("error", reject);
      resolve(server.address());
    });
  });
}

function close(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

test("coalesces concurrent DNS lookups", async () => {
  let calls = 0;
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const resolveIPv4 = createResolver({
    fetchImpl: async () => {
      calls += 1;
      await gate;
      return dohResponse();
    },
  });

  const lookups = Array.from({ length: 100 }, () => resolveIPv4("Example.COM"));
  release();
  assert.deepEqual(new Set(await Promise.all(lookups)), new Set(["203.0.113.10"]));
  assert.equal(calls, 1);
});

test("honors DNS TTL expiration", async () => {
  let calls = 0;
  let now = 1_000;
  const resolveIPv4 = createResolver({
    now: () => now,
    fetchImpl: async () => {
      calls += 1;
      return dohResponse(`203.0.113.${calls}`, 10);
    },
  });

  assert.equal(await resolveIPv4("example.com"), "203.0.113.1");
  now += 9_999;
  assert.equal(await resolveIPv4("example.com"), "203.0.113.1");
  now += 1;
  assert.equal(await resolveIPv4("example.com"), "203.0.113.2");
  assert.equal(calls, 2);
});

test("expires DNS entries at the shortest CNAME-chain TTL", async () => {
  let calls = 0;
  let now = 1_000;
  const resolveIPv4 = createResolver({
    now: () => now,
    fetchImpl: async () => {
      calls += 1;
      return new Response(
        JSON.stringify({
          Answer: [
            { name: "example.com.", type: 5, data: "alias.example.", TTL: 2 },
            {
              name: "alias.example.",
              type: 1,
              data: `203.0.113.${calls}`,
              TTL: 60,
            },
          ],
        }),
      );
    },
  });

  assert.equal(await resolveIPv4("example.com"), "203.0.113.1");
  now += 1_999;
  assert.equal(await resolveIPv4("example.com"), "203.0.113.1");
  now += 1;
  assert.equal(await resolveIPv4("example.com"), "203.0.113.2");
});

test("does not cache failed DNS lookups", async () => {
  let calls = 0;
  const resolveIPv4 = createResolver({
    fetchImpl: async () => {
      calls += 1;
      return calls === 1 ? new Response("failure", { status: 503 }) : dohResponse();
    },
  });

  await assert.rejects(resolveIPv4("example.com"), /failed: 503/);
  assert.equal(await resolveIPv4("example.com"), "203.0.113.10");
  assert.equal(calls, 2);
});

test("bounds the DNS cache", async () => {
  let calls = 0;
  const resolveIPv4 = createResolver({
    maxEntries: 2,
    fetchImpl: async () => {
      calls += 1;
      return dohResponse();
    },
  });

  await resolveIPv4("one.example");
  await resolveIPv4("two.example");
  await resolveIPv4("three.example");
  await resolveIPv4("one.example");
  assert.equal(calls, 4);
});

test("parses CONNECT authorities", () => {
  assert.deepEqual(parseAuthority("example.com:8443"), {
    hostname: "example.com",
    port: 8443,
  });
  assert.deepEqual(parseAuthority("example.com"), {
    hostname: "example.com",
    port: 443,
  });
});

test("streams HTTP responses through the real proxy boundary", async (t) => {
  const payload = Buffer.alloc(4 * 1024 * 1024, 0x5a);
  const upstream = http.createServer((_request, response) => {
    response.writeHead(200, { "content-length": payload.length });
    response.end(payload);
  });
  const upstreamAddress = await listen(upstream);
  t.after(() => close(upstream));

  const proxy = createProxy({ resolveIPv4: async () => "127.0.0.1", port: 0 });
  const proxyAddress = await proxy.listen();
  t.after(() => proxy.close());

  const received = await new Promise((resolve, reject) => {
    http.get(
      {
        host: "127.0.0.1",
        port: proxyAddress.port,
        path: `http://example.test:${upstreamAddress.port}/payload`,
      },
      (response) => {
        let bytes = 0;
        response.on("data", (chunk) => {
          bytes += chunk.length;
        });
        response.once("end", () => resolve(bytes));
        response.once("error", reject);
      },
    ).once("error", reject);
  });

  assert.equal(received, payload.length);
});

test("strips proxy and connection-scoped headers before forwarding", async (t) => {
  let receivedHeaders;
  const upstream = http.createServer((request, response) => {
    receivedHeaders = request.headers;
    response.end("ok");
  });
  const upstreamAddress = await listen(upstream);
  t.after(() => close(upstream));

  const proxy = createProxy({ resolveIPv4: async () => "127.0.0.1", port: 0 });
  const proxyAddress = await proxy.listen();
  t.after(() => proxy.close());

  await new Promise((resolve, reject) => {
    http
      .get(
        {
          host: "127.0.0.1",
          port: proxyAddress.port,
          path: `http://example.test:${upstreamAddress.port}/headers`,
          headers: {
            connection: "keep-alive, x-private-hop",
            "proxy-authorization": "Basic c2VjcmV0",
            "x-private-hop": "do-not-forward",
            "x-end-to-end": "forward-me",
          },
        },
        (response) => {
          response.resume();
          response.once("end", resolve);
        },
      )
      .once("error", reject);
  });

  assert.equal(receivedHeaders["proxy-authorization"], undefined);
  assert.equal(receivedHeaders["x-private-hop"], undefined);
  assert.equal(receivedHeaders["x-end-to-end"], "forward-me");
});

test("does not forward an HTTP request abandoned during DNS", async (t) => {
  let upstreamRequests = 0;
  const upstream = http.createServer((_request, response) => {
    upstreamRequests += 1;
    response.end("unexpected");
  });
  const upstreamAddress = await listen(upstream);
  t.after(() => close(upstream));

  let releaseDns;
  const dnsGate = new Promise((resolve) => {
    releaseDns = resolve;
  });
  const proxy = createProxy({
    resolveIPv4: async () => {
      await dnsGate;
      return "127.0.0.1";
    },
    port: 0,
  });
  const proxyAddress = await proxy.listen();
  t.after(() => proxy.close());

  const request = http.get({
    host: "127.0.0.1",
    port: proxyAddress.port,
    path: `http://example.test:${upstreamAddress.port}/abandoned`,
  });
  request.once("error", () => {});
  request.destroy();
  await new Promise((resolve) => setTimeout(resolve, 20));
  releaseDns();
  await new Promise((resolve) => setTimeout(resolve, 50));

  assert.equal(upstreamRequests, 0);
});

test("tears down the upstream tunnel when the client closes", async (t) => {
  let upstreamSocket;
  const upstream = net.createServer((socket) => {
    upstreamSocket = socket;
    socket.pipe(socket);
  });
  const upstreamAddress = await listen(upstream);
  t.after(() => close(upstream));

  const proxy = createProxy({ resolveIPv4: async () => "127.0.0.1", port: 0 });
  const proxyAddress = await proxy.listen();
  t.after(() => proxy.close());

  const client = net.connect(proxyAddress.port, "127.0.0.1");
  client.write(
    `CONNECT example.test:${upstreamAddress.port} HTTP/1.1\r\nHost: example.test\r\n\r\n`,
  );
  await new Promise((resolve, reject) => {
    client.once("data", (data) => {
      assert.match(data.toString(), /^HTTP\/1\.1 200/);
      resolve();
    });
    client.once("error", reject);
  });

  client.destroy();
  await new Promise((resolve, reject) => {
    if (upstreamSocket.destroyed) return resolve();
    upstreamSocket.once("close", resolve);
    setTimeout(() => reject(new Error("upstream tunnel remained open")), 1_000).unref();
  });
});

test("flushes a 502 response when a CONNECT target refuses the socket", async (t) => {
  const reservation = net.createServer();
  const reservedAddress = await listen(reservation);
  await close(reservation);

  const proxy = createProxy({ resolveIPv4: async () => "127.0.0.1", port: 0 });
  const proxyAddress = await proxy.listen();
  t.after(() => proxy.close());

  const response = await new Promise((resolve, reject) => {
    const chunks = [];
    const client = net.connect(proxyAddress.port, "127.0.0.1", () => {
      client.write(
        `CONNECT example.test:${reservedAddress.port} HTTP/1.1\r\nHost: example.test\r\n\r\n`,
      );
    });
    client.on("data", (chunk) => chunks.push(chunk));
    client.once("end", () => resolve(Buffer.concat(chunks).toString()));
    client.once("error", reject);
  });

  assert.match(response, /^HTTP\/1\.1 502 Bad Gateway/);
});
