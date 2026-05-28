#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const DEFAULT_PROGRESS = [0.0, 0.65];
const DEFAULT_PORT = 9224;

function parseArgs(argv) {
  const parsed = {
    url: "",
    outputDir: "",
    port: DEFAULT_PORT,
    timeoutMs: 30000,
    progress: [...DEFAULT_PROGRESS],
    frames: 0,
    width: 0,
    height: 0,
    alpha: false,
    headless: true,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    if (arg === "--url" && next) {
      parsed.url = next;
      index += 1;
    } else if (arg === "--output-dir" && next) {
      parsed.outputDir = resolve(next);
      index += 1;
    } else if (arg === "--port" && next) {
      parsed.port = Number(next);
      index += 1;
    } else if (arg === "--timeout-ms" && next) {
      parsed.timeoutMs = Number(next);
      index += 1;
    } else if (arg === "--progress" && next) {
      parsed.progress = next.split(",").map((value) => Number(value.trim())).filter((value) => Number.isFinite(value));
      index += 1;
    } else if (arg === "--frames" && next) {
      parsed.frames = Number(next);
      index += 1;
    } else if (arg === "--width" && next) {
      parsed.width = Number(next);
      index += 1;
    } else if (arg === "--height" && next) {
      parsed.height = Number(next);
      index += 1;
    } else if (arg === "--alpha") {
      parsed.alpha = true;
    } else if (arg === "--headless") {
      parsed.headless = true;
    } else if (arg === "--visible-browser") {
      if (process.env.PLAYWRIGHT_ALLOW_HEADED !== "1") {
        throw new Error("--visible-browser opens a browser window. Set PLAYWRIGHT_ALLOW_HEADED=1 to opt in.");
      }
      parsed.headless = process.env.PLAYWRIGHT_ALLOW_HEADED !== "1";
    }
  }
  if (!parsed.url) {
    throw new Error("Missing required --url");
  }
  if (!parsed.outputDir) {
    parsed.outputDir = resolve(mkdtempSync(join(tmpdir(), "particle-workbench-chrome-")));
  }
  if (parsed.frames > 0 && (parsed.width <= 0 || parsed.height <= 0)) {
    throw new Error("Sequence capture requires positive --width and --height values.");
  }
  return parsed;
}

function chromeBinary() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error("Google Chrome or Google Chrome Canary is required for workbench export-shot.");
}

