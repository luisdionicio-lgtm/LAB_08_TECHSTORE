import { createRequire } from "node:module";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("C:/Users/Luis Angel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const mode = process.argv[2] || "auth";
const out = fileURLToPath(new URL("../tmp/lab08-video/web/", import.meta.url));
await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  colorScheme: "light",
  recordVideo: { dir: out, size: { width: 1920, height: 1080 } },
});
const page = await context.newPage();
const video = page.video();
const startedAt = Date.now();
const marks = [];

function mark(label) {
  marks.push({ label, time: Number(((Date.now() - startedAt) / 1000).toFixed(3)) });
}

async function pause(milliseconds) {
  await page.waitForTimeout(milliseconds);
}

async function humanFill(locator, value) {
  await locator.fill("");
  await locator.pressSequentially(value, { delay: 65 });
}

async function shot(name) {
  await page.screenshot({ path: path.join(out, name), fullPage: false });
}

async function login(username, password) {
  await humanFill(page.locator("#username"), username);
  await humanFill(page.locator("#password"), password);
  await pause(700);
  await page.getByRole("button", { name: /Ingresar a TechStore/i }).click();
  await page.waitForLoadState("networkidle");
}

if (mode === "auth") {
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  mark("login-start");
  await pause(3500);
  await shot("01-login.png");
  mark("failed-start");

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    await login("cliente", "ClaveIncorrecta1!");
    await pause(2300);
    await shot(`02-failed-${attempt}.png`);
  }
  mark("lock-start");
  await login("cliente", "Cliente123!");
  await pause(3500);
  await shot("03-locked-correct-password.png");

  mark("admin-start");
  await login("admin", "Admin123!");
  await pause(4000);
  await shot("04-admin-dashboard.png");
  mark("roles-start");
  await page.goto("http://localhost:8080/users", { waitUntil: "networkidle" });
  await pause(4500);
  await shot("05-users-roles.png");
  mark("social-start");
  await page.getByRole("button", { name: /Cerrar sesión/i }).click();
  await page.waitForLoadState("networkidle");
  await pause(3500);
  await shot("06-gmail-github.png");
  mark("end");
}

if (mode === "client") {
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  mark("client-login-start");
  await pause(2200);
  await login("cliente", "Cliente123!");
  mark("catalog-start");
  await pause(4200);
  await page.getByRole("button", { name: "Seleccionar", exact: true }).first().click();
  await page.waitForLoadState("networkidle");
  mark("selection-start");
  await pause(4200);
  await shot("07-client-catalog.png");
  await page.locator("[data-catalog-search]").fill("PC Gamer");
  mark("search-start");
  await pause(4200);
  mark("end");
}

await context.close();
const recordedPath = await video.path();
const finalVideo = path.join(out, `${mode}-live.webm`);
await fs.copyFile(recordedPath, finalVideo);
await fs.writeFile(path.join(out, `${mode}-marks.json`), JSON.stringify(marks, null, 2), "utf8");
await browser.close();
console.log(`Capturas TechStore generadas en modo ${mode}.`);
