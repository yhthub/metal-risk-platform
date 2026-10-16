<template>
  <div class="system-layout" :class="{'single-page': formData.mode === 'single'}">

  <Sidebar default-active="1-1" />

    <main class="main-content">
     <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToHome">
            <el-icon class="back-icon">
              <ArrowLeft />
            </el-icon>
            <span class="back-text">系统首页</span>
            <span class="divider">|</span>
            <span class="page-title-top">职业暴露数据接入与特征工程</span>
          </div>

          <div class="ep-right-zone">
            <div class="user-profile">
              <div class="avatar">Dr.</div>
              <span>职业卫生评估员</span>
            </div>
          </div>
        </div>
      </header>

      <div class="page-container">
        <div class="pipeline-steps">
          <div class="step" :class="{ 'active': currentStep >= 1 }"><span class="step-num">1</span> 数据接入配置</div>
          <div class="step-line" :class="{ 'active-line': currentStep >= 2 }"></div>
          <div class="step" :class="{ 'active': currentStep >= 2 }"><span class="step-num">2</span> 多维可视化分析</div>
          <div class="step-line" :class="{ 'active-line': currentStep >= 3 }"></div>
          <div class="step pending"><span class="step-num">3</span> 风险分析模型</div>
        </div>

        <div class="input-dashboard">
          <div v-if="formData.mode === 'single'" class="single-intro">
            <div>
              <span class="eyebrow">INDIVIDUAL PROFILE</span>
              <h1>一份数据，读懂个体暴露画像</h1>
              <p>录入监测结果，按样本与单位匹配参考；也可用合成示例快速体验。</p>
            </div>
            <div class="single-intro-actions">
              <button type="button" class="btn-demo" @click="fillIndividualDemo"><el-icon><DocumentChecked /></el-icon> 一键填入演示数据</button>
              <span>填充档案、10项指标及口径，立即生成画像</span>
            </div>
          </div>
          <div class="panel-card clean-clinical-card" :class="{'single-input-card': formData.mode === 'single'}">
            <div class="card-layout-grid">
              <div class="form-entry-area">
                <div class="config-row">
                  <div class="config-group flex-2">
                    <label>目标监测工种</label>
                    <div class="radio-cards">
                      <div class="radio-card" :class="{'selected': formData.job === 'smelting'}" @click="formData.job = 'smelting'">冶炼工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'mining'}" @click="formData.job = 'mining'">采矿工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'welding'}" @click="formData.job = 'welding'">电焊工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'other'}" @click="formData.job = 'other'">其他</div>
                    </div>
                  </div>
                  <div class="config-group flex-1">
                    <label>数据录入模式</label>
                    <div class="mode-switch">
                      <button :class="{'active': formData.mode === 'single'}" :disabled="isAnalyzing || groupDemoRunning" @click="handleModeChange('single')">单人录入</button>
                      <button :class="{'active': formData.mode === 'batch'}" :disabled="isAnalyzing || groupDemoRunning" @click="handleModeChange('batch')">群体导入</button>
                    </div>
                  </div>
                </div>

                <div class="clinical-divider"></div>

                <div class="input-mode-section" v-if="formData.mode === 'single'">
                  <div v-if="demoSource" class="demo-notice" role="status">
                    <el-icon><InfoFilled /></el-icon>
                    <div><strong>{{ demoEdited ? '合成示例 · 已修改' : '合成示例 · 仅供系统演示' }}</strong><span>非真实人员或检测记录，不用于诊断。氡为独立的住宅环境示例，不是工位实测。</span></div>
                  </div>
                  <div class="form-section basic-profile-section">
                    <div class="section-heading"><h4 class="section-title"><span class="section-number">01</span> 基础个体档案</h4><span class="section-caption">身份信息与接触背景</span></div>
                    <div class="clinical-input-grid cols-4">
                      <div class="clinical-input-item"><label class="label" for="individual-name">姓名 / 编号</label><div class="input-wrap"><input id="individual-name" type="text" v-model="formData.singleData.name" placeholder="请输入编号" /></div></div>
                      <div class="clinical-input-item"><label class="label" for="individual-gender">性别</label><div class="input-wrap select-wrap"><select id="individual-gender" v-model="formData.singleData.gender" @change="individualGenderConfirmed = false"><option value="">请选择</option><option value="male">男</option><option value="female">女</option></select></div><label style="font-size:12px;color:#64748b"><input type="checkbox" v-model="individualGenderConfirmed" :disabled="!formData.singleData.gender" /> 已核对用于模型编码的性别</label></div>
                      <div class="clinical-input-item"><label class="label" for="individual-age">年龄</label><div class="input-wrap"><input id="individual-age" type="number" min="0" v-model="formData.singleData.age" placeholder="未录入" /><span class="unit">岁</span></div></div>
                      <div class="clinical-input-item"><label class="label" for="individual-work-years">接触工龄</label><div class="input-wrap"><input id="individual-work-years" type="number" min="0" v-model="formData.singleData.workYears" placeholder="未录入" /><span class="unit">年</span></div></div>
                    </div>
                    <div class="clinical-input-grid cols-4" style="margin-top: 16px;">
                      <div class="clinical-input-item">
                        <span class="label">学历</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.education">
                            <option value="">请选择</option>
                            <option value="primary">小学及以下</option>
                            <option value="middle">初中</option>
                            <option value="high">高中/中专</option>
                            <option value="college">大专</option>
                            <option value="bachelor">本科</option>
                            <option value="master">硕士及以上</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">婚姻状况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.marital">
                            <option value="">请选择</option>
                            <option value="unmarried">未婚</option>
                            <option value="married">已婚</option>
                            <option value="divorced">离异</option>
                            <option value="widowed">丧偶</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">吸烟情况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.smoking">
                            <option value="">请选择</option>
                            <option value="never">从不吸烟</option>
                            <option value="former">已戒烟</option>
                            <option value="current_lt10">现吸 (&lt;10支/日)</option>
                            <option value="current_ge10">现吸 (≥10支/日)</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">饮酒情况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.drinking">
                            <option value="">请选择</option>
                            <option value="never">从不饮酒</option>
                            <option value="occasional">偶尔饮酒</option>
                            <option value="frequent">经常饮酒</option>
                            <option value="daily">每日饮酒</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="clinical-input-grid cols-4" style="margin-top: 16px;">
                      <div class="clinical-input-item">
                        <span class="label">BMI (体质指数)</span>
                        <div class="input-wrap"><input type="number" v-model="formData.singleData.bmi" placeholder="0.0" step="0.1" /><span class="unit">kg/m²</span></div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">防护装备使用</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.ppe">
                            <option value="">请选择</option>
                            <option value="none">无防护</option>
                            <option value="basic">基本防护 (口罩/手套)</option>
                            <option value="standard">标准防护 (半面罩+护目镜)</option>
                            <option value="full">全面防护 (P100+防护服)</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item" style="grid-column: span 2;">
                        <span class="label">既往职业病史</span>
                        <div class="input-wrap"><input type="text" v-model="formData.singleData.history" placeholder="选填：已确认的职业病史" /></div>
                      </div>
                    </div>
                  </div>

                  <div class="form-section measurement-section" v-for="group in individualGroups" :key="group.id">
                    <div class="section-heading"><h4 class="section-title"><span class="section-number">{{ group.id === 'core' ? '02' : '03' }}</span> {{ group.title }}</h4><span class="section-caption">{{ group.id === 'core' ? '每项独立选择测量口径' : '区分生物样本与环境监测' }}</span></div>
                    <div class="clinical-input-grid measurement-grid">
                      <div class="clinical-input-item measurement-card" v-for="field in group.fields" :key="field.key">
                        <div class="measurement-heading"><span class="label">{{ field.label }}</span><span class="measurement-state" :class="{'is-comparable': measurementRow(field.key)?.ratio !== null}">{{ measurementRow(field.key)?.inputState === 'missing' ? '待录入' : measurementRow(field.key)?.inputState === 'invalid' ? '需修正' : measurementRow(field.key)?.ratio !== null ? '可参考比较' : '仅展示实测值' }}</span></div>
                        <div class="input-wrap" :class="{'is-error': individualProfile.rows.find(row => row.key === field.key)?.inputState === 'invalid'}">
                          <input type="number" min="0" step="any" v-model="formData.singleData[field.key]" placeholder="未录入" :aria-label="field.label + '实测值'" @input="handleMeasurementInput(field.key)" />
                        </div>
                        <div class="measurement-metadata">
                          <label class="metadata-field"><span>样本类型</span>
                          <select v-model="individualMetadata[field.key].sample" :aria-label="field.label + '样本类型'" @change="handleMetadataChange(field.key)">
                            <option v-for="sample in SAMPLE_OPTIONS" :key="sample.value" :value="sample.value">{{ sample.label }}</option>
                          </select>
                          </label>
                          <label class="metadata-field"><span>测量单位</span>
                          <select v-model="individualMetadata[field.key].unit" :aria-label="field.label + '单位'" @change="handleMetadataChange(field.key)">
                            <option v-for="unit in UNIT_OPTIONS" :key="unit" :value="unit">{{ unit || '单位未指定' }}</option>
                          </select>
                          </label>
                          <label v-if="field.key === 'as'" class="metadata-field metadata-wide"><span>分析物类型</span>
                          <select v-if="field.key === 'as'" v-model="individualMetadata.as.analyte" aria-label="砷分析物类型" @change="handleMetadataChange('as')">
                            <option value="">砷类型未指定</option><option value="total">总砷（不套用毒性砷参考）</option><option value="toxic_speciated">已分型：无机＋甲基化砷合计</option>
                          </select>
                          </label>
                          <label v-if="field.key === 'hg'" class="metadata-field metadata-wide"><span>汞分析物类型</span><select v-model="individualMetadata.hg.analyte" aria-label="汞分析物类型" @change="handleMetadataChange('hg')"><option value="">汞分析物未确认</option><option value="total_mercury">已确认：总汞（预测模型要求）</option></select></label>
                          <label v-if="['cd', 'hg', 'rn'].includes(field.key)" class="metadata-field metadata-wide"><span>参考适用情境</span>
                          <select v-if="['cd', 'hg', 'rn'].includes(field.key)" v-model="individualMetadata[field.key].context" :aria-label="field.label + '参考适用情境'" @change="handleMetadataChange(field.key)">
                            <option value="">参考情境未确认</option>
                            <option v-if="field.key === 'cd'" value="occupational_cadmium">已确认：职业镉生物监测</option>
                            <option v-if="field.key === 'hg'" value="occupational_mercury_stable">已确认：中长期较稳定职业汞接触</option>
                            <option v-if="field.key === 'rn'" value="residential_annual">已确认：住宅室内年平均</option>
                            <option value="other">其他情境／工作场所／瞬时（不自动套用）</option>
                          </select>
                          </label>
                          <button v-if="individualMetadata[field.key].confirmed === false" class="metadata-confirm" @click="confirmMetadata(field.key)">确认此数值的样本、单位与情境</button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p class="individual-caution">每项测量需独立注明样本与单位。改变口径不会换写原数字；已有数值须重新确认。年龄仅用于参考适用性，工种不自动确认职业监测情境。</p>
                  <div class="single-form-footer"><span><el-icon><Upload /></el-icon> LIS接口尚未接入 · 当前支持手动录入</span><button type="button" class="btn-clear" @click="clearIndividualInput">清空单人数据</button></div>
                </div>

                <div class="input-mode-section" v-if="formData.mode === 'batch'">
                  <div class="outcome-config-panel">
                    <div class="outcome-selector">
                      <span class="config-label">预测结局</span>
                      <el-select
                        v-model="selectedOutcomeId"
                        placeholder="请选择预测结局"
                        size="large"
                        :disabled="isAnalyzing || groupDemoRunning"
                        @change="handleOutcomeChange"
                      >
                        <el-option
                          v-for="item in outcomeOptions"
                          :key="item.id"
                          :label="item.name"
                          :value="item.id"
                        />
                      </el-select>
                      <p>{{ selectedOutcome?.description }}</p>
                    </div>
                    <div class="field-role-summary" v-if="selectedOutcome">
                      <div class="role-line">
                        <span class="role-title exposure">暴露因素</span>
                        <span v-for="item in selectedOutcome.exposures" :key="item.column" class="field-chip">
                          {{ item.label }} <small>{{ item.unit }}</small>
                        </span>
                      </div>
                      <div class="role-line">
                        <span class="role-title confounder">混杂因素</span>
                        <span v-for="item in selectedOutcome.confounders" :key="item.column" class="field-chip muted">
                          {{ item.label }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <section class="group-demo-panel" aria-label="NHANES公开数据一键体验">
                    <div class="group-demo-heading"><div><span class="group-demo-eyebrow">PUBLIC DATA · NHANES 2017–2018</span><h4>无需准备文件，体验真实公开数据</h4><p>{{ groupDemoInfo ? `${formatNumber(groupDemoInfo.rows)} 条真实成人记录 · 23 个规范字段 · 完整病例固定子集` : groupDemoLoading ? '正在核对服务器公开样本与来源说明…' : '公开样本尚未就绪，请检查后端服务。' }}</p></div><button type="button" class="btn-group-demo" :disabled="isAnalyzing || groupDemoRunning || !groupDemoInfo" @click="fillGroupDemo"><el-icon><DocumentChecked /></el-icon>{{ groupDemoRunning ? '正在载入并真实分析…' : '一键体验 NHANES 公开数据' }}</button></div>
                    <p class="group-demo-boundary">不是模拟数据，也不是职业人群；仅用于体验未加权描述性统计与数据流程，不用于总体风险推断或诊断。</p>
                    <details v-if="groupDemoInfo" class="group-demo-details"><summary>查看公开来源与筛选局限</summary><p>从 {{ formatNumber(groupDemoInfo.eligible_records) }} 条符合演示完整性条件的公开记录中，按 SEQN 升序固定选取 {{ formatNumber(groupDemoInfo.rows) }} 条；保留原转存值，未新增本地插补或缩尾，发布值可能含官方检测限替代。</p><ul><li v-for="(note, index) in groupDemoInfo.limitations" :key="index">{{ note }}</li></ul><div class="group-demo-sources"><a v-for="source in groupDemoInfo.source_links" :key="source.url" :href="source.url" target="_blank" rel="noopener noreferrer">{{ source.label }} ↗</a></div></details>
                    <p v-if="groupDemoError" class="group-demo-error" role="alert">{{ groupDemoError }} <button v-if="!groupDemoInfo" type="button" :disabled="groupDemoLoading || isAnalyzing" @click="loadGroupDemo">重新核对公开样本</button></p>
                  </section>
                  <section class="batch-format-guide" aria-label="群体数据格式说明">
                    <div class="format-guide-heading">
                      <div><h4>群体数据格式要求</h4><p>一行一人，第一行为列名；CSV / XLSX，不超过 25 MB。</p></div>
                      <button type="button" class="format-template-button" :disabled="!batchFormatSchema || batchFormatLoading" @click="downloadBatchTemplate">下载空白列名模板</button>
                    </div>
                    <ul>
                      <li>保留人员标识 SEQN、3 次收缩压与 3 次舒张压列头、5 项血液暴露及 8 项混杂因素。列名须与模板一致，缺失值留空。</li>
                      <li>血压单位 mmHg；血铅 μg/dL，其余 4 项血液暴露 μg/L。年龄单位为岁；分类变量采用原 NHANES 编码，不把“男 / 女”等文本直接当编码。</li>
                      <li>入组分析限定成人，收缩压与舒张压各至少 2 次有效读数。列头齐全不代表每行均可入组；可选调查设计列可保留。</li>
                    </ul>
                    <details class="format-field-details" v-if="batchFormatSchema">
                      <summary>查看 {{ batchFormatSchema.required_columns.length }} 个必需字段与可选字段</summary>
                      <div class="format-table-scroll"><table><thead><tr><th>含义</th><th>系统列名</th><th>单位 / 类型</th><th>要求</th></tr></thead><tbody><tr v-for="field in batchFormatSchema.fields" :key="field.column"><td>{{ field.label }}</td><td><code>{{ field.column }}</code></td><td>{{ field.unit || '—' }}</td><td>{{ field.required ? '必需列' : '可选列' }}</td></tr></tbody></table></div>
                    </details>
                    <p v-else class="format-schema-status">{{ batchFormatLoading ? '正在读取当前系统字段规范…' : batchFormatError || '字段规范尚未加载，请确认后端服务。' }}</p>
                    <div class="format-cleaning-entry"><span>原始表格列名、行列结构不符合要求？</span><NuxtLink to="/data-cleaning">前往数据清洗与格式转换 <span aria-hidden="true">→</span></NuxtLink></div>
                  </section>
                  <div v-if="batchImportError" class="batch-import-error" role="alert"><strong>本次文件未完成导入</strong><p>{{ batchImportError }}</p><NuxtLink to="/data-cleaning">先整理原始文件，再返回群体导入</NuxtLink></div>

                  <input
                    ref="fileInputRef"
                    class="hidden-file-input"
                    type="file"
                    accept=".csv,.xlsx"
                    :disabled="isAnalyzing || groupDemoRunning"
                    @change="handleFileChange"
                  />
                  <div
                    class="upload-dragger"
                    :class="{'has-file': hasFile}"
                    @dragover.prevent
                    @drop.prevent="handleFileDrop"
                  >
                    <el-icon class="upload-icon"><DocumentAdd /></el-icon>
                    <div v-if="!hasFile">
                      <div class="upload-text">拖拽群体监测数据至此 (支持 .csv / .xlsx)</div>
                      <div class="upload-hint">系统将按照“{{ selectedOutcome?.name || '所选结局' }}”自动校验结局、暴露与混杂因素字段</div>
                      <button class="btn-upload" type="button" :disabled="isAnalyzing || groupDemoRunning" @click="openFilePicker">选择本地文件</button>
                    </div>
                    <div v-else class="file-success">
                      <div class="upload-text"><el-icon style="vertical-align: middle; margin-right: 6px;"><DocumentChecked/></el-icon> {{ groupDemoSource ? groupDemoSource.sample_filename : selectedFile?.name }}</div>
                      <div v-if="groupDemoSource" class="group-demo-active">真实公开子样本 · NHANES {{ groupDemoSource.cycle }} · 非职业人群</div>
                      <div class="upload-hint success-text" v-if="uploadResult">
                        成功解析 {{ formatNumber(uploadResult.total_records) }} 条原始记录，成人有效分析队列 {{ formatNumber(uploadResult.analysis_records) }} 人。
                      </div>
                      <div class="upload-hint success-text" v-else>
                        文件大小 {{ formatFileSize(selectedFile?.size || 0) }}，等待启动真实数据分析。
                      </div>
                      <button class="btn-upload btn-reupload" type="button" :disabled="isAnalyzing || groupDemoRunning" @click="resetSelectedFile">重新上传</button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="reference-sidebar">
                <div class="ref-card" v-if="formData.mode === 'single'">
                  <h4><el-icon><InfoFilled /></el-icon> 对应情境参考比较</h4>
                  <p class="ref-desc">只匹配当前样本与单位。各来源含义不同，不是统一安全线、诊断或健康评分。</p>
                  <ul class="ref-list">
                    <li v-for="row in applicableReferenceRows" :key="row.key"><span class="metal">{{ row.label }}</span><span class="range individual-reference-status">{{ row.reference.value }} {{ row.reference.unit }}</span></li>
                  </ul>
                  <p v-if="!applicableReferenceRows.length" class="reference-empty">选择样本、单位和适用情境后，这里显示匹配的参考。未匹配的指标仍保留原始值。</p>
                  <details class="reference-details"><summary>查看全部指标与依据 <span>{{ individualProfile.rows.length }}项</span></summary>
                    <div v-for="row in individualProfile.rows" :key="row.key" class="individual-reference-note">
                      <strong>{{ row.label }}</strong>
                      <template v-if="row.reference"><a :href="row.reference.source" target="_blank" rel="noopener noreferrer">{{ row.reference.title }}</a><p>{{ row.reference.note }}</p></template>
                      <p v-else>{{ row.conditions.reference.reason }}</p>
                    </div>
                    <p class="ref-desc">资料核对日期 {{ REFERENCE_RETRIEVED_AT }}</p>
                  </details>
                </div>
                <div class="ref-card" v-else>
                  <h4><el-icon><InfoFilled /></el-icon> 群体导入检查</h4>
                  <p class="ref-desc">此处检查表格与分析条件，不使用单人页面的情境参考值作为群体安全线。</p>
                  <ul class="ref-list">
                    <li><span class="metal">必需字段</span><span>{{ batchFormatSchema?.required_columns.length ?? '待载入' }}</span></li>
                    <li><span class="metal">血压列头</span><span>收缩压 3列 + 舒张压 3列</span></li>
                    <li><span class="metal">年龄条件</span><span>≥ 18岁</span></li>
                    <li><span class="metal">有效血压读数</span><span>每类至少 2次</span></li>
                    <li><span class="metal">缺失数值</span><span>留空，不填零</span></li>
                  </ul>
                </div>
                
                <div class="action-card">
                  <h4>{{ formData.mode === 'single' ? '当前录入概览' : '生成群体特征分析' }}</h4>
                  <template v-if="formData.mode === 'single'">
                    <div class="input-progress"><strong>{{ individualProfile.counts.valid }}<small> / 10项</small></strong><span>有效录入</span><div class="input-progress-track"><i :style="{width: `${individualProfile.counts.valid * 10}%`}"></i></div></div>
                    <div class="input-summary"><span>可参考比较 <b>{{ individualProfile.counts.comparable }}项</b></span><span>待补 / 修正 <b>{{ individualProfile.counts.missing + individualProfile.counts.invalid }}项</b></span></div>
                    <p v-if="demoSource" class="demo-summary">{{ demoEdited ? '合成示例（已修改）' : '合成示例 · 演示数据' }}</p>
                    <p>在浏览器内生成可视化，不运行医疗预测模型。</p>
                  </template>
                  <p v-else>校验列名与有效队列条件，基于上传数据生成描述性统计与可视化；此步骤不运行医疗预测模型。</p>
                  <button class="btn-analyze" :class="{'is-loading': isAnalyzing}" :disabled="isAnalyzing || groupDemoRunning" @click="runAnalysis">
                    <span v-if="!isAnalyzing">{{ formData.mode === 'single' ? '生成单人可视化画像' : '启动特征可视化分析' }} ➔</span>
                    <span v-else>数据提取与处理中...</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="visualization-dashboard" v-if="showDashboard">
          
          <!-- 群体模式大屏 -->
          <div v-if="formData.mode === 'batch'" ref="groupDashboardRef" class="batch-dashboard-container animate-on-scroll is-visible">
            <div v-if="groupDemoSource" class="group-demo-dashboard-source"><strong>公开数据体验 · NHANES {{ groupDemoSource.cycle }} / {{ formatNumber(groupDemoSource.rows) }} 人固定子集</strong><span>BPXO 为振荡式血压方法比较研究；图表为未加权描述性统计，不代表职业人群或美国总体。图中血压组别按当前平均读数划分，不是临床诊断。</span></div>
            
            <div class="kpi-row">
              <div class="kpi-card total"><el-icon class="kpi-icon"><Avatar /></el-icon><div class="kpi-info"><span>成人有效分析队列</span><strong>{{ formatNumber(analysisData?.kpis.analysis_records) }}<small> / {{ formatNumber(analysisData?.kpis.total_records) }} 人</small></strong></div></div>
              <div class="kpi-card male"><el-icon class="kpi-icon"><Male /></el-icon><div class="kpi-info"><span>男性占比</span><strong>{{ formatNumber(analysisData?.kpis.male_count) }}<small> 人 ({{ analysisData?.kpis.male_ratio }}%)</small></strong></div></div>
              <div class="kpi-card female"><el-icon class="kpi-icon"><Female /></el-icon><div class="kpi-info"><span>女性占比</span><strong>{{ formatNumber(analysisData?.kpis.female_count) }}<small> 人 ({{ analysisData?.kpis.female_ratio }}%)</small></strong></div></div>
              <div class="kpi-card ready"><el-icon class="kpi-icon"><CircleCheckFilled /></el-icon><div class="kpi-info"><span>平均收缩压 / 舒张压</span><strong>{{ analysisData?.kpis.mean_sbp }} / {{ analysisData?.kpis.mean_dbp }}<small> mmHg</small></strong></div></div>
            </div>

            <details v-if="groupDemoSource && analysisData?.metadata.warnings?.length" class="analysis-notes-details">
              <summary>查看处理说明、PCA 缺失处理与公开数据局限（{{ analysisData.metadata.warnings.length }} 项）</summary>
              <div class="analysis-notes"><span v-for="note in analysisData.metadata.warnings" :key="note"><el-icon><InfoFilled /></el-icon>{{ note }}</span></div>
            </details>
            <div class="analysis-notes" v-if="!groupDemoSource && analysisData?.metadata.warnings?.length">
              <span v-for="note in analysisData.metadata.warnings" :key="note"><el-icon><InfoFilled /></el-icon>{{ note }}</span>
            </div>

            <!-- 人口学特征统计行 -->
            <div class="batch-charts-grid demographic-row">

              <!-- 婚姻状况 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>婚姻状况分布 (Marital Status)</h4>
                  <span class="sub-title">统计群体婚姻结构，评估家庭因素对职业暴露易感性的潜在修饰效应。</span>
                </div>
                <div id="batchChartMarital" class="b-c-canvas"></div>
              </div>

              <!-- 文化程度 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>文化程度构成 (Education Level)</h4>
                  <span class="sub-title">呈现群体受教育水平分布，分析文化程度与防护认知、健康素养的关联。</span>
                </div>
                <div id="batchChartEducation" class="b-c-canvas"></div>
              </div>

              <!-- 家庭年收入 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>家庭收入贫困比分布 (Income-to-Poverty Ratio)</h4>
                  <span class="sub-title">按家庭收入贫困比及性别呈现经济水平分层，作为血压分析的混杂因素之一。</span>
                </div>
                <div id="batchChartIncome" class="b-c-canvas"></div>
              </div>

            </div>

            <!-- 图表矩阵: 3 列 x 3 行 -->
            <div class="batch-charts-grid">

              <!-- 图表 1 (占 2 列) -->
              <div class="b-chart-card col-span-2">
                <div class="b-c-header">
                  <h4>特征共线性矩阵 (Correlation Heatmap)</h4>
                  <span class="sub-title">呈现暴露因子间的相关程度，辅助识别具有高度协同作用的复合暴露组合。</span>
                </div>
                <div id="batchChartCorr" class="b-c-canvas"></div>
              </div>

              <!-- 图表 2 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>核心暴露分布四分位数 (Quartiles)</h4>
                  <span class="sub-title">展示5项血中暴露指标的Q1、中位数和Q3，数值与单位均来自上传数据。</span>
                </div>
                <div id="batchChartQuartile" class="b-c-canvas"></div>
              </div>

              <!-- 图表 3 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>特征分布与异常离群点 (Boxplot)</h4>
                  <span class="sub-title">评估各项指标的分布离散度，定位偏离整体分布的极端高值个体以供重点复查。</span>
                </div>
                <div id="batchChartBoxplot" class="b-c-canvas"></div>
              </div>

              <!-- 图表 4 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>主成分降维特征聚类 (PCA Projection)</h4>
                  <span class="sub-title">将标准化后的5项暴露指标投影至二维空间，并按140/90 mmHg血压状态分组。</span>
                </div>
                <div id="batchChartPCA" class="b-c-canvas"></div>
              </div>

              <!-- 图表 5 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>数据完整度与缺失评估 (Completeness)</h4>
                  <span class="sub-title">统计上传文件中各暴露字段的有效数值与缺失比例，评估真实数据源质量。</span>
                </div>
                <div id="batchChartMissing" class="b-c-canvas"></div>
              </div>

              <!-- 图表 6 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>核密度平滑分布 (Density Smooth)</h4>
                  <span class="sub-title">将不同量纲暴露指标标准化后进行密度估计，比较人群分布形态。</span>
                </div>
                <div id="batchChartDensity" class="b-c-canvas"></div>
              </div>

              <!-- 图表 7 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>群体暴露浓度频数分布 (Concentration Histogram)</h4>
                  <span class="sub-title">按浓度区间统计群体样本频数，直观呈现各重金属的分布偏态与集中趋势。</span>
                </div>
                <div id="batchChartParallel" class="b-c-canvas"></div>
              </div>

              <!-- 图表 8 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>年龄-血压-暴露水平画像 (Bubble)</h4>
                  <span class="sub-title">横轴为年龄、纵轴为平均收缩压，气泡面积反映5项暴露指标的综合百分位。</span>
                </div>
                <div id="batchChartBubble" class="b-c-canvas"></div>
              </div>
              
            </div>
          </div>

          <!-- 单人模式科研图表 -->
          <div v-else ref="singleDashboardRef" class="single-dashboard-container animate-on-scroll is-visible">
            <div class="single-results-heading"><div><span class="eyebrow">VISUAL INSIGHTS</span><h2>单人数据可视化画像</h2><p>修改输入后图表实时更新 · {{ individualProfile.counts.valid }}项有效录入 / {{ individualProfile.counts.comparable }}项可比较</p></div><span v-if="demoSource" class="demo-badge">{{ demoEdited ? '合成示例 · 已修改' : '合成示例 · 非真实数据' }}</span></div>
            <div class="b-chart-card mb-6" style="padding-bottom: 0;">
              <div class="b-c-header">
                <h4>个体多维暴露全景画像 (Relative Exposure Index)</h4>
                <span class="sub-title">仅对样本、单位及情境匹配的指标计算实测值／该参考值。100%表示参考值，不表示安全或诊断。</span>
              </div>
              <div id="singleChartMaster" style="width: 100%; height: 350px;"></div>
            </div>

            <div class="batch-charts-grid" style="margin-top: 24px;">
              
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>参考占比雷达图 (Radar)</h4>
                  <span class="sub-title">采用与主图相同的比例尺度；至少3项可比较指标才绘制，不以零填补缺失。</span>
                </div>
                <div id="singleChartRadar" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>参考可比性条件矩阵 (Heatmap)</h4>
                  <span class="sub-title">可=条件满足，空=未提供，×=不匹配，待=口径确认。完整原因见提示；蓝灰状态不是医疗风险或安全信号。</span>
                </div>
                <div id="singleChartTimeline" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>参考占比排序 (Reference Ratio)</h4>
                  <span class="sub-title">按各自参考占比排列，仅为描述性排序，不是群体百分位或跨指标毒性排名。</span>
                </div>
                <div id="singleChartPercentile" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>指标录入状态分布 (Input Status)</h4>
                  <span class="sub-title">内环统计有效、缺失及非法输入，外环每项代表一个指标；计数不是人数或器官归因。</span>
                </div>
                <div id="singleChartRiskPie" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>相对参考值偏移 (Reference Offset)</h4>
                  <span class="sub-title">计算（实测值／参考值−1）×100%；不是Z-score、群体标准差或模型特征贡献。</span>
                </div>
                <div id="singleChartZScore" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>已录入可比较覆盖率 (Coverage)</h4>
                  <span class="sub-title">可比较指标数／有效录入指标数；只反映参考适用覆盖率，不合成医疗综合分。</span>
                </div>
                <div id="singleChartAnomaly" class="b-c-canvas"></div>
              </div>

            </div>
          </div>
          
          <div class="bottom-action-bar">
            <div class="tips">
              <el-icon><CircleCheckFilled /></el-icon>
              <template v-if="formData.mode === 'single'">单次实测画像已生成，{{ individualProfile.counts.comparable }} 项可比较；未计算趋势、相关性、医学风险或因果效应。</template>
              <template v-else>已生成群体描述性统计。真实指标估计另需年龄、性别、BMI及三种全血金属；缺失必需字段会提示，不自动补值。</template>
            </div>
            <button class="btn-next-step" @click="goToRiskWarning">
              携带当前数据进入风险分析 ➔
            </button>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderBatchAnalysisCharts } from '~/composables/useBatchAnalysisCharts'
