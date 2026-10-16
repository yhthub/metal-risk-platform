const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')

const source = fs.readFileSync(path.join(__dirname, '../app/pages/data-cleaning/index.vue'), 'utf8')
const script = source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*\n/gm, '')
const schema = {
  outcome_id: 'blood_pressure', name: '血压',
  fields: [{ column: 'SEQN', label: '编号', required: true }, { column: 'PBCD_J__LBXBPB', label: '血铅', unit: 'μg/dL', required: true }, { column: 'optional', label: '设计变量', required: false }],
  required_columns: ['SEQN', 'PBCD_J__LBXBPB'], notes: [], limits: { max_file_bytes: 25 * 1024 * 1024 }
}
const inspection = { filename: 'raw.csv', columns: ['SEQN', 'lead', 'tag'], total_rows: 3, preview: [{ SEQN: '0001', lead: '1.5', tag: 'a' }], warnings: [] }
const preview = { columns: ['SEQN', 'PBCD_J__LBXBPB'], total_rows: 2, preview: [{ SEQN: '0001', PBCD_J__LBXBPB: '1.5' }], audit: [], warnings: [], missing_required_columns: [], system_ready: true }
const ok = data => ({ success: true, data })
const failure = error => ({ success: false, data: null, error })
function deferred() { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }

function createPage(overrides = {}) {
  const calls = { inspect: [], preview: [], download: [], clicks: 0, revokes: 0 }
  const api = {
    getCleaningSchema: async () => ok(structuredClone(schema)),
    inspectCleaningFile: async file => { calls.inspect.push(file); return ok(structuredClone(inspection)) },
    previewCleanedData: async (file, options) => { calls.preview.push({ file, options }); return ok(structuredClone(preview)) },
    downloadCleanedData: async (file, options) => { calls.download.push({ file, options }); return ok(new Blob(['SEQN\n0001\n'], { type: 'text/csv' })) },
    ...overrides
  }
  const context = vm.createContext({
    ref: vue.ref, reactive: vue.reactive, computed: vue.computed, watch: vue.watch,
    onMounted: () => {}, nextTick: vue.nextTick, useHead: () => {}, useApi: () => api,
    Blob, JSON, Number, String, Set, Object, Math,
    URL: { createObjectURL: () => 'blob:test-cleaning', revokeObjectURL: () => { calls.revokes += 1 } },
    document: { body: { appendChild: () => {} }, createElement: () => ({ click: () => { calls.clicks += 1 }, remove: () => {} }) },
    setTimeout: callback => { callback(); return 1 }
  })
  vm.runInContext(`${script}\nglobalThis.page = {
    loadSchema, selectSourceFile, restoreExactMappings, setAllColumns, addFilter, validateSettings, runCleaning, downloadResult,
    confirmAndRecheck, keepOnlyRequiredColumns, removeInvalidSystemRows, qualityReasonText, auditLabel,
    schema, schemaError, sourceFile, sourceInfo, sourceError, mode, systemMappings, customColumns,
    rowStart, rowEnd, filters, trimText, dropBlankRows, dropDuplicates, confirmSystemSemantics,
    dropInvalidSystemRows, requireCompleteSystemRows, hasInvalidSystemRows,
    options, result, processError, canPreview, canDownload, previewing, inspecting
  }`, context)
  return { page: context.page, calls }
}
function fileEvent(name = 'raw.csv', size = 100) { return { target: { files: [{ name, size }], value: 'chosen' } } }
async function loadedPage(overrides) { const state = createPage(overrides); await state.page.loadSchema(); await state.page.selectSourceFile(fileEvent()); return state }
async function completeSystemPage(overrides) { const state = await loadedPage(overrides); state.page.systemMappings.PBCD_J__LBXBPB = 'lead'; state.page.confirmSystemSemantics.value = true; return state }

test('matches only exact source column names, never guesses unit or column meaning', async () => {
  const { page } = await loadedPage()
  assert.equal(page.systemMappings.SEQN, 'SEQN')
  assert.equal(page.systemMappings.PBCD_J__LBXBPB, '')
  assert.equal(page.systemMappings.optional, '')
  assert.equal(page.confirmSystemSemantics.value, false)
  assert.equal(page.sourceInfo.value.preview[0].SEQN, '0001')
})

