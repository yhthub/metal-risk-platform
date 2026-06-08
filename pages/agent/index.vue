<template>
  <div class="system-layout">
    
    <transition name="toast-fade">
      <div v-if="toast.visible" class="custom-toast">
        <el-icon class="toast-icon"><Select /></el-icon>
        <span>{{ toast.message }}</span>
      </div>
    </transition>

  <Sidebar default-active="6" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToHome">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">首页</span>
            <span class="divider">|</span>
            <span class="page-title-top">智能知识问答与决策溯源助手 (RAG Agent)</span>
          </div>
          <div class="ep-right-zone">
            <div class="user-profile">
              <div class="avatar">Dr.</div>
              <span>职业卫生评估员</span>
            </div>
          </div>
        </div>
      </header>

      <div class="page-container chat-page-container">
        
        <div class="model-selector-top-left">
          <el-select v-model="currentModel" size="default" style="width: 240px;" @change="handleModelChange">
            <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </div>

        <div class="agent-hero-section" v-if="!hasStartedChat">
          <div class="hero-title">
            职业环境健康的难题，交给我试试看吧 ~ 🤗
          </div>
          
          <div class="ai-group-badge">
            <img src="https://api.iconify.design/lucide:bot.svg?color=%231f77b4" alt="bot" />
            <span>{{ currentKBDisplay }} 已挂载</span>
          </div>

          <div class="hero-input-wrapper" :class="{ 'is-focused': inputFocused }">
            <el-popover placement="bottom-start" :width="320" trigger="click" :visible="showKBPopover">
              <template #reference>
                <div class="kb-selector-btn" @click="showKBPopover = !showKBPopover">
                  <el-icon><FolderOpened /></el-icon>
                  <span class="truncate-text">{{ currentKBDisplay }}</span>
                  <el-icon><ArrowDown /></el-icon>
                </div>
              </template>
              <div class="kb-popover-list">
                <div v-for="(kb, idx) in kbList" :key="idx"
                     :class="['kb-item', { 'active': selectedKBs.includes(kb) }]"
                     @click="toggleKB(kb)">
                  <el-checkbox :model-value="selectedKBs.includes(kb)" @click.stop @change="toggleKB(kb)" />
                  <span>{{ kb }}</span>
                </div>
                <div class="kb-divider"></div>
                <div class="kb-item"><el-icon><Upload /></el-icon> 上传本地私有知识库 (.pdf/.md)</div>
              </div>
            </el-popover>

            <textarea 
              class="hero-textarea" 
              placeholder="请输入重金属名称（如：铅、镉）、机制或疾病进行查询，或要求生成风险预警报告..."
              v-model="userInput"
              @focus="inputFocused = true"
              @blur="inputFocused = false"
              @keydown.enter.prevent="sendMessage"
            ></textarea>

            <div class="hero-input-actions">
              <div class="actions-left">
                <el-button circle class="action-btn"><el-icon><Paperclip /></el-icon></el-button>
                <el-button round class="action-btn" :class="{'is-active': enableDeepThink}" @click="toggleDeepThink">
                  <el-icon><MagicStick /></el-icon> 深度思考 {{ enableDeepThink ? 'ON' : '' }}
                </el-button>
                <el-button round class="action-btn"><el-icon><ChromeFilled /></el-icon> 联网检索</el-button>
              </div>
              <div class="actions-right">
                <span class="agent-tag"><el-icon><Connection /></el-icon> RAG Agent</span>
                <el-button type="primary" circle class="send-btn" :disabled="!userInput.trim()" @click="sendMessage">
                  <el-icon><Position /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <div class="quick-prompts">
            <div class="prompt-chip" @click="quickSend('详细解析一下铅(Pb)的致病机制与靶器官')">
              <el-icon><Microphone /></el-icon> 解析铅(Pb)的致病机制
            </div>
            <div class="prompt-chip" @click="quickSend('重金属暴露导致的慢性肾病(CKD)有哪些前兆标志物？')">
              <el-icon><DataAnalysis /></el-icon> 重金属与慢性肾病关系
            </div>
            <div class="prompt-chip" @click="quickSend('对比砷(As)和镉(Cd)的暴露来源与致癌性差异')">
              <el-icon><ScaleToOriginal /></el-icon> 对比砷(As)和镉(Cd)
            </div>
          </div>
        </div>

        <div class="chat-thread-section" v-else>
          <div class="message-list" ref="messageListRef">
            <div v-for="(msg, index) in chatHistory" :key="index" :class="['message-wrapper', msg.role]">
              
              <div v-if="msg.role === 'user'" class="message user-message">
                <div class="msg-content">{{ msg.content }}</div>
                <div class="msg-avatar">User</div>
              </div>
              
              <div v-if="msg.role === 'ai'" class="message ai-message">
                <div class="msg-avatar ai-avatar"><el-icon><Monitor /></el-icon></div>
                <div class="msg-body">
                  
                  <div class="deep-think-box" v-if="msg.thinkProcess">
                    <div class="think-header" @click="msg.thinkExpanded = !msg.thinkExpanded">
                      <div class="think-title">
                        <el-icon class="spin-icon" v-if="msg.loading"><Loading /></el-icon>
                        <el-icon v-else><CircleCheck /></el-icon>
                        {{ msg.loading ? `正在从 ${currentKB} 检索与思考...` : `深度思考完成 (耗时 1.8s)` }}
                      </div>
                      <el-icon class="arrow-icon" :class="{'is-open': msg.thinkExpanded}"><ArrowDown /></el-icon>
                    </div>
                    <div class="think-content" v-show="msg.thinkExpanded" v-html="msg.thinkProcess"></div>
                  </div>

                  <div class="kb-citation" v-if="msg.cited && !msg.loading">
                    <el-icon><Reading /></el-icon> 已结合检索源: <strong>{{ currentKBText }}</strong>
                  </div>

                  <div v-if="!msg.loading" class="msg-content markdown-body" v-html="msg.content"></div>

                  <div class="msg-actions" v-if="!msg.loading">
                    <div class="action-item" title="复制回答" @click="showToast('✅ 内容已复制到剪贴板')"><el-icon><DocumentCopy /></el-icon></div>
                    <div class="action-item" title="重新生成"><el-icon><RefreshRight /></el-icon></div>
                    <div class="action-item" title="赞"><el-icon><Pointer /></el-icon></div>
                    <div class="action-item" title="踩"><el-icon><Bottom /></el-icon></div>
                  </div>

                </div>
              </div>
            </div>
          </div>

          <div class="sticky-input-container">
            <div class="hero-input-wrapper is-chatting">
              <textarea 
                class="hero-textarea" 
                placeholder="继续提问，或输入 / 唤起工具..."
                v-model="userInput"
                @keydown.enter.prevent="sendMessage"
              ></textarea>
              <div class="hero-input-actions">
                <div class="actions-left">
                  <el-button circle class="action-btn"><el-icon><Paperclip /></el-icon></el-button>
                  <el-popover placement="top-start" :width="320" trigger="hover">
                    <template #reference>
                      <el-button round class="action-btn kb-mini-btn">
                        <el-icon><FolderOpened /></el-icon> <span class="truncate-text ax-w-25">{{ currentKBDisplay }}</span>
                      </el-button>
                    </template>
                    <div class="kb-popover-list mini">
                      <div v-for="(kb, idx) in kbList" :key="idx"
                           :class="['kb-item', { 'active': selectedKBs.includes(kb) }]"
                           @click="toggleKB(kb)">
                        <el-checkbox :model-value="selectedKBs.includes(kb)" @click.stop @change="toggleKB(kb)" />
                        <span>{{ kb }}</span>
                      </div>
                    </div>
                  </el-popover>
                </div>
                <div class="actions-right">
                  <el-button type="primary" circle class="send-btn" :disabled="!userInput.trim() || isGenerating" @click="sendMessage">
                    <el-icon><Position /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Position, Paperclip, MagicStick, ChromeFilled, Connection,
  Microphone, DataAnalysis, ScaleToOriginal, FolderOpened,
  Document, Upload, Monitor, Reading, Loading, CircleCheck,
  DocumentCopy, RefreshRight, Pointer, Bottom
} from '@element-plus/icons-vue'

