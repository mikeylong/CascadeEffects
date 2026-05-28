import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const defaultDataPath = path.join(repoRoot, 'brand', 'cascade-effects-signal.style-system.json');
const defaultSchemaPath = path.join(
  repoRoot,
  'brand',
  'cascade-effects-signal.style-system.schema.json',
);

const resolveInputPath = (inputPath, fallbackPath) =>
  inputPath ? path.resolve(process.cwd(), inputPath) : fallbackPath;

const readJson = (targetPath) => JSON.parse(fs.readFileSync(targetPath, 'utf8'));

const formatInstancePath = (instancePath) => (instancePath ? instancePath : '/');

const dataPath = resolveInputPath(process.argv[2], defaultDataPath);
const schemaPath = resolveInputPath(process.argv[3], defaultSchemaPath);

const schema = readJson(schemaPath);
const data = readJson(dataPath);

const ajv = new Ajv2020({
  allErrors: true,
  strict: false,
});

const validate = ajv.compile(schema);
const valid = validate(data);

if (!valid) {
  console.error(`Style-system validation failed for ${path.relative(repoRoot, dataPath)}.`);
  console.error(`Schema: ${path.relative(repoRoot, schemaPath)}`);

  for (const error of validate.errors ?? []) {
    const location = formatInstancePath(error.instancePath);
    const message = error.message ?? 'Validation error';
    console.error(`- ${location}: ${message}`);
  }

  process.exit(1);
}

console.log(`Style-system validation passed for ${path.relative(repoRoot, dataPath)}.`);