test('sends explicit mapping, original row range and source-column filters', async () => {
  const { page, calls } = await completeSystemPage()
  page.rowStart.value = 2
  page.rowEnd.value = 3
  page.addFilter()
  page.filters.value[0].column = 'lead'
  page.filters.value[0].operator = 'gt'
  page.filters.value[0].value = '1.2'
  await page.runCleaning()
  const options = calls.preview[0].options
  assert.deepEqual(JSON.parse(JSON.stringify(options.columns)), [{ source: 'SEQN', target: 'SEQN' }, { source: 'lead', target: 'PBCD_J__LBXBPB' }])
  assert.equal(options.row_start, 2)
  assert.equal(options.row_end, 3)
  assert.equal(options.filters[0].column, 'lead')
  assert.equal(options.drop_duplicates, false)
  assert.equal(options.confirm_system_semantics, true)
  assert.equal(page.canDownload.value, true)
})

test('setting changes invalidate preview and disable old download', async () => {
  const { page, calls } = await completeSystemPage()
  await page.runCleaning()
  assert.equal(page.canDownload.value, true)
  page.dropDuplicates.value = true
  assert.equal(page.result.value, null)
  assert.equal(page.canDownload.value, false)
  await page.downloadResult()
  assert.equal(calls.download.length, 0)
})

test('late preview cannot overwrite changed settings', async () => {
  const pending = deferred()
  const { page } = await completeSystemPage({ previewCleanedData: () => pending.promise })
  const running = page.runCleaning()
  assert.equal(page.previewing.value, true)
  page.rowStart.value = 2
  pending.resolve(ok(structuredClone(preview)))
  await running
  assert.equal(page.result.value, null)
  assert.equal(page.canDownload.value, false)
  assert.equal(page.previewing.value, false)
})

test('late file inspection cannot replace a more recently selected file', async () => {
  const first = deferred()
  const second = deferred()
  const { page } = createPage({ inspectCleaningFile: file => file.name === 'first.csv' ? first.promise : second.promise })
  await page.loadSchema()
  const runningFirst = page.selectSourceFile(fileEvent('first.csv'))
  const runningSecond = page.selectSourceFile(fileEvent('second.csv'))
  second.resolve(ok({ ...structuredClone(inspection), filename: 'second.csv' }))
  await runningSecond
  first.resolve(ok({ ...structuredClone(inspection), filename: 'first.csv' }))
  await runningFirst
  assert.equal(page.sourceInfo.value.filename, 'second.csv')
  assert.equal(page.sourceFile.value.name, 'second.csv')
  assert.equal(page.inspecting.value, false)
})

test('custom selection and rename are explicit, and empty selection is blocked', async () => {
  const { page, calls } = await loadedPage()
  page.mode.value = 'custom'
  page.setAllColumns(false)
  assert.equal(page.canPreview.value, false)
  page.customColumns.value[0].selected = true
  page.customColumns.value[0].target = 'record_id'
  assert.equal(page.canPreview.value, true)
  await page.runCleaning()
  assert.deepEqual(JSON.parse(JSON.stringify(calls.preview[0].options.columns)), [{ source: 'SEQN', target: 'record_id' }])
})

test('invalid row ranges, duplicate names and numeric filters fail before API', async () => {
  const { page, calls } = await loadedPage()
  page.mode.value = 'custom'
  page.rowStart.value = 0
  await page.runCleaning()
  assert.match(page.processError.value, /起始行/)
  page.rowStart.value = 2
  page.rowEnd.value = 1
  assert.match(page.validateSettings(), /结束行/)
  page.rowEnd.value = ''
  page.customColumns.value[1].target = 'SEQN'
  assert.match(page.validateSettings(), /重复/)
  page.customColumns.value[1].target = 'lead'
  page.addFilter()
  assert.match(page.validateSettings(), /原始列/)
  Object.assign(page.filters.value[0], { column: 'lead', operator: 'gt', value: 'abc' })
  assert.match(page.validateSettings(), /数字/)
  assert.equal(calls.preview.length, 0)
})

