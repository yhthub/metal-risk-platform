<template>
  <div v-if="isMobile" class="mobile-navigation-bar">
    <button ref="mobileTrigger" type="button" class="navigation-toggle" aria-label="打开导航菜单"
      :aria-expanded="mobileOpen" :aria-controls="navigationId" @click="openMobile">
      <el-icon><Menu /></el-icon>
    </button>
    <NuxtLink to="/" class="mobile-brand" :title="PRODUCT_NAME">AI Intervention <span>{{ PRODUCT_SHORT_NAME }}</span></NuxtLink>
  </div>
  <div v-if="isMobile && mobileOpen" class="navigation-backdrop" aria-hidden="true" @click="closeMobile()" />
  <aside :id="navigationId" ref="sidebarElement" class="sidebar" :class="{ 'is-collapsed': compact, 'is-mobile': isMobile, 'is-open': mobileOpen }"
    :role="isMobile ? 'dialog' : 'complementary'" :aria-modal="isMobile && mobileOpen ? true : undefined"
    :aria-hidden="isMobile && !mobileOpen ? true : undefined" :inert="isMobile && !mobileOpen"
    aria-label="系统导航" tabindex="-1">
    <div class="brand-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
      <div class="brand-text" :title="PRODUCT_NAME">
        <span class="title-en">AI Intervention</span>
        <span class="title-cn">{{ PRODUCT_SHORT_NAME }}</span>
      </div>
      <button ref="collapseTrigger" type="button" class="navigation-toggle sidebar-toggle"
        :aria-label="isMobile ? '关闭导航菜单' : compact ? '展开侧边栏' : '收起侧边栏'"
        :title="isMobile ? '关闭导航菜单' : compact ? '展开侧边栏' : '收起侧边栏'"
        :aria-expanded="isMobile ? mobileOpen : !compact" :aria-controls="navigationId"
        @click="isMobile ? closeMobile() : toggleDesktop()">
        <el-icon><Close v-if="isMobile" /><Expand v-else-if="compact" /><Fold v-else /></el-icon>
      </button>
    </div>

    <div class="menu-container">
      <el-menu :default-active="defaultActive" class="custom-el-menu" :unique-opened="true" :collapse="compact" :collapse-transition="false">
        <div v-if="!compact" class="menu-group-title">数据管理</div>
        <el-sub-menu index="1" aria-label="数据接入">
          <template #title><el-icon><Coin /></el-icon><span>数据接入</span></template>
          <el-menu-item index="1-1" @click="goTo('/datainput')">单人录入与群体导入</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="2" aria-label="数据整理">
          <template #title><el-icon><DataLine /></el-icon><span>数据整理</span></template>
          <el-menu-item index="2-1" @click="goTo('/data-cleaning')">数据清洗与格式转换</el-menu-item>
        </el-sub-menu>

        <div v-if="!compact" class="menu-group-title">分析与干预</div>
        <el-sub-menu index="3" aria-label="风险分析">
          <template #title><el-icon><TrendCharts /></el-icon><span>风险分析</span></template>
          <el-menu-item index="3-1" @click="goTo('/risk?mode=individual')">单人风险分析</el-menu-item>
          <el-menu-item index="3-2" @click="goTo('/risk?mode=batch')">群体风险分析</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="4" aria-label="因果知识推理" @click="goTo('/causal')">
          <el-icon><Share /></el-icon><span>因果知识推理</span>
        </el-menu-item>
        
        <el-menu-item index="5" aria-label="方案推荐" @click="goTo('/plan')">
          <el-icon><DocumentChecked /></el-icon><span>方案推荐</span>
        </el-menu-item>
        
        <div v-if="!compact" class="menu-group-title">知识服务</div>
        <el-menu-item index="6" aria-label="医学知识问答" @click="goTo('/agent')">
          <el-icon><ChatDotRound /></el-icon><span>医学知识问答</span>
        </el-menu-item>
      </el-menu>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onDeactivated, onMounted, onUnmounted, ref, useId, watch } from 'vue'
import { PRODUCT_NAME, PRODUCT_SHORT_NAME } from '~/utils/product'
import { 
  Coin, DataLine, TrendCharts, Share, DocumentChecked, ChatDotRound, Menu, Close, Fold, Expand
} from '@element-plus/icons-vue'

// 定义 props 接收父组件（各个页面）传来的激活项 index
defineProps({
  defaultActive: {
    type: String,
    required: true,
    default: '1-1'
  }
})

const router = useRouter()
const navigationId = `system-navigation-${useId()}`
const collapsed = useState<boolean>('navigation:collapsed', () => false)
const isMobile = ref(import.meta.client && window.matchMedia('(max-width: 1024px)').matches)
const mobileOpen = ref(false)
const compact = computed(() => !isMobile.value && collapsed.value)
const sidebarElement = ref<HTMLElement | null>(null)
const mobileTrigger = ref<HTMLButtonElement | null>(null)
const collapseTrigger = ref<HTMLButtonElement | null>(null)
let media: MediaQueryList | undefined
let active = false
let inertContent: HTMLElement | null = null
let previouslyInert = false