const router = useRouter()
const navigateTo = (path) => { router.push(path) }
const goToHome = () => { router.push('/') }

const hasStartedChat = ref(false)
const inputFocused = ref(false)
const userInput = ref('')
const isGenerating = ref(false)
const messageListRef = ref(null)
const enableDeepThink = ref(true)

const toast = ref({ visible: false, message: '' })
const showToast = (msg) => {
  toast.value.message = msg
  toast.value.visible = true
  setTimeout(() => { toast.value.visible = false }, 2500)
}

const currentModel = ref('XGBoost')
const modelOptions = [
  'XGBoost', 'DNN', 'LightGBM', 'G-computation', 'BKMR',
  'Random Forest', 'CatBoost', 'Elastic Net', 'Cox-PH', 'Weibull-AFT',
  'Bayesian Network', 'GAM', 'SHAP-Integrated MLP', 'QG-Comp', 'TMLE',
  'DeepSurv', 'AFT-NN', 'BKMR-CS', 'SuperLearner', 'Causal Forest'
]
const handleModelChange = (cmd) => {
  showToast(`已切换至：${cmd}`)
}

const showKBPopover = ref(false)
const kbList = [
  '职业重金属复合暴露因果库',
  'IARC 致癌物风险评级报告',
  'WHO 化学品安全与毒理库 (IPCS)',
  'ToxNet 毒理学数据网络',
  'NHANES 营养与健康调查库',
  'CTD 比较毒理基因组学数据库',
  'EPA/ATSDR 毒物学概况库',
  '职业病临床诊疗指南 (2025版)',
  'PubMed 职业流行病学文献库'
]
const selectedKBs = ref([kbList[0], kbList[1]])