import { buildIndividualProfile, parseMeasurement } from '~/utils/individualProfile'
import { MEASUREMENTS, SAMPLE_OPTIONS, UNIT_OPTIONS, REFERENCE_RETRIEVED_AT, createIndividualMetadata } from '~/utils/individualReferences'
import { createIndividualDemo } from '~/utils/individualDemo'
import { 
  Coin, DataLine, TrendCharts, Share, DocumentChecked, Upload, DocumentAdd,
  CircleCheckFilled, InfoFilled, ArrowLeft, Male, Female, Avatar
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const currentStep = ref(1)
const { getOutcomeConfigs, uploadBatchData, getDatasetAnalysis, getCleaningSchema, getGroupDemo, importGroupDemo } = useApi()

const createEmptySingleData = () => ({
    name: '', gender: '', age: null, workYears: null,
    pb: null, cd: null, hg: null, th: null, li: null, cr: null, ni: null, co: null, as: null, rn: null,
    education: '', marital: '', smoking: '', drinking: '', bmi: null, ppe: '', history: ''
})
const formData = ref({
  job: 'smelting', mode: 'batch', singleData: createEmptySingleData()
})

const individualMetadata = ref(createIndividualMetadata())
const individualGenderConfirmed = ref(false)
const predictionState = usePredictionState()
const individualProfile = computed(() => buildIndividualProfile(formData.value.singleData, individualMetadata.value))
const applicableReferenceRows = computed(() => individualProfile.value.rows.filter(row => row.reference && row.metadata.confirmed !== false))
const measurementRow = (key) => individualProfile.value.rows.find(row => row.key === key)
const singleDashboardRef = ref(null)
const demoSource = ref(false)
const demoSnapshot = ref('')
const individualSnapshot = () => JSON.stringify({ job: formData.value.job, singleData: formData.value.singleData, metadata: individualMetadata.value, genderConfirmed: individualGenderConfirmed.value })
const demoEdited = computed(() => demoSource.value && individualSnapshot() !== demoSnapshot.value)
const hasIndividualInput = computed(() => {
  const empty = createEmptySingleData()
  return individualGenderConfirmed.value || Object.entries(formData.value.singleData).some(([key, value]) => value !== empty[key]) ||
    JSON.stringify(individualMetadata.value) !== JSON.stringify(createIndividualMetadata())
})
const confirmInputReplacement = async (action) => {
  if (!hasIndividualInput.value) return true
  try {
    await ElMessageBox.confirm(`${action}会替换当前单人档案和测量口径。当前内容尚未保存，是否继续？`, '确认替换单人数据', {
      confirmButtonText: '确认替换', cancelButtonText: '保留当前数据', type: 'warning', closeOnClickModal: false
    })
    return true
  } catch { return false }
}
const fillIndividualDemo = async () => {
  if (demoSource.value && !demoEdited.value) {
    await runAnalysis()
    return
  }
  if (!await confirmInputReplacement('填入合成示例')) return
  const demo = createIndividualDemo()
  formData.value.job = demo.job
  formData.value.singleData = demo.singleData
  individualMetadata.value = demo.metadata
  individualGenderConfirmed.value = true // Explicit synthetic fixture, not a default for real records.
  demoSnapshot.value = individualSnapshot()
  demoSource.value = true
  await runAnalysis()
  ElMessage.success('已填入合成示例并生成画像；非真实人员检测记录。')
}
const clearIndividualInput = async () => {
  if (!await confirmInputReplacement('清空')) return
  disposeSingleCharts()
  formData.value.singleData = createEmptySingleData()
  individualMetadata.value = createIndividualMetadata()
  individualGenderConfirmed.value = false
  demoSource.value = false
  demoSnapshot.value = ''
  showDashboard.value = false
  currentStep.value = 1
}
const individualGroups = [
  { id: 'core', title: '元素实测指标 (8种)', fields: MEASUREMENTS.slice(0, 8) },
  { id: 'companion', title: '伴生元素与环境指标', fields: MEASUREMENTS.slice(8) }
]
const sampleLabel = (sample) => SAMPLE_OPTIONS.find(item => item.value === sample)?.label || '样本未指定'
const rawMeasurement = (row) => row.raw === null || row.raw === undefined || row.raw === '' ? '未录入' : String(row.raw)
const handleMetadataChange = (key) => {
  // Never rewrite or reinterpret the measured number after changing its metadata.
  if (parseMeasurement(formData.value.singleData[key]).state === 'valid') {
    individualMetadata.value[key].confirmed = false
    ElMessage.info('原数字未改变。请核对并确认此数值的样本、单位及适用情境。')
  }
}
const handleMeasurementInput = (key) => {
  if (parseMeasurement(formData.value.singleData[key]).state === 'missing') individualMetadata.value[key].confirmed = true
}
const confirmMetadata = (key) => { individualMetadata.value[key].confirmed = true }

const outcomeOptions = ref([
  {
    id: 'blood_pressure',
    name: '血压（连续结局）',
    description: '分别分析平均收缩压和平均舒张压，限定18岁及以上且两类血压均至少有2次有效读数的人群。',
    exposures: [
      { column: 'PBCD_J__LBXBPB', label: 'Pb 血铅', unit: 'μg/dL' },
      { column: 'PBCD_J__LBXBCD', label: 'Cd 血镉', unit: 'μg/L' },
      { column: 'PBCD_J__LBXTHG', label: 'Hg 总汞', unit: 'μg/L' },
      { column: 'PBCD_J__LBXBSE', label: 'Se 血硒', unit: 'μg/L' },
      { column: 'PBCD_J__LBXBMN', label: 'Mn 血锰', unit: 'μg/L' }
    ],
    confounders: [
      { column: 'DEMO_J__RIDAGEYR', label: '年龄' },
      { column: 'DEMO_J__RIAGENDR', label: '性别' },
      { column: 'DEMO_J__RIDRETH3', label: '种族/族裔' },
      { column: 'DEMO_J__DMDEDUC2', label: '教育程度' },
      { column: 'DEMO_J__DMDMARTL', label: '婚姻状况' },
      { column: 'DEMO_J__INDFMPIR', label: '家庭收入贫困比' },
      { column: 'SMQ_J__SMQ020', label: '终生吸烟 ≥100支' },
      { column: 'ALQ_J__ALQ111', label: '终生曾饮酒 ≥1杯' }
    ]
  }
])
const selectedOutcomeId = ref('blood_pressure')
const selectedOutcome = computed(() =>
  outcomeOptions.value.find(item => item.id === selectedOutcomeId.value)
)
const batchFormatSchema = ref(null)
const batchFormatLoading = ref(false)
const batchFormatError = ref('')
const batchImportError = ref('')
let formatRequestVersion = 0
const loadBatchFormat = async () => {
  const version = ++formatRequestVersion
  batchFormatSchema.value = null
  batchFormatError.value = ''
  batchFormatLoading.value = true
  try {
    const result = await getCleaningSchema(selectedOutcomeId.value)
    if (version !== formatRequestVersion) return
    if (result.success) batchFormatSchema.value = result.data
    else batchFormatError.value = result.error || '无法读取字段规范。'
  } catch { if (version === formatRequestVersion) batchFormatError.value = '无法读取字段规范，请检查后端服务。' }
  finally { if (version === formatRequestVersion) batchFormatLoading.value = false }
}
const downloadBatchTemplate = () => {
  if (!batchFormatSchema.value) return
  // Column headers only: no invented patients, measurements or categorical codes.
  const columns = batchFormatSchema.value.required_columns
  const csv = '\uFEFF' + columns.map(column => '"' + String(column).replace(/"/g, '""') + '"').join(',') + '\r\n'
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `group_${selectedOutcomeId.value}_columns.csv`
  link.click()
  URL.revokeObjectURL(url)
}
watch(selectedOutcomeId, loadBatchFormat)
const fileInputRef = ref(null)
const selectedFile = ref(null)
const hasFile = computed(() => Boolean(selectedFile.value || groupDemoSource.value))
const uploadResult = ref(null)
const analysisData = ref(null)
const isAnalyzing = ref(false)
const showDashboard = ref(false)

// PUBLIC_GROUP_DEMO_START: fixed server-side public records, not synthetic form values.
const groupDemoInfo = ref(null)
const groupDemoSource = ref(null)
const groupDemoLoading = ref(false)
const groupDemoRunning = ref(false)
const groupDemoError = ref('')
const groupDashboardRef = ref(null)
const loadGroupDemo = async () => {
  groupDemoLoading.value = true
  groupDemoError.value = ''
  try {
    const response = await getGroupDemo()
    if (response.success) groupDemoInfo.value = response.data
    else { groupDemoInfo.value = null; groupDemoError.value = response.error || '服务器公开样本暂不可用。' }
  } catch { groupDemoInfo.value = null; groupDemoError.value = '无法读取公开样本来源，请检查后端服务。' }
  finally { groupDemoLoading.value = false }
}
const fillGroupDemo = async () => {
  if (isAnalyzing.value || groupDemoRunning.value || !groupDemoInfo.value) return
  groupDemoRunning.value = true
  groupDemoError.value = ''
  let committed = false
  try {
    if (selectedFile.value || uploadResult.value || analysisData.value || groupDemoSource.value) {
      try {
        await ElMessageBox.confirm('公开样本分析成功后，将替换当前群体输入与图表展示；已有服务器分析记录不会删除。是否继续？', '切换到公开数据体验', {
          confirmButtonText: '使用公开样本', cancelButtonText: '保留当前数据', type: 'warning', closeOnClickModal: false
        })
      } catch { return }
    }
    isAnalyzing.value = true
    const response = await importGroupDemo()
    if (!response.success) { groupDemoError.value = response.error || '公开样本载入失败；当前数据未被替换。'; return }
    const payload = response.data
    if (!payload?.import_result?.file_id || !payload?.analysis?.kpis || !payload?.provenance?.id) {
      groupDemoError.value = '公开样本响应不完整；当前输入和图表已保留。'
      return
    }
    // Commit only after the genuine import+analysis has succeeded; preserve old input on any failure.
    selectedFile.value = null
    selectedOutcomeId.value = payload.import_result.outcome_id
    uploadResult.value = payload.import_result
    analysisData.value = payload.analysis
    groupDemoSource.value = payload.provenance
    committed = true
    batchImportError.value = ''
    showDashboard.value = true
    currentStep.value = 2
    await nextTick()
    initBatchECharts()
    groupDashboardRef.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
    ElMessage.success(`已载入 ${formatNumber(payload.import_result.analysis_records)} 人的 NHANES 公开子样本；不是模拟记录。`)
  } catch { groupDemoError.value = committed ? '公开样本已载入，但图表渲染失败；请刷新页面或检查浏览器。' : '公开样本分析请求失败；当前输入和已有效分析未被替换。' }
  finally { isAnalyzing.value = false; groupDemoRunning.value = false }
}
// PUBLIC_GROUP_DEMO_END

const activeFilter = ref('all')
const toggleFilter = (status) => { activeFilter.value = activeFilter.value === status ? 'all' : status }

const handleModeChange = (mode) => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  if (formData.value.mode === 'single') disposeSingleCharts()
  formData.value.mode = mode
  showDashboard.value = false
}

const formatNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '--'
  return Number(value).toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const openFilePicker = () => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  fileInputRef.value?.click()
}

const setSelectedFile = (file) => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  if (!file) return
  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!['csv', 'xlsx'].includes(extension)) {
    ElMessage.error('仅支持 CSV 或 XLSX 文件；旧 XLS 文件请先另存为 XLSX')
    return
  }
  if (file.size > 25 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 25 MB')
    return
  }
  selectedFile.value = file
  groupDemoSource.value = null
  batchImportError.value = ''
  uploadResult.value = null
  analysisData.value = null
  showDashboard.value = false
  currentStep.value = 1
}