const restoreContent = () => {
  if (inertContent) inertContent.inert = previouslyInert
  inertContent = null
}
const closeMobile = (restoreFocus = true) => {
  mobileOpen.value = false
  restoreContent()
  if (restoreFocus) nextTick(() => mobileTrigger.value?.focus())
}
const openMobile = async () => {
  mobileOpen.value = true
  await nextTick()
  inertContent = sidebarElement.value?.closest('.system-layout')?.querySelector<HTMLElement>('.main-content') ?? null
  if (inertContent) { previouslyInert = inertContent.inert; inertContent.inert = true }
  collapseTrigger.value?.focus()
}
const toggleDesktop = () => { collapsed.value = !collapsed.value }
watch(collapsed, async (value) => {
  if (!active) return
  try { localStorage.setItem('zhiwei-sidebar-collapsed', String(value)) } catch { /* Preferences are optional. */ }
  await nextTick()
  // Existing chart pages resize on this event after the layout has changed.
  requestAnimationFrame(() => window.dispatchEvent(new Event('resize')))
})
const syncViewport = () => {
  isMobile.value = media?.matches ?? false
  closeMobile(false)
}
const handleKey = (event: KeyboardEvent) => {
  if (!mobileOpen.value) return
  if (event.key === 'Escape') { event.preventDefault(); closeMobile(); return }
  if (event.key !== 'Tab') return
  const items = Array.from(sidebarElement.value?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], [tabindex="0"]') ?? [])
    .filter(el => el.getClientRects().length && !el.closest('[aria-hidden="true"]'))
  const first = items[0], last = items[items.length - 1]
  if (!first) { event.preventDefault(); sidebarElement.value?.focus(); return }
  if (event.shiftKey && (document.activeElement === first || !sidebarElement.value?.contains(document.activeElement))) {
    event.preventDefault(); last?.focus()
  } else if (!event.shiftKey && (document.activeElement === last || !sidebarElement.value?.contains(document.activeElement))) {
    event.preventDefault(); first.focus()
  }
}
const activate = () => {
  if (active) return
  active = true
  try { collapsed.value = localStorage.getItem('zhiwei-sidebar-collapsed') === 'true' } catch { /* Keep session preference. */ }
  media = window.matchMedia('(max-width: 1024px)')
  syncViewport()
  media.addEventListener('change', syncViewport)
  document.addEventListener('keydown', handleKey)
}
const deactivate = () => {
  active = false
  closeMobile(false)
  media?.removeEventListener('change', syncViewport)
  document.removeEventListener('keydown', handleKey)
}
onMounted(activate)
onActivated(activate)
onDeactivated(deactivate)
onUnmounted(deactivate)

// 统一的路由跳转方法（避免与 Nuxt 自动导入的 navigateTo 冲突）
const goTo = async (path: string) => {
  closeMobile(false)
  await router.push(path)
  await nextTick()
  if (isMobile.value) document.querySelector<HTMLButtonElement>('.mobile-navigation-bar .navigation-toggle')?.focus()
}
</script>

<style lang="scss" scoped>
/* 侧边栏专属局部变量，保证独立组件色彩精确 */
$c-primary: #1f77b4;
$c-primary-light: #EFF6FF;
$border-light: #E2E8F0;

* { box-sizing: border-box; }

.sidebar { 
  width: 280px; 
  background-color: #fff; 
  border-right: 1px solid $border-light; 
  display: flex; 
  flex-direction: column; 
  z-index: 10; 
  flex-shrink: 0; 
  box-shadow: 2px 0 15px rgba(0,0,0,0.03); 
  height: 100%; /* 占满父容器高度 */
}

.brand-logo { 
  height: 70px; 
  display: flex; 
  align-items: center; 
  gap: 14px; 
  padding: 0 24px; 
  border-bottom: 1px solid $border-light; 
  svg { 
    width: 30px; 
    height: 30px; 
    color: #2563EB; 
    flex-shrink: 0; 
  } 
  .brand-text { 
    display: flex; 
    flex-direction: column; 
  } 
  .title-en { 
    font-size: 1.1rem; 
    font-weight: 900; 
    color: #111827; 
    letter-spacing: -0.5px;
  } 
  .title-cn { 
    font-size: 0.8rem; 
    font-weight: 600; 
    color: #64748B; 
    letter-spacing: 1px; 
    margin-top: 2px;
  } 
}

