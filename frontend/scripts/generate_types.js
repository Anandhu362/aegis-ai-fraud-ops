import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { compileFromFile } from "json-schema-to-typescript";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const contractsDir = path.resolve(__dirname, "../../contracts/jsonschema");
const outputDir = path.resolve(__dirname, "../src/types/generated");

async function generate() {
  if (!fs.existsSync(contractsDir)) {
    console.log(`No contracts found at ${contractsDir}`);
    return;
  }

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const files = fs.readdirSync(contractsDir).filter((f) => f.endsWith(".json"));

  for (const file of files) {
    const filePath = path.join(contractsDir, file);
    const tsName = file.replace(".json", ".d.ts");
    const outPath = path.join(outputDir, tsName);

    try {
      const ts = await compileFromFile(filePath, {
        bannerComment: "/* eslint-disable */\n/**\n* Auto-generated from Aegis Pydantic Schema. Do NOT edit manually.\n*/",
      });
      fs.writeFileSync(outPath, ts, "utf-8");
      console.log(`Generated ${outPath}`);
    } catch (err) {
      console.error(`Failed to compile ${file}:`, err);
    }
  }
}

generate();