const toggleKB = (kb) => {
  const idx = selectedKBs.value.indexOf(kb)
  if (idx >= 0) {
    if (selectedKBs.value.length <= 1) { showToast('至少需要挂载一个知识库'); return }
    selectedKBs.value.splice(idx, 1)
  } else {
    selectedKBs.value.push(kb)
  }
}

const currentKBDisplay = computed(() => {
  if (selectedKBs.value.length === kbList.length) return '全部知识库'
  if (selectedKBs.value.length === 1) return selectedKBs.value[0]
  return `已选 ${selectedKBs.value.length} 个知识库`
})

const currentKBText = computed(() => selectedKBs.value.map(k => `《${k}》`).join('、'))

const toggleDeepThink = () => {
  enableDeepThink.value = !enableDeepThink.value
  showToast(enableDeepThink.value ? '已开启 R1 深度思考模式' : '已关闭深度思考')
}

const chatHistory = ref([])

const mockKnowledgeBase = {
  '铅': {
    name: '铅 (Pb)',
    source: '冶炼、废旧电池、含铅管道、含铅涂料、烟草烟雾等',
    mechanism: 'Pb²⁺可替代Ca²⁺干扰细胞信号通路，诱导<strong>氧化应激</strong>和<strong>表观遗传变化</strong>；与硫醇(-SH)结合损伤蛋白质。',
    disease: '神经系统(认知发育迟缓、共济失调)、肾脏损伤(慢性肾病)、高血压、血液(贫血)',
    biomarker: '血铅浓度、δ-氨基酯酶(ALAD)活性↓、ROS生成↑、尿β₂-微球蛋白↑',
    evidence: '高（系统综述与队列研究证实低剂量可致血压升高和肾功能下降，IARC 2A类致癌）'
  },
  '砷': {
    name: '砷 (As)',
    source: '地下水污染、农用化学品、工业废气、含砷农产品',
    mechanism: '在肝脏中甲基化代谢产生有毒形式，产生<strong>氧化应激</strong>、抑制DNA修复并改变DNA甲基化。',
    disease: '皮肤(色素异常、皮肤癌)、肺(肺癌)、膀胱(膀胱癌)、心血管(动脉硬化)',
    biomarker: '尿总砷及其代谢物(MMA/DMA)、血砷、DNA甲基化变化',
    evidence: '高（无机砷为IARC 1类致癌物，慢性低剂量暴露可导致皮肤损伤、癌症）'
  },
  '镉': {
    name: '镉 (Cd)',
    source: '烟草烟雾、电镀/电池工业废气、矿山和冶炼尘埃',
    mechanism: '镉在肝脏结合金属硫蛋白(MT)后累积于肾脏，长期释放产生<strong>氧化应激</strong>、线粒体损伤和DNA损伤。',
    disease: '肾小管(蛋白尿、慢性肾功能衰竭)、骨骼(骨质疏松、“痛痛病”)、呼吸(肺纤维化)',
    biomarker: '尿镉、血镉、肾功能指标(肌酐、尿蛋白)、骨密度',
    evidence: '高（IARC 1类致肺癌，广泛流行病学证据表明慢性暴露显著损伤肾脏和骨骼）'
  },
  '汞': {
    name: '汞 (Hg)',
    source: '海产品甲基汞、工业矿井和燃烧排放、水银采矿',
    mechanism: 'Hg⁰/MeHg与硫醇(-SH)强烈结合，跨越血脑屏障导致<strong>神经毒性</strong>和<strong>氧化应激</strong>。',
    disease: '中枢神经系统(神经发育损伤、感觉障碍)；肾脏(蛋白尿)、免疫系统',
    biomarker: '血/尿总汞和有机汞浓度、神经行为测试',
    evidence: '中（孕期甲基汞神经发育毒性证据充分；高剂量致肾癌）'
  }
}