.menu-container { 
  overflow-y: auto; 
  flex: 1; 
  padding: 16px 0; 
  
  /* 隐藏滚动条让视觉更干净 */
  &::-webkit-scrollbar { width: 0; }
  
  :deep(.custom-el-menu) { 
    border-right: none; 
    
    .menu-group-title { 
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 0.78rem;
      font-weight: 650;
      color: #5b7084;
      padding: 22px 24px 8px;
      &::after { content: ''; flex: 1; height: 1px; background: #dce5ed; }
    } 
    
    .el-menu-item { 
      font-weight: 600; 
      color: #475569; 
      font-size: 1.05rem; 
      margin: 6px 12px; 
      border-radius: 8px; 
      height: 50px; 
      transition: all 0.2s ease;
    } 
    
    .el-menu-item:hover { 
      background-color: #F8FAFC; 
      color: $c-primary; 
    } 
    
    .el-menu-item.is-active { 
      background: #e9eef9;
      color: #243f76;
      box-shadow: inset 4px 0 #3b58a1;
      font-weight: 700;
    } 
    
    /* 修复下拉菜单标题样式 */
    .el-sub-menu__title {
      font-weight: 600; 
      color: #475569; 
      font-size: 1.05rem;
      margin: 0 12px;
      border-radius: 8px;
      height: 50px;
      transition: all 0.2s ease;
      &:hover {
        background-color: #F8FAFC; 
        color: $c-primary;
      }
    }
    .el-sub-menu.is-active > .el-sub-menu__title { color: #273f71; }
  } 
}
</style>

<style scoped>
.sidebar { width: 280px !important; min-width: 0; min-height: 0; }
.sidebar .brand-logo { flex: 0 0 70px; padding: 0 14px; gap: 10px; }
.sidebar .brand-logo { background: linear-gradient(110deg, #f2f6fe, white 83%); }
.sidebar .brand-logo > svg { width: 27px; height: 27px; }
.sidebar .brand-text { min-width: 0; flex: 1; }
.sidebar .title-en { font-size: 16px; white-space: nowrap; }
.sidebar .title-cn { font-size: 11px; letter-spacing: 0; line-height: 1.5; white-space: normal; }
.navigation-toggle { width: 40px; height: 40px; padding: 0; flex-shrink: 0; display: inline-flex; justify-content: center; align-items: center; border: 1px solid #e0e8f1; border-radius: 10px; color: #4c7195; background: #fff; cursor: pointer; }
.navigation-toggle:hover { background: #eff6ff; border-color: #bed8f3; color: #2563eb; }
.navigation-toggle:focus-visible, .mobile-brand:focus-visible { outline: 2px solid #4295d6; outline-offset: 3px; }
.navigation-toggle .el-icon { font-size: 20px; }
.sidebar .menu-container { min-height: 0; overscroll-behavior: contain; }
.sidebar.is-collapsed { width: 72px !important; }
.is-collapsed .brand-logo { justify-content: center; padding: 0; }
.is-collapsed .brand-logo > svg, .is-collapsed .brand-text, .is-collapsed .menu-group-title { display: none; }
.is-collapsed :deep(.el-menu--collapse) { width: 72px; }
.is-collapsed :deep(.custom-el-menu > .el-menu-item), .is-collapsed :deep(.el-sub-menu__title) { width: 48px; margin: 6px 12px; padding: 0 12px !important; }
.is-collapsed :deep(.el-menu-tooltip__trigger) { padding: 0 12px !important; }
.is-collapsed :deep(.el-sub-menu__icon-arrow) { display: none; }
.mobile-navigation-bar { position: fixed; z-index: 1800; top: 0; left: 0; right: 0; height: calc(56px + env(safe-area-inset-top)); box-sizing: border-box; padding: env(safe-area-inset-top) 14px 0; display: flex; gap: 12px; align-items: center; background: #fffffffa; border-bottom: 1px solid #e2eaf3; }
.mobile-brand { color: #243e5b; font-size: 14px; font-weight: 750; text-decoration: none; line-height: 1.4; }
.mobile-brand span { display: block; font-size: 10px; color: #8294a8; font-weight: 500; }
.navigation-backdrop { position: fixed; inset: 0; z-index: 2100; background: #12284166; backdrop-filter: blur(2px); touch-action: none; }
@media screen and (max-width: 1024px) {
  .sidebar.is-mobile { display: flex !important; position: fixed; inset: 0 auto 0 0; z-index: 2200; width: min(300px, 86vw) !important; height: 100vh !important; height: 100dvh !important; padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom); transform: translateX(-100%); visibility: hidden; box-shadow: 10px 0 40px #10274224; }
  .sidebar.is-mobile.is-open { transform: translateX(0); visibility: visible; }
  .sidebar.is-mobile .brand-logo { padding-inline: 16px; }
  .sidebar.is-mobile .navigation-toggle { width: 44px; height: 44px; }
}
@media print { .sidebar, .mobile-navigation-bar, .navigation-backdrop { display: none !important; } }
</style>
