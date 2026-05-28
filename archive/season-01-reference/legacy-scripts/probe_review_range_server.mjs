#!/usr/bin/env node
import fs from "node:fs";
import http from "node:http";
import https from "node:https";

function usage(message = "") {
  if (message) console.error(message);
  console.error("Usage: node scripts/probe_review_range_server.mjs REVIEW_OR_MEDIA_URL [--write RECEIPT_PATH]");
  process.exit(message ? 2 : 0);
}

const args = process.argv.slice(2);
const targetUrl = args[0] || "";
if (!targetUrl || targetUrl === "--help" || targetUrl === "-h") usage(targetUrl ? "" : "Missing URL");
let writePath = "";
for (let i = 1; i < args.length; i += 1) {
  if (args[i] === "--write") {
    writePath = args[++i] || "";
    if (!writePath) usage("Missing value for --write");
  } else {
    usage(`Unknown argument: ${args[i]}`);
  }
}

function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const client = parsed.protocol === "https:" ? https : http;
    const req = client.request(
      parsed,
      {
        method: options.method || "GET",
        headers: options.headers || {},
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks),
          });
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

function mediaUrlFromHtml(html, baseUrl) {
  const sourceMatch =
    /<(?:audio|video)\b[^>]*\bsrc=["']([^"']+)["']/i.exec(html) ||
    /<(?:audio|video)\b[\s\S]*?<source\b[^>]*\bsrc=["']([^"']+)["']/i.exec(html);
  if (!sourceMatch) return "";
  return new URL(sourceMatch[1], baseUrl).toString();
}

async function main() {
  const url = new URL(targetUrl);
  if (url.protocol === "file:") {
    throw new Error("file:// review URLs cannot satisfy byte-range media review. Use node scripts/range_static_server.mjs.");
  }
  let mediaUrl = url.toString();
  if (!/\.(wav|mp3|m4a|mp4|mov)(?:[?#]|$)/i.test(url.pathname)) {
    const page = await request(url.toString());
    if (page.status !== 200) throw new Error(`Review page request returned HTTP ${page.status}`);
    mediaUrl = mediaUrlFromHtml(page.body.toString("utf8"), url.toString());
    if (!mediaUrl) throw new Error("Could not find an audio/video src in the review page");
  }
  const probe = await request(mediaUrl, { headers: { Range: "bytes=0-1023" } });
  const acceptRanges = String(probe.headers["accept-ranges"] || "");
  const contentRange = String(probe.headers["content-range"] || "");
  const ok = probe.status === 206 && /bytes/i.test(acceptRanges) && /^bytes\s+\d+-\d+\/\d+/i.test(contentRange);
  const receipt = {
    model: "review_range_server_probe_v1",
    ok,
    review_url: url.toString(),
    media_url: mediaUrl,
    http_status: probe.status,
    accept_ranges: acceptRanges,
    content_range: contentRange,
    range_server_read: ok
      ? "pass_http_206_partial_content_byte_range_server"
      : "fail_missing_http_206_partial_content_byte_range_server",
    required_server_command: "node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects",
  };
  const text = `${JSON.stringify(receipt, null, 2)}\n`;
  if (writePath) fs.writeFileSync(writePath, text, "utf8");
  console.log(text.trimEnd());
  if (!ok) process.exit(1);
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