const quickSend = (text) => {
  userInput.value = text
  sendMessage()
}

// ✨ 修复：增大延迟确保内容撑开高度后再滚动
const scrollToBottom = () => {
  nextTick(() => {
    setTimeout(() => {
      if (messageListRef.value) {
        messageListRef.value.scrollTo({ top: messageListRef.value.scrollHeight, behavior: 'smooth' })
      }
    }, 100) 
  })
}

const generateThinkingProcess = (query) => {
  return `
    <div style="color: #64748B; font-size: 0.9rem; line-height: 1.6;">
      <p>> 正在解析用户意图：意图识别为对 "${query.substring(0, 10)}..." 的机制/评估请求...</p>
      <p>> 正在调用 <strong>${currentModel.value}</strong> 推理模型...</p>
      <p>> 正在通过 RAG 向量引擎检索 <strong>${currentKBText.value}</strong> ...</p>
      <p>> 提取关键三元组：[暴露源] -> [病理机制] -> [靶器官疾病]</p>
      <p>> 融合知识图谱完毕，准备生成最终推演报告。</p>
    </div>
  `
}

const getRecommendedKBs = (query) => {
  const rules = [
    { keywords: ['铅', 'Pb', '铅中毒', '驱铅', 'EDTA'], kbs: ['职业重金属复合暴露因果库', '职业病临床诊疗指南 (2025版)', 'EPA/ATSDR 毒物学概况库'], reason: '铅暴露因果机制与临床驱铅方案' },
    { keywords: ['砷', 'As', '砷中毒', '皮肤癌'], kbs: ['IARC 致癌物风险评级报告', 'CTD 比较毒理基因组学数据库', 'PubMed 职业流行病学文献库'], reason: '砷致癌性评估与基因组毒理学' },
    { keywords: ['镉', 'Cd', '肾病', '骨质疏松', '痛痛病'], kbs: ['WHO 化学品安全与毒理库 (IPCS)', 'NHANES 营养与健康调查库', 'ToxNet 毒理学数据网络'], reason: '镉的肾毒性与骨骼损伤机制' },
    { keywords: ['汞', 'Hg', '甲基汞', '神经毒性'], kbs: ['ToxNet 毒理学数据网络', 'WHO 化学品安全与毒理库 (IPCS)', 'PubMed 职业流行病学文献库'], reason: '汞的神经毒理学与甲基汞代谢' },
    { keywords: ['癌症', '致癌', '肿瘤', 'IARC'], kbs: ['IARC 致癌物风险评级报告', 'CTD 比较毒理基因组学数据库', 'PubMed 职业流行病学文献库'], reason: '致癌物分级与流行病学证据' },
    { keywords: ['肾', '肾脏', 'CKD', '肾衰竭', '蛋白尿'], kbs: ['NHANES 营养与健康调查库', '职业病临床诊疗指南 (2025版)', 'EPA/ATSDR 毒物学概况库'], reason: '慢性肾病的营养流行病学与临床管理' },
    { keywords: ['神经', '认知', '脑', '帕金森', '阿尔茨海默'], kbs: ['PubMed 职业流行病学文献库', '职业重金属复合暴露因果库', 'IARC 致癌物风险评级报告'], reason: '神经退行性病变的职业暴露流行病学' },
    { keywords: ['干预', '治疗', '防护', '方案', '策略'], kbs: ['职业病临床诊疗指南 (2025版)', 'EPA/ATSDR 毒物学概况库', '职业重金属复合暴露因果库'], reason: '临床干预方案与毒物防护指南' },
    { keywords: ['暴露', '监测', '生物标志', '筛查'], kbs: ['NHANES 营养与健康调查库', 'ToxNet 毒理学数据网络', 'CTD 比较毒理基因组学数据库'], reason: '暴露生物标志物与健康监测数据' }
  ]

  const matched = rules.find(r => r.keywords.some(k => query.includes(k) || query.toLowerCase().includes(k.toLowerCase())))
  if (matched) {
    const recommended = matched.kbs.filter(kb => !selectedKBs.value.includes(kb))
    if (recommended.length > 0) return { kbs: recommended, reason: matched.reason }
  }

  const fallback = kbList.filter(kb => !selectedKBs.value.includes(kb)).slice(0, 2)
  return fallback.length > 0 ? { kbs: fallback, reason: '扩展检索以补充更多维度的毒理学证据' } : null
}

