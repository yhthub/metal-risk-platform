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
          <span class="logo-text">Intelligent Intervention System</span>
        </div>
        
        <nav class="nav-menu">
          <div class="nav-item">
            <a href="#" class="active">评估模型</a>
            <div class="dropdown">
              <a href="#">多级风险预警</a>
              <a href="#">复合暴露测算</a>
              <a href="#">因果知识推理</a>
              <a href="#">干预策略引擎</a>
            </div>
          </div>
          <div class="nav-item">
            <a href="#">数据视图</a>
            <div class="dropdown">
              <a href="#">环境监测档案</a>
              <a href="#">流行病学流调</a>
              <a href="#">靶器官标志物</a>
              <a href="#">数据字典规范</a>
            </div>
          </div>
          <div class="nav-item">
            <a href="#">因果图谱</a>
            <div class="dropdown">
              <a href="#">系统技术白皮书</a>
              <a href="#">算法评估报告</a>
              <a href="#">干预控制规范</a>
              <a href="#">暴露限制标准</a>
            </div>
          </div>
          <div class="nav-item">
            <a href="#">系统文档</a>
            <div class="dropdown">
              <a href="#">研发团队</a>
              <a href="#">API 接口文档</a>
              <a href="#">隐私与数据安全</a>
              <a href="#">合作机构</a>
            </div>
          </div>
        </nav>
        
        <div class="nav-right">
          <button class="btn-outline">操作手册</button>
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
        <h1 class="title">
          <span class="title-dark">面向职业金属复合暴露的</span><br />
          <span class="title-blue">智能干预推荐与决策支持系统</span>
        </h1>
        <p class="subtitle">
          融合职业环境监测、流行病学调查及多组学数据，构建基于因果推理的风险评估与干预推荐模型。<br/>实现职业金属暴露健康风险的精准预警与智能决策支持。
        </p>
        <div class="core-mission-badge">
          <el-icon><Monitor /></el-icon>
          构建“暴露—生物标志物—疾病—干预”全链条智能决策体系
        </div>
      </section>

      <div class="system-loop-declaration animate-on-scroll">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        实现风险识别 — 因果解析 — 干预推荐 — 效果反馈的闭环智能决策流程
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

      <section class="capability-blocks showcase-list">
        <div class="showcase-card animate-on-scroll">
          <div class="media-container interactive-card"
               @mousemove="(e) => handleMouseMove(e, 0)"
               @mouseleave="handleMouseLeave(0)">
            <div class="mock-ui-clean float-anim">
              <div class="alert-badge pulse-red">
                <el-icon><Warning /></el-icon> Threshold Alert
              </div>
              <div class="data-row interactive-row">
                <span class="label-text">Target: <strong>Pb</strong></span>
                <span class="danger-text">1.24 μg/L &uarr;</span>
              </div>
              <div class="data-row interactive-row">
                <span class="label-text">Target: <strong>Cd</strong></span>
                <span class="warning-text">0.89 μg/L &uarr;</span>
              </div>
            </div>
          </div>
          
          <div class="text-content">
            <h4>多级风险预警与规则驱动干预</h4>
            <p>基于职业暴露限值与健康风险阈值构建分级预警机制。对 Pb、Cd 等关键污染物进行高频动态监测，当指标跨越阈值时，触发自动化、标准化的干预工单与风险响应。</p>
          </div>
        </div>

        <div class="showcase-card animate-on-scroll">
          <div class="media-container interactive-card flex-col-card"
               @mousemove="(e) => handleMouseMove(e, 1)"
               @mouseleave="handleMouseLeave(1)">
            <div class="chart-header-dark">
              <span class="chart-title">剂量-效应综合评估曲线 (Dose-Response)</span>
              <div class="chart-legend">
                <span class="legend-item"><i style="background: #3B82F6"></i> 模型预测</span>
                <span class="legend-item"><i style="background: #A855F7"></i> 观测基线</span>
              </div>
            </div>
            <div class="chart-body">
              <svg class="line-chart" viewBox="0 0 400 200" overflow="visible">
                <defs>
                  <linearGradient id="areaBlue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.15" />
                    <stop offset="100%" stop-color="#3B82F6" stop-opacity="0" />
                  </linearGradient>
                </defs>
                <line x1="40" y1="20" x2="40" y2="170" stroke="#E5E7EB" stroke-width="1.5"/>
                <line x1="40" y1="170" x2="380" y2="170" stroke="#E5E7EB" stroke-width="1.5"/>
                <path class="anim-dash" d="M40,150 Q120,130 200,90 T380,50" fill="none" stroke="#A855F7" stroke-width="3" stroke-linecap="round"/>
                <path class="anim-dash-solid" d="M40,160 Q130,160 210,70 T380,30" fill="none" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
                <path class="anim-fade-in" d="M40,170 L40,160 Q130,160 210,70 T380,30 L380,170 Z" fill="url(#areaBlue)"/>
              </svg>
            </div>
          </div>
          <div class="text-content">
            <h4>多源数据融合与健康风险评估模型</h4>
            <p>融合环境监测、个体暴露与健康档案等异构数据，构建多金属复合暴露风险评估模型。量化各因子的健康贡献度，输出高可信的非线性剂量-效应评估结果。</p>
          </div>
        </div>

        <div class="showcase-card animate-on-scroll">
          <div class="media-container interactive-card causal-grid"
               @mousemove="(e) => handleMouseMove(e, 2)"
               @mouseleave="handleMouseLeave(2)">
            <div class="causal-header">
              <span class="title">四层干预因果推断网络 (Causal Inference Graph)</span>
            </div>
            <div class="causal-layer-labels">
              <span>暴露层</span><span>分子层</span><span>疾病层</span><span>干预层</span>
            </div>
            <div class="causal-graph-area">
              <svg class="graph-edges" viewBox="0 0 100 100" preserveAspectRatio="none">
                <defs>
                  <marker id="arrowBlue" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                    <polygon points="0 0, 8 4, 0 8" fill="#3B82F6" />
                  </marker>
                </defs>
                <path d="M 12.5 30 C 25 30, 25 70, 37.5 70" stroke="#E5E7EB" stroke-width="1.5" fill="none" />
                <path d="M 37.5 70 C 50 70, 50 50, 62.5 50" stroke="#E5E7EB" stroke-width="1.5" fill="none" />
                <path d="M 12.5 70 C 25 70, 25 30, 37.5 30" stroke="#3B82F6" stroke-width="3" fill="none" class="flow-path-anim"/>
                <path d="M 37.5 30 C 50 30, 50 50, 62.5 50" stroke="#3B82F6" stroke-width="3" fill="none" class="flow-path-anim" style="animation-delay: 0.5s"/>
                <path d="M 62.5 50 L 87.5 50" stroke="#3B82F6" stroke-width="3" fill="none" marker-end="url(#arrowBlue)" class="flow-path-anim" style="animation-delay: 1s"/>
              </svg>
              <div class="mock-node-rect node-inactive" style="left: 12.5%; top: 30%;">Pb</div>
              <div class="mock-node-rect node-active" style="left: 12.5%; top: 70%;">Hg</div>
              <div class="mock-node-rect node-active" style="left: 37.5%; top: 30%;">BM-1</div>
              <div class="mock-node-rect node-inactive" style="left: 37.5%; top: 70%;">BM-2</div>
              <div class="mock-node-rect node-active" style="left: 62.5%; top: 50%;">靶器官</div>
              <div class="mock-node-rect node-action" style="left: 87.5%; top: 50%;">推荐方案</div>
            </div>
          </div>
          <div class="text-content">
            <h4>因果知识图谱驱动的智能干预推荐</h4>
            <p>基于“暴露—分子层—疾病层—干预层”构建四层因果推理结构。突破统计学相关性局限，利用图神经网络识别靶向致病路径，生成具备强可解释性的个性化医学/工程干预方案。</p>
          </div>
        </div>
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
              Intelligent Intervention System
            </div>
            <p class="brand-slogan">负责任地构建健康数据网络，为职业环境筑起科学防线。</p>
          </div>
          
          <div class="footer-links-grid">
            <div class="link-column">
              <h4>核心模型</h4>
              <a href="#">多级风险预警</a>
              <a href="#">复合暴露测算</a>
              <a href="#">因果知识推理</a>
              <a href="#">干预策略引擎</a>
            </div>
            <div class="link-column">
              <h4>多源数据</h4>
              <a href="#">环境监测档案</a>
              <a href="#">流行病学流调</a>
              <a href="#">靶器官标志物</a>
              <a href="#">数据字典规范</a>
            </div>
            <div class="link-column">
              <h4>学术研究</h4>
              <a href="#">系统技术白皮书</a>
              <a href="#">算法评估报告</a>
              <a href="#">干预控制规范</a>
              <a href="#">暴露限制标准</a>
            </div>
            <div class="link-column">
              <h4>关于系统</h4>
              <a href="#">研发团队</a>
              <a href="#">API 接口文档</a>
              <a href="#">隐私与数据安全</a>
              <a href="#">合作机构</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <div class="bottom-legal">
            <span>&copy; 2026 Occupational Health AI System. All rights reserved.</span>
            <div class="legal-links">
              <a href="#">隐私政策</a>
              <a href="#">服务条款</a>
              <a href="#">伦理声明</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router' // ✨ 引入路由
