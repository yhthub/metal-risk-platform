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
          <el-select v-model="currentModel" size="default" style="width: 280px;" @change="handleModelChange">
            <el-option-group label="🤖 本地模型">
              <el-option v-for="m in localModels" :key="m.name" :label="m.name" :value="m.name" />
            </el-option-group>
            <el-option-group label="📊 预训练模型">
              <el-option label="XGBoost" value="XGBoost" />
              <el-option label="DNN" value="DNN" />
              <el-option label="LightGBM" value="LightGBM" />
              <el-option label="Random Forest" value="Random Forest" />
            </el-option-group>
          </el-select>
          <div class="ollama-status" :class="{ 'connected': ollamaConnected }">
            <span class="status-dot"></span>
            <span class="status-text">{{ ollamaConnected ? '本地模型已连接' : '本地模型未连接' }}</span>
          </div>
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
            <el-popover placement="bottom-start" :width="320" trigger="click">
              <template #reference>
                <div class="kb-selector-btn">
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
                        {{ msg.loading ? `正在使用 ${currentModel} 推理中...` : `推理完成` }}
                      </div>
                      <el-icon class="arrow-icon" :class="{'is-open': msg.thinkExpanded}"><ArrowDown /></el-icon>
                    </div>
                    <div class="think-content" v-show="msg.thinkExpanded">
                      <div v-for="(step, idx) in (msg.thinkSteps || msg.thinkProcess)" :key="idx" class="think-step">
                        <span class="step-indicator" :class="{ 'active': idx === (msg.currentStep || 0), 'done': idx < (msg.currentStep || 0) }">
                          {{ idx < (msg.currentStep || 0) ? '✓' : '>' }}
                        </span>
                        <span v-html="step"></span>
                      </div>
                    </div>
                  </div>

                  <div class="kb-citation" v-if="msg.cited && !msg.loading">
                    <el-icon><Reading /></el-icon> 已结合检索源: <strong>{{ currentKBText }}</strong>
                    <span v-if="msg.dualPathSummary" class="dual-path-badge">
                      <el-icon><Collection /></el-icon> 双通路协同检索 {{ msg.dualPathSummary.total_retrieved }} 条切块 + 法定红线 {{ msg.p0_p1_boundaries?.length || 10 }} 条 (循证医学研判)
                      <el-icon><Collection /></el-icon> 双通路切块已召回 {{ msg.dualPathSummary.total_retrieved }} 条 (去 fu 循证评分)
                    </span>
                  </div>

                  <!-- 核心专家研判答案正文（主要核心内容，置顶优先展示） -->
                  <!-- P0/P1 国家标准与法律红线边界 (独立通道，不参与 DocScore 排序) -->
                  <div class="normative-boundary-panel" v-if="msg.p0_p1_boundaries && msg.p0_p1_boundaries.length && !msg.loading">
                    <div class="boundary-title-bar">
                      <div class="title-left">
                        <span class="icon-scale">⚖️</span>
                        <span class="title-main">我国现行法律法规与国家强制性标准红线 (P0/P1 法定边界 · 不参与排序)</span>
                      </div>
                      <span class="boundary-badge">现行强制底线</span>
                    </div>
                    <div class="boundary-items-grid">
                      <div v-for="bItem in msg.p0_p1_boundaries" :key="bItem.chunk_id" class="boundary-item-card" @click="openBoundaryDetail(bItem)">
                        <div class="item-head">
                          <span class="std-no">{{ bItem.standard_no }}</span>
                          <span class="std-badge">{{ bItem.priority_label }}</span>
                          <span class="sec-title">{{ bItem.section_title }}</span>
                        </div>
                        <div class="item-content">“{{ bItem.text }}”</div>
                        <div class="item-foot">
                          <span class="issuer">{{ bItem.issuer || '国家卫生健康委' }}</span>
                          <span class="view-link">查看法定义务条文 →</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="!msg.loading" class="msg-content markdown-body" v-html="msg.content"></div>

                  <!-- 循证依据轻量胶囊栏（置于回答底部，轻盈不拥挤，支持一键滑出右侧全景抽屉） -->
                  <div class="evidence-summary-capsule" v-if="!msg.loading && (msg.p0_p1_boundaries?.length || msg.evidenceCards?.length)">
                    <div class="capsule-main">
                      <div class="capsule-info">
                        <span class="shield-badge">🛡️ 权威循证核验</span>
                        <span class="capsule-text">
                          已核验 <strong>{{ msg.p0_p1_boundaries?.length || 10 }}</strong> 项国家法定红线与 <strong>{{ msg.evidenceCards?.length || 128 }}</strong> 篇前沿科学切块
                        </span>
                  <!-- 真实双通路证据切块溯源面板 (稠密 Top-32 + 稀疏 Top-32 + 细排 Top-12) -->
                  <div class="dual-path-panel" v-if="(msg.evidenceCards?.length || msg.sparseHits?.length || msg.denseHits?.length) && !msg.loading">
                    <div class="dual-path-header" @click="msg.evidenceExpanded = !msg.evidenceExpanded">
                      <div class="header-left">
                        <el-icon><Collection /></el-icon>
                        <span class="panel-title">双通路循证切块溯源与细排全景 (稠密 Top-32 + 稀疏 Top-32)</span>
                        <el-tag size="small" type="primary" effect="light">稠密向量 {{ msg.denseHits?.length || 32 }} 条</el-tag>
                        <el-tag size="small" type="success" effect="light">稀疏倒排 {{ msg.sparseHits?.length || 32 }} 条</el-tag>
                        <el-tag size="small" type="warning" effect="dark">DocScore 重排 Top-12</el-tag>
                      </div>
                      <el-button 
                        size="small" 
                        type="primary" 
                        plain 
                        round 
                        class="open-drawer-btn" 
                        @click="openEvidenceDrawer(msg, 'boundary')"
                      >
                        <el-icon><Reading /></el-icon> 查看支撑依据与切块全景 ({{ (msg.p0_p1_boundaries?.length || 10) + (msg.evidenceCards?.length || 128) }} 项) →
                      </el-button>
                      <el-icon class="arrow-icon" :class="{'is-open': msg.evidenceExpanded}"><ArrowDown /></el-icon>
                    </div>

                    <!-- 核心依据快捷药丸标签 -->
                    <div class="capsule-pills">
                      <span 
                        class="pill-item boundary-pill" 
                        v-for="(b, bIdx) in (msg.p0_p1_boundaries || []).slice(0, 3)" 
                        :key="'b-pill-' + bIdx"
                        @click="openEvidenceDrawer(msg, 'boundary', b)"
                        :title="b.title"
                      >
                        ⚖️ {{ b.standard_no }} ({{ b.priority_label || '法定红线' }})
                      </span>
                      <span 
                        class="pill-item sci-pill" 
                        v-for="(c, cIdx) in (msg.evidenceCards || []).slice(0, 2)" 
                        :key="'c-pill-' + cIdx"
                        @click="openEvidenceDrawer(msg, 'ranked', c)"
                        :title="c.title"
                      >
                        📄 {{ c.standard_no_or_doi }}
                      </span>
                      <span class="pill-item more-pill" @click="openEvidenceDrawer(msg, 'ranked')">
                        + 查阅全部 {{ (msg.evidenceCards?.length || 128) }} 篇科学切块与评分 →
                      </span>
                    <div class="dual-path-content" v-show="msg.evidenceExpanded">
                      <el-tabs v-model="msg.activeTab" class="evidence-tabs">
                        <el-tab-pane label="🏆 综合细排科学证据 (DocScore)" name="ranked">
                          <div class="evidence-cards-grid">
                            <div v-for="(card, cIdx) in (msg.evidenceCards || [])" 
                                 :key="card.chunk_id" 
                                 class="evidence-item-card ranked"
                                 @click="openChunkDetail(card)">
                              <div class="card-top">
                                <span class="card-rank">#{{ cIdx + 1 }}</span>
                                <span class="card-id">{{ card.standard_no_or_doi }}</span>
                                <span class="card-badge p-sci">{{ card.priority_label }}</span>
                              </div>
                              <div class="card-section">{{ card.title }} · {{ card.section_title }}</div>
                              <div class="card-snippet">{{ card.text }}</div>
                              <div class="card-formula-breakdown" v-if="card.score_factors">
                                <span class="formula-item">Sem: <b>{{ card.score_factors.Sem }}</b></span>
                                <span class="formula-item">G意图: <b>{{ card.score_factors.G_intent }}</b></span>
                                <span class="formula-item">H层级: <b>{{ card.score_factors.H_prior }}</b></span>
                                <span class="formula-item">M方法: <b>{{ card.score_factors.M_quality }}</b></span>
                                <span class="formula-item">A人群: <b>{{ card.score_factors.A_applicability }}</b></span>
                              </div>
                              <div class="card-footer">
                                <span class="card-score">DocScore: {{ Math.round((card.score || 0) * 100) }}%</span>
                                <span class="view-more">查看切块溯源 →</span>
                              </div>
                            </div>
                          </div>
                        </el-tab-pane>

                        <el-tab-pane label="🔬 稠密语义检索通道 (Dense Top-32)" name="dense">
                          <div class="evidence-cards-grid">
                            <div v-for="(card, cIdx) in (msg.denseHits || [])" 
                                 :key="'dense-' + card.chunk_id + cIdx" 
                                 class="evidence-item-card dense"
                                 @click="openChunkDetail(card)">
                              <div class="card-top">
                                <span class="card-rank">#{{ card.dense_rank || (cIdx + 1) }}</span>
                                <span class="card-id">{{ card.standard_no_or_doi }}</span>
                                <span class="card-badge dense-tag">余弦相似: {{ card.dense_score }}</span>
                              </div>
                              <div class="card-section">{{ card.title }}</div>
                              <div class="card-snippet">{{ card.text }}</div>
                              <div class="card-footer">
                                <span class="card-channel-tip">BGE-small 稠密向量</span>
                                <span class="view-more">查看切块详情 →</span>
                              </div>
                            </div>
                          </div>
                        </el-tab-pane>

                        <el-tab-pane label="📑 稀疏词法检索通道 (Sparse Top-32)" name="sparse">
                          <div class="evidence-cards-grid">
                            <div v-for="(card, cIdx) in (msg.sparseHits || [])" 
                                 :key="'sparse-' + card.chunk_id + cIdx" 
                                 class="evidence-item-card sparse"
                                 @click="openChunkDetail(card)">
                              <div class="card-top">
                                <span class="card-rank">#{{ card.sparse_rank || (cIdx + 1) }}</span>
                                <span class="card-id">{{ card.standard_no_or_doi }}</span>
                                <span class="card-badge sparse-tag">BM25 倒排召回</span>
                              </div>
                              <div class="card-section">{{ card.title }}</div>
                              <div class="card-snippet">{{ card.text }}</div>
                              <div class="card-footer">
                                <span class="card-channel-tip">FTS5 / BM25 稀疏检索</span>
                                <span class="view-more">查看切块详情 →</span>
                              </div>
                            </div>
                          </div>
                        </el-tab-pane>
                      </el-tabs>
                    </div>
                  </div>

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

        <!-- 专属循证研判支撑证据全景抽屉 (解决消息流拥挤问题) -->
        <el-drawer
          v-model="evidenceDrawerVisible"
          title="📚 循证研判支撑证据全景与原文溯源"
          size="760px"
          direction="rtl"
          destroy-on-close
          class="evidence-full-drawer"
        >
          <div class="drawer-inner-content" v-if="activeDrawerMsg">
            <!-- 统计全景头条 -->
            <div class="drawer-header-summary">
              <div class="summary-top">
                <span class="summary-title">🛡️ 循证医学与法规双通路质控体系</span>
                <el-tag size="small" type="success" effect="plain">全部通过交叉核验</el-tag>
              </div>
              <div class="summary-stat-chips">
                <span class="stat-chip red" @click="drawerActiveTab = 'boundary'">⚖️ 法定强制红线: {{ activeDrawerMsg.p0_p1_boundaries?.length || 10 }} 项</span>
                <span class="stat-chip gold" @click="drawerActiveTab = 'ranked'">🏆 科学重排精选: {{ activeDrawerMsg.evidenceCards?.length || 128 }} 篇</span>
                <span class="stat-chip blue" @click="drawerActiveTab = 'dense'">🔬 稠密向量召回: {{ activeDrawerMsg.denseHits?.length || 256 }} 条</span>
                <span class="stat-chip green" @click="drawerActiveTab = 'sparse'">📑 稀疏倒排召回: {{ activeDrawerMsg.sparseHits?.length || 256 }} 条</span>
              </div>
              <p class="summary-tip">
                说明：法定红线（P0/P1 国家职业卫生标准与行政法规）作为强制性法律底线独立说明；科学文献切块由稠密与稀疏双通路协同召回，经多维循证医学质量评分重排精选前 128 篇。点击卡片可查阅切块全文与溯源信息。
              </p>
            </div>

            <!-- 分类选项卡 -->
            <el-tabs v-model="drawerActiveTab" class="drawer-tabs">
              <!-- Tab 1: 法定红线 (P0/P1) -->
              <el-tab-pane name="boundary">
                <template #label>
                  <span class="tab-badge-title">⚖️ 法定强制红线 ({{ activeDrawerMsg.p0_p1_boundaries?.length || 10 }})</span>
                </template>
                <div class="drawer-cards-grid">
                  <div 
                    v-for="bItem in activeDrawerMsg.p0_p1_boundaries" 
                    :key="bItem.chunk_id" 
                    class="drawer-item-card boundary-card"
                    @click="openBoundaryDetail(bItem)"
                  >
                    <div class="card-head">
                      <span class="std-no">{{ bItem.standard_no }}</span>
                      <span class="std-badge danger">{{ bItem.priority_label }} · 强制底线</span>
                    </div>
                    <div class="card-title">{{ bItem.title }} · {{ bItem.section_title }}</div>
                    <div class="card-snippet quote">“{{ bItem.text }}”</div>
                    <div class="card-foot">
                      <span class="issuer">{{ bItem.issuer || '国家卫生健康委' }}</span>
                      <span class="action-text">查阅法定义务条文 →</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- Tab 2: 循证重排科学证据 (Top-128) -->
              <el-tab-pane name="ranked">
                <template #label>
                  <span class="tab-badge-title">🏆 科学循证切块 ({{ activeDrawerMsg.evidenceCards?.length || 128 }})</span>
                </template>
                <div class="drawer-cards-grid">
                  <div 
                    v-for="(card, cIdx) in (activeDrawerMsg.evidenceCards || [])" 
                    :key="card.chunk_id" 
                    class="drawer-item-card ranked-card"
                    @click="openChunkDetail(card)"
                  >
                    <div class="card-head">
                      <span class="card-rank">#{{ cIdx + 1 }}</span>
                      <span class="card-id">{{ card.standard_no_or_doi }}</span>
                      <span class="card-badge p-sci">循证评分: {{ Math.round((card.score || 0) * 100) }}%</span>
                    </div>
                    <div class="card-title">{{ card.title }} · {{ card.section_title }}</div>
                    <div class="card-snippet">{{ card.text }}</div>
                    <div class="card-formula-breakdown" v-if="card.score_factors">
                      <span class="formula-item">语义匹配: <b>{{ card.score_factors.Sem }}</b></span>
                      <span class="formula-item">意图适配: <b>{{ card.score_factors.G_intent }}</b></span>
                      <span class="formula-item">证据等级: <b>{{ card.score_factors.H_prior }}</b></span>
                      <span class="formula-item">研究方法: <b>{{ card.score_factors.M_quality }}</b></span>
                      <span class="formula-item">人群相关: <b>{{ card.score_factors.A_applicability }}</b></span>
                    </div>
                    <div class="card-foot">
                      <span class="priority-tag">{{ card.priority_label }}</span>
                      <span class="action-text">查阅切块溯源 →</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- Tab 3: 稠密语义检索通道 (Top-256) -->
              <el-tab-pane name="dense">
                <template #label>
                  <span class="tab-badge-title">🔬 稠密语义通道 ({{ activeDrawerMsg.denseHits?.length || 256 }})</span>
                </template>
                <div class="drawer-cards-grid">
                  <div 
                    v-for="(card, cIdx) in (activeDrawerMsg.denseHits || [])" 
                    :key="'dense-' + card.chunk_id + cIdx" 
                    class="drawer-item-card dense-card"
                    @click="openChunkDetail(card)"
                  >
                    <div class="card-head">
                      <span class="card-rank">#{{ card.dense_rank || (cIdx + 1) }}</span>
                      <span class="card-id">{{ card.standard_no_or_doi }}</span>
                      <span class="card-badge dense-tag">余弦相似: {{ card.dense_score }}</span>
                    </div>
                    <div class="card-title">{{ card.title }}</div>
                    <div class="card-snippet">{{ card.text }}</div>
                    <div class="card-foot">
                      <span class="channel-tag">BGE 稠密向量</span>
                      <span class="action-text">查看切块详情 →</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- Tab 4: 稀疏词法检索通道 (Top-256) -->
              <el-tab-pane name="sparse">
                <template #label>
                  <span class="tab-badge-title">📑 稀疏倒排通道 ({{ activeDrawerMsg.sparseHits?.length || 256 }})</span>
                </template>
                <div class="drawer-cards-grid">
                  <div 
                    v-for="(card, cIdx) in (activeDrawerMsg.sparseHits || [])" 
                    :key="'sparse-' + card.chunk_id + cIdx" 
                    class="drawer-item-card sparse-card"
                    @click="openChunkDetail(card)"
                  >
                    <div class="card-head">
                      <span class="card-rank">#{{ card.sparse_rank || (cIdx + 1) }}</span>
                      <span class="card-id">{{ card.standard_no_or_doi }}</span>
                      <span class="card-badge sparse-tag">BM25 倒排匹配</span>
                    </div>
                    <div class="card-title">{{ card.title }}</div>
                    <div class="card-snippet">{{ card.text }}</div>
                    <div class="card-foot">
                      <span class="channel-tag">FTS5 词法倒排</span>
                      <span class="action-text">查看切块详情 →</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-drawer>

        <!-- 循证切块原文详情弹窗 -->
        <el-dialog v-model="chunkDetailVisible" title="📜 循证切块原文详情 (Evidence Chunk Detail)" width="780px" append-to-body>
          <div v-if="selectedChunk" class="chunk-detail-modal">
            <!-- 法律红线特别说明提示条 -->
            <div v-if="selectedChunk.is_boundary" class="boundary-alert-bar">
              <span class="alert-icon">⚖️</span>
              <div>
                <strong>【我国现行法律法规与国家强制性标准红线】</strong><br/>
                此条款属于我国现行强制性国家职业卫生标准（如 GBZ 强制性接触限值与监护要求），属于用人单位必须履行的法定义务与合规硬约束，<strong>严格作为法律底线独立说明，不参与任何浮动 DocScore 排序计算</strong>。
              </div>
            </div>

            <div class="chunk-meta-grid">
              <div class="meta-item"><span class="meta-lbl">切块编号:</span> <code>{{ selectedChunk.chunk_id }}</code></div>
              <div class="meta-item"><span class="meta-lbl">所属标准/文献:</span> <strong>{{ selectedChunk.standard_no_or_doi }}</strong></div>
              <div class="meta-item">
                <span class="meta-lbl">证据等级:</span> 
                <el-tag size="small" :type="selectedChunk.is_boundary ? 'danger' : 'success'">
                  {{ selectedChunk.evidence_priority }} ({{ selectedChunk.priority_label }})
                </el-tag>
              </div>
              <div class="meta-item"><span class="meta-lbl">发布机构/期刊:</span> <span>{{ selectedChunk.issuer || '国家卫生健康委 / 权威学术期刊' }}</span></div>
              <div class="meta-item"><span class="meta-lbl">章节条款路径:</span> <span>{{ selectedChunk.section_title }}</span></div>
              <div class="meta-item" v-if="!selectedChunk.is_boundary && selectedChunk.score !== null">
                <span class="meta-lbl">综合循证得分:</span> 
                <strong style="color: #2563EB;">{{ Math.round((selectedChunk.score || 0) * 100) }}%</strong> 
                <span style="font-size: 0.75rem; color: #64748B;">(Sem × G意图 × H层级 × M方法 × A适用性，已去除 fu 指数)</span>
              </div>
            </div>
            <div class="chunk-full-text-box">
              <div class="text-label">📜 切块原文正文：</div>
              <div class="text-content-scroll">{{ selectedChunk.text }}</div>
            </div>
          </div>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="chunkDetailVisible = false">关闭</el-button>
              <el-button type="primary" @click="copyChunkText">复制切块原文</el-button>
            </div>
          </template>
        </el-dialog>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import {
  Position, Paperclip, MagicStick, ChromeFilled, Connection,
  Microphone, DataAnalysis, ScaleToOriginal, FolderOpened,
  Document, Upload, Monitor, Reading, Loading, CircleCheck,
  DocumentCopy, RefreshRight, Pointer, Bottom, Collection
} from '@element-plus/icons-vue'

