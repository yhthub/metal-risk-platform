<template>
  <div class="research-system-home">
    <header :class="['system-nav', { 'nav-scrolled': isScrolled }]">
      <div class="nav-wrapper">
        <div class="nav-left">
          <div class="logo-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span class="logo-text" :title="PRODUCT_NAME">{{ PRODUCT_SHORT_NAME }}</span><span class="logo-text-mobile" :title="PRODUCT_NAME">AI Intervention</span>
        </div>
        
        <nav class="nav-menu" aria-label="主要功能">
          <div class="nav-item">
            <NuxtLink to="/datainput">数据接入</NuxtLink>
            <div class="dropdown">
              <NuxtLink to="/datainput">单人录入与群体导入</NuxtLink>
              <NuxtLink to="/data-cleaning">数据清洗与格式转换</NuxtLink>
            </div>
          </div>
          <div class="nav-item">
            <NuxtLink to="/risk?mode=individual">风险分析</NuxtLink>
            <div class="dropdown">
              <NuxtLink to="/risk?mode=individual">单人风险分析</NuxtLink>
              <NuxtLink to="/risk?mode=batch">群体风险分析</NuxtLink>
            </div>
          </div>
          <div class="nav-item">
            <NuxtLink to="/plan">方案推荐</NuxtLink>
          </div>
          <div class="nav-item">
            <NuxtLink to="/agent">知识服务</NuxtLink>
            <div class="dropdown">
              <NuxtLink to="/agent">医学知识问答</NuxtLink>
              <NuxtLink to="/causal">因果知识推理</NuxtLink>
            </div>
          </div>
        </nav>
        
        <div class="nav-right">
          <a class="btn-outline" href="#experience-guide">体验指南</a>
          <button class="btn-primary" @click="goToWorkspace">进入工作台</button>
        </div>
      </div>
    </header>

    <div class="data-space-bg">
      <div class="particle p-pb">Pb</div>
      <div class="particle p-hg">Hg</div>
      <div class="particle p-cr">Cr</div>
      <div class="particle p-cd">Cd</div>
      <div class="particle p-as">As</div>
      <div class="particle p-ni">Ni</div>
      <div class="particle p-zn">Zn</div>
      <div class="particle p-cu">Cu</div>
      <div class="particle p-mn">Mn</div>
      <div class="particle p-v">V</div>
    </div>

    <main class="content-wrapper">
      <section class="hero-section animate-on-scroll">
        <h1 class="title" :aria-label="PRODUCT_NAME">
          <span class="title-dark">面向职业金属复合暴露的</span><br />
          <span class="title-blue">智能干预推荐与决策支持系统</span>
        </h1>
        <p class="subtitle">
          连接数据接入、风险分析、医学知识与干预方案，让职业金属暴露相关信息更易理解。<br/>从单人指标到群体数据，探索有依据的健康管理与决策支持。
        </p>
        <div class="core-mission-badge">
          <el-icon><Monitor /></el-icon>
          构建“暴露—生物标志物—疾病—干预”全链条智能决策体系
        </div>
      </section>

      <div class="system-loop-declaration animate-on-scroll">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        数据接入 — 数据分析 — 风险分析 — 方案推荐
      </div>

      <div class="particle-wave-container animate-on-scroll">
        <svg class="data-wave" viewBox="0 0 1000 150" preserveAspectRatio="none">
          <circle 
            v-for="(dot, index) in waveDots" 
            :key="index" 
            :cx="dot.x" 
            :cy="dot.y" 
            :r="dot.r" 
            class="wave-dot"
            :style="{ animationDelay: `${dot.delay}s` }"
          />
        </svg>
      </div>

      <section id="capabilities" ref="capabilities" class="showcase-list" aria-label="功能概览">
        <article v-for="feature in features" :key="feature.id" class="showcase-card animate-on-scroll"
          :data-feature="feature.id" :aria-labelledby="'feature-' + feature.id">
          <div class="text-content">
            <h2 :id="'feature-' + feature.id">{{ feature.title }}</h2>
            <p>{{ feature.description }}</p>
          </div>
          <HomeFeaturePreview :kind="feature.id" />
        </article>
      </section>

      <section id="experience-guide" ref="experienceGuide" class="experience-guide" data-workflow-art aria-labelledby="experience-guide-title">
        <div class="guide-heading"><span>快速开始</span><h2 id="experience-guide-title">选择适合你的体验方式</h2></div>
        <div class="guide-options">
          <NuxtLink to="/datainput" class="guide-card guide-analysis">
            <img class="guide-art" :src="exposureIllustration" alt="" width="300" height="200" loading="lazy" decoding="async">
            <strong>01 · 体验数据分析</strong>
            <span>载入公开案例，查看单人或群体的数据与分析结果。</span>
            <b>进入数据接入 →</b>
          </NuxtLink>
          <NuxtLink to="/data-cleaning" class="guide-card guide-cleaning">
            <img class="guide-art" :src="cleaningIllustration" alt="" width="300" height="200" loading="lazy" decoding="async">
            <strong>02 · 整理一份表格</strong>
            <span>用合成案例体验清洗预览，并下载规范 CSV 文件。</span>
            <b>体验数据清洗 →</b>
          </NuxtLink>
          <NuxtLink to="/agent" class="guide-card guide-medicine">
            <img class="guide-art" :src="evidenceIllustration" alt="" width="300" height="200" loading="lazy" decoding="async">
            <strong>03 · 查询医学知识</strong>
            <span>直接提出问题，阅读回答及其引用的资料。</span>
            <b>开始知识问答 →</b>
          </NuxtLink>
        </div>
        <p id="experience-note" class="guide-note">公开体验请使用公开或合成示例。分析与方案仅供研究参考，不能替代专业诊疗。</p>
      </section>
    </main>

    <footer class="system-footer">
      <div class="footer-wrapper">
        <div class="footer-content">
          <div class="footer-brand">
            <div class="footer-logo">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              {{ PRODUCT_SHORT_NAME }}
            </div>
            <p class="brand-slogan">负责任地构建健康数据网络，为职业环境筑起科学防线。</p>
          </div>
          
          <div class="footer-links-grid">
            <div class="link-column">
              <h4>数据准备</h4>
              <NuxtLink to="/datainput">数据接入</NuxtLink>
              <NuxtLink to="/data-cleaning">数据清洗与格式转换</NuxtLink>
            </div>
            <div class="link-column">
              <h4>分析与方案</h4>
              <NuxtLink to="/risk?mode=individual">单人风险分析</NuxtLink>
              <NuxtLink to="/risk?mode=batch">群体风险分析</NuxtLink>
              <NuxtLink to="/plan">方案推荐</NuxtLink>
            </div>
            <div class="link-column">
              <h4>知识服务</h4>
              <NuxtLink to="/causal">因果知识推理</NuxtLink>
              <NuxtLink to="/agent">医学知识问答</NuxtLink>
            </div>
            <div class="link-column">
              <h4>使用帮助</h4>
              <a href="#capabilities">功能概览</a>
              <a href="#experience-guide">体验指南</a>
              <a href="#experience-note">使用说明</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <div class="bottom-legal">
            <span>&copy; 2026 Occupational Health AI System. All rights reserved.</span>
            <div class="legal-links">
              <a href="#experience-note">体验与数据说明</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import { PRODUCT_NAME, PRODUCT_SHORT_NAME } from '~/utils/product'