test('range overflow, duplicate source mapping and whitespace-colliding column names are rejected', async () => {
  const { page } = await completeSystemPage()
  page.rowEnd.value = 4
  assert.match(page.validateSettings(), /超出/)
  page.rowEnd.value = ''
  page.systemMappings.PBCD_J__LBXBPB = 'SEQN'
  assert.match(page.validateSettings(), /多个系统字段/)
  page.mode.value = 'custom'
  page.trimText.value = false
  page.customColumns.value[1].target = 'SEQN '
  assert.match(page.validateSettings(), /重复/)
  page.customColumns.value[1].target = 'lead'
  page.addFilter()
  Object.assign(page.filters.value[0], { column: 'lead', operator: 'gt', value: '0x10' })
  assert.match(page.validateSettings(), /数字/)
})

test('system download is blocked without semantics confirmation or complete format', async () => {
  const { page } = await loadedPage({ previewCleanedData: async () => ok({ ...structuredClone(preview), system_ready: false, missing_required_columns: ['PBCD_J__LBXBPB'] }) })
  await page.runCleaning()
  assert.equal(page.canDownload.value, false)
  page.confirmSystemSemantics.value = true
  await page.runCleaning()
  assert.equal(page.canDownload.value, false)
})

test('download uses latest preview options and genuine Blob response', async () => {
  const { page, calls } = await completeSystemPage()
  await page.runCleaning()
  await page.downloadResult()
  assert.equal(calls.download.length, 1)
  assert.deepEqual(calls.download[0].options, calls.preview[0].options)
  assert.equal(calls.clicks, 1)
  assert.equal(calls.revokes, 1)
})

test('empty output cannot download and backend errors are shown without fake success', async () => {
  const { page, calls } = await completeSystemPage({ previewCleanedData: async () => ok({ ...structuredClone(preview), total_rows: 0, preview: [] }) })
  await page.runCleaning()
  assert.equal(page.canDownload.value, false)
  await page.downloadResult()
  assert.equal(calls.download.length, 0)
  const failed = await completeSystemPage({ previewCleanedData: async () => failure('字段不匹配') })
  await failed.page.runCleaning()
  assert.equal(failed.page.result.value, null)
  assert.equal(failed.page.processError.value, '字段不匹配')
})

test('unsupported XLS and oversized files never reach inspection API', async () => {
  const { page, calls } = createPage()
  await page.selectSourceFile(fileEvent('raw.xls'))
  assert.match(page.sourceError.value, /另存为 XLSX/)
  await page.selectSourceFile(fileEvent('raw.csv', 26 * 1024 * 1024))
  assert.match(page.sourceError.value, /超过 25 MB/)
  assert.equal(calls.inspect.length, 0)
  assert.equal(page.canPreview.value, false)
})

test('schema failure blocks system mode but allows independently inspected custom output', async () => {
  const { page } = await loadedPage({ getCleaningSchema: async () => failure('后端不可用') })
  assert.equal(page.schema.value, null)
  assert.equal(page.schemaError.value, '后端不可用')
  assert.equal(page.canPreview.value, false)
  page.mode.value = 'custom'
  assert.equal(page.canPreview.value, true)
})

test('download errors and non-Blob responses do not trigger browser downloads', async () => {
  const { page, calls } = await completeSystemPage({ downloadCleanedData: async () => failure('需确认口径') })
  await page.runCleaning()
  await page.downloadResult()
  assert.equal(page.processError.value, '需确认口径')
  assert.equal(calls.clicks, 0)
  const invalid = await completeSystemPage({ downloadCleanedData: async () => ok({ error: 'not a file' }) })
  await invalid.page.runCleaning()
  await invalid.page.downloadResult()
  assert.match(invalid.page.processError.value, /不是文件/)
  assert.equal(invalid.calls.clicks, 0)
})

test('result confirmation is explicit and automatically rechecks the latest options', async () => {
  const { page, calls } = await loadedPage()
  page.systemMappings.PBCD_J__LBXBPB = 'lead'
  await page.runCleaning()
  assert.equal(page.confirmSystemSemantics.value, false)
  assert.equal(page.canDownload.value, false)
  await page.confirmAndRecheck({ target: { checked: true } })
  assert.equal(calls.preview.length, 2)
  assert.equal(calls.preview[1].options.confirm_system_semantics, true)
  assert.equal(calls.preview[1].options.drop_invalid_system_rows, false)
  assert.equal(page.canDownload.value, true)
})