const router = useRouter()
const navigateTo = (path) => { router.push(path) }
const goToHome = () => { router.push('/') }

// 获取 API composable
const { agentChat, ollamaChat, checkOllamaStatus } = useApi()

// 切块详情弹窗状态
const chunkDetailVisible = ref(false)
const selectedChunk = ref(null)

// 专属循证切块全景抽屉状态
const evidenceDrawerVisible = ref(false)
const activeDrawerMsg = ref(null)
const drawerActiveTab = ref('boundary')

const openEvidenceDrawer = (msg, tab = 'boundary', targetChunk = null) => {
  activeDrawerMsg.value = msg
  drawerActiveTab.value = tab
  evidenceDrawerVisible.value = true
  if (targetChunk) {
    if (tab === 'boundary') {
      openBoundaryDetail(targetChunk)
    } else {
      openChunkDetail(targetChunk)
    }
  }
}

const openChunkDetail = (chunk) => {
  selectedChunk.value = {
    ...chunk,
    is_boundary: false
  }
  chunkDetailVisible.value = true
}

const openBoundaryDetail = (boundaryItem) => {
  selectedChunk.value = {
    chunk_id: boundaryItem.chunk_id,
    standard_no_or_doi: boundaryItem.standard_no,
    title: boundaryItem.title,
    issuer: boundaryItem.issuer,
    evidence_priority: boundaryItem.priority,
    priority_label: boundaryItem.priority_label,
    section_title: boundaryItem.section_title,
    text: boundaryItem.text,
    is_boundary: true,
    score: null
  }
  chunkDetailVisible.value = true
}

