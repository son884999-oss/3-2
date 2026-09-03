const fs = require("fs");
const api = process.env.API_BASE_URL || "http://localhost:8000";
fs.writeFileSync("config.js", `window.APP_CONFIG = { API_BASE_URL: ${JSON.stringify(api)} };\n`);

