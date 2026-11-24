// The report remains on GitHub Pages in snowfall-hw. This only routes requests.
const PREFIX = "/snowfall";
const ORIGIN = "https://justinthebergejr.github.io";
const PROJECT = "/snowfall-hw";

export async function handle(request, fetcher = fetch) {
  const url = new URL(request.url);
  // The route wildcard also matches /snowfall-anything. Leave those paths alone.
  if (url.pathname !== PREFIX && !url.pathname.startsWith(PREFIX + "/")) {
    return fetcher(request);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
  }
  if (url.pathname === PREFIX) {
    url.pathname += "/";
    return Response.redirect(url.toString(), 308);
  }
  const upstream = new URL(ORIGIN);
  upstream.pathname = PROJECT + url.pathname.slice(PREFIX.length);
  upstream.search = url.search;
  // Never send justi.zone cookies or credentials to github.io.
  const headers = new Headers();
  for (const name of ["Accept", "Accept-Language", "If-None-Match", "If-Modified-Since", "Range"]) {
    if (request.headers.has(name)) headers.set(name, request.headers.get(name));
  }
  let response;
  try {
    response = await fetcher(new Request(upstream, {
      method: request.method, headers, redirect: "manual",
    }));
  } catch {
    return new Response("The snowfall report is temporarily unavailable. Try again shortly.", {
      status: 502, headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
  const outgoing = new Response(response.body, response);
  const location = outgoing.headers.get("Location");
  if (location) {
    const target = new URL(location, upstream);
    if (target.origin === ORIGIN &&
        (target.pathname === PROJECT || target.pathname.startsWith(PROJECT + "/"))) {
      target.host = url.host;
      target.protocol = url.protocol;
      target.pathname = PREFIX + target.pathname.slice(PROJECT.length);
      outgoing.headers.set("Location", target.toString());
    }
  }
  outgoing.headers.delete("Set-Cookie");
  outgoing.headers.set("X-Content-Type-Options", "nosniff");
  return outgoing;
}

export default {
  fetch(request) {
    return handle(request);
  },
};
