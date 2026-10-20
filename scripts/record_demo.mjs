import { chromium } from "file:///C:/Users/C Vishal/AppData/Local/npm-cache/_npx/af752b90495482d7/node_modules/playwright-core/index.mjs";
import path from "node:path";

const outDir = "C:/Users/C Vishal/.gemini/antigravity/brain/f835a858-d55a-4d3a-af6e-425838c59ebb";
const sampleImage = "C:/Users/C Vishal/.gemini/antigravity/brain/f835a858-d55a-4d3a-af6e-425838c59ebb/.user_uploaded/media_1792496825300_db6becd7.jpg";

async function run() {
  console.log("Launching Edge browser...");
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  console.log("Navigating to http://127.0.0.1:8000...");
  await page.goto("http://127.0.0.1:8000", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Frame 1: Tab 1 Top - KPI Cards & Size Chart
  console.log("Capturing Frame 1: Docker KPI metrics & size breakdown...");
  await page.screenshot({ path: path.join(outDir, "demo_frame1_metrics.png") });

  // Frame 2: Tab 1 Bottom - Side-by-side Dockerfiles & REA MCP Integration
  console.log("Capturing Frame 2: Side-by-side Dockerfiles & REA section...");
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(outDir, "demo_frame2_dockerfiles.png") });

  // Frame 3: Tab 2 - Media Image Compressor
  console.log("Navigating to Tab 2: Media Compressor...");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.click("#tab-btn-compressor");
  await page.waitForTimeout(400);

  console.log("Uploading sample image and running compression...");
  const fileInput = await page.$("#imageFileInput");
  await fileInput.setInputFiles(sampleImage);
  await page.waitForTimeout(500);

  await page.click("#optimizeBtn");
  await page.waitForSelector("#resultPreview:not(.hidden)", { timeout: 10000 });
  await page.waitForTimeout(1000);
  console.log("Capturing Frame 3: Media image compression result...");
  await page.screenshot({ path: path.join(outDir, "demo_frame3_compressor.png") });

  // Frame 4: Tab 3 - PostgreSQL Database Explorer
  console.log("Navigating to Tab 3: PostgreSQL Database Explorer...");
  await page.click("#tab-btn-database");
  await page.waitForTimeout(1000);
  console.log("Capturing Frame 4: PostgreSQL Database records...");
  await page.screenshot({ path: path.join(outDir, "demo_frame4_database.png") });

  await browser.close();
  console.log("All frames captured successfully!");
}

run().catch(err => {
  console.error("Error during recording:", err);
  process.exit(1);
});
