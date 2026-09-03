import {createReadStream, existsSync, statSync} from "node:fs";
import {createServer} from "node:http";
import {extname, join, normalize, resolve, sep} from "node:path";
import {fileURLToPath} from "node:url";

const root = resolve(fileURLToPath(new URL("./", import.meta.url)));
const port = Number.parseInt(process.env.WEBMCP_EXAMPLES_PORT ?? "4173", 10);
const types = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".svg", "image/svg+xml; charset=utf-8"],
  [".woff2", "font/woff2"],
]);

function resolveRequest(url) {
  const pathname = decodeURIComponent(new URL(url, "http://localhost").pathname);
  const relative = normalize(pathname).replace(/^([/\\])+/, "");
  const candidate = resolve(root, relative || "index.html");
  if (candidate !== root && !candidate.startsWith(`${root}${sep}`)) return null;
  if (existsSync(candidate) && statSync(candidate).isDirectory()) return join(candidate, "index.html");
  return candidate;
}

createServer((request, response) => {
  const file = resolveRequest(request.url ?? "/");
  if (!file || !existsSync(file) || !statSync(file).isFile()) {
    response.writeHead(404, {"content-type": "text/plain; charset=utf-8"});
    response.end("No example exists at this path.\n");
    return;
  }
  response.writeHead(200, {
    "cache-control": "no-store",
    "content-type": types.get(extname(file).toLowerCase()) ?? "application/octet-stream",
  });
  createReadStream(file).pipe(response);
}).listen(port, "127.0.0.1", () => {
  console.log(`WebMCP examples: http://127.0.0.1:${port}`);
});