test('repair drops only when explicitly requested and rechecks before enabling download', async () => {
  const requestOptions = []
  const { page, calls } = await completeSystemPage({ previewCleanedData: async (_file, options) => {
    requestOptions.push(options)
    return ok({ ...structuredClone(preview), total_rows: options.drop_invalid_system_rows ? 1 : 2,
      system_ready: options.drop_invalid_system_rows,
      row_quality: { checked: true, invalid_rows: 1, dropped_rows: options.drop_invalid_system_rows ? 1 : 0,
        reasons: [{ code: 'age', label: '年龄不符合成人条件', count: 1 }] } })
  } })
  const originalFile = page.sourceFile.value
  await page.runCleaning()
  assert.equal(page.hasInvalidSystemRows.value, true)
  assert.equal(page.canDownload.value, false)
  assert.equal(page.dropInvalidSystemRows.value, false)
  assert.equal(page.qualityReasonText(['age']), '年龄不符合成人条件')
  await page.removeInvalidSystemRows()
  assert.equal(requestOptions.length, 2)
  assert.equal(requestOptions[1].drop_invalid_system_rows, true)
  assert.equal(page.sourceFile.value, originalFile)
  assert.equal(page.hasInvalidSystemRows.value, false)
  assert.equal(page.canDownload.value, true)
  await page.downloadResult()
  assert.equal(calls.download[0].options.drop_invalid_system_rows, true)
  assert.match(page.auditLabel('check_system_rows'), /检查/)
})

test('whole missing mandatory columns cannot be repaired by removing records', async () => {
  const { page, calls } = await completeSystemPage({ previewCleanedData: async () => ok({ ...structuredClone(preview),
    system_ready: false, missing_required_columns: ['PBCD_J__LBXBPB'],
    row_quality: { checked: false, invalid_rows: 0, dropped_rows: 0, column_errors: ['PBCD_J__LBXBPB'] } }) })
  await page.runCleaning()
  const current = page.result.value
  await page.removeInvalidSystemRows()
  await page.keepOnlyRequiredColumns()
  assert.equal(page.result.value, current)
  assert.equal(page.dropInvalidSystemRows.value, false)
  assert.equal(page.hasInvalidSystemRows.value, false)
  assert.equal(page.canDownload.value, false)
})

test('only-required repair removes optional fields, keeps required mappings and raw source', async () => {
  const { page, calls } = await completeSystemPage()
  page.systemMappings.optional = 'tag'
  await page.runCleaning()
  const originalFile = page.sourceFile.value
  await page.keepOnlyRequiredColumns()
  assert.equal(calls.preview.length, 2)
  assert.equal(page.systemMappings.optional, '')
  assert.equal(page.systemMappings.SEQN, 'SEQN')
  assert.equal(page.systemMappings.PBCD_J__LBXBPB, 'lead')
  assert.equal(page.sourceFile.value, originalFile)
  assert.equal(page.confirmSystemSemantics.value, true)
  assert.equal(calls.preview[1].options.columns.length, 2)
})

test('quality flags invalidate previews, are system-only, and reset for a new file', async () => {
  const { page } = await completeSystemPage()
  await page.runCleaning()
  page.requireCompleteSystemRows.value = true
  assert.equal(page.result.value, null)
  assert.equal(page.canDownload.value, false)
  page.dropInvalidSystemRows.value = true
  assert.equal(page.options.value.require_complete_system_rows, true)
  page.mode.value = 'custom'
  assert.equal(page.options.value.require_complete_system_rows, false)
  assert.equal(page.options.value.drop_invalid_system_rows, false)
  await page.selectSourceFile(fileEvent('new.csv'))
  assert.equal(page.dropInvalidSystemRows.value, false)
  assert.equal(page.requireCompleteSystemRows.value, false)
  assert.equal(page.confirmSystemSemantics.value, false)
})

test('mandatory mapping changes require fresh semantics confirmation; optional removal does not', async () => {
  const { page } = await completeSystemPage()
  page.systemMappings.optional = 'tag'
  assert.equal(page.confirmSystemSemantics.value, true)
  await page.runCleaning()
  await page.keepOnlyRequiredColumns()
  assert.equal(page.confirmSystemSemantics.value, true)
  page.systemMappings.PBCD_J__LBXBPB = 'tag'
  assert.equal(page.confirmSystemSemantics.value, false)
  assert.equal(page.result.value, null)
  assert.equal(page.canDownload.value, false)
})
