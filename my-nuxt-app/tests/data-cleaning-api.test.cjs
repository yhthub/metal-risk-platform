/** Offline API/format contract checks using existing dependencies only. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const source = fs.readFileSync(path.join(root, 'app/composables/useApi.ts'), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
assert.equal(compiled.diagnostics.length, 0)
const requests = []
let failure = null
const exportsObject = {}
vm.runInNewContext(compiled.outputText, {
  exports: exportsObject, Blob, FormData, encodeURIComponent,
  useRuntimeConfig: () => ({ public: { apiBase: 'http://127.0.0.1:8001/' } }),
  $fetch: async (url, options) => {
    requests.push({ url, options })
    if (failure) throw failure
    return options.responseType === 'blob' ? new Blob(['\uFEFFSEQN\r\n00042\r\n']) : { marker: 'real-api-contract' }
  }
})
const api = exportsObject.useApi()
let checks = 0
const check = (name, run) => { run(); checks++; console.log('PASS ' + name) }
;(async () => {
  api.setApiKey(' scoped-key ')
  await api.getCleaningSchema('blood pressure&x')
  check('schema URL encodes selected outcome and uses configured API base', () => {
    assert.equal(requests.at(-1).url, 'http://127.0.0.1:8001/api/datainput/cleaning/schema?outcome_id=blood%20pressure%26x')
    assert.equal(requests.at(-1).options.headers.Authorization, 'Bearer scoped-key')
  })
  const file = new Blob(['SEQN,age\r\n00042,40'], { type: 'text/csv' })
  await api.inspectCleaningFile(file)
  check('inspection uploads actual multipart file, not a local pathname', () => {
    const call = requests.at(-1)
    assert.equal(call.url.endsWith('/cleaning/inspect'), true)
    assert.equal(call.options.body.get('file').size, file.size)
    assert.equal(call.options.body.has('options'), false)
    assert.equal(call.options.headers['Content-Type'], undefined)
  })
  const options = { mode: 'custom', columns: [{ source: 'SEQN', target: 'id' }], row_start: 2, row_end: 3, filters: [{ column: 'age', operator: 'gte', value: '18' }] }
  await api.previewCleanedData(file, options)
  check('preview sends row/column settings in the documented JSON form field', () => {
    const call = requests.at(-1)
    assert.equal(call.url.endsWith('/cleaning/preview'), true)
    assert.deepEqual(JSON.parse(call.options.body.get('options')), options)
    assert.equal(call.options.retry, 0)
  })
  const download = await api.downloadCleanedData(file, options)
  check('export requests Blob with identical settings and inherited authentication', () => {
    const call = requests.at(-1)
    assert.equal(call.url.endsWith('/cleaning/export'), true)
    assert.equal(call.options.responseType, 'blob')
    assert.equal(call.options.headers.Authorization, 'Bearer scoped-key')
    assert.deepEqual(JSON.parse(call.options.body.get('options')), options)
    assert.equal(download.success, true)
    assert(download.data instanceof Blob)
  })
  failure = { status: 422, data: new Blob([JSON.stringify({ detail: { message: '缺少系统列', missing_columns: ['SEQN'] } })], { type: 'application/json' }) }
  const rejected = await api.downloadCleanedData(file, options)
  check('Blob error responses preserve JSON validation details instead of downloading an error', () => {
    assert.equal(rejected.success, false)
    assert.equal(rejected.error, '缺少系统列')
    assert.equal(rejected.details.missing_columns[0], 'SEQN')
    assert.equal(rejected.data, null)
  })
  failure = { status: 401, data: new Blob(['{"detail":"Unauthorized"}']) }
  const unauthorized = await api.downloadCleanedData(file, options)
  check('export authorization failure remains explicit and does not become a successful file', () => {
    assert.equal(unauthorized.success, false)
    assert.match(unauthorized.error, /401/)
  })
  api.setApiKey('')
  failure = null
  await api.inspectCleaningFile(file)
  check('clearing memory-only credentials removes Authorization from cleaning requests', () => assert.equal(requests.at(-1).options.headers.Authorization, undefined))
  const page = fs.readFileSync(path.join(root, 'app/pages/datainput/index.vue'), 'utf8')
  check('batch upload has governed format fields, blank-header template and conversion recovery route', () => {
    assert.match(page, /群体数据格式要求/)
    assert.match(page, /batchFormatSchema\.required_columns\.length/)
    assert.match(page, /const columns = batchFormatSchema\.value\.required_columns/)
    assert.match(page, /to="\/data-cleaning"/)
    assert.match(page, /v-if="batchImportError"/)
    assert.match(page, /缺失值留空/)
    assert.match(page, /至少 2 次有效读数/)
    assert.doesNotMatch(source, /localStorage|sessionStorage/)
  })
  console.log(`\n${checks} cleaning API/format checks passed. No HTTP or model calls.`)
})().catch(error => { console.error(error); process.exitCode = 1 })
