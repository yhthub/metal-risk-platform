/** Offline checks only: mocked HTTP, Vue SFC compilation, and entry-state tests. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules', '.pnpm')
const packagePath = (prefix, name) => path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name)
const ts = require(packagePath('typescript@', 'typescript'))
const vueCompiler = require(packagePath('@vue+compiler-sfc@', '@vue/compiler-sfc'))
const compileTs = source => {
  const result = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
  assert.equal((result.diagnostics || []).length, 0, 'TypeScript syntax diagnostics')
  return result.outputText
}
const evaluate = (source, context = {}) => {
  const exports = {}
  vm.runInNewContext(compileTs(source), { exports, ...context })
  return exports
}
const apiSource = fs.readFileSync(path.join(root, 'app/composables/useApi.ts'), 'utf8')
const appFile = path.join(root, 'app/app.vue')
const appSource = fs.readFileSync(appFile, 'utf8')
const helpers = evaluate(fs.readFileSync(path.join(root, 'app/utils/systemAccess.ts'), 'utf8'))
const validInfo = { title: 'test API', version: '1.0.0', endpoints: { datainput: {} } }
let checks = 0
const check = (name, run) => { run(); checks++; console.log(`PASS ${name}`) }

check('only valid system API information passes, never HTML/empty or failed payload', () => {
  assert.equal(helpers.verifySystemAccessResult({ success: true, data: validInfo }).accepted, true)
  for (const data of [null, undefined, '<html>SPA fallback</html>', {}, { title: 'API', version: '1' }]) {
    const result = helpers.verifySystemAccessResult({ success: true, data })
    assert.equal(result.accepted, false)
    assert.match(result.error, /代理配置/)
  }
  assert.equal(helpers.verifySystemAccessResult({ success: false, data: validInfo }).accepted, false)
  assert.equal(helpers.verifySystemAccessResult({ success: false, statusCode: 401 }).needsKey, true)
  assert.equal(helpers.verifySystemAccessResult({ success: false, statusCode: 403 }).needsKey, false)
})

const parsed = vueCompiler.parse(appSource, { filename: appFile })
check('root Vue SFC, template, TypeScript and scoped styles compile', () => {
  assert.equal(parsed.errors.length, 0)
  const script = vueCompiler.compileScript(parsed.descriptor, { id: 'system-access-test' })
  compileTs(script.content)
  const template = vueCompiler.compileTemplate({ source: parsed.descriptor.template.content, filename: appFile, id: 'system-access-test', compilerOptions: { bindingMetadata: script.bindings } })
  assert.equal(template.errors.length, 0)
  const style = vueCompiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename: appFile, id: 'system-access-test', scoped: true })
  assert.equal(style.errors.length, 0)
})
check('first page mount is gated, settings remain accessible and password is masked', () => {
  assert.match(appSource, /NuxtPage v-if="pageMounted"/)
  assert.match(appSource, /aria-label="系统访问设置"/)
  assert.match(appSource, /type="password" autocomplete="off"/)
  assert.equal(/localStorage|sessionStorage|useState\(|public\.[\w]*key|console\./i.test(appSource + apiSource), false)
  assert.equal(/location\.reload|window\.location|v-html/.test(appSource), false)
})

const ref = value => ({ value })
const componentFor = (getApiInfo, publicDemo = false) => {
  const keys = []
  let mount
  let unmount
  let listener
  let removed = false
  const component = evaluate(parsed.descriptor.scriptSetup.content + '\nexport { publicDemo, openAccessSettings, checkCurrentAccess, verifyCandidateKey, clearSessionAccess, closeAccessSettings, pageMounted, accessVerified, candidateKey, checkingAccess, dialogVisible, accessError, needsAccessKey };', {
    require: name => {
      if (name === 'vue') return { ref, nextTick: async () => {}, onMounted: callback => { mount = callback }, onUnmounted: callback => { unmount = callback } }
      if (name === '~/utils/systemAccess') return helpers
      throw new Error(`Unexpected import ${name}`)
    },
    useRuntimeConfig: () => ({ public: { publicDemo } }),
    useApi: () => ({
      getApiInfo,
      setApiKey: key => keys.push(key),
      onAccessRequired: callback => { listener = callback; return () => { removed = true } }
    })
  })
  return { component, keys, mount: () => mount(), unmount: () => unmount(), unauthorized: () => listener?.(), hasListener: () => Boolean(listener), removed: () => removed }
}

;(async () => {
  check('public demo is opt-in at build time, never accidentally enabled by a false string', () => {
    const configSource = fs.readFileSync(path.join(root, 'nuxt.config.ts'), 'utf8')
    for (const [setting, enabled] of [[undefined, false], ['', false], ['false', false], ['true', true]]) {
      const config = evaluate(configSource, { defineNuxtConfig: config => config, process: { env: { NUXT_PUBLIC_PUBLIC_DEMO: setting } } }).default
      assert.equal(config.runtimeConfig.public.publicDemo, enabled)
    }
    for (const setting of [undefined, false, '', 'false', '1']) {
      assert.equal(componentFor(async () => validInfo, setting).component.publicDemo, false)
    }
  })
  check('public mode removes access settings and dialog, with a normal-flow data privacy note', () => {
    assert.match(appSource, /<button v-if="!publicDemo" class="access-settings-trigger"/)
    assert.match(appSource, /<el-dialog v-if="!publicDemo"/)
    assert.match(appSource, /<p v-if="publicDemo" class="public-demo-note" role="note"/)
    assert.match(appSource, /公开或脱敏数据/)
    assert.match(appSource, /\.public-demo-note \{ position: static;/)
  })
  let publicProbes = 0
  for (const setting of [true, 'true']) {
    const publicApp = componentFor(async () => { publicProbes++; return { success: false, statusCode: 401 } }, setting)
    assert.equal(publicApp.component.pageMounted.value, true)
    publicApp.mount()
    await publicApp.component.checkCurrentAccess()
    await publicApp.component.openAccessSettings()
    publicApp.component.candidateKey.value = 'must-not-be-installed'
    await publicApp.component.verifyCandidateKey()
    await publicApp.component.clearSessionAccess()
    publicApp.unauthorized()
    publicApp.unmount()
    check(`public mode ${setting === true ? 'boolean' : 'string'} enters immediately without a probe, key or 401 prompt`, () => {
      assert.equal(publicProbes, 0)
      assert.equal(publicApp.component.pageMounted.value, true)
      assert.equal(publicApp.component.dialogVisible.value, false)
      assert.equal(publicApp.component.checkingAccess.value, false)
      assert.equal(publicApp.hasListener(), false)
      assert.equal(publicApp.keys.length, 0)
    })
  }
  const calls = []
  let responseError = null
  const module = evaluate(apiSource, {
    useRuntimeConfig: () => ({ public: { apiBase: '' } }),
    $fetch: async (url, options) => { calls.push({ url, options }); if (responseError) throw responseError; return validInfo }
  })
  const firstPage = module.useApi()
  const secondPage = module.useApi()
  firstPage.setApiKey(' shared-memory-key ')
  await secondPage.getOutcomeConfigs()
  await secondPage.getCleaningSchema()
  await secondPage.agentChat('test only')
  check('different pages share the same memory-only Bearer credential', () => {
    assert.equal(calls.length, 3)
    for (const call of calls) assert.equal(call.options.headers.Authorization, 'Bearer shared-memory-key')
    assert.equal(calls[0].url, '/api/datainput/outcomes')
    assert.equal(calls[1].url, '/api/datainput/cleaning/schema?outcome_id=blood_pressure')
    assert.equal(calls[2].url, '/api/agent/chat')
  })
  await secondPage.getApiInfo('candidate-only')
  await firstPage.getApiInfo()
  await secondPage.getApiInfo('')
  check('read-only bounded probe can validate a candidate without replacing the shared key', () => {
    assert.equal(calls[3].options.headers.Authorization, 'Bearer candidate-only')
    assert.equal(calls[4].options.headers.Authorization, 'Bearer shared-memory-key')
    assert.equal(calls[5].options.headers.Authorization, undefined)
    for (const call of calls.slice(3)) {
      assert.equal(call.url, '/api/info')
      assert.equal(call.options.method, 'GET')
      assert.equal(call.options.timeout, 10000)
      assert.equal(call.options.retry, 0)
    }
  })
  const prefixedCalls = []
  const prefixedApi = evaluate(apiSource, {
    useRuntimeConfig: () => ({ public: { apiBase: '/zhiwei/' } }),
    $fetch: async (url, options) => { prefixedCalls.push({ url, options }); return validInfo }
  }).useApi()
  await prefixedApi.getApiInfo('site-token')
  await prefixedApi.getCleaningSchema()
  check('same-site independent path respects the configured API prefix without root interception', () => {
    assert.equal(prefixedCalls[0].url, '/zhiwei/api/info')
    assert.equal(prefixedCalls[1].url, '/zhiwei/api/datainput/cleaning/schema?outcome_id=blood_pressure')
    assert.equal(/\$fetch|fetch\(/.test(parsed.descriptor.scriptSetup.content), false)
    assert.equal(prefixedCalls[0].options.headers.Authorization, 'Bearer site-token')
  })
  let notices = 0
  const unsubscribe = secondPage.onAccessRequired(() => { notices++ })
  responseError = { response: { status: 401 }, message: 'Unauthorized' }
  const countBeforePost = calls.length
  const denied = await firstPage.importGroupDemo()
  check('401 exposes its status and notifies once, never automatically repeats a mutation', () => {
    assert.equal(denied.success, false)
    assert.equal(denied.statusCode, 401)
    assert.equal(notices, 1)
    assert.equal(calls.length, countBeforePost + 1)
    assert.equal(calls.at(-1).options.method, 'POST')
    assert.equal(calls.at(-1).options.retry, 0)
  })
  unsubscribe()
  await firstPage.getApiInfo()
  assert.equal(notices, 1)
  responseError = { statusCode: 503, message: 'Unavailable' }
  const unavailable = await firstPage.getApiInfo()
  check('503/network failures remain failures, not key prompts or synthetic success', () => {
    assert.equal(unavailable.success, false)
    assert.equal(unavailable.statusCode, 503)
    assert.equal(notices, 1)
  })
  responseError = null
  firstPage.setApiKey('')
  await secondPage.getOutcomeConfigs()
  assert.equal(calls.at(-1).options.headers.Authorization, undefined)

  const local = componentFor(async () => ({ success: true, data: validInfo }))
  assert.equal(local.component.pageMounted.value, false)
  await local.component.checkCurrentAccess()
  check('local open API passes without asking for a key; only then can pages mount', () => {
    assert.equal(local.component.pageMounted.value, true)
    assert.equal(local.component.accessVerified.value, true)
    assert.equal(local.component.dialogVisible.value, false)
    assert.equal(local.keys.length, 0)
  })

  let protectedResult = { success: false, statusCode: 401, error: 'key required' }
  const probes = []
  const protectedApp = componentFor(async key => { probes.push(key); return protectedResult })
  protectedApp.mount()
  await protectedApp.component.checkCurrentAccess()
  // The mounted hook's first probe is asynchronous; await it before changing inputs.
  await Promise.resolve()
  check('protected API does not mount a page before validation', () => {
    assert.equal(protectedApp.component.pageMounted.value, false)
    assert.equal(protectedApp.component.needsAccessKey.value, true)
    assert.equal(protectedApp.component.dialogVisible.value, true)
    assert.equal(probes.length, 1)
  })
  protectedApp.component.candidateKey.value = ' wrong-key '
  await protectedApp.component.verifyCandidateKey()
  check('wrong key never becomes shared credential and is removed from the form', () => {
    assert.equal(protectedApp.keys.length, 0)
    assert.equal(protectedApp.component.candidateKey.value, '')
    assert.equal(protectedApp.component.pageMounted.value, false)
    assert.equal(probes.at(-1), 'wrong-key')
  })
  protectedResult = { success: true, data: validInfo }
  protectedApp.component.candidateKey.value = ' correct-key '
  await protectedApp.component.verifyCandidateKey()
  check('successful verification commits the key and enters the requested page', () => {
    assert.deepEqual(protectedApp.keys, ['correct-key'])
    assert.equal(protectedApp.component.pageMounted.value, true)
    assert.equal(protectedApp.component.accessVerified.value, true)
    assert.equal(protectedApp.component.dialogVisible.value, false)
    assert.equal(protectedApp.component.candidateKey.value, '')
  })
  protectedApp.unauthorized()
  check('later 401 reopens settings without unmounting user input or replaying a request', () => {
    assert.equal(protectedApp.component.pageMounted.value, true)
    assert.equal(protectedApp.component.accessVerified.value, false)
    assert.equal(protectedApp.component.dialogVisible.value, true)
    assert.match(protectedApp.component.accessError.value, /不会自动重新提交/)
    assert.equal(probes.length, 3)
  })
  protectedApp.component.closeAccessSettings()
  assert.equal(protectedApp.component.dialogVisible.value, true)
  protectedApp.unmount()
  assert.equal(protectedApp.removed(), true)

  const offline = componentFor(async () => ({ success: false, statusCode: null, error: 'network unavailable' }))
  await offline.component.checkCurrentAccess()
  check('network failure blocks first load with an explicit retryable error', () => {
    assert.equal(offline.component.pageMounted.value, false)
    assert.equal(offline.component.accessVerified.value, false)
    assert.equal(offline.component.needsAccessKey.value, false)
    assert.equal(offline.component.dialogVisible.value, true)
    assert.equal(offline.component.accessError.value, 'network unavailable')
  })
  const previousRequests = probes.length
  protectedApp.component.candidateKey.value = ' '
  await protectedApp.component.verifyCandidateKey()
  assert.equal(probes.length, previousRequests)
  assert.match(protectedApp.component.accessError.value, /填写访问密钥/)

  let release
  let inflightCount = 0
  const slow = componentFor(async () => { inflightCount++; return await new Promise(resolve => { release = resolve }) })
  const pending = slow.component.checkCurrentAccess()
  await slow.component.checkCurrentAccess()
  await slow.component.verifyCandidateKey()
  assert.equal(inflightCount, 1)
  release({ success: true, data: validInfo })
  await pending
  check('one access probe at a time prevents duplicate verification dispatch', () => {
    assert.equal(inflightCount, 1)
    assert.equal(slow.component.checkingAccess.value, false)
  })
  protectedResult = { success: false, statusCode: 401, error: 'key required' }
  await protectedApp.component.clearSessionAccess()
  check('clearing the shared credential rechecks access without losing the mounted page', () => {
    assert.equal(protectedApp.keys.at(-1), '')
    assert.equal(protectedApp.component.accessVerified.value, false)
    assert.equal(protectedApp.component.pageMounted.value, true)
    assert.equal(protectedApp.component.dialogVisible.value, true)
  })
  console.log(`\n${checks} offline system-access checks passed. No live network, browser or deployment.`)
})().catch(error => { console.error(error); process.exitCode = 1 })