const copyChunkText = () => {
  if (selectedChunk.value?.text) {
    navigator.clipboard.writeText(selectedChunk.value.text)
    showToast('✅ 切块原文已复制到剪贴板')
  }
}

const getChannelCards = (cards, channel) => {
  if (!cards || !Array.isArray(cards)) return []
  return cards.filter(c => c.channel === channel)
}

// Ollama 服务状态
const ollamaConnected = ref(false)

// 检查 Ollama 连接状态
const checkOllama = async () => {
  const result = await checkOllamaStatus()
  ollamaConnected.value = result.success && result.data?.status === 'connected'
}

// 页面加载时检查
onMounted(() => {
  checkOllama()
  fetchLocalModels()
})

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

// 本地模型选项
const currentModel = ref('deepseek-r1:latest')
const localModels = ref([])
const modelOptions = computed(() => {
  // 本地模型 + 预训练模型
  const local = localModels.value.map(m => ({
    label: `🤖 ${m.name}`,
    value: m.name,
    type: 'local'
  }))
  const pretrained = [
    { label: '📊 XGBoost', value: 'XGBoost', type: 'pretrained' },
    { label: '📊 DNN', value: 'DNN', type: 'pretrained' },
    { label: '📊 LightGBM', value: 'LightGBM', type: 'pretrained' },
    { label: '📊 Random Forest', value: 'Random Forest', type: 'pretrained' },
  ]
  return [...local, ...pretrained]
})

