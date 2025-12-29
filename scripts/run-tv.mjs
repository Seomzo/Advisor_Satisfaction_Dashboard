import { spawn } from "node:child_process";

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: "inherit", env: process.env });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) return resolve();
      reject(new Error(`${command} ${args.join(" ")} exited with code ${code}`));
    });
  });
}

// Build the client, then start the server (which statically serves client/dist).
await run("npm", ["run", "build", "--workspace", "client"]);
await run("npm", ["run", "start", "--workspace", "server"]);