import { Warning, Monitor } from '@element-plus/icons-vue'

const router = useRouter() // ✨ 初始化路由
const isScrolled = ref(false)
const waveDots = ref([])

// ✨ 跳转到数据录入控制台
const goToWorkspace = () => {
  router.push('/datainput')
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

const handleMouseMove = (e, index) => {
  const cards = document.querySelectorAll('.interactive-card')
  if (!cards[index]) return
  const card = cards[index]
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const glowColor = 'rgba(59, 130, 246, 0.06)'
  card.style.setProperty('--mouse-x', `${x}px`)
  card.style.setProperty('--mouse-y', `${y}px`)
  card.style.setProperty('--glow-color', glowColor)
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateX = ((y - centerY) / centerY) * -2 
  const rotateY = ((x - centerX) / centerX) * 2
  card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`
}

const handleMouseLeave = (index) => {
  const cards = document.querySelectorAll('.interactive-card')
  if (cards[index]) {
    cards[index].style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)'
  }
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
      &:hover .dropdown { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
    }
  }
  
  .nav-right {
    display: flex; gap: 12px;
    button { height: 36px; padding: 0 18px; border-radius: 6px; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; font-weight: 600; }
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

.showcase-list { display: flex; flex-direction: column; gap: 120px; }
.showcase-card { display: flex; flex-direction: row; align-items: center; gap: 80px; }
.text-content { flex: 1; padding: 0 20px; h4 { font-size: 2rem; font-weight: 700; color: $text-main; margin-bottom: 20px; letter-spacing: -0.5px; line-height: 1.3; } p { font-size: 1.15rem; color: $color-text-muted; line-height: 1.8; strong { color: $text-main; font-weight: 700; } } }
.media-container { flex: 1.2; perspective: 1000px; height: 420px; display: flex; justify-content: center; align-items: center; }

.interactive-card {
  background-color: #ffffff; border-radius: 16px; padding: 30px; width: 100%; height: 100%;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08); border: 1px solid #F3F4F6;
  transition: transform 0.1s linear, box-shadow 0.2s ease-out;
  position: relative; overflow: hidden; display: flex; justify-content: center; align-items: center;
  &::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle 300px at var(--mouse-x, 50%) var(--mouse-y, 50%), var(--glow-color, rgba(255,255,255,0.1)), transparent 50%); pointer-events: none; z-index: 0; opacity: 0; transition: opacity 0.3s; }
  &:hover { box-shadow: 0 25px 40px -10px rgba(0, 0, 0, 0.12); z-index: 10; }
  &:hover::before { opacity: 1; }
  > * { position: relative; z-index: 1; }
  &.flex-col-card { display: flex; flex-direction: column; justify-content: flex-start; align-items: stretch; padding: 40px 30px; }
  &.causal-grid { display: block; }
}

.mock-ui-clean {
  background: #ffffff; padding: 35px 40px; border-radius: 20px; border: 1px solid #E5E7EB; width: 75%; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.08);
  .alert-badge { display: inline-flex; align-items: center; gap: 8px; background: #FEF2F2; color: #EF4444; border: 1px solid #FCA5A5; padding: 8px 18px; border-radius: 30px; font-size: 1.05rem; margin-bottom: 25px; font-weight: 600; }
  .pulse-red { animation: pulseRed 2s infinite; }
  .interactive-row { display: flex; justify-content: space-between; font-size: 1.15rem; padding: 14px 10px; border-bottom: 1px solid #F3F4F6; transition: all 0.3s ease; cursor: pointer; border-radius: 8px; .label-text { color: #4B5563; } &:hover { background: #F9FAFB; transform: translateX(8px); border-bottom-color: transparent; } }
  .danger-text { color: #EF4444; font-weight: 700; }
}
.float-anim { animation: floatingCard 6s ease-in-out infinite alternate; }
@keyframes floatingCard { 0% { transform: translateY(0); } 100% { transform: translateY(-15px); } }
@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.2); } 70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

.chart-header-dark { width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; color: #1F2937; font-weight: 600; font-size: 1.05rem; .chart-legend { display: flex; gap: 16px; font-size: 0.85rem; color: #6B7280; .legend-item { display: flex; align-items: center; gap: 6px; } i { width: 14px; height: 4px; border-radius: 2px; } } }
.chart-body { width: 100%; flex: 1; display: flex; align-items: center; position: relative; min-height: 180px; }
.line-chart { 
  width: 100%; height: 100%; overflow: visible; 
  display: block !important; max-height: none !important; max-width: none !important; /* ✨ 防挤压 */
}
.anim-dash { stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: drawLine 3s ease-out forwards; }
.anim-fade-in { opacity: 0; animation: fadeIn 2s ease-out forwards; animation-delay: 1.5s; }
@keyframes drawLine { to { stroke-dashoffset: 0; } }
@keyframes fadeIn { to { opacity: 1; } }

.causal-header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid rgba(0,0,0,0.05); .title { font-size: 1.1rem; font-weight: 700; color: $text-main; } }
.causal-layer-labels { display: flex; justify-content: space-between; padding: 0 5%; span { font-size: 0.85rem; color: $color-text-muted; font-weight: 500; width: 25%; text-align: center;} }
.causal-graph-area {
  position: relative; width: 100%; height: 240px; margin-top: 10px;
  .graph-edges { 
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; 
    display: block !important; max-height: none !important; max-width: none !important; /* ✨ 防挤压 */
  }
  .flow-path-anim { stroke-dasharray: 8 6; animation: pathFlow 1.5s linear infinite; }
  @keyframes pathFlow { to { stroke-dashoffset: -14; } }
  .mock-node-rect { position: absolute; transform: translate(-50%, -50%); padding: 8px 18px; border-radius: 8px; font-weight: 500; font-size: 0.95rem; background: #fff; z-index: 2; display: flex; justify-content: center; align-items: center; transition: all 0.3s ease; cursor: pointer; &:hover { transform: translate(-50%, -50%) scale(1.1); z-index: 10; } }
  .node-inactive { border: 1px solid #D1D5DB; color: #9CA3AF; }
  .node-active { border: 2px solid #3B82F6; color: #3B82F6; font-weight: 600; box-shadow: 0 4px 12px rgba(59,130,246,0.15); }
  .node-action { border: 2px solid #22C55E; color: #22C55E; font-weight: 600; border-radius: 20px; box-shadow: 0 0 20px rgba(34,197,94,0.3); animation: pulseGreen 2s infinite; }
  @keyframes pulseGreen { 0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); } 70% { box-shadow: 0 0 0 10px rgba(34,197,94,0); } 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); } }
}

.system-footer { background: #FFFFFF; border-top: 1px solid rgba(0,0,0,0.05); padding: 80px 0 30px; margin-top: 80px; position: relative; z-index: 10; display: flex; justify-content: center; }
.footer-wrapper { width: 100%; max-width: 1200px; padding: 0 24px; }
.footer-content { display: flex; gap: 80px; margin-bottom: 60px; }
.footer-brand { flex: 1; .footer-logo { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 700; color: $text-main; margin-bottom: 16px; svg { width: 26px; height: 26px; color: #1f77b4; } } .brand-slogan { font-size: 1rem; color: $color-text-muted; line-height: 1.6; max-width: 320px; } }
.footer-links-grid { flex: 2; display: flex; justify-content: space-between; gap: 20px; .link-column { display: flex; flex-direction: column; gap: 14px; h4 { font-size: 1rem; font-weight: 600; color: $text-main; margin-bottom: 8px; } a { font-size: 0.95rem; color: $color-text-muted; text-decoration: none; transition: color 0.2s; } a:hover { color: #1f77b4; } } }
.footer-bottom { padding-top: 30px; border-top: 1px solid rgba(0,0,0,0.05); .bottom-legal { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: $color-text-muted; .legal-links { display: flex; gap: 24px; a { color: $color-text-muted; text-decoration: none; transition: color 0.2s; &:hover{ color: #1f77b4; } } } } }

@media (max-width: 992px) {
  .showcase-card { flex-direction: column; gap: 40px; text-align: center; }
  .system-nav .nav-menu { display: none; }
  .hero-section .title { font-size: 2.5rem; }
  .causal-graph-interactive { transform: scale(0.8); }
  .footer-content { flex-direction: column; gap: 40px; }
  .footer-links-grid { flex-wrap: wrap; gap: 40px; .link-column { min-width: 140px; } }
  .footer-bottom .bottom-legal { flex-direction: column; gap: 16px; align-items: flex-start; }
}
</style>