const handleFileChange = (event) => {
  setSelectedFile(event.target.files?.[0])
}

const handleFileDrop = (event) => {
  setSelectedFile(event.dataTransfer?.files?.[0])
}

const resetSelectedFile = () => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  groupDemoSource.value = null
  batchImportError.value = ''
  selectedFile.value = null
  uploadResult.value = null
  analysisData.value = null
  showDashboard.value = false
  currentStep.value = 1
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const handleOutcomeChange = () => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  groupDemoSource.value = null
  batchImportError.value = ''
  uploadResult.value = null
  analysisData.value = null
  showDashboard.value = false
  currentStep.value = 1
}

const loadOutcomeConfigs = async () => {
  const result = await getOutcomeConfigs()
  if (result.success && Array.isArray(result.data) && result.data.length) {
    outcomeOptions.value = result.data
    if (!result.data.some(item => item.id === selectedOutcomeId.value)) {
      selectedOutcomeId.value = result.data[0].id
    }
  }
}

const runAnalysis = async () => {
  if (isAnalyzing.value || groupDemoRunning.value) return
  if (formData.value.mode === 'batch' && groupDemoSource.value && analysisData.value) {
    showDashboard.value = true
    currentStep.value = 2
    await nextTick()
    initBatchECharts()
    window.scrollTo({ top: 800, behavior: 'smooth' })
    return
  }
  if (formData.value.mode === 'batch' && !hasFile.value) {
    ElMessage.warning('请先上传群体数据文件')
    return
  }

  if (formData.value.mode === 'batch') {
    isAnalyzing.value = true
    batchImportError.value = ''
    showDashboard.value = false
    try {
      const upload = await uploadBatchData(selectedFile.value, selectedOutcomeId.value)
      if (!upload.success) {
        const missing = upload.details?.missing_columns || []
        const missingMessage = missing.length
          ? `；缺少字段：${missing.join('、')}`
          : ''
        batchImportError.value = `${upload.error}${missingMessage}`
        ElMessage.error(batchImportError.value)
        return
      }

      uploadResult.value = upload.data
      const analysis = await getDatasetAnalysis(upload.data.file_id)
      if (!analysis.success) {
        batchImportError.value = analysis.error || '统计分析结果获取失败'
        ElMessage.error(analysis.error || '统计分析结果获取失败')
        return
      }

      analysisData.value = analysis.data
      showDashboard.value = true
      currentStep.value = 2
      ElMessage.success(`已完成 ${formatNumber(upload.data.analysis_records)} 人的真实数据分析`)
      await nextTick()
      initBatchECharts()
      window.scrollTo({ top: 800, behavior: 'smooth' })
    } catch (error) {
      batchImportError.value = '群体数据分析失败，请检查后端服务和上传文件。'
      console.error('群体数据分析失败:', error)
      ElMessage.error('群体数据分析失败，请检查后端服务和上传文件')
    } finally {
      isAnalyzing.value = false
    }
    return
  }

  showDashboard.value = true
  currentStep.value = 2
  await nextTick()
  initSingleECharts()
  if (individualProfile.value.counts.invalid) ElMessage.warning('存在非法输入；已保留原值，但不参与参考比较。')
  singleDashboardRef.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
}