const buildRecommendedHTML = (query) => {
  const rec = getRecommendedKBs(query)
  if (!rec) return ''
  return `
    <div class="kb-recommend">
      <div class="kb-rec-title">📚 推荐追加知识库 <span class="kb-rec-reason">${rec.reason}</span></div>
      <div class="kb-rec-tags">${rec.kbs.map(kb => `<span class="kb-rec-tag">${kb}</span>`).join('')}</div>
    </div>
  `
}

const retrieveKnowledge = (query) => {
  let matchedMetal = null
  for (let key in mockKnowledgeBase) {
    if (query.includes(key) || query.toLowerCase().includes(mockKnowledgeBase[key].name.split(' ')[1].toLowerCase())) {
      matchedMetal = mockKnowledgeBase[key]
      break
    }
  }

  const recommendedHTML = buildRecommendedHTML(query)

  if (matchedMetal) {
    return `
      <p>为您从 ${currentKBText.value} 中提取到关于 <span class="highlight-blue">${matchedMetal.name}</span> 的因果分析图谱结构化数据：</p>
      <div class="kb-card">
        <div class="kb-row"><span class="kb-label">📍 核心暴露来源</span> <span class="kb-val">${matchedMetal.source}</span></div>
        <div class="kb-row"><span class="kb-label">🧬 关键分子机制</span> <span class="kb-val">${matchedMetal.mechanism}</span></div>
        <div class="kb-row"><span class="kb-label">🩸 关键生物标志物</span> <span class="kb-val">${matchedMetal.biomarker}</span></div>
        <div class="kb-row"><span class="kb-label">🏥 主要靶器官/疾病</span> <span class="kb-val text-red-600 font-bold">${matchedMetal.disease}</span></div>
        <div class="kb-row"><span class="kb-label">⚖️ 循证证据等级</span> <span class="kb-val text-emerald-600 font-bold">${matchedMetal.evidence}</span></div>
      </div>
      <p style="margin-top: 10px;"><strong>💡 智能干预建议：</strong>建议在图谱沙盘中将 ${matchedMetal.name.split(' ')[1]} 的环境特征参数下调 30%，即可在因果图神经网络中观察其对 <em>氧化应激</em> 与 <em>靶器官</em> 风险的涟漪阻断效应。</p>
      ${recommendedHTML}
    `
  } else {
    return `
      <p>在当前已挂载的知识库中未匹配到单一重金属特征。系统目前已挂载 <strong>铅(Pb)、砷(As)、镉(Cd)、汞(Hg)</strong> 等常见金属的毒理机制库。</p>
      <p>您可以尝试修改提问：<br/>
      👉 "深度解析一下镉(Cd)的靶器官衰竭路径是什么？"<br/>
      👉 "重金属诱导的氧化应激会导致哪些慢性疾病？"
      </p>
      ${recommendedHTML}
    `
  }
}

const sendMessage = () => {
  if (!userInput.value.trim() || isGenerating.value) return

  const query = userInput.value
  hasStartedChat.value = true
  
  chatHistory.value.push({ role: 'user', content: query })
  userInput.value = ''
  scrollToBottom()

  isGenerating.value = true
  const aiMessageIndex = chatHistory.value.push({ 
    role: 'ai', 
    content: '', 
    loading: true, 
    cited: true,
    thinkProcess: enableDeepThink.value ? generateThinkingProcess(query) : null,
    thinkExpanded: enableDeepThink.value 
  }) - 1
  scrollToBottom()

  setTimeout(() => {
    chatHistory.value[aiMessageIndex].loading = false
    chatHistory.value[aiMessageIndex].thinkExpanded = false 
    chatHistory.value[aiMessageIndex].content = retrieveKnowledge(query)
    isGenerating.value = false
    scrollToBottom()
  }, 2000) 
}
</script>

