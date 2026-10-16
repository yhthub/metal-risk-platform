/** Public risk demo API boundaries: no server, training or generator calls. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const compiled = ts.transpileModule(fs.readFileSync(path.join(root, 'app/composables/useApi.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText

test('fixed demo import uses shared auth, no caller file path and no automatic retry', async () => {
  const calls = []
  const exported = {}
  vm.runInNewContext(compiled, {
    exports: exported, Blob, FormData, encodeURIComponent,
    useRuntimeConfig: () => ({ public: { apiBase: 'http://127.0.0.1:8000/' } }),
    $fetch: async (url, options) => { calls.push({ url, options }); return { import_result: { file_id: 'FILE-1234abcd' } } },
  })
  const api = exported.useApi()
  api.setApiKey('test-session-key')
  const response = await api.importPredictionBatchDemo()
  assert.equal(response.success, true)
  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/risk/demo-batch/import')
  assert.equal(calls[0].options.method, 'POST')
  assert.equal(calls[0].options.headers.Authorization, 'Bearer test-session-key')
  assert.equal(calls[0].options.retry, 0)
  assert.equal(calls[0].options.timeout, 60000)
  assert.equal(calls[0].options.body, undefined)
})

test('failed integrity response stays a failure and cannot become a demo result', async () => {
  const exported = {}
  vm.runInNewContext(compiled, {
    exports: exported, Blob, FormData, encodeURIComponent,
    useRuntimeConfig: () => ({ public: { apiBase: '' } }),
    $fetch: async () => { throw { response: { status: 503 }, data: { detail: '演示资产完整性校验失败' } } },
  })
  const response = await exported.useApi().importPredictionBatchDemo()
  assert.equal(response.success, false)
  assert.equal(response.statusCode, 503)
  assert.equal(response.data, null)
  assert.equal(response.error, '演示资产完整性校验失败')
})
test('full cohort inference is one request without a display-page offset or hidden limit', async () => {
  const calls = []
  const exported = {}
  vm.runInNewContext(compiled, {
    exports: exported, Blob, FormData, encodeURIComponent,
    useRuntimeConfig: () => ({ public: { apiBase: '' } }),
    $fetch: async (url, options) => { calls.push({ url, options }); return { complete: true } },
  })
  const api = exported.useApi()
  const body = { file_id: 'FILE-1234abcd', measurements: { fixture: true } }
  await api.predictCohort(body)
  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, '/api/risk/predict-cohort')
  assert.equal(calls[0].options.method, 'POST')
  assert.equal(calls[0].options.body, body)
  assert.equal(calls[0].options.retry, 0)
  assert.equal(calls[0].options.timeout, 600000)
  assert.equal(calls[0].options.body.limit, undefined)
  assert.equal(calls[0].options.body.offset, undefined)
})