const goToRiskWarning = async () => {
  predictionState.invalidate()
  if (formData.value.mode === 'batch') {
    if (!uploadResult.value?.file_id) {
      ElMessage.warning('请先成功导入群体数据；不能用页面示例代替真实数据文件。')
      return
    }
    predictionState.batchIntake.value = { file_id: uploadResult.value.file_id, filename: uploadResult.value.filename }
    currentStep.value = 3
    await navigateTo('/risk?mode=batch')
    return
  }
  const person = formData.value.singleData
  const number = (value) => parseMeasurement(value).value
  predictionState.batchIntake.value = null
  predictionState.setIntake({
    person: { id: person.name || '', age: number(person.age), gender: person.gender || null,
      gender_confirmed: individualGenderConfirmed.value, bmi: number(person.bmi),
      pb: number(person.pb), cd: number(person.cd), hg: number(person.hg) },
    measurements: Object.fromEntries(['pb', 'cd', 'hg'].map(key => [key, {
      sample: individualMetadata.value[key].sample, unit: individualMetadata.value[key].unit,
      analyte: key === 'pb' ? 'lead' : key === 'cd' ? 'cadmium' : individualMetadata.value.hg.analyte,
      confirmed: individualMetadata.value[key].confirmed,
    }])),
    // Old education/frequency labels do not define the training categories.
    covariates: { education: null, marital: null, smoking: null, alcohol_any_past_year: null },
  })
  currentStep.value = 3
  await navigateTo('/risk?mode=individual')
}

const goToHome = async () => {
  await navigateTo('/')
}

let batchCharts = []

const initBatchECharts = () => {
  batchCharts.forEach(chart => chart.dispose())
  batchCharts = renderBatchAnalysisCharts(analysisData.value, echarts)
}

