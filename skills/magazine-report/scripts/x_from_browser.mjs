#!/usr/bin/env node
// Read one month of an X account's posts through a logged-in Chrome (no cookies exported).
//
//   node x_from_browser.mjs --handle hindufund_ --month 2026-09 --out x-raw.json [--port 9222]
//   python3 fetch_x.py <issue> --month 2026-09 --from-json x-raw.json
//
// Needs a Chrome listening on --port (scripts/chrome-debug-profile.sh "<profile>").
// Opens X search "from:<handle> since:<start> until:<end>" (Latest), scrolls, and captures X's own
// SearchTimeline responses. Output uses twitter-cli's JSON schema so fetch_x.py can parse it.
// Node 22+ (built-in WebSocket/fetch). Read-only: it never clicks, posts, likes or follows.

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) =>
  v.startsWith("--") ? [...a, [v.slice(2), arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : true]] : a, []));
const port = args.port || 9222, handle = (args.handle || "").replace(/^@/, "");
if (!handle || !args.month || !args.out) { console.error("usage: --handle NAME --month YYYY-MM --out FILE [--port 9222]"); process.exit(1); }
const [y, m] = args.month.split("-").map(Number);
const pad = n => String(n).padStart(2, "0");
const since = `${y}-${pad(m)}-01`, until = m === 12 ? `${y + 1}-01-01` : `${y}-${pad(m + 1)}-01`;
const maxScrolls = Number(args.scrolls || 60);

let version;
try { version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); }
catch { console.error(`No Chrome on port ${port}. Run: bash scripts/chrome-debug-profile.sh "<profile>"`); process.exit(2); }

const q = encodeURIComponent(`from:${handle} since:${since} until:${until}`);
const url = `https://x.com/search?q=${q}&src=typed_query&f=live`;
const target = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent("about:blank")}`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
let seq = 0; const pending = new Map(), bodies = [];
const send = (method, params = {}) => new Promise(ok => { const id = ++seq; pending.set(id, ok); ws.send(JSON.stringify({ id, method, params })); });
const wanted = new Set();
ws.onmessage = async ev => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result || msg); pending.delete(msg.id); return; }
  if (msg.method === "Network.responseReceived" && /\/graphql\/[^/]+\/(SearchTimeline|UserTweets)/.test(msg.params.response.url)) wanted.add(msg.params.requestId);
  if (msg.method === "Network.loadingFinished" && wanted.has(msg.params.requestId)) {
    const r = await send("Network.getResponseBody", { requestId: msg.params.requestId });
    if (r.body) bodies.push(r.base64Encoded ? Buffer.from(r.body, "base64").toString() : r.body);
  }
};
const sleep = ms => new Promise(r => setTimeout(r, ms));
await send("Network.enable"); await send("Page.enable");
await send("Page.navigate", { url });
await sleep(6000);

const loggedIn = (await send("Runtime.evaluate", { expression: "!location.pathname.includes('/login') && !document.querySelector('a[href=\"/login\"]')", returnByValue: true })).result?.value;
if (!loggedIn) { console.error("This Chrome profile is not logged in to X."); ws.close(); process.exit(3); }

let lastCount = -1, still = 0;
for (let i = 0; i < maxScrolls && still < 4; i++) {
  await send("Runtime.evaluate", { expression: "window.scrollBy(0, document.body.scrollHeight)" });
  await sleep(1800 + Math.random() * 800);  // gentle pacing
  const n = bodies.length;
  still = n === lastCount ? still + 1 : 0; lastCount = n;
}
await send("Target.closeTarget", { targetId: target.id }).catch(() => {});
ws.close();

// ---- parse GraphQL timelines into twitter-cli's schema
const tweets = new Map();
const walk = o => {
  if (!o || typeof o !== "object") return;
  if (o.tweet_results?.result) take(o.tweet_results.result);
  for (const v of Object.values(o)) walk(v);
};
function take(r) {
  if (r.__typename === "TweetWithVisibilityResults") r = r.tweet;
  const L = r?.legacy; if (!L || tweets.has(r.rest_id)) return;
  const u = r.core?.user_results?.result || {};
  const screen = u.core?.screen_name || u.legacy?.screen_name || handle;
  const name = u.core?.name || u.legacy?.name || "";
  const text = r.note_tweet?.note_tweet_results?.result?.text || L.full_text || "";
  const media = (L.extended_entities?.media || L.entities?.media || []).map(md => ({
    type: md.type, url: md.media_url_https, width: md.original_info?.width, height: md.original_info?.height }));
  tweets.set(r.rest_id, {
    id: r.rest_id, text, author: { id: u.rest_id || "", name, screenName: screen },
    metrics: { likes: L.favorite_count || 0, retweets: L.retweet_count || 0, replies: L.reply_count || 0,
               quotes: L.quote_count || 0, views: Number(r.views?.count || 0), bookmarks: L.bookmark_count || 0 },
    createdAt: L.created_at, createdAtISO: new Date(L.created_at).toISOString(),
    media, urls: (L.entities?.urls || []).map(x => x.expanded_url),
    isRetweet: !!L.retweeted_status_result, lang: L.lang || "",
  });
}
for (const b of bodies) { try { walk(JSON.parse(b)); } catch {} }
const data = [...tweets.values()].filter(t => t.author.screenName.toLowerCase() === handle.toLowerCase())
  .sort((a, b) => a.createdAtISO.localeCompare(b.createdAtISO));
const fs = await import("node:fs");
fs.writeFileSync(args.out, JSON.stringify({ ok: true, schema_version: "1", data }, null, 2));
console.log(`@${handle} ${since}..${until}: ${data.length} posts (${bodies.length} timeline pages) → ${args.out}`);
