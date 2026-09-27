import { spawnSync } from 'node:child_process'
import { readFile, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import openapiTS, { astToString } from 'openapi-typescript'

const root = fileURLToPath(new URL('../../', import.meta.url))
const result = spawnSync('uv', ['run', '--extra', 'web', '--no-sync', 'python', '-m', 'szurubooru_toolkit.web.schema'], {
  cwd: root,
  encoding: 'utf8',
  windowsHide: true,
})
if (result.error) throw result.error
if (result.status !== 0) throw new Error(result.stderr || 'Schema export failed. Run uv sync --extra web first.')
const output = astToString(await openapiTS(JSON.parse(result.stdout)))
const destination = new URL('../src/api.generated.ts', import.meta.url)
if (process.argv.includes('--check')) {
  if (await readFile(destination, 'utf8') !== output) {
    throw new Error('API types are stale. Run npm run api:generate.')
  }
  console.log('API types match the backend schema.')
} else {
  await writeFile(destination, output)
  console.log('Generated src/api.generated.ts')
}