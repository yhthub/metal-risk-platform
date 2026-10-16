<template>
  <div class="application-root">
    <!-- 公开演示直接挂载；私有模式完成预检后才启动各页面请求。 -->
    <NuxtPage v-if="pageMounted" :keepalive="{}" />
    <main v-else class="access-bootstrap" aria-live="polite">
      <div class="access-bootstrap-card">
        <span class="access-eyebrow">ZHIWEI · SYSTEM ACCESS</span>
        <h1>{{ checkingAccess ? '正在连接系统' : '欢迎体验知微系统' }}</h1>
        <p>{{ checkingAccess ? '先确认系统 API 连接，再加载各功能页面。' : '请完成访问检查后进入。密钥仅在本次浏览器运行内存中使用。' }}</p>
        <button v-if="!checkingAccess" class="access-action primary" type="button" @click="openAccessSettings">打开访问设置</button>
      </div>
    </main>

    <p v-if="publicDemo" class="public-demo-note" role="note">公开演示 · 仅使用公开或脱敏数据；HTTP 连接不加密，请勿上传真实个人健康资料。</p>

    <button v-if="!publicDemo" class="access-settings-trigger" type="button" aria-label="系统访问设置" @click="openAccessSettings">
      <span :class="['access-status-dot', { verified: accessVerified }]" aria-hidden="true" />
      访问设置
    </button>

    <el-dialog v-if="!publicDemo" v-model="dialogVisible" title="系统访问设置" width="440px" append-to-body
      :close-on-click-modal="false" :close-on-press-escape="accessVerified" :show-close="accessVerified"
      class="system-access-dialog" @closed="candidateKey = ''">
      <p class="access-description">数据接入、数据清洗与智能问答共用此访问密钥。本地未配置密钥时，系统会直接进入。</p>
      <p class="access-memory-note">公网演示请仅使用公开示例或已脱敏数据；HTTP 连接不加密，请勿上传真实个人健康资料。此处是网站体验密钥，不是模型 API Key。</p>
      <p class="access-current-state" role="status">{{ accessVerified ? '当前会话已通过访问检查' : needsAccessKey ? '此服务器需要访问密钥' : '当前会话尚未通过访问检查' }}</p>
      <form class="access-form" @submit.prevent="verifyCandidateKey">
        <label for="system-access-key">访问密钥</label>
        <input id="system-access-key" ref="keyInput" v-model="candidateKey" type="password" autocomplete="off"
          spellcheck="false" placeholder="填写管理员提供的体验密钥" :disabled="checkingAccess" />
        <p class="access-memory-note">不写入浏览器存储；刷新或关闭页面后需重新填写。请勿填写阿里云账号密码。</p>
        <p v-if="accessError" class="access-error" role="alert">{{ accessError }}</p>
        <div class="access-form-actions">
          <button class="access-action primary" type="submit" :disabled="checkingAccess">{{ checkingAccess ? '正在检查…' : '验证并进入' }}</button>
          <button class="access-action" type="button" :disabled="checkingAccess" @click="checkCurrentAccess">重新检查连接</button>
        </div>
      </form>
      <template #footer>
        <div class="access-dialog-footer">
          <button class="access-clear" type="button" :disabled="checkingAccess" @click="clearSessionAccess">清除本次密钥</button>
          <button v-if="accessVerified" class="access-action" type="button" :disabled="checkingAccess" @click="closeAccessSettings">返回页面</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { verifySystemAccessResult } from '~/utils/systemAccess'

const { setApiKey, getApiInfo, onAccessRequired } = useApi()
const publicDemoSetting = useRuntimeConfig().public.publicDemo
// 不使用 Boolean(value)：环境配置中的字符串 "false" 不应开启公开模式。
const publicDemo = String(publicDemoSetting) === 'true'
const pageMounted = ref(publicDemo)
const accessVerified = ref(false)
const checkingAccess = ref(false)
const needsAccessKey = ref(false)
const dialogVisible = ref(false)
const candidateKey = ref('')
const accessError = ref('')
const keyInput = ref<HTMLInputElement | null>(null)
let removeAccessListener: (() => void) | undefined

