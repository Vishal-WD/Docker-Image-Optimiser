import { chromium } from "file:///C:/Users/C Vishal/AppData/Local/npm-cache/_npx/af752b90495482d7/node_modules/playwright-core/index.mjs";
import path from "node:path";

const outDir = "C:/Users/C Vishal/.gemini/antigravity/brain/f835a858-d55a-4d3a-af6e-425838c59ebb";

async function run() {
  console.log("Launching Edge browser...");
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  console.log("Navigating to http://127.0.0.1:8000...");
  await page.goto("http://127.0.0.1:8000", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // 1. Click optimize button on the loaded 1.5 GB sample Dockerfile
  console.log("Running Docker Image Optimizer analysis...");
  await page.click("#optimizeBtn");
  await page.waitForTimeout(1000);

  // Frame 1: Optimizer Studio - Input Dockerfile, detected issues, and generated multi-stage build
  console.log("Capturing Frame 1: Dockerfile Optimizer Studio...");
  await page.screenshot({ path: path.join(outDir, "demo_frame1_studio.png") });

  // Frame 2: Generated .dockerignore tab
  console.log("Capturing Frame 2: Generated .dockerignore rules...");
  await page.click("#out-btn-dockerignore");
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outDir, "demo_frame2_dockerignore.png") });

  // Frame 3: Tab 2 - Benchmarks & Layer Analysis
  console.log("Navigating to Tab 2: Benchmarks & Layers...");
  await page.click("#tab-btn-metrics");
  await page.waitForTimeout(1000);
  console.log("Capturing Frame 3: Docker size benchmarks & bloat breakdown...");
  await page.screenshot({ path: path.join(outDir, "demo_frame3_benchmarks.png") });

  // Frame 4: Tab 3 - PostgreSQL Database Explorer
  console.log("Navigating to Tab 3: PostgreSQL Database Audits...");
  await page.click("#tab-btn-database");
  await page.waitForTimeout(1000);
  console.log("Capturing Frame 4: PostgreSQL audit logs...");
  await page.screenshot({ path: path.join(outDir, "demo_frame4_database.png") });

  await browser.close();
  console.log("All Docker Image Optimizer demo frames captured successfully!");
}

run().catch(err => {
  console.error("Error during recording:", err);
  process.exit(1);
});