import exposureIllustration from '~/assets/illustrations/workflow/exposure-analysis.svg?no-inline'
import cleaningIllustration from '~/assets/illustrations/workflow/table-cleaning.svg?no-inline'
import evidenceIllustration from '~/assets/illustrations/workflow/medical-evidence.svg?no-inline'

useHead({ title: PRODUCT_NAME })

const isScrolled = ref(false)
const waveDots = ref([])
const experienceGuide = ref(null)
const capabilities = ref(null)
const features = [
  { id: 'risk', title: '从单人到群体的风险分析', description: '录入个人信息或导入群体数据，查看健康指标估计、群体分布和相对排序。结合输入质量与结果说明，理解不同对象的指标特征。' },
  { id: 'cleaning', title: '清晰的数据整理与模型解释', description: '通过字段映射、清洗预览和格式转换整理原始表格。分析完成后，可查看各项输入对模型估计值的贡献，以及改变输入时的模型响应。' },
  { id: 'knowledge', title: '医学知识问答与干预方案推荐', description: '围绕职业暴露与健康提出问题，查看回答及相关研究。进入方案推荐后，可按预防层级查阅岗位防护措施、随访安排和方案报告。' },
]

// ✨ 跳转到数据录入控制台
const goToWorkspace = async () => {
  await navigateTo('/datainput')
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

const generateWaveDots = () => {
  const dots = []
  for (let i = 0; i < 180; i++) {
    dots.push({ x: i * (1000/180), y: 75 + Math.sin(i * 0.08) * 35, r: 1.8, delay: (i * 0.015).toFixed(2) })
  }
  waveDots.value = dots
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  generateWaveDots()
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible')
        observer.unobserve(entry.target) 
      }
    })
  }, { threshold: 0.15, rootMargin: '0px 0px -20px 0px' })
  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el))
  const section = { '#experience-guide': experienceGuide, '#capabilities': capabilities }[window.location.hash]
  if (section) {
    requestAnimationFrame(() => section.value?.scrollIntoView({ block: 'start', behavior: 'instant' }))
  }
})