const openAccessSettings = async () => {
  if (publicDemo) return
  candidateKey.value = ''
  dialogVisible.value = true
  await nextTick()
  keyInput.value?.focus()
}
const closeAccessSettings = () => {
  candidateKey.value = ''
  if (accessVerified.value) dialogVisible.value = false
}
const applyProbeResult = (result: Parameters<typeof verifySystemAccessResult>[0], validatedKey?: string) => {
  const verified = verifySystemAccessResult(result)
  accessVerified.value = verified.accepted
  needsAccessKey.value = verified.needsKey
  accessError.value = verified.error
  if (verified.accepted) {
    // 先提交已验证的密钥，再允许任何页面的初始请求运行。
    if (validatedKey !== undefined) setApiKey(validatedKey)
    pageMounted.value = true
    dialogVisible.value = false
  } else dialogVisible.value = true
  // 后续鉴权/网络失败不卸载已经打开的页面，不丢弃用户的表单输入。
  return verified.accepted
}
const checkCurrentAccess = async () => {
  if (publicDemo || checkingAccess.value) return
  checkingAccess.value = true
  accessError.value = ''
  try { applyProbeResult(await getApiInfo()) }
  catch { applyProbeResult({ success: false, error: '访问检查失败，请检查系统连接后重试。' }) }
  finally { checkingAccess.value = false }
}
const verifyCandidateKey = async () => {
  if (publicDemo || checkingAccess.value) return
  const key = candidateKey.value.trim()
  if (!key) { accessError.value = '请填写访问密钥；本地无需密钥时可点击“重新检查连接”。'; return }
  checkingAccess.value = true
  accessError.value = ''
  try {
    const result = await getApiInfo(key)
    applyProbeResult(result, key)
  } catch { applyProbeResult({ success: false, error: '访问检查失败，请检查系统连接后重试。' }) }
  finally { candidateKey.value = ''; checkingAccess.value = false }
}
const clearSessionAccess = async () => {
  if (publicDemo || checkingAccess.value) return
  setApiKey('')
  candidateKey.value = ''
  accessVerified.value = false
  await checkCurrentAccess()
}

onMounted(() => {
  if (publicDemo) return
  removeAccessListener = onAccessRequired(() => {
    accessVerified.value = false
    needsAccessKey.value = true
    accessError.value = '当前请求未通过访问验证。请填写有效密钥；失败的操作不会自动重新提交。'
    candidateKey.value = ''
    dialogVisible.value = true
  })
  checkCurrentAccess()
})
onUnmounted(() => { removeAccessListener?.() })
</script>

<style scoped>
.public-demo-note { position: static; margin: 0; padding: 12px 24px; background: #f5f8fc; border-top: 1px solid #e2eaf4; color: #73869e; font-size: 11px; line-height: 1.7; text-align: center; }
.access-bootstrap { min-height: 100vh; display: grid; place-items: center; background: #f5f8fc; padding: 40px; }
.access-bootstrap-card { width: min(560px, 100%); padding: 46px; background: #fff; border: 1px solid #dfe8f4; border-radius: 18px; box-shadow: 0 16px 45px #18375b0c; }
.access-eyebrow { color: #3682d5; font-size: 11px; font-weight: 700; letter-spacing: .13em; }
.access-bootstrap h1 { margin: 18px 0 12px; color: #1c3555; font-size: 27px; }
.access-bootstrap p { margin-bottom: 24px; font-size: 14px; color: #63768d; line-height: 1.8; }
.access-settings-trigger { position: fixed; right: 20px; bottom: 18px; z-index: 1900; display: flex; gap: 8px; align-items: center; padding: 9px 13px; border: 1px solid #d8e5f3; border-radius: 20px; background: #ffffffed; color: #436183; font-size: 12px; box-shadow: 0 3px 14px #1938570b; cursor: pointer; }
.access-status-dot { width: 6px; height: 6px; border-radius: 50%; background: #d1a45a; }
.access-status-dot.verified { background: #31a58b; }
.access-description { margin: 0 0 16px; color: #68788d; line-height: 1.75; font-size: 13px; }
.access-current-state { background: #f1f7fd; border: 1px solid #e0ecf8; border-radius: 8px; padding: 10px 12px; color: #2c609c; font-size: 13px; }
.access-form { margin-top: 20px; }
.access-form label { display: block; margin-bottom: 8px; color: #253b58; font-size: 13px; font-weight: 600; }
.access-form input { box-sizing: border-box; width: 100%; border: 1px solid #d7e1ec; border-radius: 8px; padding: 11px 12px; color: #24415f; background: #fff; font: inherit; }
.access-form input:focus { outline: 2px solid #b6d9ff; border-color: #3784d8; }
.access-memory-note { margin: 9px 0 18px; color: #8190a4; line-height: 1.7; font-size: 11px; }
.access-error { color: #b94d4d; font-size: 12px; line-height: 1.7; }
.access-form-actions, .access-dialog-footer { display: flex; align-items: center; gap: 10px; }
.access-dialog-footer { justify-content: space-between; }
.access-action { border: 1px solid #d4e0ed; border-radius: 8px; padding: 10px 14px; background: #fff; color: #466482; cursor: pointer; font-size: 12px; }
.access-action.primary { color: #fff; background: #287fd5; border-color: #287fd5; }
.access-action:disabled, .access-clear:disabled { cursor: wait; opacity: .65; }
.access-clear { padding: 5px 0; border: 0; background: none; color: #73869e; font-size: 12px; cursor: pointer; }
</style>
