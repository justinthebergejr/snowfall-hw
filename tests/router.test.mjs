import test from "node:test";
import assert from "node:assert/strict";
import worker, { handle } from "../routing/worker.mjs";

test("Cloudflare entry point accepts environment and context arguments", async () => {
  const result = await worker.fetch(new Request("https://justi.zone/snowfall"), {}, {});
  assert.equal(result.status, 308);
});

test("maps report and asset paths to the original repository, preserving queries", async () => {
  for (const path of ["/", "/style.css?v=2", "/assets/results.json"]) {
    let received;
    const result = await handle(new Request("https://justi.zone/snowfall" + path), async req => {
      received = req;
      return new Response("report", { headers: { "Content-Type": "text/plain" } });
    });
    assert.equal(received.url, "https://justinthebergejr.github.io/snowfall-hw" + path);
    assert.equal(await result.text(), "report");
    assert.equal(result.headers.get("Content-Type"), "text/plain");
  }
});

test("adds the trailing slash without losing the query", async () => {
  const result = await handle(new Request("https://justi.zone/snowfall?year=2000"));
  assert.equal(result.status, 308);
  assert.equal(result.headers.get("Location"), "https://justi.zone/snowfall/?year=2000");
});

test("leaves main-site and similarly named paths untouched", async () => {
  for (const path of ["/", "/photos/example.jpg", "/snowfall-other"]) {
    const request = new Request("https://justi.zone" + path);
    await handle(request, async forwarded => {
      assert.equal(forwarded, request);
      return new Response("main site");
    });
  }
});

test("does not leak domain cookies or credentials", async () => {
  const request = new Request("https://justi.zone/snowfall/", {
    headers: { Cookie: "private=secret", Authorization: "Bearer secret", Accept: "text/html" },
  });
  const result = await handle(request, async forwarded => {
    assert.equal(forwarded.headers.get("Cookie"), null);
    assert.equal(forwarded.headers.get("Authorization"), null);
    assert.equal(forwarded.headers.get("Accept"), "text/html");
    return new Response("ok", { headers: { "Set-Cookie": "unexpected=cookie" } });
  });
  assert.equal(result.headers.get("Set-Cookie"), null);
});

test("maps upstream redirects back to the custom path", async () => {
  const result = await handle(new Request("https://justi.zone/snowfall/test"), async () =>
    Response.redirect("https://justinthebergejr.github.io/snowfall-hw/test/?a=1", 301));
  assert.equal(result.headers.get("Location"), "https://justi.zone/snowfall/test/?a=1");
});

test("preserves HEAD and origin errors", async () => {
  const result = await handle(new Request("https://justi.zone/snowfall/missing", { method: "HEAD" }),
    async forwarded => {
      assert.equal(forwarded.method, "HEAD");
      return new Response(null, { status: 404 });
    });
  assert.equal(result.status, 404);
});

test("handles network errors and rejects writes", async () => {
  const failed = await handle(new Request("https://justi.zone/snowfall/"), async () => {
    throw new Error("unavailable");
  });
  assert.equal(failed.status, 502);
  const post = await handle(new Request("https://justi.zone/snowfall/", { method: "POST" }));
  assert.equal(post.status, 405);
});