/* 已停用的静态群体图表实现（保留历史视觉参数，运行时不再执行）
  batchCharts.forEach(c => c.dispose())
  batchCharts = []

  // 1. 共线性矩阵 (Heatmap)
  const domCorr = document.getElementById('batchChartCorr')
  if (domCorr) {
    const chartCorr = echarts.init(domCorr)
    const corrData = [
      [0,0, 1.00], [0,1, 0.45], [0,2, 0.62], [0,3, 0.15], [0,4, 0.22],
      [1,0, 0.45], [1,1, 1.00], [1,2, 0.38], [1,3, 0.11], [1,4, 0.28],
      [2,0, 0.62], [2,1, 0.38], [2,2, 1.00], [2,3, 0.33], [2,4, 0.19],
      [3,0, 0.15], [3,1, 0.11], [3,2, 0.33], [3,3, 1.00], [3,4, 0.41],
      [4,0, 0.22], [4,1, 0.28], [4,2, 0.19], [4,3, 0.41], [4,4, 1.00]
    ]
    chartCorr.setOption({
      tooltip: { position: 'top', formatter: (p) => `Pearson(r): ${p.data[2]}` },
      grid: { left: '10%', right: '5%', top: '5%', bottom: '15%' },
      xAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisLine: {show: false}, axisTick: {show: false} },
      yAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisLine: {show: false}, axisTick: {show: false} },
      visualMap: { 
        min: 0, max: 1, calculable: true, orient: 'horizontal', 
        left: 'center', bottom: '0%', itemWidth: 12, itemHeight: 120, 
        inRange: { color: ['#F8FAFC', '#93C5FD', '#1E3A8A'] }, show: false 
      },
      series: [{ 
        type: 'heatmap', data: corrData, 
        label: { show: true, color: '#fff', fontWeight: 'bold' }, 
        itemStyle: { borderWidth: 2, borderColor: '#fff', borderRadius: 4 } 
      }]
    })
    batchCharts.push(chartCorr)
  }

  // 2. 四分位数分布 (Bar)
  const domQuartile = document.getElementById('batchChartQuartile')
  if (domQuartile) {
    const chartQuartile = echarts.init(domQuartile)
    chartQuartile.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: ['Q1 (<25%)', 'Q2 (中位)', 'Q3 (75%)', 'Q4 (极端)'], axisLabel: { fontSize: 11, fontWeight: 'bold' }, axisTick: {show: false} },
      yAxis: { type: 'value', name: '样本分布数量', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        name: '样本数', type: 'bar', barWidth: '45%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3B82F6' }, { offset: 1, color: '#93C5FD' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        label: { show: true, position: 'top', fontWeight: 'bold', color: '#1E3A8A' },
        data: [312, 450, 280, 203]
      }]
    })
    batchCharts.push(chartQuartile)
  }

  // 3. 异常值检测 (Boxplot)
  const domBoxplot = document.getElementById('batchChartBoxplot')
  if (domBoxplot) {
    const chartBoxplot = echarts.init(domBoxplot)
    chartBoxplot.setOption({
      tooltip: { trigger: 'item', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisTick: {show: false}, axisLabel: {fontWeight: 'bold'} },
      yAxis: { type: 'value', name: 'Z-Score 浓度', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: '分布范围', type: 'boxplot',
          itemStyle: { color: '#EFF6FF', borderColor: '#3B82F6', borderWidth: 2 },
          data: [
            [-1.2, -0.5, 0.2, 0.8, 2.5],
            [-0.8, -0.2, 0.4, 1.1, 3.2],
            [-1.5, -0.6, 0.1, 0.9, 2.1],
            [-0.9, -0.3, 0.3, 0.7, 1.8],
            [-1.0, -0.4, 0.0, 0.5, 1.5]
          ]
        },
        {
          name: '极端离群点', type: 'scatter',
          itemStyle: { color: '#EF4444' },
          data: [ [0, 3.1], [0, 3.5], [1, 4.2], [1, 4.5], [2, 2.8], [3, 2.5] ]
        }
      ]
    })
    batchCharts.push(chartBoxplot)
  }

  // 4. PCA 主成分降维投影 (Scatter)
  const domPCA = document.getElementById('batchChartPCA')
  if (domPCA) {
    const chartPCA = echarts.init(domPCA)
    const dataCluster1 = Array.from({length: 40}, () => [Math.random()*10 - 5, Math.random()*10 - 5]);
    const dataCluster2 = Array.from({length: 30}, () => [Math.random()*8 + 2, Math.random()*8 + 3]);
    chartPCA.setOption({
      tooltip: { trigger: 'item', formatter: 'PC1: {c[0]}<br/>PC2: {c[1]}' },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', name: 'PC1 (45%)', scale: true, splitLine: { show: false } },
      yAxis: { type: 'value', name: 'PC2 (22%)', scale: true, splitLine: { show: false } },
      series: [
        { type: 'scatter', name: '健康本底组', data: dataCluster1, itemStyle: { color: '#10B981', opacity: 0.6 } },
        { type: 'scatter', name: '高暴露风险组', data: dataCluster2, itemStyle: { color: '#EF4444', opacity: 0.6 } }
      ]
    })
    batchCharts.push(chartPCA)
  }

  // 5. 缺失值与检出率占比 (Stacked Bar)
  const domMissing = document.getElementById('batchChartMissing')
  if (domMissing) {
    const chartMissing = echarts.init(domMissing)
    chartMissing.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: ['Cr', 'Hg', 'As', 'Cd', 'Pb'], axisTick: {show: false}, axisLabel: {fontWeight: 'bold'} },
      series: [
        { name: '有效检出', type: 'bar', stack: 'total', barWidth: '40%', itemStyle: { color: '#34D399', borderRadius: [0,0,0,0] }, label: { show: true, position: 'insideRight', formatter: '{c}%', color: '#fff' }, data: [88, 76, 92, 85, 98] },
        { name: '低于LOD/缺失', type: 'bar', stack: 'total', barWidth: '40%', itemStyle: { color: '#FCA5A5', borderRadius: [0,4,4,0] }, data: [12, 24, 8, 15, 2] }
      ]
    })
    batchCharts.push(chartMissing)
  }

  // 6. 暴露浓度“偏科”纠正 (Density Area Line)
  const domDensity = document.getElementById('batchChartDensity')
  if (domDensity) {
    const chartDensity = echarts.init(domDensity)
    const xData = Array.from({length: 50}, (_, i) => i);
    const yBefore = xData.map(x => Math.exp(-Math.pow(x - 10, 2) / 20) * 100 + Math.random()*5);
    const yAfter = xData.map(x => Math.exp(-Math.pow(x - 25, 2) / 100) * 60);
    chartDensity.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: xData, show: false },
      yAxis: { type: 'value', name: '数据密度', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        { name: '处理前', type: 'line', smooth: true, symbol: 'none', data: yBefore, itemStyle: { color: '#EF4444' }, areaStyle: { opacity: 0.2 } },
        { name: '处理后', type: 'line', smooth: true, symbol: 'none', data: yAfter, itemStyle: { color: '#3B82F6' }, areaStyle: { opacity: 0.4 } }
      ]
    })
    batchCharts.push(chartDensity)
  }

  // 7. 群体暴露浓度频数分布 (Histogram)
  const domParallel = document.getElementById('batchChartParallel')
  if (domParallel) {
    const chartParallel = echarts.init(domParallel)
    const bins = ['0-20', '20-40', '40-60', '60-80', '80-100', '100-150', '150-200', '200-300', '300+']
    const pbFreq  = [68, 195, 312, 278, 186, 112, 58, 28, 8]
    const asFreq  = [124, 248, 305, 241, 158, 98, 48, 18, 5]
    chartParallel.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function (params) {
          let res = params[0].axisValue + ' μg/L<br/>'
          params.forEach(p => { res += `${p.marker} ${p.seriesName}: ${p.value} 人<br/>` })
          return res
        }
      },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '18%' },
      xAxis: {
        type: 'category',
        data: bins,
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 10, rotate: 30 }
      },
      yAxis: { type: 'value', name: '样本数 (人)', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: 'Pb (铅)', type: 'bar', barWidth: '35%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#60A5FA' }, { offset: 1, color: '#3B82F6' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          data: pbFreq
        },
        {
          name: 'As (砷)', type: 'bar', barWidth: '35%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#A7F3D0' }, { offset: 1, color: '#10B981' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          data: asFreq
        }
      ]
    })
    batchCharts.push(chartParallel)
  }

  // 8. 工龄-年龄-毒素累积画像 (Bubble Scatter)
  const domBubble = document.getElementById('batchChartBubble')
  if (domBubble) {
    const chartBubble = echarts.init(domBubble)
    const bubbleData = [
      [25, 2, 15], [30, 5, 25], [35, 8, 40], [42, 15, 65], [48, 20, 85], [55, 25, 110],
      [28, 4, 20], [38, 12, 55], [45, 18, 75], [52, 22, 95], [58, 28, 130]
    ]
    chartBubble.setOption({
      tooltip: { formatter: (p) => `年龄: ${p.data[0]}岁<br/>工龄: ${p.data[1]}年<br/>特征指数: ${p.data[2]}` },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', name: '年龄 (岁)', splitLine: { show: false } },
      yAxis: { type: 'value', name: '工龄 (年)', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        type: 'scatter',
        data: bubbleData,
        symbolSize: function (data) { return Math.max(data[2] / 3, 10); }, 
        itemStyle: {
          color: function(params) { return params.data[2] > 70 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)'; },
          borderColor: '#fff', borderWidth: 1
        }
      }]
    })
    batchCharts.push(chartBubble)
  }

  // ========== 人口学特征统计图表 ==========

  // D1. 婚姻状况分布 (Pie)
  const domMarital = document.getElementById('batchChartMarital')
  if (domMarital) {
    const chartMarital = echarts.init(domMarital)
    chartMarital.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
      legend: { orient: 'horizontal', bottom: '2%', itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 12, fontWeight: 600 } },
      series: [{
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
        label: { show: true, formatter: '{b}\n{d}%', fontWeight: 'bold', fontSize: 12 },
        labelLine: { show: true, length: 8, length2: 12 },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' }
        },
        data: [
          { value: 682, name: '已婚', itemStyle: { color: '#3B82F6' } },
          { value: 327, name: '未婚', itemStyle: { color: '#10B981' } },
          { value: 158, name: '离异', itemStyle: { color: '#F59E0B' } },
          { value: 78,  name: '丧偶', itemStyle: { color: '#8B5CF6' } }
        ]
      }]
    })
    batchCharts.push(chartMarital)
  }

  // D2. 文化程度构成 (Horizontal Bar)
  const domEducation = document.getElementById('batchChartEducation')
  if (domEducation) {
    const chartEducation = echarts.init(domEducation)
    chartEducation.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '22%', right: '10%', bottom: '10%', top: '10%' },
      xAxis: { type: 'value', name: '人数', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: {
        type: 'category',
        data: ['小学及以下', '初中', '高中/中专', '大专', '本科', '硕士及以上'],
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 12 }
      },
      series: [{
        type: 'bar',
        barWidth: '50%',
        data: [
          { value: 86,  itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FCA5A5' }, { offset: 1, color: '#EF4444' }]) } },
          { value: 312, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FCD34D' }, { offset: 1, color: '#F59E0B' }]) } },
          { value: 428, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#A7F3D0' }, { offset: 1, color: '#10B981' }]) } },
          { value: 245, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#93C5FD' }, { offset: 1, color: '#3B82F6' }]) } },
          { value: 142, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#C4B5FD' }, { offset: 1, color: '#6366F1' }]) } },
          { value: 32,  itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#DDD6FE' }, { offset: 1, color: '#8B5CF6' }]) } }
        ],
        label: { show: true, position: 'right', fontWeight: 'bold', fontSize: 12, color: '#374151', formatter: '{c} 人' },
        itemStyle: { borderRadius: [0, 4, 4, 0] }
      }]
    })
    batchCharts.push(chartEducation)
  }

  // D3. 家庭年收入分布 (Stacked Bar by range)
  const domIncome = document.getElementById('batchChartIncome')
  if (domIncome) {
    const chartIncome = echarts.init(domIncome)
    chartIncome.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: function(params) {
        let res = params[0].axisValue + '<br/>'
        params.forEach(p => { res += `${p.marker} ${p.seriesName}: ${p.value} 人<br/>` })
        return res
      }},
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '18%' },
      xAxis: {
        type: 'category',
        data: ['<3万', '3~5万', '5~8万', '8~12万', '12~20万', '>20万'],
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 11 }
      },
      yAxis: { type: 'value', name: '人数', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: '男性', type: 'bar', stack: 'total', barWidth: '45%',
          itemStyle: { color: '#3B82F6', borderRadius: [0, 0, 0, 0] },
          label: { show: true, color: '#fff', fontWeight: 'bold', fontSize: 11 },
          data: [52, 148, 245, 218, 138, 55]
        },
        {
          name: '女性', type: 'bar', stack: 'total', barWidth: '45%',
          itemStyle: { color: '#EC4899', borderRadius: [4, 4, 0, 0] },
          label: { show: true, color: '#fff', fontWeight: 'bold', fontSize: 11 },
          data: [38, 102, 118, 72, 42, 17]
        }
      ]
    })
    batchCharts.push(chartIncome)
  }
}
*/

/* ==============================================
   初始化单人模式科研 ECharts (纯 EDA 阶段)
   ============================================== */
let singleCharts = []

const disposeSingleCharts = () => {
  singleCharts.forEach(chart => chart.dispose())
  singleCharts = []
}
const chartEmpty = (message) => ({
  series: [],
  graphic: [{ type: 'text', left: 'center', top: 'middle', style: { text: message, fill: '#64748B', font: '12px sans-serif', lineHeight: 20, textAlign: 'center' } }]
})
const escapeTooltip = (value) => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]))
const preciseLabel = (value) => Number.isFinite(value) ? Number(value.toPrecision(5)).toString() : '不可计算'
const measurementTooltip = (row) => [
  escapeTooltip(row.label),
  '原始值：' + escapeTooltip(rawMeasurement(row)) + ' ' + escapeTooltip(row.metadata.unit || '单位未指定'),
  '样本：' + escapeTooltip(sampleLabel(row.metadata.sample)),
  row.ratio === null ? escapeTooltip(row.comparisonLabel) : '参考占比：' + preciseLabel(row.ratio) + '%',
  row.reference ? escapeTooltip(row.reference.title) + '：' + row.reference.value + ' ' + escapeTooltip(row.reference.unit) : '暂无适用参考',
  escapeTooltip(row.comparisonLabel)
].join('<br/>')
const initSingleECharts = () => {
  const profile = individualProfile.value
  const ratios = profile.comparable
  const max = profile.scaleMax
  const gradient = (reached) => new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: reached ? '#FCA5A5' : '#93C5FD' },
    { offset: 1, color: reached ? '#EF4444' : '#3B82F6' }
  ])
  const render = (id, option) => {
    const element = document.getElementById(id)
    if (!element) return
    let chart = echarts.getInstanceByDom(element)
    if (!chart) { chart = echarts.init(element); singleCharts.push(chart) }
    // Replacing all options removes stale data when a reference becomes inapplicable.
    chart.setOption(option, { notMerge: true })
  }
  const ratioAxis = { type: 'value', max, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } }
  const referenceLine = { silent: true, symbol: 'none', lineStyle: { color: '#64748B', type: 'dashed' }, data: [{ yAxis: 100, label: { position: 'insideMiddle', formatter: '参考100%' } }] }
  render('singleChartMaster', {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => measurementTooltip(profile.rows[params[0].dataIndex]) },
    grid: { left: '5%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: profile.rows.map(row => row.label), axisLabel: { interval: 0, fontWeight: 'bold', fontSize: 10, formatter: (label, index) => label + '\n' + rawMeasurement(profile.rows[index]) + '\n' + (profile.rows[index].metadata.unit || '单位未指定') }, axisTick: { show: false } },
    yAxis: ratioAxis,
    series: ratios.length ? [{
      name: '参考占比', type: 'bar', barWidth: '40%',
      data: profile.rows.map(row => ({ value: row.ratio, itemStyle: { color: gradient(row.reached === true), borderRadius: [4, 4, 0, 0] } })),
      label: { show: true, position: 'top', formatter: params => params.value === null ? '' : preciseLabel(params.value) + '%', fontWeight: 'bold' },
      markLine: referenceLine
    }] : [],
    graphic: ratios.length ? [] : chartEmpty('暂无可比较指标\n原始数值与单位仍显示在横轴').graphic
  })
  render('singleChartRadar', ratios.length >= 3 ? {
    tooltip: { formatter: () => ratios.map(measurementTooltip).join('<br/><br/>') },
    legend: { bottom: 0, itemWidth: 12, itemHeight: 12 },
    radar: { indicator: ratios.map(row => ({ name: row.label, max })), radius: '60%', center: ['50%', '45%'] },
    series: [{ type: 'radar', data: [
      { value: ratios.map(row => row.ratio), name: '实测参考占比', areaStyle: { color: 'rgba(239, 68, 68, 0.3)' }, lineStyle: { color: '#EF4444' }, itemStyle: { color: '#EF4444' } },
      { value: ratios.map(() => 100), name: '各自参考值（非安全线）', areaStyle: { color: 'rgba(16, 185, 129, 0.1)' }, lineStyle: { color: '#10B981', type: 'dashed' }, itemStyle: { color: '#10B981' } }
    ] }]
  } : chartEmpty('雷达图至少需要3项可比较指标\n当前：' + ratios.length + '项；不以零填补'))
  const conditionKeys = ['input', 'sample', 'unit', 'reference']
  const conditionLabels = ['输入', '样本', '单位', '参考']
  // These codes are categorical condition states, never substitute missing concentrations with zero.
  const stateCodes = { pass: 1, missing: -1, incompatible: 0, pending: 2 }
  const stateLabels = { pass: '可', missing: '空', incompatible: '×', pending: '待' }
  const cells = profile.rows.flatMap((row, x) => conditionKeys.map((key, y) => [x, y, stateCodes[row.conditions[key].state]]))
  render('singleChartTimeline', {
    tooltip: { position: 'top', formatter: params => {
      const [x, y] = params.data
      return measurementTooltip(profile.rows[x]) + '<br/>' + conditionLabels[y] + '：' + escapeTooltip(profile.rows[x].conditions[conditionKeys[y]].reason)
    } },
    grid: { left: '15%', right: '4%', top: '10%', bottom: '20%' },
    xAxis: { type: 'category', data: profile.rows.map(row => row.key.toUpperCase()), axisTick: { show: false } },
    yAxis: { type: 'category', data: conditionLabels, axisTick: { show: false } },
    visualMap: { show: false, pieces: [{ value: -1, color: '#F1F5F9' }, { value: 0, color: '#CBD5E1' }, { value: 1, color: '#93C5FD' }, { value: 2, color: '#DBEAFE' }] },
    series: [{ type: 'heatmap', data: cells, label: { show: true, fontSize: 11, width: 12, overflow: 'truncate', align: 'center', color: '#334155', formatter: params => stateLabels[Object.keys(stateCodes).find(key => stateCodes[key] === params.value[2])] }, itemStyle: { borderColor: '#fff', borderWidth: 2 } }]
  })
  render('singleChartPercentile', ratios.length ? {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => measurementTooltip(profile.sorted[params[0].dataIndex]) },
    grid: { left: '18%', right: '15%', bottom: '15%', top: '10%' },
    xAxis: ratioAxis, yAxis: { type: 'category', inverse: true, data: profile.sorted.map(row => row.label), axisTick: { show: false }, axisLabel: { fontWeight: 'bold' } },
    series: [{ name: '参考占比（非百分位）', type: 'bar', barWidth: '40%', data: profile.sorted.map(row => ({ value: row.ratio, itemStyle: { color: gradient(row.reached === true), borderRadius: [0, 4, 4, 0] } })), label: { show: true, position: 'right', formatter: params => preciseLabel(params.value) + '%', fontWeight: 'bold' },
      markLine: { silent: true, symbol: 'none', lineStyle: { color: '#64748B', type: 'dashed' }, data: [{ xAxis: 100, label: { show: false } }] } }]
  } : chartEmpty('暂无参考占比可排序\n不是群体百分位'))
  const inputColors = { valid: '#3B82F6', missing: '#CBD5E1', invalid: '#EF4444' }
  render('singleChartRiskPie', {
    legend: { bottom: 0, selectedMode: false, itemWidth: 10, itemHeight: 10, icon: 'circle', textStyle: { color: '#64748B', fontSize: 11 }, data: ['有效', '缺失', '非法'], formatter: name => name + ' ' + profile.counts[{ '有效': 'valid', '缺失': 'missing', '非法': 'invalid' }[name]] + '项' },
    // A separate centered summary does not follow a slice's angular label anchor.
    graphic: [{ type: 'text', left: 'center', top: 'middle', silent: true, z: 100, style: {
      text: '{count|' + profile.counts.valid + '/' + profile.counts.total + '}\n{caption|有效录入}',
      align: 'center', verticalAlign: 'middle', rich: {
        count: { fontSize: 23, fontWeight: 'bold', fill: '#1D4ED8', lineHeight: 30, align: 'center' },
        caption: { fontSize: 11, fill: '#64748B', lineHeight: 20, align: 'center' }
      }
    } }],
    tooltip: { trigger: 'item', formatter: params => {
      if (params.seriesIndex === 1) return measurementTooltip(profile.rows[params.dataIndex])
      return escapeTooltip(params.name) + '：' + params.value + '项（指标计数）'
    } },
    series: [
      { name: '录入状态计数', type: 'pie', radius: ['33%', '47%'], label: { show: false }, labelLine: { show: false }, itemStyle: { borderColor: '#fff', borderWidth: 1 }, data: [
        { value: profile.counts.valid, name: '有效', itemStyle: { color: inputColors.valid } },
        { value: profile.counts.missing, name: '缺失', itemStyle: { color: inputColors.missing } },
        { value: profile.counts.invalid, name: '非法', itemStyle: { color: inputColors.invalid } }
      ].filter(item => item.value > 0) },
      { name: '每项指标的录入状态', type: 'pie', radius: ['53%', '77%'], itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }, label: { position: 'inside', formatter: '{b}', fontSize: 10, color: '#0F172A' }, labelLine: { show: false }, data: profile.rows.map(row => ({ value: 1, name: row.key.toUpperCase(), itemStyle: { color: inputColors[row.inputState] } })) }
    ]
  })
  render('singleChartZScore', ratios.length ? {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => measurementTooltip(ratios[params[0].dataIndex]) + '<br/>相对参考偏移：' + preciseLabel(ratios[params[0].dataIndex].offset) + '%' },
    grid: { left: '18%', right: '18%', bottom: '15%', top: '15%' },
    xAxis: { type: 'value', name: '相对参考偏移 (%)', nameLocation: 'middle', nameGap: 28, nameTextStyle: { fontSize: 11 }, splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: { type: 'category', data: ratios.map(row => row.label), axisTick: { show: false }, axisLabel: { fontWeight: 'bold' } },
    series: [{ name: '参考偏移（非Z-score）', type: 'bar', barWidth: '50%', data: ratios.map(row => ({ value: row.offset, itemStyle: { color: row.offset > 0 ? '#EF4444' : '#34D399' } })), label: { show: true, position: 'right', formatter: params => preciseLabel(params.value) + '%' } }]
  } : chartEmpty('暂无可计算的参考偏移\n不是Z-score'))
  render('singleChartAnomaly', profile.coverage === null ? chartEmpty('尚无有效测量\n覆盖率不可计算（不显示为0%）') : {
    tooltip: { formatter: () => '可比较 ' + profile.counts.comparable + '项 / 有效录入 ' + profile.counts.valid + '项<br/>非医疗综合分；不表示安全或健康' },
    series: [{
      name: '已录入可比较覆盖率', type: 'gauge', center: ['50%', '60%'], radius: '80%', min: 0, max: 100, splitNumber: 4,
      axisLine: { lineStyle: { width: 12, color: [[1, '#E2E8F0']] } },
      progress: { show: true, width: 12, itemStyle: { color: '#3B82F6' } },
      pointer: { show: false }, axisTick: { distance: -12, length: 8, lineStyle: { color: '#fff', width: 2 } },
      splitLine: { distance: -12, length: 20, lineStyle: { color: '#fff', width: 3 } }, axisLabel: { color: '#64748B', distance: 20, fontSize: 10 },
      detail: { offsetCenter: [0, '6%'], valueAnimation: true, formatter: value => preciseLabel(value) + '%', color: '#1D4ED8', fontSize: 24, fontWeight: 'bold' },
      data: [{ value: profile.coverage, name: profile.counts.comparable + ' / ' + profile.counts.valid + '项（非医疗分）' }],
      title: { offsetCenter: [0, '38%'], fontSize: 12, color: '#64748B', fontWeight: 'bold' }
    }]
  })
}
// Real-time single-profile updates only; batch requests/data/chart logic are untouched.
watch(individualProfile, () => {
  if (formData.value.mode !== 'single' || !showDashboard.value) return
  initSingleECharts()
}, { flush: 'post' })

