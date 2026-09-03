const fs = require("fs");
const path = require("path");
const api = process.env.API_BASE_URL || "http://localhost:8000";
const output = path.join(__dirname, "dist");
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output, { recursive: true });
for (const filename of ["index.html", "styles.css", "app.js", "favicon.svg"]) {
  fs.copyFileSync(path.join(__dirname, filename), path.join(output, filename));
}
fs.writeFileSync(
  path.join(output, "config.js"),
  `window.APP_CONFIG = { API_BASE_URL: ${JSON.stringify(api)} };\n`,
);