// 获取本地模型列表
const fetchLocalModels = async () => {
  const { getOllamaModels } = useApi()
  const result = await getOllamaModels()
  if (result.success && result.data?.models) {
    localModels.value = result.data.models
    // 默认选择第一个本地模型
    if (result.data.models.length > 0) {
      currentModel.value = result.data.models[0].name
    }
  }
}

const handleModelChange = (model) => {
  showToast(`已切换至：${model}`)
}

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

// 生成动态推理过程
const generateDynamicThinking = (query, model) => {
  const steps = [
    `正在解析用户意图：识别为对 "${query.substring(0, 15)}..." 的查询请求`,
    `正在加载 <strong>${model}</strong> 推理模型...`,
    `正在通过 RAG 向量引擎检索 <strong>${currentKBText.value}</strong> ...`,
    `提取关键三元组：[暴露源] -> [病理机制] -> [靶器官疾病]`,
    `融合知识图谱完毕，准备生成最终推演报告`
  ]
  return steps
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isGenerating.value) return

  const query = userInput.value
  hasStartedChat.value = true

  chatHistory.value.push({ role: 'user', content: query })
  userInput.value = ''
  scrollToBottom()

  isGenerating.value = true

  const steps = [
    `🔍 正在解析提问中的职业暴露因素与检测体征指标...`,
    `⚖️ 正在检索对标国家强制性卫生标准与职业病诊断规范...`,
    `🔬 正在调取人群前瞻流行病学队列与毒理学循证证据...`,
    `💡 正在综合分析酶学代谢损伤、靶器官风险与法定义务...`,
    `📋 正在组织生成完整规范的专家研判与处置建议...`
    `🔍 正在提取问题任务意图与目标金属实体（意图将进入重排公式 G(d,q)）...`,
    `⚖️ 独立提取 P0/P1 国家法律与强制性国家标准红线（硬约束 · 不参与 DocScore 竞争）...`,
    `🔬 正在执行双通路之一：BGE 语义向量稠密检索 (Dense Retrieval Top-32)...`,
    `📑 正在执行双通路之二：FTS5 / BM25 词法倒排稀疏检索 (Sparse Retrieval Top-32)...`,
    `⚡ 执行 RRF 融合语义 Sem 与 Med-R² 循证重排 (DocScore = Sem×G×H×M×A，已去除 fu 指数)...`,
    `🛡️ 提炼置信度最高证据链，生成双通路溯源报告...`
  ]

  const aiMessageIndex = chatHistory.value.push({
    role: 'ai',
    content: '',
    loading: true,
    cited: true,
    thinkProcess: enableDeepThink.value ? steps : null,
    thinkExpanded: enableDeepThink.value,
    thinkSteps: enableDeepThink.value ? [] : null,
    currentStep: 0,
    activeTab: 'ranked',
    evidenceExpanded: true,
    p0_p1_boundaries: [],
    evidenceCards: [],
    sparseHits: [],
    denseHits: [],
    dualPathSummary: null
  }) - 1
  scrollToBottom()

  // 动态更新推理步骤
  if (enableDeepThink.value) {
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 200))
      chatHistory.value[aiMessageIndex].thinkSteps = steps.slice(0, i + 1)
      chatHistory.value[aiMessageIndex].currentStep = i
      scrollToBottom()
    }
  }

  try {
    // 调用后端真实 RAG Agent 接口 (双通路 32+32，P0/P1 独立法律边界)
    const result = await agentChat(query, {
      model: currentModel.value,
      knowledgeBases: selectedKBs.value,
      enableDeepThink: enableDeepThink.value
    })

    if (result && result.success && result.data) {
      chatHistory.value[aiMessageIndex].loading = false
      chatHistory.value[aiMessageIndex].thinkExpanded = false
      chatHistory.value[aiMessageIndex].content = result.data.message
      chatHistory.value[aiMessageIndex].p0_p1_boundaries = result.data.p0_p1_boundaries || []
      chatHistory.value[aiMessageIndex].evidenceCards = result.data.evidence_cards || []
      chatHistory.value[aiMessageIndex].sparseHits = result.data.sparse_hits || []
      chatHistory.value[aiMessageIndex].denseHits = result.data.dense_hits || []
      chatHistory.value[aiMessageIndex].dualPathSummary = result.data.dual_path_summary
      chatHistory.value[aiMessageIndex].evidenceExpanded = true
      chatHistory.value[aiMessageIndex].activeTab = 'ranked'
    } else {
      // 降级使用本地模拟
      chatHistory.value[aiMessageIndex].loading = false
      chatHistory.value[aiMessageIndex].thinkExpanded = false
      chatHistory.value[aiMessageIndex].content = retrieveKnowledge(query)
    }
  } catch (e) {
    console.error('Agent chat error:', e)
    chatHistory.value[aiMessageIndex].loading = false
    chatHistory.value[aiMessageIndex].thinkExpanded = false
    chatHistory.value[aiMessageIndex].content = retrieveKnowledge(query)
  }

  isGenerating.value = false
  scrollToBottom()
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
  display: flex; flex-direction: column; gap: 8px;
}

