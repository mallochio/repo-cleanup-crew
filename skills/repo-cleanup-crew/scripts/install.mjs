#!/usr/bin/env node
import { cpSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const skillRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(skillRoot, "assets/repo-cleanup-crew");
const args = process.argv.slice(2);
const targetArgument = args.find((a) => !a.startsWith("--"));
const target = resolve(process.cwd(), targetArgument ?? "tools/repo-cleanup-crew");
const force = args.includes("--force");

if (existsSync(target) && !force) {
  console.error(`Refusing to overwrite ${target}. Re-run with --force only after reviewing the existing files.`);
  process.exit(1);
}

mkdirSync(dirname(target), { recursive: true });
cpSync(source, target, { recursive: true, force });
console.log(`Copied repo-cleanup-crew to ${target}`);