onUnmounted(() => window.removeEventListener('scroll', handleScroll))
</script>

<style lang="scss" scoped>
@use "sass:color"; /* ✨ 解决 Sass 弃用警告 */

$color-primary: #1f77b4;
$color-bg: #F9FAFB;
$text-main: #1F2937;
$color-text-muted: #6B7280;
$color-border: #E5E7EB;

.research-system-home {
  min-height: 100vh;
  background-color: $color-bg;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow-x: hidden; position: relative;
  -webkit-font-smoothing: antialiased;
}

/* ==========================================
   顶部导航
   ========================================== */
.system-nav {
  position: fixed; top: 0; left: 0;
  width: 100%; height: 72px;
  background: #ffffff; border-bottom: 1px solid rgba(0,0,0,0.05);
  z-index: 100; transition: all 0.3s ease; display: flex; justify-content: center;
  &.nav-scrolled { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(8px); }
  
  .nav-wrapper {
    width: 100%;
    max-width: 1200px; padding: 0 24px;
    display: flex; justify-content: space-between; align-items: center; height: 100%;
  }

  .nav-left { 
    display: flex; align-items: center; gap: 12px; 
    color: $text-main;
    .logo-mark {
      width: 28px; height: 28px; color: $color-primary; display: flex; align-items: center;
    }
    .logo-text { font-weight: 700; font-size: 1.15rem; }
  }
  
  .nav-menu {
    display: flex; gap: 32px; height: 100%;
    .nav-item {
      position: relative; display: flex; align-items: center; height: 100%;
      > a {
        color: $color-text-muted; text-decoration: none; 
        font-size: 1.05rem; font-weight: 600;
        transition: color 0.2s;
        &:hover, &.active { color: $color-primary; }
      }

      .dropdown {
        position: absolute;
        top: 100%; left: 50%;
        transform: translateX(-50%) translateY(15px);
        background: #ffffff; border: 1px solid rgba(0,0,0,0.05);
        border-radius: 12px;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.1);
        padding: 8px 0; min-width: 170px; opacity: 0; visibility: hidden;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); display: flex; flex-direction: column; z-index: 200;
        &::before {
          content: ''; position: absolute; top: -6px; left: 50%;
          transform: translateX(-50%) rotate(45deg);
          width: 12px; height: 12px; background: #ffffff;
          border-left: 1px solid rgba(0,0,0,0.05); border-top: 1px solid rgba(0,0,0,0.05);
        }
        a {
          color: $text-main;
          padding: 12px 24px; font-size: 0.95rem; text-decoration: none; 
          font-weight: 500; transition: all 0.2s; &:hover { color: $color-primary; background: #F9FAFB; }
        }
      }
      &:hover .dropdown, &:focus-within .dropdown { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
    }
  }
  
  .nav-right {
    display: flex; gap: 12px;
    button, a.btn-outline { height: 36px; padding: 0 18px; border-radius: 6px; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; font-weight: 600; display: inline-flex; align-items: center; text-decoration: none; }
    .btn-outline { background: transparent; border: 1px solid $color-border; color: $text-main; &:hover { border-color: $color-text-muted; } }
    .btn-primary { 
      background: $color-primary; border: none; color: white; 
      &:hover { background: color.adjust($color-primary, $lightness: -5%); } /* ✨ 替换为现代语法 */
    }
  }
}