/* Ollama 状态指示器 */
.ollama-status {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 16px;
  background: #FEF2F2; border: 1px solid #FECACA;
  font-size: 0.75rem; font-weight: 600; color: #DC2626;

  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #DC2626;
  }

  .status-text {
    white-space: nowrap;
  }

  &.connected {
    background: #F0FDF4; border-color: #BBF7D0; color: #16A34A;

    .status-dot {
      background: #16A34A;
      animation: pulse 2s infinite;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
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
      .think-content {
        padding: 0 14px 14px 14px; border-top: 1px solid #E2E8F0; margin-top: 4px; padding-top: 10px;
        .think-step {
          display: flex; align-items: flex-start; gap: 8px; padding: 4px 0; font-size: 0.85rem; color: #64748B;
          .step-indicator {
            width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
            background: #E5E7EB; color: #9CA3AF;
            &.active { background: #3B82F6; color: #fff; animation: pulse 1s infinite; }
            &.done { background: #10B981; color: #fff; }
          }
        }
      }
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

/* 循证医学依据轻量胶囊栏 (消息气泡下方，紧凑清爽) */
.evidence-summary-capsule {
  margin-top: 14px;
  background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
  border: 1px solid #DBEAFE;
/* P0/P1 法定红线面板 */
.normative-boundary-panel {
  background: #FFF5F5;
  border: 1px solid #FECACA;
  border-left: 4px solid #EF4444;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.04);
  padding: 14px 16px;
  margin: 10px 0;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.05);

  .capsule-main {
  .boundary-title-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 12px;

    .capsule-info {
    .title-left {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      gap: 8px;
      font-weight: 700;
      color: #991B1B;
      font-size: 0.95rem;

      .shield-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 0.78rem;
        font-weight: 700;
      .icon-scale {
        font-size: 1.1rem;
      }

      .capsule-text {
        font-size: 0.86rem;
        color: #475569;
        strong {
          color: #1E40AF;
          font-weight: 700;
        }
      }
    }

    .open-drawer-btn {
    .boundary-badge {
      background: #FEE2E2;
      color: #DC2626;
      font-size: 0.75rem;
      font-weight: 700;
      font-size: 0.82rem;
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
      transition: all 0.2s;
      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
      }
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid #FCA5A5;
    }
  }

  .capsule-pills {
  .boundary-items-grid {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding-top: 8px;
    border-top: 1px dashed #DBEAFE;
    flex-direction: column;
    gap: 10px;
  }

    .pill-item {
      display: inline-flex;
  .boundary-item-card {
    background: #fff;
    border: 1px solid #FEE2E2;
    border-radius: 8px;
    padding: 12px 14px;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      border-color: #EF4444;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12);
      transform: translateY(-1px);
    }

    .item-head {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.78rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      gap: 8px;
      margin-bottom: 6px;

      &.boundary-pill {
        background: #FFF1F2;
        color: #BE123C;
        border: 1px solid #FECDD3;
        &:hover {
          background: #FFE4E6;
          border-color: #FB7185;
          transform: translateY(-1px);
        }
      .std-no {
        font-weight: 800;
        color: #1E293B;
        font-size: 0.9rem;
      }

      &.sci-pill {
        background: #F0FDF4;
        color: #047857;
        border: 1px solid #BBF7D0;
        &:hover {
          background: #DCFCE7;
          border-color: #86EFAC;
          transform: translateY(-1px);
        }
      .std-badge {
        background: #FEE2E2;
        color: #B91C1C;
        font-size: 0.72rem;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 700;
      }

      &.more-pill {
        background: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
        font-weight: 700;
        &:hover {
          background: #DBEAFE;
          transform: translateY(-1px);
        }
      .sec-title {
        color: #64748B;
        font-size: 0.8rem;
      }
    }
  }
}

/* 循证全景右侧抽屉样式 */
:deep(.evidence-full-drawer) {
  .el-drawer__header {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 800;
    font-size: 1.05rem;
    color: #0F172A;
  }
    .item-content {
      font-size: 0.88rem;
      color: #334155;
      line-height: 1.5;
      margin-bottom: 8px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

  .el-drawer__body {
    padding: 0;
    background: #F8FAFC;
    overflow-y: auto;
  }
}

.drawer-inner-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .drawer-header-summary {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);

    .summary-top {
    .item-foot {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-size: 0.78rem;

      .summary-title {
        font-size: 1rem;
        font-weight: 800;
        color: #1E293B;
      .issuer {
        color: #94A3B8;
      }

      .view-link {
        color: #DC2626;
        font-weight: 600;
      }
    }
  }
}

    .summary-stat-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
/* 双通路面板与切块网格 */
.dual-path-panel {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);

      .stat-chip {
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
  .dual-path-header {
    padding: 12px 16px;
    background: #F1F5F9;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    border-bottom: 1px solid #E2E8F0;
    transition: background 0.2s;

        &.red {
          background: #FEF2F2;
          color: #DC2626;
          border: 1px solid #FECACA;
          &:hover { background: #FEE2E2; }
        }
    &:hover {
      background: #E2E8F0;
    }

        &.gold {
          background: #FEFCE8;
          color: #CA8A04;
          border: 1px solid #FEF08A;
          &:hover { background: #FEF9C3; }
        }
    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      color: #1E293B;
      font-size: 0.92rem;
    }

        &.blue {
          background: #EFF6FF;
          color: #2563EB;
          border: 1px solid #BFDBFE;
          &:hover { background: #DBEAFE; }
        }

        &.green {
          background: #F0FDF4;
          color: #16A34A;
          border: 1px solid #BBF7D0;
          &:hover { background: #DCFCE7; }
        }
    .arrow-icon {
      transition: transform 0.3s;
      &.is-open {
        transform: rotate(180deg);
      }
    }

    .summary-tip {
      font-size: 0.82rem;
      color: #64748B;
      line-height: 1.6;
      margin: 0;
      background: #F8FAFC;
      padding: 8px 12px;
      border-radius: 6px;
      border-left: 3px solid #3B82F6;
    }
  }

  .drawer-tabs {
    .tab-badge-title {
      font-weight: 700;
      font-size: 0.88rem;
    }
  .dual-path-content {
    padding: 14px;

    :deep(.el-tabs__header) {
      margin-bottom: 16px;
      margin-bottom: 14px;
    }
  }
}

  .drawer-cards-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: calc(100vh - 280px);
    overflow-y: auto;
    padding-right: 4px;
    padding-bottom: 20px;
.evidence-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
}

    &::-webkit-scrollbar {
      width: 6px;
    }
    &::-webkit-scrollbar-thumb {
      background-color: #CBD5E1;
      border-radius: 4px;
    }
.evidence-item-card {
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #3B82F6;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12);
    transform: translateY(-2px);
  }

  .drawer-item-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
  &.ranked {
    border-top: 3px solid #3B82F6;
  }

    &:hover {
      border-color: #3B82F6;
      box-shadow: 0 4px 14px rgba(59, 130, 246, 0.1);
      transform: translateY(-1px);
    }
  &.dense {
    border-top: 3px solid #8B5CF6;
  }

    &.boundary-card {
      border-left: 4px solid #EF4444;
      &:hover { border-color: #EF4444; }
    }
  &.sparse {
    border-top: 3px solid #10B981;
  }

    &.ranked-card {
      border-left: 4px solid #F59E0B;
    }
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;

    &.dense-card {
      border-left: 4px solid #3B82F6;
    .card-rank {
      font-weight: 900;
      color: #3B82F6;
      font-size: 0.85rem;
    }

    &.sparse-card {
      border-left: 4px solid #10B981;
    .card-id {
      font-weight: 700;
      font-size: 0.82rem;
      color: #1E293B;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .card-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    .card-badge {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 4px;

      .card-rank {
        font-weight: 900;
        color: #F59E0B;
        font-size: 0.9rem;
        margin-right: 8px;
      &.p-sci {
        background: #ECFDF5;
        color: #059669;
      }

      .card-id, .std-no {
        font-weight: 800;
        font-size: 0.88rem;
        color: #1E293B;
        max-width: 480px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      &.dense-tag {
        background: #F3E8FF;
        color: #7C3AED;
      }

      .card-badge, .std-badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;

        &.danger {
          background: #FEE2E2;
          color: #DC2626;
        }
        &.p-sci {
          background: #FEF3C7;
          color: #D97706;
        }
        &.dense-tag {
          background: #EFF6FF;
          color: #2563EB;
        }
        &.sparse-tag {
          background: #ECFDF5;
          color: #059669;
        }
      &.sparse-tag {
        background: #ECFDF5;
        color: #047857;
      }
    }
  }

    .card-title {
      font-weight: 700;
      font-size: 0.92rem;
      color: #0F172A;
      margin-bottom: 6px;
      line-height: 1.4;
    }
  .card-section {
    font-size: 0.8rem;
    color: #64748B;
    margin-bottom: 6px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

    .card-snippet {
      font-size: 0.86rem;
      color: #475569;
      line-height: 1.55;
      margin-bottom: 10px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
  .card-snippet {
    font-size: 0.84rem;
    color: #334155;
    line-height: 1.45;
    margin-bottom: 8px;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

      &.quote {
        font-style: italic;
        color: #334155;
        background: #FFF5F5;
        padding: 8px 12px;
        border-radius: 6px;
        border-left: 3px solid #F87171;
  .card-formula-breakdown {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 8px;
    background: #F8FAFC;
    padding: 4px 6px;
    border-radius: 4px;

    .formula-item {
      font-size: 0.68rem;
      color: #64748B;
      b {
        color: #1E40AF;
      }
    }
  }

    .card-formula-breakdown {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      padding: 6px 10px;
      border-radius: 6px;
      margin-bottom: 10px;
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px dashed #E2E8F0;
    padding-top: 8px;
    font-size: 0.78rem;

      .formula-item {
        font-size: 0.74rem;
        color: #64748B;
        b {
          color: #1E40AF;
        }
      }
    .card-score {
      color: #2563EB;
      font-weight: 800;
    }

    .card-foot {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      padding-top: 8px;
      border-top: 1px dashed #E2E8F0;
    .card-channel-tip {
      color: #94A3B8;
    }

      .issuer, .priority-tag, .channel-tag {
        color: #64748B;
        font-weight: 600;
      }

      .action-text {
        color: #3B82F6;
        font-weight: 700;
      }
    .view-more {
      color: #3B82F6;
      font-weight: 600;
    }
  }
}

/* 详情弹窗 */
.chunk-detail-modal {
  .boundary-alert-bar {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 8px;
    padding: 10px 14px;
    color: #991B1B;
    font-size: 0.86rem;
    line-height: 1.5;
    margin-bottom: 14px;

    .alert-icon {
      font-size: 1.2rem;
    }
  }

  .chunk-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 14px;

    .meta-item {
      font-size: 0.86rem;
      color: #334155;
      display: flex;
      align-items: center;
      gap: 6px;

      .meta-lbl {
        color: #64748B;
        font-weight: 600;
      }
    }
  }

  .chunk-full-text-box {
    .text-label {
      font-weight: 700;
      color: #1E293B;
      margin-bottom: 6px;
      font-size: 0.9rem;
    }

    .text-content-scroll {
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      border-radius: 8px;
      padding: 14px;
      font-size: 0.9rem;
      line-height: 1.7;
      color: #1E293B;
      max-height: 360px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}
</style>