onMounted(() => {
  loadOutcomeConfigs()
  loadBatchFormat()
  loadGroupDemo()
  window.addEventListener('resize', handleResize)
})

const handleResize = () => {
  batchCharts.forEach(chart => chart.resize())
  singleCharts.forEach(chart => chart.resize())
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  batchCharts.forEach(chart => chart.dispose())
  singleCharts.forEach(chart => chart.dispose())
})
</script>

<style lang="scss" scoped>
@use "sass:color";
.measurement-metadata { display: grid; gap: 6px; margin-top: 8px; select { width: 100%; min-width: 0; padding: 6px 4px; border: 1px solid #E2E8F0; border-radius: 4px; background: #F8FAFC; color: #475569; font-size: 11px; } }
.metadata-confirm { padding: 6px; border: 1px solid #FBBF24; border-radius: 4px; background: #FFFBEB; color: #92400E; font-size: 11px; cursor: pointer; }
.individual-caution { font-size: 12px; line-height: 1.7; color: #64748B; }
.individual-reference-note { margin-top: 12px; font-size: 11px; line-height: 1.6; a { color: #1D4ED8; } p { margin: 4px 0; color: #64748B; } }
.reference-sidebar .ref-card .ref-list .range.individual-reference-status { color: #64748B; }
:deep(.el-icon svg) {
  max-width: 1em;
  max-height: 1em;
  width: 1em;
  height: 1em;
}
$color-primary: #1f77b4;
$color-primary-light: #EFF6FF;
$color-bg: #F1F5F9; 
$text-main: #111827;
$text-muted: #6B7280;
$border-color: #E2E8F0;

$color-safe: #34D399;   
$color-warn: #FBBF24;   
$color-danger: #F87171; 
* { box-sizing: border-box; }

.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }

.main-content { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow-y: auto; scroll-behavior: smooth; background: #F8FAFC;}

.ep-header { 
  height: 64px; 
  background: #fff; 
  border-bottom: 1px solid $border-color; 
  position: sticky; 
  top: 0; 
  z-index: 50; 
  display: flex !important; 
  justify-content: center; 
  flex-shrink: 0;
}
.nav-wrapper { 
  width: 100%; 
  padding: 0 32px; 
  display: flex !important; 
  flex-direction: row !important; 
  flex-wrap: nowrap !important; 
  justify-content: space-between !important; 
  align-items: center !important; 
  height: 100%; 
  max-width: none; 
}
.back-link { 
  display: flex; 
  flex-direction: row;
  align-items: center; 
  gap: 12px; 
  cursor: pointer; 
  color: $text-main; 
  transition: color 0.2s; 
  &:hover { color: $color-primary; } 
  .back-icon { font-size: 1.2rem; font-weight: bold;} 
  .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px;} 
  .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; } 
  .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-main; } 
}
.ep-right-zone {
  display: flex;
  align-items: center;
  flex-direction: row;
}
.user-profile { 
  display: flex; 
  flex-direction: row;
  align-items: center; 
  gap: 12px; 
  font-weight: 600; 
  color: $text-main; 
  font-size: 0.95rem; 
  white-space: nowrap; 
  .avatar { 
    width: 32px; 
    height: 32px; 
    border-radius: 50%; 
    background: $color-primary-light; 
    color: $color-primary; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    font-weight: 700; 
    font-size: 0.9rem;
  } 
}

.page-container { padding: 40px; max-width: 1400px; margin: 0 auto; width: 100%; padding-bottom: 100px; }

.pipeline-steps { display: flex; align-items: center; margin-bottom: 30px; background: transparent; padding: 0; border: none; .step { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; color: $text-muted; .step-num { width: 24px; height: 24px; border-radius: 50%; background: #E5E7EB; display: flex; justify-content: center; align-items: center; font-size: 0.85rem; } &.active { color: $color-primary; .step-num { background: $color-primary; color: #FFF; } } } .step-line { flex: 1; height: 2px; background: #E5E7EB; margin: 0 16px; position: relative; transition: 0.3s; &.active-line { background: $color-primary; } } }

.clean-clinical-card { background: #fff; border-radius: 12px; border: 1px solid $border-color; box-shadow: 0 4px 15px rgba(0,0,0,0.03); overflow: hidden; margin-bottom: 40px; }
.card-layout-grid { display: flex; min-height: 400px; }
.form-entry-area { flex: 2.2; min-width: 0; padding: 40px; border-right: 1px solid $border-color; }
.reference-sidebar { flex: 1; min-width: 0; background: #F8FAFC; padding: 40px 30px; display: flex; flex-direction: column; justify-content: space-between; }

.config-row { display: flex; gap: 40px; label { display: block; font-size: 0.95rem; font-weight: 700; color: $text-main; margin-bottom: 12px; } }
.flex-2 { flex: 2; } .flex-1 { flex: 1; }
.radio-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.radio-card { background: #fff; border: 1px solid #D1D5DB; padding: 10px; text-align: center; border-radius: 6px; font-weight: 600; color: $text-main; cursor: pointer; transition: all 0.2s; &:hover { border-color: $color-primary; } &.selected { background: #EFF6FF; border-color: $color-primary; color: $color-primary; } }
.mode-switch { display: flex; background: #F1F5F9; border-radius: 6px; padding: 4px; button { flex: 1; padding: 8px; border: none; background: transparent; border-radius: 4px; font-weight: 600; color: $text-muted; cursor: pointer; transition: 0.3s; &.active { background: #fff; color: $color-primary; box-shadow: 0 2px 4px rgba(0,0,0,0.05); } } }
.clinical-divider { border: 0; height: 1px; background: $border-color; margin: 30px 0; }

.form-section { margin-bottom: 30px; }
.section-title { font-size: 1.05rem; font-weight: 700; color: $text-main; border-left: 4px solid $color-primary; padding-left: 10px; margin-bottom: 20px; }
.clinical-input-grid { display: grid; gap: 16px; }
.cols-4 { grid-template-columns: repeat(4, 1fr); } 
.cols-3 { grid-template-columns: repeat(3, 1fr); } 

.clinical-input-item { 
  display: flex; flex-direction: column; gap: 8px; 
  .label { font-size: 0.9rem; font-weight: 600; color: $text-main; } 
  .input-wrap { 
    display: flex; align-items: center; border: 1px solid #D1D5DB; border-radius: 6px; background: #fff; transition: 0.2s;
    &:focus-within { border-color: $color-primary; box-shadow: 0 0 0 2px #EFF6FF; }
    &.is-error { border-color: $color-danger; background: #FEF2F2; color: $color-danger;}
    input, select { flex: 1; width: 100%; padding: 8px 12px; border: none; font-size: 0.95rem; outline: none; background: transparent; color: $text-main; font-weight: 500;}
    .unit { padding: 0 10px; color: #9CA3AF; font-size: 0.85rem; font-weight: 500; background: #F8FAFC; border-left: 1px solid $border-color; height: 100%; display: flex; align-items: center; }
  }
}

.upload-addon .btn-mini-upload { 
  height: 100%; width: 100%; background: #EFF6FF; border: 1px dashed #60A5FA; border-radius: 6px; 
  color: $color-primary; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;
  &:hover { border-color: $color-primary; background: $color-primary; color: #fff;} 
}

.outcome-config-panel {
  border: 1px solid #DBEAFE;
  background: #F8FAFF;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 18px;
}
.outcome-selector {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr);
  align-items: center;
  gap: 14px;
  .config-label { font-size: 0.95rem; font-weight: 800; color: $text-main; }
  p { grid-column: 1 / -1; margin: 0; color: $text-muted; font-size: 0.85rem; line-height: 1.5; }
}
.field-role-summary { margin-top: 18px; padding-top: 16px; border-top: 1px dashed #CBD5E1; }
.role-line { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 9px; }
.role-title {
  min-width: 72px;
  padding: 5px 9px;
  border-radius: 5px;
  font-size: 0.78rem;
  font-weight: 800;
  text-align: center;
  &.exposure { background: #DBEAFE; color: #1D4ED8; }
  &.confounder { background: #EDE9FE; color: #6D28D9; }
}
.field-chip {
  padding: 5px 9px;
  border: 1px solid #BFDBFE;
  border-radius: 5px;
  background: #fff;
  color: #1E40AF;
  font-size: 0.78rem;
  font-weight: 700;
  small { color: #64748B; font-weight: 500; margin-left: 3px; }
  &.muted { border-color: #DDD6FE; color: #5B21B6; }
}
.hidden-file-input { display: none; }
.group-demo-panel { margin-bottom: 20px; padding: 20px; border: 1px solid #cddff2; border-radius: 12px; background: linear-gradient(110deg, #f4f9ff, #fff); }
.group-demo-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.group-demo-eyebrow { color: #4c80aa; font-size: 11px; letter-spacing: .8px; font-weight: 700; }
.group-demo-heading h4 { margin: 8px 0; color: #233f5b; font-size: 17px; }
.group-demo-heading p, .group-demo-details p { margin: 0; color: #64748b; font-size: 13px; line-height: 1.8; }
.btn-group-demo { display: flex; align-items: center; justify-content: center; gap: 7px; padding: 12px 16px; border: 0; border-radius: 8px; color: #fff; background: #267cbd; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.btn-group-demo:disabled { opacity: .55; cursor: not-allowed; }
.group-demo-boundary { font-size: 12px; color: #64748b; line-height: 1.8; margin: 14px 0 0; }
.group-demo-details { margin-top: 12px; border-top: 1px solid #e2ebf6; padding-top: 12px; }
.group-demo-details summary { color: #397bae; font-weight: 700; font-size: 12px; cursor: pointer; }
.group-demo-details p { margin-top: 12px; }
.group-demo-details ul { margin: 10px 0; padding-left: 18px; color: #64748b; font-size: 12px; line-height: 1.85; }
.group-demo-details li + li { margin-top: 5px; }
.group-demo-sources { display: flex; gap: 8px 16px; flex-wrap: wrap; margin-top: 10px; }
.group-demo-sources a { color: #2b79af; font-size: 12px; }
.group-demo-error { font-size: 13px; line-height: 1.8; color: #a45543; margin-bottom: 0; }
.group-demo-error button { color: #267cbd; font-size: 12px; background: transparent; border: 0; cursor: pointer; }
.group-demo-active { font-size: 13px; font-weight: 650; color: #2a7c78; margin: 12px 0; }
.group-demo-dashboard-source { display: flex; flex-direction: column; gap: 9px; padding: 18px 20px; border: 1px solid #d8e7f6; background: #f3f8fe; border-radius: 12px; margin-bottom: 20px; }
.group-demo-dashboard-source strong { color: #2d638c; font-size: 15px; }
.group-demo-dashboard-source span { color: #64748b; font-size: 13px; line-height: 1.8; }
.batch-dashboard-container { scroll-margin-top: 88px; }
.analysis-notes-details { border: 1px solid #dce7f2; background: #f8fbfe; border-radius: 9px; padding: 12px 16px; margin-bottom: 18px; }
.analysis-notes-details summary { font-size: 12px; line-height: 1.8; color: #547493; cursor: pointer; }
.analysis-notes-details .analysis-notes { margin-top: 12px; margin-bottom: 0; }
.batch-format-guide {
  margin-bottom: 20px; padding: 20px; border: 1px solid #DBEAFE; border-radius: 12px; background: #fff;
  .format-guide-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
  h4 { margin: 0 0 7px; font-size: 15px; color: #0F172A; font-weight: 800; }
  p { margin: 0; color: #64748B; font-size: 12px; line-height: 1.7; }
  ul { margin: 14px 0; padding-left: 18px; color: #475569; font-size: 12px; line-height: 1.85; }
  li + li { margin-top: 5px; }
  .format-template-button { padding: 8px 11px; background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 700; white-space: nowrap; &:disabled { opacity: .5; cursor: not-allowed; } }
  .format-field-details { margin-top: 12px; summary { cursor: pointer; font-size: 12px; font-weight: 700; color: #1D4ED8; } }
  .format-table-scroll { overflow-x: auto; margin-top: 12px; max-width: 100%; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; text-align: left; th, td { padding: 8px; border-bottom: 1px solid #E2E8F0; } th { background: #F8FAFC; color: #475569; } code { font-size: 10px; white-space: nowrap; } }
  .format-cleaning-entry { margin-top: 16px; padding-top: 13px; border-top: 1px dashed #DBEAFE; display: flex; flex-wrap: wrap; gap: 7px 12px; font-size: 12px; color: #64748B; a { font-weight: 700; color: #1D4ED8; } }
  .format-schema-status { margin-top: 12px; }
}
.batch-import-error { margin: 0 0 18px; padding: 15px; border: 1px solid #FECACA; border-radius: 10px; background: #FEF2F2; font-size: 12px; color: #991B1B; p { overflow-wrap: anywhere; line-height: 1.7; } a { color: #1D4ED8; font-weight: 700; } }

.upload-dragger { border: 2px dashed #CBD5E1; border-radius: 12px; padding: 60px; text-align: center; background: #F8FAFC; cursor: pointer; transition: all 0.3s; &:hover { border-color: $color-primary; background: #EFF6FF; } &.has-file { border-color: $color-safe; background: #ecfdf5; } .upload-icon { font-size: 2.5rem; color: #94A3B8; margin-bottom: 16px; } .upload-text { font-size: 1.1rem; font-weight: 700; color: $text-main; margin-bottom: 8px; } .upload-hint { font-size: 0.95rem; color: $text-muted; margin-bottom: 24px; &.success-text { color: #059669; } } .btn-upload { background: #fff; border: 1px solid $border-color; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.95rem; color: $text-main; &.btn-reupload{ border-color: $color-safe; color: #059669;} } }

.reference-sidebar {
  .ref-card {
    h4 { margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; font-size: 1.05rem; font-weight: 800; color: $text-main; .el-icon { color: $color-primary; } }
    .ref-desc { font-size: 0.85rem; color: $text-muted; line-height: 1.5; margin-bottom: 16px; }
    .ref-list { list-style: none; padding: 0; margin: 0; li { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px dashed #E2E8F0; font-size: 0.9rem; } .metal { font-weight: 700; color: $text-main; } .range { color: $color-safe; font-weight: 700; font-family: monospace; } }
  }
  .action-card {
    background: #fff; padding: 24px; border-radius: 12px; border: 1px solid $border-color; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    h4 { margin: 0 0 8px 0; font-size: 1.05rem; font-weight: 800; color: $text-main;}
    p { font-size: 0.9rem; color: $text-muted; margin: 0 0 20px 0; line-height: 1.5;}
    .btn-analyze { width: 100%; background: $text-main; color: #fff; border: none; padding: 14px; border-radius: 8px; font-size: 1.05rem; font-weight: 700; cursor: pointer; transition: 0.3s; &:hover { background: $color-primary; transform: translateY(-2px); box-shadow: 0 8px 16px rgba(31,119,180,0.2); } &.is-loading { background: #9CA3AF; cursor: wait; transform: none; box-shadow: none; } }
  }
}

.visualization-dashboard { animation: slideUp 0.5s ease-out forwards; margin-top: 20px;}
@keyframes slideUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }

.analysis-notes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: -12px 0 24px;
  span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 10px;
    border: 1px solid #DBEAFE;
    border-radius: 6px;
    background: #F8FAFF;
    color: #475569;
    font-size: 0.78rem;
    line-height: 1.35;
  }
  .el-icon { color: #3B82F6; flex-shrink: 0; }
}

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
.kpi-card { 
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  .kpi-icon { font-size: 2.5rem; padding: 12px; border-radius: 12px; }
  &.total .kpi-icon { background: #EFF6FF; color: #3B82F6; }
  &.male .kpi-icon { background: #F0FDF4; color: #10B981; }
  &.female .kpi-icon { background: #FDF2F8; color: #EC4899; }
  &.ready .kpi-icon { background: #ECFDF5; color: #10B981; }
  .kpi-info { display: flex; flex-direction: column; span { font-size: 0.85rem; color: $text-muted; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;} strong { font-size: 1.8rem; font-weight: 900; color: $text-main; small { font-size: 0.9rem; color: #94A3B8; font-weight: 600;}} .text-danger { color: #EF4444; } }
}

.batch-charts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 40px; }
.demographic-row { margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px dashed #E2E8F0; }
.b-chart-card { 
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column;
  .b-c-header { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #F1F5F9; h4 { margin: 0; font-size: 1.05rem; font-weight: 800; color: $text-main; } .sub-title { font-size: 0.85rem; color: $text-muted; margin-top: 6px; display: block;} }
  .b-c-canvas { flex: 1; min-height: 280px; width: 100%; }
}
.col-span-2 { grid-column: span 2; }
.col-span-1 { grid-column: span 1; }
.mb-6 { margin-bottom: 24px; }

.chart-card { background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); h4 { margin: 0 0 16px 0; font-size: 1.05rem; font-weight: 700; color: $text-main; } }

.main-master-chart { 
  margin-bottom: 30px; width: 100%; padding: 40px; box-sizing: border-box;
  .chart-title-wrap { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 50px; .title-left h4 { margin: 0 0 8px 0; font-size: 1.5rem; font-weight: 800; color: $text-main;} p { margin: 0; font-size: 0.95rem; color: $text-muted; line-height: 1.5;} }
  .filter-legend { display: flex; gap: 16px; font-size: 0.9rem; font-weight: 600; span { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; cursor: pointer; transition: 0.2s; &:hover { background: #F3F4F6; } &.dimmed { opacity: 0.4; } } .dot { width: 10px; height: 10px; border-radius: 50%; } .safe{background:$color-safe;} .warn{background:$color-warn;} .danger{background:$color-danger;} .reset-filter { color: $color-primary; font-weight: 700; background: transparent; &:hover { background: transparent; text-decoration: underline; } } }
}

.master-bar-chart {
  height: 500px; width: 100%; display: flex; align-items: flex-end; padding-left: 60px; position: relative; box-sizing: border-box;
  .axis-y-label { position: absolute; left: 0; top: -30px; font-size: 0.9rem; font-weight: 600; color: $text-muted;}
  .axis-y { position: absolute; left: 10px; top: 0; height: 100%; width: 40px; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end; color: #9CA3AF; font-size: 0.9rem; font-weight: 600; font-family: monospace; padding-bottom: 25px; }
  .threshold-line { position: absolute; left: 50px; right: 0; height: 1px; border-top: 2px dashed; z-index: 0; pointer-events: none; span { position: absolute; right: 0; top: -26px; font-size: 0.85rem; font-weight: 700; padding: 4px 10px; border-radius: 4px; } }
  .danger-line { border-color: $color-danger; span { background: #FEF2F2; color: $color-danger; } }
  .warn-line { border-color: $color-warn; span { background: #FFFBEB; color: $color-warn; } }

  .bars-container { width: 100%; height: 100%; display: flex; justify-content: space-around; align-items: flex-end; border-bottom: 2px solid #D1D5DB; position: relative; z-index: 1; padding: 0 20px;}
  .master-bar-item {
    display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; width: 6.5%; position: relative; transition: opacity 0.3s;
    &.dimmed-bar { opacity: 0.15; }
    .bar-val-static { font-size: 1rem; font-weight: 800; margin-bottom: 8px; transition: transform 0.3s; }
    .bar-track { width: 100%; height: 100%; display: flex; align-items: flex-end; background: transparent; border-radius: 6px 6px 0 0;}
    .bar-fill { width: 100%; border-radius: 6px 6px 0 0; transition: height 1s cubic-bezier(0.16, 1, 0.3, 1); }
    .bar-label { margin-top: 12px; font-weight: 800; font-size: 1.1rem; color: $text-main; display: flex; flex-direction: column; align-items: center; .cn { font-size: 0.8rem; font-weight: 500; color: $text-muted; margin-top: 2px;} }
    
    &.status-safe { .bar-val-static{color: $color-safe;} .bar-fill { background: linear-gradient(to top, #6EE7B7, #34D399); border: 1px solid #10B981; border-bottom: none;} }
    &.status-warn { .bar-val-static{color: $color-warn;} .bar-fill { background: linear-gradient(to top, #FCD34D, #FBBF24); border: 1px solid #F59E0B; border-bottom: none;} }
    &.status-danger { .bar-val-static{color: $color-danger;} .bar-fill { background: linear-gradient(to top, #FCA5A5, #F87171); border: 1px solid #EF4444; border-bottom: none; box-shadow: 0 -4px 15px rgba(239, 68, 68, 0.25); } }

    .hover-detail-box {
      position: absolute; bottom: calc(100% + 15px); left: 50%; transform: translateX(-50%) translateY(10px);
      width: 200px; background: #fff; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); opacity: 0; visibility: hidden; transition: all 0.2s; z-index: 100; pointer-events: none;
      .h-head { padding: 10px 12px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: #fff; .badge{ background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;} }
      .bg-safe { background: $color-safe; } .bg-warn { background: $color-warn; } .bg-danger { background: $color-danger; }
      .h-body { padding: 12px; p { margin: 0 0 6px 0; font-size: 0.85rem; color: $text-muted; } strong { color: $text-main; font-size: 1rem;} .h-risk { margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E5E7EB; line-height: 1.4; color: $text-main; font-weight: 500;} }
      &::after { content:''; position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid #fff; }
    }
    &:hover .hover-detail-box { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
    &:hover .bar-val-static { transform: translateY(-5px); }
  }
}

.sub-charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 40px; }
.chart-content { height: 280px; position: relative; display: flex; justify-content: center; align-items: center;}

.distribution-chart { width: 100%; align-items: flex-end; overflow: hidden; padding-bottom: 20px; }
.dist-layer { position: absolute; bottom: 20px; width: 120%; height: 100px; border-radius: 50% 50% 0 0 / 100% 100% 0 0; mix-blend-mode: multiply; }
.layer-pb { left: -10%; background: rgba(248, 113, 113, 0.4); height: 180px; transform: scaleX(0.6); }
.layer-cd { left: 10%; background: rgba(251, 191, 36, 0.4); height: 200px; transform: scaleX(0.7); }
.layer-hg { left: 30%; background: rgba(52, 211, 153, 0.4); height: 150px; transform: scaleX(0.8); }
.axis-x { position: absolute; bottom: 18px; width: 100%; height: 2px; background: $border-color; }
.chart-legend { position: absolute; top: 10px; right: 20px; display: flex; gap: 12px; font-size: 0.85rem; font-weight: 600; span { display: flex; align-items: center; gap: 4px; &::before { content:''; width:12px; height:12px; border-radius:2px;} } .c-pb::before{background:rgba(248,113,113,0.6);} .c-cd::before{background:rgba(251,191,36,0.6);} .c-hg::before{background:rgba(52,211,153,0.6);} }

.line-trend-chart { 
  display: block !important;
  width: 100%; 
  height: 100%;
  padding: 15px 20px 0 20px;
  svg { 
    display: block !important;
    width: 100% !important; 
    height: 220px !important;
    min-height: 220px !important;
    max-height: none !important; 
    max-width: none !important;
    overflow: visible;
  } 
  
  .trend-line { 
    stroke-dasharray: 800; 
    stroke-dashoffset: 0; 
    animation: lineGrow 2s ease-out forwards;
  } 
} 

@keyframes lineGrow { 
  from { stroke-dashoffset: 800; } 
  to { stroke-dashoffset: 0; } 
}

.heatmap-chart { width: 100%; padding: 10px; } .hm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; width: 100%; height: 100%; } .hm-cell { display: flex; justify-content: center; align-items: center; font-size: 0.85rem; font-weight: 700; color: #fff; border-radius: 4px; } .bg-high { background: #3B82F6; } .bg-med { background: #93C5FD; } .bg-low { background: #DBEAFE; color: #1E3A8A; } .bg-med-low { background: #BFDBFE; color: #1E3A8A; }

.pie-chart-area { display: flex; justify-content: space-around; align-items: center; width: 100%; padding: 0 20px; }
.donut-chart { width: 180px; height: 180px; border-radius: 50%; background: conic-gradient(#F87171 0% 45%, #FBBF24 45% 80%, #34D399 80% 100%); position: relative; }
.donut-center { position: absolute; left: 50%; top: 50%; width: 130px; height: 130px; background: #fff; border-radius: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; justify-content: center; align-items: center; .val { font-size: 1.5rem; font-weight: 800; color: $color-danger; } .lbl { font-size: 0.85rem; color: $text-muted; font-weight: 600;} }
.pie-legend { display: flex; flex-direction: column; gap: 14px; font-size: 1rem; font-weight: 600; color: $text-main; div { display: flex; align-items: center; gap: 8px; } .dot { width: 14px; height: 14px; border-radius: 50%; } .d-pb { background: #F87171; } .d-as { background: #FBBF24; } .d-cd { background: #34D399; } }


/* 底部操作条 */
.bottom-action-bar { display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; padding: 24px 32px; border-radius: 12px; border: 1px solid $border-color; box-shadow: 0 4px 20px -5px rgba(0,0,0,0.05); .tips { display: flex; align-items: center; gap: 8px; color: $text-muted; font-size: 1rem; .el-icon { color: $color-primary; font-size: 1.4rem; } strong { color: $text-main; } } .btn-next-step { background: $color-primary; color: #FFFFFF; border: none; padding: 16px 32px; border-radius: 8px; font-size: 1.1rem; font-weight: 700; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3); &:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(31, 119, 180, 0.4); background: color.adjust($color-primary, $lightness: -5%); } } }

.single-page {
  .main-content { min-width: 0; }
  .page-container { padding: 30px 32px 80px; }
  .single-intro { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 26px 30px; margin-bottom: 24px; border: 1px solid #DBEAFE; border-radius: 16px; background: linear-gradient(110deg, #EFF6FF, #F8FAFC 70%); h1 { font-size: clamp(20px, 1.6vw, 28px); color: #0F172A; margin: 8px 0 10px; font-weight: 800; } p { color: #64748B; font-size: 14px; line-height: 1.7; margin: 0; } }
  .eyebrow { font-size: 10px; font-weight: 800; letter-spacing: 2px; color: #1F77B4; }
  .single-intro-actions { display: flex; flex-direction: column; align-items: center; gap: 10px; flex-shrink: 0; > span { color: #64748B; font-size: 11px; } }
  .btn-demo { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: none; border-radius: 9px; padding: 13px 20px; background: #1F77B4; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 10px #1F77B425; &:hover { background: #166596; } }
  button:focus-visible, select:focus-visible, summary:focus-visible { outline: 3px solid #93C5FD; outline-offset: 3px; }
  .single-input-card { background: transparent; border: none; box-shadow: none; overflow: visible; }
  .card-layout-grid { display: grid; grid-template-columns: minmax(0, 1fr) 280px; gap: 22px; align-items: start; min-height: 0; }
  .form-entry-area { padding: 26px; background: #fff; border: 1px solid #E2E8F0; border-radius: 14px; min-width: 0; box-shadow: 0 3px 12px #0F172A03; }
  .config-row { gap: 20px; label { font-size: 13px; margin-bottom: 10px; } .config-group { min-width: 0; } }
  .radio-cards { gap: 8px; }
  .radio-card { font-size: 13px; padding: 10px 6px; }
  .mode-switch button { font-size: 13px; white-space: nowrap; padding: 9px; }
  .clinical-divider { margin: 24px 0; }
  .demo-notice { display: flex; gap: 10px; padding: 13px 15px; margin-bottom: 24px; border-radius: 9px; border: 1px solid #BFDBFE; background: #EFF6FF; color: #1E40AF; .el-icon { flex-shrink: 0; margin-top: 2px; } strong { display: block; font-size: 13px; margin-bottom: 4px; } span { display: block; font-size: 12px; line-height: 1.7; color: #475569; } }
  .form-section { margin-bottom: 28px; }
  .section-heading { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 18px; }
  .section-title { display: flex; align-items: center; border: none; padding: 0; margin: 0; font-size: 15px; font-weight: 800; gap: 9px; }
  .section-number { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 7px; background: #EFF6FF; color: #1F77B4; font-size: 11px; }
  .section-caption { font-size: 11px; color: #94A3B8; }
  .clinical-input-item { min-width: 0; gap: 7px; .label { font-size: 12px; } .input-wrap { border-color: #DCE3EC; border-radius: 7px; input, select { min-width: 0; padding: 10px; font-size: 13px; } .unit { flex-shrink: 0; font-size: 11px; padding: 0 7px; } } }
  .basic-profile-section .clinical-input-grid { gap: 14px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .measurement-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
  .measurement-card { padding: 16px; border: 1px solid #E2E8F0; border-radius: 10px; background: #FAFCFF; .input-wrap { margin: 5px 0 3px; input { font-size: 18px; font-weight: 700; padding: 10px 12px; } } }
  .measurement-heading { display: flex; align-items: center; justify-content: space-between; gap: 5px; .label { font-size: 14px; } }
  .measurement-state { font-size: 10px; color: #64748B; background: #F1F5F9; border-radius: 4px; padding: 3px 5px; &.is-comparable { color: #1D4ED8; background: #DBEAFE; } }
  .measurement-metadata { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 5px; select { font-size: 12px; border-radius: 6px; padding: 8px 5px; background: #fff; min-height: 34px; } .metadata-field { min-width: 0; display: grid; gap: 5px; > span { font-size: 10px; color: #64748B; } } .metadata-wide, .metadata-confirm { grid-column: 1 / -1; } }
  .metadata-confirm { font-size: 12px; padding: 8px; }
  .individual-caution { margin: 0; padding: 14px; border-radius: 8px; background: #F8FAFC; font-size: 11px; line-height: 1.8; }
  .single-form-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 18px; color: #94A3B8; font-size: 11px; > span { display: inline-flex; align-items: center; gap: 5px; } }
  .btn-clear { background: #fff; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 12px; color: #475569; font-size: 12px; cursor: pointer; flex-shrink: 0; &:hover { background: #F8FAFC; } }
  .reference-sidebar { padding: 0; background: transparent; gap: 18px; position: sticky; top: 84px; justify-content: flex-start; min-width: 0; .ref-card, .action-card { background: #fff; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; box-shadow: 0 3px 12px #0F172A03; h4 { font-size: 14px; } } .ref-card .ref-desc { font-size: 12px; line-height: 1.8; } .ref-card .ref-list li { gap: 8px; font-size: 12px; padding: 11px 0; .range { font-size: 12px; } } .action-card { order: -1; margin: 0; border-top: 3px solid #1F77B4; p { font-size: 12px; line-height: 1.8; margin-bottom: 16px; } .btn-analyze { background: #1F77B4; font-size: 13px; padding: 13px 10px; } } }
  .input-progress { position: relative; margin: 20px 0 18px; strong { display: block; font-size: 32px; color: #0F172A; small { color: #94A3B8; font-size: 13px; font-weight: 500; } } > span { display: block; color: #64748B; font-size: 11px; margin: 5px 0 12px; } }
  .input-progress-track { height: 5px; background: #F1F5F9; border-radius: 3px; overflow: hidden; i { display: block; height: 100%; background: #3B82F6; transition: width .25s; } }
  .input-summary { display: grid; gap: 9px; font-size: 12px; color: #64748B; padding-bottom: 16px; margin-bottom: 14px; border-bottom: 1px solid #F1F5F9; span { display: flex; justify-content: space-between; } b { color: #334155; font-weight: 600; } }
  .demo-summary, .demo-badge { color: #1D4ED8; font-size: 11px; background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 6px; padding: 7px 10px; }
  .reference-empty { font-size: 12px; color: #64748B; line-height: 1.8; padding: 13px; background: #F8FAFC; border-radius: 8px; }
  .reference-details { margin-top: 16px; summary { cursor: pointer; font-size: 12px; color: #1F77B4; line-height: 1.7; span { color: #94A3B8; font-size: 11px; margin-left: 8px; } } }
  .individual-reference-note { font-size: 12px; padding-top: 12px; border-top: 1px solid #F1F5F9; strong { color: #334155; display: block; margin-bottom: 5px; } a { display: block; overflow-wrap: anywhere; } p { line-height: 1.8; } }
  .single-results-heading { display: flex; justify-content: space-between; flex-wrap: wrap; align-items: center; gap: 14px; margin: 10px 0 24px; h2 { font-size: 23px; color: #0F172A; margin: 8px 0; font-weight: 800; } p { font-size: 12px; color: #64748B; margin: 0; } }
  .single-dashboard-container { scroll-margin-top: 88px; .batch-charts-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .b-chart-card { min-width: 0; } .b-c-header .sub-title { line-height: 1.7; font-size: 12px; } }
}

@media (max-width: 1350px) {
  .single-page { .card-layout-grid { grid-template-columns: minmax(0, 1fr); } .reference-sidebar { position: static; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: start; } .single-intro { align-items: flex-start; } .single-intro-actions { align-items: flex-start; } }
}

@media (max-width: 1200px) {
  .batch-charts-grid { grid-template-columns: 1fr 1fr; }
  .kpi-row { grid-template-columns: 1fr 1fr; }
  .card-layout-grid { flex-direction: column; }
  .form-entry-area { border-right: none; border-bottom: 1px solid $border-color; }
  .clinical-input-grid { grid-template-columns: repeat(2, 1fr); }
  .outcome-selector { grid-template-columns: 100px 1fr; p { grid-column: 1 / -1; } }
  .bottom-action-bar { flex-direction: column; gap: 20px; align-items: stretch; .btn-next-step{ width: 100%; } }
}

@media (max-width: 1050px) {
  .single-page { :deep(.sidebar) { display: none; } .page-container { padding: 24px; } .basic-profile-section .clinical-input-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
}

@media (max-width: 720px) {
  .single-page {
    .page-container { padding: 20px 14px 60px; }
    .nav-wrapper { padding: 0 16px; } .ep-right-zone, .back-link .divider, .page-title-top { display: none; }
    .pipeline-steps { gap: 8px; margin-bottom: 20px; .step { font-size: 11px; gap: 5px; } .step-num { width: 20px; height: 20px; flex-shrink: 0; font-size: 10px; } .step-line { margin: 0; min-width: 10px; } }
    .single-intro { flex-direction: column; padding: 22px; gap: 20px; h1 { font-size: 21px; line-height: 1.5; } p { font-size: 12px; } }
    .single-intro-actions { width: 100%; .btn-demo { width: 100%; } > span { font-size: 10px; } }
    .form-entry-area { padding: 20px 16px; }
    .config-row { flex-direction: column; gap: 18px; }
    .basic-profile-section .clinical-input-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .measurement-grid, .reference-sidebar, .single-dashboard-container .batch-charts-grid { grid-template-columns: minmax(0, 1fr); }
    .section-caption { display: none; }
    .measurement-card { padding: 16px; }
    .single-form-footer { align-items: flex-start; > span { line-height: 1.7; } }
    .single-dashboard-container .b-chart-card { padding: 18px 14px; }
    .single-results-heading h2 { font-size: 20px; }
    .bottom-action-bar { padding: 20px; .tips { font-size: 12px; line-height: 1.8; } .btn-next-step { font-size: 13px; padding: 13px; } }
  }
}
</style>