/* ==========================================
   背景：复合动效
   ========================================== */
.data-space-bg {
  position: fixed; top: 0; left: 0;
  width: 100vw; height: 100vh; pointer-events: none; z-index: 0;
  .particle { position: absolute; font-weight: 900; opacity: 0.12; user-select: none;
  will-change: transform, opacity; animation: floatComplex 12s ease-in-out infinite alternate; }
  .p-pb { top: 12%; left: 15%; font-size: 4rem; color: #d62728; }
  .p-hg { top: 45%; left: 22%; font-size: 5rem; color: #9467bd; animation-delay: -2s; }
  .p-cr { top: 82%; left: 12%; font-size: 3.5rem; color: #1f77b4; animation-delay: -4s; }
  .p-cd { top: 18%; right: 20%; font-size: 4.8rem; color: #ff7f0e; animation-delay: -1s; }
  .p-as { top: 72%; right: 24%; font-size: 3.8rem; color: #8c564b; animation-delay: -3s; }
  .p-ni { top: 10%; right: 40%; font-size: 3.2rem; color: #2ca02c; animation-delay: -5s; }
  .p-zn { top: 60%; left: 8%; font-size: 4.5rem; color: #7f7f7f; animation-delay: -1.5s; }
  .p-cu { top: 55%; right: 12%; font-size: 4.2rem; color: #bcbd22; }
  .p-mn { top: 30%; left: 45%; font-size: 3rem; color: #17becf; }
  .p-v { top: 85%; right: 45%; font-size: 4rem; color: #e377c2; }
}

@keyframes floatComplex {
  0% { transform: translateY(0) translateX(0) rotate(-5deg) scale(1); opacity: 0.08; }
  50% { transform: translateY(-40px) translateX(20px) rotate(10deg) scale(1.1); opacity: 0.18; }
  100% { transform: translateY(20px) translateX(-15px) rotate(-10deg) scale(0.95); opacity: 0.1; }
}

.content-wrapper { position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 140px 24px 100px; }

.animate-on-scroll { opacity: 0; transform: translateY(40px); transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  &.is-visible { opacity: 1; transform: translateY(0); } }

.hero-section {
  display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 60px; margin-top: 40px;
  .title { font-size: 4rem; font-weight: 800; line-height: 1.3; margin-bottom: 24px; letter-spacing: 2px; .title-dark { color: #2B2F36; } .title-blue { color: #1f77b4; } }
  .subtitle { font-size: 1.2rem; color: #5f6368; max-width: 850px; margin: 0 auto 36px; line-height: 1.8; }
  .core-mission-badge { display: inline-flex; align-items: center; gap: 8px; background: #f0f7ff; border: 1px solid #cce3ff; color: #1f77b4; padding: 12px 30px; border-radius: 30px; font-size: 1.05rem; font-weight: 500; }
}

.system-loop-declaration { display: flex; justify-content: center; align-items: center; gap: 8px; font-size: 0.95rem; color: $color-text-muted; margin-bottom: 40px; padding-bottom: 40px; border-bottom: 1px solid $color-border; svg { width: 18px; height: 18px; opacity: 0.8;} }

.particle-wave-container { width: 100%; height: 160px; margin-bottom: 80px; display: flex; justify-content: center; 
  .data-wave { width: 90%; height: 100%; display: block !important; max-height: none !important; max-width: none !important;} /* ✨ 防止被 Tailwind 压缩 */
  .wave-dot { fill: #60A5FA; opacity: 0.6; animation: wavePulse 2s ease-in-out infinite alternate; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); } 
}
@keyframes wavePulse { 0% { transform: translateY(0); opacity: 0.3; } 100% { transform: translateY(-15px); opacity: 1; } }

.showcase-list { display:grid; gap:clamp(56px,7vw,100px); }
.showcase-card { display:grid; grid-template-columns:minmax(0,1.22fr) minmax(0,1fr); grid-template-areas:"preview copy"; align-items:center; gap:clamp(34px,5vw,76px); }
.showcase-card > [data-feature-preview] { grid-area:preview; }
.text-content { grid-area:copy; min-width:0; }
.text-content h2 { margin:0 0 14px; color:$text-main; font-size:clamp(1.55rem,2.4vw,2rem); font-weight:700; line-height:1.35; letter-spacing:-.025em; text-wrap:balance; }
.text-content p { margin:0; color:$color-text-muted; font-size:clamp(1rem,1.3vw,1.12rem); line-height:1.8; }

.system-footer { background: #FFFFFF; border-top: 1px solid rgba(0,0,0,0.05); padding: 80px 0 30px; margin-top: 80px; position: relative; z-index: 10; display: flex; justify-content: center; }
.footer-wrapper { width: 100%; max-width: 1200px; padding: 0 24px; }
.footer-content { display: flex; gap: 80px; margin-bottom: 60px; }
.footer-brand { flex: 1; .footer-logo { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 700; color: $text-main; margin-bottom: 16px; svg { width: 26px; height: 26px; color: #1f77b4; } } .brand-slogan { font-size: 1rem; color: $color-text-muted; line-height: 1.6; max-width: 320px; } }
.footer-links-grid { flex: 2; display: flex; justify-content: space-between; gap: 20px; .link-column { display: flex; flex-direction: column; gap: 14px; h4 { font-size: 1rem; font-weight: 600; color: $text-main; margin-bottom: 8px; } a { font-size: 0.95rem; color: $color-text-muted; text-decoration: none; transition: color 0.2s; } a:hover { color: #1f77b4; } } }
.footer-bottom { padding-top: 30px; border-top: 1px solid rgba(0,0,0,0.05); .bottom-legal { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: $color-text-muted; .legal-links { display: flex; gap: 24px; a { color: $color-text-muted; text-decoration: none; transition: color 0.2s; &:hover{ color: #1f77b4; } } } } }

@media (max-width: 992px) {
  .showcase-card { grid-template-columns:minmax(0,1fr); grid-template-areas:"copy" "preview"; gap:18px; max-width:680px; width:100%; margin:auto; }
  .system-nav .nav-menu { display: none; }
  .hero-section .title { font-size: 2.5rem; }
  .footer-content { flex-direction: column; gap: 40px; }
  .footer-links-grid { flex-wrap: wrap; gap: 40px; .link-column { min-width: 140px; } }
  .footer-bottom .bottom-legal { flex-direction: column; gap: 16px; align-items: flex-start; }
}

.logo-text-mobile { display: none; }
#capabilities, #experience-guide, #experience-note { scroll-margin-top: 96px; }
.experience-guide { position: relative; margin: 56px 0 64px; padding: 32px; border: 1px solid #dfe9f2; border-radius: 18px; background: #ffffffed; }
.guide-heading { margin-bottom: 22px; > span { font-size: 12px; color: #1f77b4; font-weight: 700; } h2 { margin: 7px 0 0; font-size: 23px; color: #243b53; } }
.guide-options { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.guide-card {
  --guide-ink: #245e87;
  --guide-paper: #eef5fa;
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 8px;
  overflow: hidden;
  min-width: 0;
  background: #fff;
  border: 1px solid #dce6ed;
  border-radius: 12px;
  text-decoration: none;

  &.guide-cleaning { --guide-ink: #27645a; --guide-paper: #edf5f1; }
  &.guide-medicine { --guide-ink: #514c81; --guide-paper: #f3f2f8; }
  &:hover, &:focus-visible { border-color: var(--guide-ink); }
  &:hover b, &:focus-visible b { text-decoration: underline; text-underline-offset: 3px; }
  .guide-art {
    display: block;
    width: 100%;
    height: clamp(122px, 12vw, 157px);
    object-fit: contain;
    background: var(--guide-paper);
  }
  strong, span, b { margin-inline: 18px; }
  strong { margin-top: 6px; font-size: 16px; line-height: 1.5; color: #243b53; }
  span { font-size: 13px; line-height: 1.75; color: #526476; }
  b { margin-block: 4px 17px; font-size: 13px; line-height: 1.6; color: var(--guide-ink); font-weight: 650; }
}
.guide-note { color: #708196; font-size: 12px; line-height: 1.8; margin: 20px 0 0; }
.research-system-home a:focus-visible, .research-system-home button:focus-visible { outline: 2px solid #4295d6; outline-offset: 4px; }
@media (max-width: 720px) {
  .experience-guide { padding: 22px 16px; margin: 32px 0; }
  .guide-heading h2 { font-size: 19px; line-height: 1.6; }
  .guide-options { grid-template-columns: 1fr; gap: 12px; }
  .guide-card {
    grid-template-columns: minmax(0, 1fr) clamp(76px, 26vw, 150px);
    grid-template-rows: auto 1fr auto;
    gap: 5px 0;
    .guide-art { grid-column: 2; grid-row: 1 / 4; align-self: stretch; height: 100%; min-height: 0; }
    strong, span, b { grid-column: 1; margin-inline: 14px 10px; }
    strong { margin-top: 13px; font-size: 15px; }
    b { margin-block: 3px 12px; }
  }
}
@media screen and (max-width: 1200px) {
  .system-nav .nav-menu { gap: 16px; }
  .system-nav .nav-left .logo-text { font-size: .95rem; }
  .system-nav .nav-right button { padding: 0 12px; }
}
@media screen and (max-width: 992px) {
  .showcase-card > * { min-width: 0; width: 100%; box-sizing: border-box; }
  .footer-brand, .footer-links-grid { min-width: 0; }
  .system-nav .nav-wrapper { gap: 16px; }
}
@media screen and (max-width: 600px) {
  .system-nav { height: calc(64px + env(safe-area-inset-top)); padding-top: env(safe-area-inset-top); box-sizing: border-box; }
  .system-nav .nav-wrapper { padding: 0 16px; gap: 10px; }
  .system-nav .nav-left { min-width: 0; gap: 8px; }
  .system-nav .nav-left .logo-text { display: none; }
  .logo-text-mobile { display: inline; font-weight: 750; font-size: 14px; }
  .system-nav .nav-left .logo-mark { flex-shrink: 0; width: 23px; height: 23px; }
  .system-nav .nav-right .btn-outline { display: none; }
  .system-nav .nav-right button { font-size: 12px; height: 38px; padding: 0 12px; white-space: nowrap; }
  .content-wrapper { padding: 104px 18px 48px; }
  .hero-section { margin: 12px 0 28px; }
  .hero-section .title { font-size: clamp(25px,6.6vw,36px); letter-spacing: 0; line-height: 1.55; margin: 0 0 20px; overflow-wrap: anywhere; }
  .hero-section .subtitle { font-size: 14px; margin-bottom: 22px; line-height: 1.9; }
  .hero-section .subtitle br { display: none; }
  .hero-section .core-mission-badge { font-size: 12px; line-height: 1.8; padding: 10px 14px; border-radius: 14px; }
  .core-mission-badge .el-icon { flex-shrink: 0; }
  .system-loop-declaration { font-size: 12px; line-height: 1.8; padding-bottom: 24px; margin-bottom: 12px; }
  .system-loop-declaration svg { flex-shrink: 0; }
  .particle-wave-container { height: 80px; margin-bottom: 32px; }
  .showcase-list { gap: 50px; }
  .showcase-card { gap: 24px; text-align: left; }
  .text-content { padding: 0 4px; }
  .text-content h2 { font-size: 22px; line-height: 1.45; margin-bottom: 8px; }
  .text-content p { font-size: 14px; line-height: 1.9; }
  .system-footer { padding: 36px 0 24px; margin-top: 20px; }
  .footer-wrapper { padding: 0 20px; }
  .footer-content { gap: 30px; margin-bottom: 30px; }
  .footer-brand .footer-logo { font-size: 14px; line-height: 1.5; }
  .footer-brand .footer-logo svg { flex-shrink: 0; }
  .footer-brand .brand-slogan { font-size: 13px; }
  .footer-links-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 28px 16px; }
  .footer-links-grid .link-column { min-width: 0; gap: 10px; }
  .footer-links-grid .link-column h4 { font-size: 14px; }
  .footer-links-grid .link-column a { font-size: 12px; }
  .footer-bottom .bottom-legal { font-size: 11px; line-height: 1.8; }
  .footer-bottom .bottom-legal .legal-links { flex-wrap: wrap; gap: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .animate-on-scroll { opacity: 1; transform: none; transition: none; }
  .particle, .wave-dot { animation: none !important; }
}
</style>
