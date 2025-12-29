import { spawn } from "node:child_process";

function prefixLines(prefix, chunk) {
  const text = chunk.toString();
  const lines = text.split(/\r?\n/);
  return lines
    .filter((l, i) => !(i === lines.length - 1 && l === "")) // drop trailing empty line
    .map((l) => `${prefix}${l}\n`)
    .join("");
}

function spawnNpmWorkspace(workspace, npmArgs) {
  const child = spawn("npm", ["run", ...npmArgs, "--workspace", workspace], {
    stdio: ["inherit", "pipe", "pipe"],
    env: process.env,
  });

  child.stdout.on("data", (d) => process.stdout.write(prefixLines(`[${workspace}] `, d)));
  child.stderr.on("data", (d) => process.stderr.write(prefixLines(`[${workspace}] `, d)));

  return child;
}

const children = [
  spawnNpmWorkspace("server", ["dev"]),
  spawnNpmWorkspace("client", ["dev"]),
];

let shuttingDown = false;
function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;

  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM");
  }

  // If something hangs, hard-kill after a short grace period.
  setTimeout(() => {
    for (const child of children) {
      if (!child.killed) child.kill("SIGKILL");
    }
    process.exit(code);
  }, 1500).unref();
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

for (const child of children) {
  child.on("exit", (code) => {
    // If either process exits, stop the other and exit with that code.
    shutdown(typeof code === "number" ? code : 0);
  });
}