<style lang="scss" scoped>
$c-primary: #1f77b4;
$c-primary-light: #EFF6FF;
$bg-main: #F8FAFC;
$text-dark: #111827;
$text-muted: #6B7280;
$border-light: #E2E8F0;

* { box-sizing: border-box; }

.system-layout { display: flex; height: 100vh; background-color: $bg-main; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }

.custom-toast {
  position: fixed; top: 24px; left: 50%; transform: translateX(-50%); z-index: 9999;
  background: rgba(31, 41, 55, 0.9); backdrop-filter: blur(10px); color: #fff;
  padding: 12px 24px; border-radius: 30px; font-size: 0.95rem; font-weight: 600;
  display: flex; align-items: center; gap: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  .toast-icon { color: #10B981; font-size: 1.2rem; }
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translate(-50%, -20px); }

/* 侧边栏与顶栏 */
.sidebar { width: 280px; background-color: #fff; border-right: 1px solid $border-light; display: flex; flex-direction: column; z-index: 10; flex-shrink: 0; box-shadow: 2px 0 15px rgba(0,0,0,0.03); }
.brand-logo { 
  height: 70px; display: flex; align-items: center; gap: 14px; padding: 0 24px; border-bottom: 1px solid $border-light; 
  svg { width: 30px; height: 30px; color: #2563EB; flex-shrink: 0; } 
  .brand-text { display: flex; flex-direction: column; } 
  .title-en { font-size: 1.1rem; font-weight: 900; color: #111827; letter-spacing: -0.5px;} 
  .title-cn { font-size: 0.8rem; font-weight: 600; color: #64748B; letter-spacing: 1px; margin-top: 2px;} 
}
.menu-container { overflow-y: auto; flex: 1; padding: 16px 0; :deep(.custom-el-menu) { border-right: none; .menu-group-title { font-size: 0.85rem; font-weight: 800; color: #94A3B8; padding: 24px 24px 10px 24px; letter-spacing: 1px;} .el-menu-item { font-weight: 600; color: #475569; font-size: 1.05rem; margin: 6px 12px; border-radius: 8px; height: 50px; } .el-menu-item:hover { background-color: #F8FAFC; color: $c-primary; } .el-menu-item.is-active { background-color: $c-primary-light; color: $c-primary; font-weight: 700;} } }

.main-content { flex: 1; display: flex; flex-direction: column; background: $bg-main; }
.ep-header { height: 64px; background: rgba(255,255,255,0.9); backdrop-filter: blur(8px); border-bottom: 1px solid $border-light; display: flex; justify-content: center; flex-shrink: 0; z-index: 40;}
.nav-wrapper { width: 100%; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; height: 100%; }
.back-link { display: flex; align-items: center; gap: 12px; cursor: pointer; color: $text-dark; &:hover { color: $c-primary; } .back-text { font-size: 1.05rem; font-weight: 700;} .divider { color: #D1D5DB; margin: 0 8px; } .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-dark; } }
.user-profile { display: flex; align-items: center; gap: 12px; font-weight: 600; color: $text-dark; font-size: 0.95rem; .avatar { width: 32px; height: 32px; border-radius: 50%; background: $c-primary-light; color: $c-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 0.9rem;} }

/* 页面区容器 */
.chat-page-container {
  flex: 1; display: flex; flex-direction: column; align-items: center; padding: 0; max-width: 100%; overflow: hidden;
  position: relative; 
}

/* 左上角大模型选择器 */
.model-selector-top-left {
  position: absolute; top: 24px; left: 32px; z-index: 20;
}

/* 初始欢迎态 */
.agent-hero-section {
  width: 100%; max-width: 850px; margin: auto; padding: 40px 20px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  animation: fadeIn 0.6s ease-out; position: relative;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

.hero-title {
  font-size: 2rem; font-weight: 800; color: #1F2937; margin-bottom: 40px; letter-spacing: 0.5px;
}
.ai-group-badge {
  position: absolute; right: 0; top: 0; transform: rotate(5deg) translateY(-20px);
  background: linear-gradient(135deg, #1f77b4, #0369a1); color: #fff;
  padding: 8px 16px; border-radius: 12px; font-size: 0.8rem; font-weight: 700;
  display: flex; align-items: center; gap: 8px; box-shadow: 0 10px 25px rgba(31,119,180,0.3);
  img { width: 16px; height: 16px; filter: brightness(0) invert(1);}
}

/* 下拉列表 */
.kb-popover-list {
  display: flex; flex-direction: column; gap: 4px; max-height: 350px; overflow-y: auto;
  &.mini { max-height: 250px; }
  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb { background-color: #E5E7EB; border-radius: 4px; }
  .kb-item { 
    padding: 10px 12px; font-size: 0.9rem; color: #4B5563; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-weight: 500;
    &:hover { background: #F3F4F6; color: #111827; }
    &.active { background: #EFF6FF; color: #1f77b4; font-weight: 700; }
  }
  .kb-divider { height: 1px; background: #E5E7EB; margin: 4px 0; }
}

.hero-input-wrapper {
  width: 100%; background: #fff; border: 1px solid #E5E7EB; border-radius: 16px;
  padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); transition: all 0.3s ease;
  position: relative;
  &.is-focused { border-color: #93C5FD; box-shadow: 0 8px 30px rgba(59,130,246,0.12); }
  
  .kb-selector-btn {
    display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; max-width: 250px;
    background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
    font-size: 0.85rem; font-weight: 600; color: #475569; cursor: pointer; transition: 0.2s;
    margin-bottom: 12px;
    &:hover { background: #EFF6FF; color: #1f77b4; border-color: #BFDBFE; }
  }

  .truncate-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .hero-textarea {
    width: 100%; min-height: 80px; border: none; outline: none; resize: none;
    font-size: 1.05rem; line-height: 1.6; color: #1F2937; background: transparent;
    &::placeholder { color: #9CA3AF; }
  }

  .hero-input-actions {
    display: flex; justify-content: space-between; align-items: center; margin-top: 10px;
    .actions-left { display: flex; gap: 8px; }
    .action-btn { 
      border: none; background: #F3F4F6; color: #4B5563; font-weight: 600; font-size: 0.85rem; padding: 8px 16px; transition: 0.2s;
      &:hover { background: #E5E7EB; color: #1F2937; }
      &.is-active { background: #EFF6FF; color: #1f77b4; border: 1px solid #BFDBFE; }
      &.kb-mini-btn { padding: 8px 12px; }
    }
    .actions-right {
      display: flex; align-items: center; gap: 16px;
      .agent-tag { font-size: 0.85rem; font-weight: 700; color: #1f77b4; display: flex; align-items: center; gap: 4px;}
      .send-btn { background: #1f77b4; border: none; font-size: 1.2rem; width: 44px; height: 44px; transition: 0.3s; &:disabled{ background: #9CA3AF; cursor: not-allowed; opacity: 0.5;} }
    }
  }

  &.is-chatting {
    border-radius: 24px; padding: 12px 20px; box-shadow: 0 -10px 30px rgba(0,0,0,0.05);
    .hero-textarea { min-height: 50px; font-size: 1rem; }
    .hero-input-actions { margin-top: 4px; }
  }
}

.quick-prompts {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-top: 30px;
  .prompt-chip {
    padding: 10px 16px; background: #fff; border: 1px solid #E5E7EB; border-radius: 20px;
    font-size: 0.9rem; font-weight: 500; color: #4B5563; cursor: pointer; transition: 0.2s;
    display: flex; align-items: center; gap: 6px;
    &:hover { border-color: #1f77b4; color: #1f77b4; background: #EFF6FF; transform: translateY(-2px);}
  }
}

/* 对话流态 */
.chat-thread-section {
  width: 100%; height: 100%; display: flex; flex-direction: column; position: relative;
}

.message-list {
  flex: 1; width: 100%; max-width: 900px; margin: 0 auto; 
  /* ✨ 核心修复：加大底部的 padding-bottom 到 220px，保证能完整露出操作图标 */
  padding: 60px 20px 220px 20px; 
  overflow-y: auto; display: flex; flex-direction: column; gap: 30px; scroll-behavior: smooth;
  &::-webkit-scrollbar { width: 0; }
}

.message-wrapper {
  display: flex; flex-direction: column; max-width: 85%;
  &.user { align-self: flex-end; align-items: flex-end; }
  &.ai { align-self: flex-start; align-items: flex-start; }
}

.message {
  display: flex; gap: 16px;
  &.user-message {
    flex-direction: row-reverse;
    .msg-content { background: #1f77b4; color: #fff; border-radius: 16px 16px 0 16px; padding: 14px 20px; font-size: 1rem; line-height: 1.5; box-shadow: 0 4px 15px rgba(31,119,180,0.2);}
    .msg-avatar { background: #E5E7EB; color: #4B5563; width: 36px; height: 36px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 0.8rem; flex-shrink: 0;}
  }
  
  &.ai-message {
    .msg-avatar { background: #1f77b4; color: #fff; width: 36px; height: 36px; border-radius: 8px; display: flex; justify-content: center; align-items: center; font-size: 1.2rem; flex-shrink: 0;}
    .msg-body { display: flex; flex-direction: column; gap: 10px; width: 100%;}
    
    .deep-think-box {
      background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; max-width: 600px;
      .think-header { 
        padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; color: #64748B; font-size: 0.9rem; font-weight: 600;
        &:hover { background: #F1F5F9; }
        .think-title { display: flex; align-items: center; gap: 6px; }
        .spin-icon { animation: spin 2s linear infinite; }
        .arrow-icon { transition: transform 0.3s; &.is-open { transform: rotate(180deg); } }
      }
      .think-content { padding: 0 14px 14px 14px; border-top: 1px solid #E2E8F0; margin-top: 4px; padding-top: 10px; }
    }

    .kb-citation { display: inline-flex; align-items: center; gap: 6px; background: #F0FDF4; border: 1px solid #BBF7D0; color: #059669; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; width: fit-content;}
    
    .msg-content { background: #fff; border: 1px solid #E5E7EB; color: #1F2937; border-radius: 0 16px 16px 16px; padding: 20px; font-size: 1rem; line-height: 1.7; box-shadow: 0 4px 15px rgba(0,0,0,0.03);}
    
    /* 操作图标悬浮栏 */
    .msg-actions { 
      display: flex; gap: 10px; opacity: 0.5; transition: opacity 0.2s; margin-top: -4px;
      .action-item { cursor: pointer; padding: 6px; border-radius: 6px; color: #64748B; font-size: 1.1rem; display: flex; align-items: center; justify-content: center; transition: 0.2s; &:hover { background: #E5E7EB; color: #111827; } }
    }
    &:hover .msg-actions { opacity: 1; }
  }
}
@keyframes spin { 100% { transform: rotate(360deg); } }

:deep(.kb-card) {
  background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin: 12px 0;
  .kb-row { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #E2E8F0; &:last-child { border: none; margin-bottom: 0; padding-bottom: 0;} }
  .kb-label { font-weight: 800; color: #475569; font-size: 0.9rem;}
  .kb-val { color: #1F2937; font-size: 0.95rem; line-height: 1.5;}
  .highlight-blue { color: #1f77b4; font-weight: 800; }
}

/* 推荐知识库 */
:deep(.kb-recommend) {
  margin-top: 16px; padding: 14px 16px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px;
  .kb-rec-title { font-size: 0.9rem; font-weight: 700; color: #1E40AF; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
    .kb-rec-reason { font-size: 0.8rem; font-weight: 500; color: #64748B; }
  }
  .kb-rec-tags { display: flex; flex-wrap: wrap; gap: 8px; }
  .kb-rec-tag { display: inline-flex; align-items: center; padding: 5px 12px; background: #fff; border: 1px solid #93C5FD; border-radius: 6px; font-size: 0.82rem; font-weight: 600; color: #1D4ED8; cursor: pointer; transition: all 0.2s;
    &:hover { background: #1D4ED8; color: #fff; border-color: #1D4ED8; }
  }
}

.typing-indicator {
  display: flex; gap: 6px; padding: 10px 16px; background: #fff; border: 1px solid #E5E7EB; border-radius: 0 16px 16px 16px; width: fit-content;
  span { width: 8px; height: 8px; background: #9CA3AF; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
  span:nth-child(1) { animation-delay: -0.32s; }
  span:nth-child(2) { animation-delay: -0.16s; }
}
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.sticky-input-container {
  position: absolute; bottom: 0; left: 0; width: 100%; padding: 20px 0 30px;
  background: linear-gradient(to top, #F8FAFC 80%, transparent);
  display: flex; justify-content: center; z-index: 30;
  .hero-input-wrapper { width: 100%; max-width: 850px; }
}
</style>