function sleep(ms) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, ms));
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} from ${url}`);
  }
  return response.json();
}

async function waitFor(fn, timeoutMs, message) {
  const started = Date.now();
  for (;;) {
    try {
      return await fn();
    } catch (error) {
      if ((Date.now() - started) >= timeoutMs) {
        throw new Error(`${message}: ${error instanceof Error ? error.message : String(error)}`);
      }
      await sleep(250);
    }
  }
}

function createCdpClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  let nextId = 1;
  const pending = new Map();
  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(String(event.data));
    if (payload.id && pending.has(payload.id)) {
      const { resolvePromise, rejectPromise } = pending.get(payload.id);
      pending.delete(payload.id);
      if (payload.error) {
        rejectPromise(new Error(payload.error.message || "CDP error"));
      } else {
        resolvePromise(payload.result || {});
      }
    }
  });
  return {
    async open() {
      if (socket.readyState === WebSocket.OPEN) {
        return;
      }
      await new Promise((resolvePromise, rejectPromise) => {
        socket.addEventListener("open", () => resolvePromise(), { once: true });
        socket.addEventListener("error", (event) => rejectPromise(event.error || new Error("WebSocket failed")), { once: true });
      });
    },
    async send(method, params = {}) {
      await this.open();
      const id = nextId;
      nextId += 1;
      const payload = { id, method, params };
      return new Promise((resolvePromise, rejectPromise) => {
        pending.set(id, { resolvePromise, rejectPromise });
        socket.send(JSON.stringify(payload));
      });
    },
    close() {
      socket.close();
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  mkdirSync(args.outputDir, { recursive: true });

  const userDataDir = mkdtempSync(join(tmpdir(), "particle-workbench-chrome-profile-"));
  const chrome = spawn(
    chromeBinary(),
    [
      `--remote-debugging-port=${args.port}`,
      `--user-data-dir=${userDataDir}`,
      "--disable-background-networking",
      "--disable-default-apps",
      "--disable-sync",
      "--no-first-run",
      "--no-default-browser-check",
      "--force-device-scale-factor=1",
      "--enable-webgl",
      "--ignore-gpu-blocklist",
      "--use-angle=metal",
      "--window-size=1728,1240",
      ...(args.headless ? ["--headless=new"] : []),
      args.url,
    ],
    { stdio: "ignore" },
  );

  const cleanup = async () => {
    if (!chrome.killed) {
      chrome.kill("SIGTERM");
      await Promise.race([
        new Promise((resolvePromise) => chrome.once("exit", resolvePromise)),
        sleep(1500).then(() => {
          if (!chrome.killed) {
            chrome.kill("SIGKILL");
          }
        }),
      ]);
    }
    rmSync(userDataDir, { recursive: true, force: true });
  };

  try {
    await waitFor(
      async () => fetchJson(`http://127.0.0.1:${args.port}/json/version`),
      args.timeoutMs,
      "Chrome DevTools did not start",
    );

    const target = await waitFor(
      async () => {
        const targets = await fetchJson(`http://127.0.0.1:${args.port}/json/list`);
        const page = targets.find((entry) => entry.type === "page" && String(entry.url || "").startsWith(args.url));
        if (!page?.webSocketDebuggerUrl) {
          throw new Error("Workbench page target not ready");
        }
        return page;
      },
      args.timeoutMs,
      "Workbench page target did not appear",
    );

    const cdp = createCdpClient(target.webSocketDebuggerUrl);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");

    await waitFor(
      async () => {
        const result = await cdp.send("Runtime.evaluate", {
          expression: "window.__particleWorkbenchAppReady === true && typeof window.__particleWorkbench?.exportEffectFrame === 'function'",
          returnByValue: true,
        });
        if (result?.result?.value !== true) {
          throw new Error("Workbench app is not ready");
        }
        return true;
      },
      args.timeoutMs,
      "Workbench app did not become ready",
    );

    const metadata = [];
    const progressValues = args.frames > 0
      ? Array.from({ length: args.frames }, (_value, index) => (args.frames <= 1 ? 0 : index / Math.max(args.frames - 1, 1)))
      : args.progress;
    for (let index = 0; index < progressValues.length; index += 1) {
      const progress = progressValues[index];
      const result = await cdp.send("Runtime.evaluate", {
        expression: `(async () => {
          const capture = await window.__particleWorkbench.exportEffectFrame({
            progress: ${Number(progress).toFixed(8)},
            width: ${Math.max(0, Number(args.width || 0))},
            height: ${Math.max(0, Number(args.height || 0))},
            alpha: ${args.alpha ? "true" : "false"},
          });
          return {
            progress: capture.progress,
            data_url: capture.data_url,
            effect_model: capture.scene.effect_model,
          };
        })()`,
        awaitPromise: true,
        returnByValue: true,
      });
      const capture = result?.result?.value;
      if (!capture?.data_url) {
        throw new Error(`Capture failed for progress ${progress}`);
      }
      const canvasBytes = Buffer.from(String(capture.data_url).split(",", 2)[1] || "", "base64");
      const basename = args.frames > 0
        ? `frame_${String(index).padStart(5, "0")}`
        : `effect_progress_${Number(progress).toFixed(2).replace(".", "_")}`;
      writeFileSync(join(args.outputDir, `${basename}.png`), canvasBytes);
      writeFileSync(
        join(args.outputDir, `${basename}.json`),
        JSON.stringify({ progress: capture.progress, effect_model: capture.effect_model, url: args.url }, null, 2),
      );
      metadata.push({ progress: capture.progress, path: join(args.outputDir, `${basename}.png`) });
    }

    writeFileSync(join(args.outputDir, "captures.json"), JSON.stringify({ url: args.url, captures: metadata }, null, 2));
    process.stdout.write(`${JSON.stringify({ output_dir: args.outputDir, captures: metadata }, null, 2)}\n`);
    cdp.close();
  } finally {
    await cleanup();
  }
}

main().catch((error) => {
  process.stderr.write(`ERROR ${error instanceof Error ? error.message : String(error)}\n`);
  process.exit(1);
});
