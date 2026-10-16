<template>
  <div class="system-layout cleaning-page">
    <Sidebar default-active="2-1" />
    <main class="main-content">
      <header class="page-header">
        <NuxtLink to="/" class="home-link"><el-icon><ArrowLeft /></el-icon> 系统首页</NuxtLink>
        <span class="header-divider">/</span><h1>数据清洗与格式转换</h1>
        <NuxtLink to="/datainput" class="return-link">返回群体数据导入 <span>↗</span></NuxtLink>
      </header>

      <div class="page-container">
        <section class="page-intro">
          <div><span class="eyebrow">DATA PIPELINE · FORMAT WORKSPACE</span><h2>让原始表格，进入规范的数据流程</h2><p>上传 → 选择字段与清洗规则 → 核对预览 → 下载。原文件不变，不自动补值或猜测医学单位。</p></div>
          <div class="intro-badge"><el-icon><DocumentChecked /></el-icon><span>先预览，再下载<br /><small>每一步都有处理记录</small></span></div>
        </section>

        <section class="panel source-panel">
          <div class="section-heading"><div><span class="section-number">01</span><h3>上传原始数据</h3></div><span class="subtle">CSV / XLSX · 最大 {{ maxUploadMb }} MB · Excel 读取第一个工作表</span></div>
          <div class="source-upload-row">
            <label class="upload-zone" :class="{ disabled: busy }" for="cleaning-source-file">
              <el-icon><UploadFilled /></el-icon><span><strong>{{ sourceInfo ? sourceInfo.filename : '选择原始数据文件' }}</strong><small>{{ sourceInfo ? '可重新选择文件，原预览将被清除' : '表头放在第一行；一行代表一名受试者或一条记录' }}</small></span>
              <span class="upload-link">{{ inspecting ? '读取中…' : sourceInfo ? '更换文件' : '浏览文件' }}</span>
            </label>
            <input id="cleaning-source-file" ref="fileInputRef" class="file-input" type="file" accept=".csv,.xlsx" :disabled="busy" @change="selectSourceFile" />
            <div class="source-stats"><div><span>原始数据行</span><strong>{{ sourceInfo ? formatCount(sourceInfo.total_rows) : '—' }}</strong></div><div><span>原始字段列</span><strong>{{ sourceInfo ? sourceInfo.columns.length : '—' }}</strong></div></div>
          </div>
          <p class="privacy-note">旧版 XLS 请先另存为 XLSX。文件仅用于本次格式处理；不要上传非必要身份信息。清洗不等于数据正确性、科学有效性或临床评估。</p>
          <el-alert v-if="sourceError" :title="sourceError" type="error" :closable="false" show-icon />
          <div v-if="sourceInfo?.warnings?.length" class="notice-list"><p v-for="(warning, index) in sourceInfo.warnings" :key="index">{{ warning }}</p></div>
          <details v-if="sourceInfo" class="preview-details"><summary>查看原始数据预览 <span>前 {{ sourcePreviewRows.length }} 行；表头两端空白自动去除，单元格值尚未清洗</span></summary>
            <div class="table-scroll" tabindex="0" aria-label="原始数据预览，可横向滚动"><table class="data-table"><thead><tr><th v-for="column in sourceInfo.columns" :key="column">{{ column }}</th></tr></thead><tbody><tr v-for="(row, rowIndex) in sourcePreviewRows" :key="rowIndex"><td v-for="column in sourceInfo.columns" :key="column" :title="displayCell(row[column])">{{ displayCell(row[column]) }}</td></tr><tr v-if="!sourcePreviewRows.length"><td :colspan="Math.max(1, sourceInfo.columns.length)">文件没有数据行。</td></tr></tbody></table></div>
          </details>
        </section>

        <div class="workspace-grid">
          <section class="panel rules-panel">
            <div class="section-heading"><div><span class="section-number">02</span><h3>配置输出与清洗规则</h3></div></div>
            <fieldset :disabled="busy || !sourceInfo" class="rules-fieldset">
              <div class="mode-switch" aria-label="输出格式"><button type="button" :class="{ active: mode === 'system' }" @click="mode = 'system'">系统导入格式</button><button type="button" :class="{ active: mode === 'custom' }" @click="mode = 'custom'">自定义行与列</button></div>
              <div v-if="mode === 'system'" class="format-description"><strong>{{ schema?.name || '血压（连续结局）系统格式' }}</strong><p>将原始列映射为系统标准字段。只有完全相同的字段名会自动匹配；其他字段需要手动选择。缺失的字段不会被伪造或自动填充。</p></div>
              <div v-else class="format-description"><strong>保留需要的数据，按自己的列名导出</strong><p>勾选要保留的列，调整输出列名；可按原始行号截取或添加筛选条件。自定义文件不一定满足群体导入要求。</p></div>

              <div v-if="mode === 'system' && schema" class="mapping-toolbar"><span>必需字段 {{ mappedRequiredCount }} / {{ requiredFieldCount }} 已映射</span><button type="button" class="text-button" @click="restoreExactMappings">重新匹配同名列</button></div>
              <div v-if="mode === 'system' && schema" class="table-scroll mapping-scroll" tabindex="0" aria-label="系统字段映射">
                <table class="mapping-table"><thead><tr><th>系统字段 / 口径</th><th>对应的原始列</th></tr></thead><tbody><tr v-for="field in schema.fields" :key="field.column"><td><span class="field-label">{{ field.label }} <span v-if="field.required" class="required-mark">必需</span><span v-else class="optional-mark">可选</span></span><code>{{ field.column }}</code><small v-if="field.unit">{{ field.unit }}</small></td><td><select v-model="systemMappings[field.column]" :aria-label="`${field.label}对应原始列`"><option value="">{{ field.required ? '请选择原始列（尚未映射）' : '不导出此可选字段' }}</option><option v-for="column in sourceInfo?.columns || []" :key="column" :value="column">{{ column }}</option></select></td></tr></tbody></table>
              </div>
              <div v-if="mode === 'custom'" class="custom-columns"><div class="mapping-toolbar"><span>{{ selectedCustomCount }} / {{ customColumns.length }} 列已选择</span><div><button type="button" class="text-button" @click="setAllColumns(true)">全选</button><button type="button" class="text-button" @click="setAllColumns(false)">取消全选</button></div></div><div class="table-scroll mapping-scroll" tabindex="0" aria-label="自定义输出字段"><table class="mapping-table"><thead><tr><th>保留原始列</th><th>输出列名</th></tr></thead><tbody><tr v-for="column in customColumns" :key="column.source"><td><label class="checkbox-row"><input v-model="column.selected" type="checkbox" /><span>{{ column.source }}</span></label></td><td><input v-model="column.target" type="text" :disabled="!column.selected" :aria-label="`${column.source}输出列名`" /></td></tr></tbody></table></div></div>

              <div class="rule-section"><h4>通用清洗规则</h4><div class="check-options"><label class="checkbox-row"><input v-model="trimText" type="checkbox" /><span>去除单元格值两端空白 <small>表头空白始终去除</small></span></label><label class="checkbox-row"><input v-model="dropBlankRows" type="checkbox" /><span>删除所选输出字段全为空的记录</span></label><label class="checkbox-row"><input v-model="dropDuplicates" type="checkbox" /><span>删除完全重复的输出行 <small>可选，不按姓名或 ID 合并</small></span></label></div></div>
              <div class="rule-section"><h4>原始行范围 <span>先截取，其他规则在其后执行；不包含表头</span></h4><div class="range-row"><label>起始行<input v-model="rowStart" type="number" min="1" step="1" aria-label="原始数据起始行" /></label><span>—</span><label>结束行<input v-model="rowEnd" type="number" min="1" step="1" placeholder="留空表示最后一行" aria-label="原始数据结束行" /></label></div></div>
              <div class="rule-section filters-section"><div class="filter-heading"><h4>行筛选 <span>多条条件全部满足时保留</span></h4><button type="button" class="text-button" @click="addFilter">＋ 添加条件</button></div><p v-if="!filters.length" class="empty-filter">未设置筛选，保留所选范围内的全部记录。</p><div v-for="(filter, index) in filters" :key="filter.id" class="filter-row"><select v-model="filter.column" :aria-label="`筛选${index + 1}原始列`"><option value="">选择原始列</option><option v-for="column in sourceInfo?.columns || []" :key="column" :value="column">{{ column }}</option></select><select v-model="filter.operator" :aria-label="`筛选${index + 1}条件`"><option v-for="operator in filterOperators" :key="operator.value" :value="operator.value">{{ operator.label }}</option></select><input v-if="!['is_empty', 'not_empty'].includes(filter.operator)" v-model="filter.value" type="text" placeholder="比较值" :aria-label="`筛选${index + 1}比较值`" /><span v-else class="no-filter-value">无需比较值</span><button type="button" class="remove-filter" :aria-label="`删除筛选${index + 1}`" @click="filters.splice(index, 1)">×</button></div></div>
              <div v-if="mode === 'system'" class="semantic-confirm"><label class="checkbox-row"><input v-model="confirmSystemSemantics" type="checkbox" /><span>我已核对样本、单位与分类编码：金属为规定的血样单位，人口学、吸烟和饮酒等字段使用系统所需 NHANES 编码。</span></label><p>本页只调整表格结构，不自动换算单位，也不把“男/女”“是/否”等文本猜测为数值编码。不匹配时请选择自定义导出并先完成数据口径核对。</p></div>
              <div v-if="mode === 'system'" class="rule-section system-quality-options"><h4>系统记录检查 <span>按当前群体分析要求，不是临床判断</span></h4><div class="check-options"><label class="checkbox-row"><input v-model="dropInvalidSystemRows" type="checkbox" /><span>剔除不满足系统记录规则的行 <small>编号、数值格式、成人条件及有效血压读数；原文件保留</small></span></label><label class="checkbox-row"><input v-model="requireCompleteSystemRows" type="checkbox" /><span>仅保留关键字段完整的记录 <small>排除空白及明确非回答编码，会改变样本构成；不插补缺失值</small></span></label></div></div>
            </fieldset>
          </section>

          <aside class="action-column">
            <section class="panel action-panel"><span class="eyebrow">READY TO REVIEW</span><h3>核对后，生成规范文件</h3><p>{{ mode === 'system' ? '系统格式需要完整字段映射和明确的口径确认。仍可先预览，查看缺少哪些字段。' : '自定义输出可保留所需列和行；下载前请核对列名、筛选与处理记录。' }}</p><div class="action-summary"><span>输出方式<strong>{{ mode === 'system' ? '系统导入格式' : '自定义格式' }}</strong></span><span>预计输出列<strong>{{ outputColumnCount }} 列</strong></span><span>缺失值处理<strong>保留，不自动补值</strong></span></div><button type="button" class="primary-button" :disabled="!canPreview" @click="runCleaning"><el-icon v-if="previewing" class="is-loading"><Loading /></el-icon><el-icon v-else><MagicStick /></el-icon>{{ previewing ? '正在清洗与预览…' : '一键清洗并预览' }}</button><p class="action-footnote">只处理当前所选文件，原文件不被覆盖。</p><p v-if="!sourceInfo" class="action-status">请先上传原始数据。</p><p v-else-if="!outputColumnCount" class="action-status">请至少选择一个输出字段。</p></section>
            <section class="panel help-panel"><h4>当前系统格式说明</h4><p v-if="loadingSchema">正在读取后端字段规范…</p><template v-else-if="schema"><p>一行一名受试者。表头包含 {{ requiredFieldCount }} 个必需字段；可选字段按需映射。</p><ul><li v-for="(note, index) in schema.notes || []" :key="index">{{ note }}</li></ul></template><p v-if="schemaError" class="error-text">{{ schemaError }}</p><button v-if="schemaError" type="button" class="text-button" :disabled="busy" @click="loadSchema">重新读取字段规范</button><NuxtLink to="/datainput" class="help-link">查看群体导入与分析入口 ↗</NuxtLink></section>
          </aside>
        </div>

        <el-alert v-if="processError" class="process-alert" :title="processError" type="error" :closable="false" show-icon />
        <section v-if="result" ref="resultSectionRef" class="panel result-panel" aria-live="polite">
          <div class="section-heading"><div><span class="section-number">03</span><h3>清洗结果与下载</h3></div><button type="button" class="primary-button download-button" :disabled="!canDownload" @click="downloadResult"><el-icon><Download /></el-icon>{{ downloading ? '生成文件中…' : '下载清洗后的 CSV' }}</button></div>
          <div class="result-stats"><div><span>原始记录</span><strong>{{ formatCount(sourceInfo.total_rows) }} <small>行</small></strong></div><div><span>清洗后记录</span><strong>{{ formatCount(result.total_rows) }} <small>行</small></strong></div><div><span>输出字段</span><strong>{{ result.columns.length }} <small>列</small></strong></div><div><span>格式状态</span><strong class="status-text" :class="{ ready: mode === 'system' && result.system_ready }">{{ mode === 'custom' ? '自定义输出' : result.system_ready ? '结构与口径已确认' : '尚不满足系统导入' }}</strong></div></div>
          <el-alert v-if="mode === 'system' && result.missing_required_columns?.length" :title="`缺少 ${result.missing_required_columns.length} 个必需字段，请返回字段映射补充。`" type="warning" :closable="false" show-icon><div class="missing-columns"><code v-for="column in result.missing_required_columns" :key="column">{{ column }}</code></div></el-alert>
          <section v-if="mode === 'system'" class="recovery-panel" aria-label="系统格式修复与确认">
            <div class="recovery-heading"><div><h4>检查与整理后，再下载</h4><p>缺少必需列时请补充映射；删列或删行不能补齐字段，也不会自动确认测量口径。</p></div><button type="button" class="secondary-button" :disabled="busy || !!result.missing_required_columns?.length" @click="keepOnlyRequiredColumns">仅保留必需列并重新预览</button></div>
            <label class="checkbox-row result-semantic-confirm"><input type="checkbox" :checked="confirmSystemSemantics" :disabled="busy" @change="confirmAndRecheck" /><span>我已核对血液样本、列示单位与 NHANES 分类编码 <small>勾选后自动重新检查；未核对时请勿勾选。</small></span></label>
            <div v-if="result.row_quality?.checked" class="quality-summary"><div><span>已检查记录</span><strong>{{ formatCount(result.row_quality.checked_rows) }}</strong></div><div><span>满足所选规则</span><strong>{{ formatCount(result.row_quality.valid_rows) }}</strong></div><div><span>不满足所选规则</span><strong>{{ formatCount(result.row_quality.invalid_rows) }}</strong></div><div><span>本次已剔除</span><strong>{{ formatCount(result.row_quality.dropped_rows) }}</strong></div></div>
            <p v-if="result.row_quality && !result.row_quality.checked" class="warning-note">必需列尚未齐全，暂不能检查或剔除系统记录。请先完成字段映射。</p>
            <div v-if="result.row_quality?.reasons?.length" class="quality-reasons"><span v-for="reason in result.row_quality.reasons" :key="reason.code">{{ reason.label }}：{{ formatCount(reason.count) }}行</span><small>同一行可能有多个原因，原因计数不能相加作为总行数。</small></div>
            <div class="recovery-actions"><button type="button" class="primary-button" :disabled="busy || !hasInvalidSystemRows" @click="removeInvalidSystemRows">剔除不合格行并重新预览</button><button type="button" class="secondary-button" :disabled="busy" @click="runCleaning">重新检查当前规则</button><span>只影响下载副本；原文件不删除、不补值。</span></div>
            <details v-if="result.row_quality?.invalid_preview?.length" class="invalid-preview"><summary>查看不合格原始行号与原因（最多20行）</summary><ul><li v-for="row in result.row_quality.invalid_preview" :key="row.row_number">原始数据第 {{ row.row_number }} 行：{{ qualityReasonText(row.reason_codes) }}</li></ul></details>
          </section>
          <div v-if="result.warnings?.length" class="notice-list"><p v-for="(warning, index) in result.warnings" :key="index">{{ warning }}</p></div>
          <div class="result-caption"><h4>输出数据预览</h4><span>展示前 {{ result.preview.length }} 行 · 缺失单元格显示“—”，导出仍为空</span></div>
          <div class="table-scroll result-table" tabindex="0" aria-label="清洗结果预览，可横向滚动"><table class="data-table"><thead><tr><th v-for="column in result.columns" :key="column">{{ column }}</th></tr></thead><tbody><tr v-for="(row, rowIndex) in result.preview" :key="rowIndex"><td v-for="column in result.columns" :key="column" :title="displayCell(row[column])">{{ displayCell(row[column]) }}</td></tr><tr v-if="!result.preview.length"><td :colspan="Math.max(1, result.columns.length)">没有满足当前条件的数据行，请检查范围与筛选条件。</td></tr></tbody></table></div>
          <div class="result-caption"><h4>处理记录</h4><span>行数按实际处理顺序统计，不代表临床有效样本量</span></div>
          <div class="table-scroll audit-scroll"><table class="audit-table"><thead><tr><th>处理步骤</th><th>处理前</th><th>处理后</th><th>移除行</th><th>处理说明</th></tr></thead><tbody><tr v-for="(entry, index) in result.audit || []" :key="index"><td>{{ auditLabel(entry.action) }}</td><td>{{ formatCount(entry.before) }}</td><td>{{ formatCount(entry.after) }}</td><td>{{ formatCount(entry.removed) }}</td><td :title="auditDetails(entry)">{{ auditDetails(entry) }}</td></tr></tbody></table></div>
          <p class="result-boundary">下载文件只完成格式和所选规则转换。回到群体导入后，系统仍会检查必需字段、有效血压读数和成人分析条件；格式通过不等于数据质量或分析有效性通过。</p>
        </section>
        <footer class="page-footer">DATA PIPELINE · 原始输入保留，处理过程可核对</footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch, onMounted, nextTick } from 'vue'
import { ArrowLeft, UploadFilled, DocumentChecked, MagicStick, Loading, Download } from '@element-plus/icons-vue'

useHead({ title: '数据清洗与格式转换 · 智能风险预警系统' })
const api = useApi()
const schema = ref(null)
const schemaError = ref('')
const loadingSchema = ref(false)
const sourceFile = ref(null)
const sourceInfo = ref(null)
const sourceError = ref('')
const inspecting = ref(false)
const previewing = ref(false)
const downloading = ref(false)
const result = ref(null)
const processError = ref('')
const sourceVersion = ref(0)
const fileInputRef = ref(null)
const resultSectionRef = ref(null)
const mode = ref('system')
const systemMappings = reactive({})
const customColumns = ref([])
const trimText = ref(true)
const dropBlankRows = ref(true)
const dropDuplicates = ref(false)
const dropInvalidSystemRows = ref(false)
const requireCompleteSystemRows = ref(false)
const rowStart = ref(1)
const rowEnd = ref('')
const filters = ref([])
const confirmSystemSemantics = ref(false)
let inspectionGeneration = 0
let processingGeneration = 0
let filterGeneration = 0
const filterOperators = [
  { value: 'eq', label: '等于' }, { value: 'ne', label: '不等于' },
  { value: 'contains', label: '包含文本' }, { value: 'gt', label: '数值大于' },
  { value: 'gte', label: '数值大于等于' }, { value: 'lt', label: '数值小于' },
  { value: 'lte', label: '数值小于等于' }, { value: 'is_empty', label: '为空' },
  { value: 'not_empty', label: '不为空' }
]
const busy = computed(() => inspecting.value || previewing.value || downloading.value)
const requiredFieldCount = computed(() => schema.value?.fields.filter(field => field.required).length || 0)
const mappedRequiredCount = computed(() => schema.value?.fields.filter(field => field.required && systemMappings[field.column]).length || 0)
const selectedCustomCount = computed(() => customColumns.value.filter(column => column.selected).length)
const outputColumnCount = computed(() => mode.value === 'system' ? Object.values(systemMappings).filter(Boolean).length : selectedCustomCount.value)
const sourcePreviewRows = computed(() => sourceInfo.value?.preview?.slice(0, 6) || [])
const maxUploadMb = computed(() => Math.round((schema.value?.limits?.max_file_bytes || 25 * 1024 * 1024) / 1024 / 1024))
const options = computed(() => ({
  mode: mode.value,
  outcome_id: 'blood_pressure',
  columns: mode.value === 'system'
    ? (schema.value?.fields || []).filter(field => systemMappings[field.column]).map(field => ({ source: systemMappings[field.column], target: field.column }))
    : customColumns.value.filter(column => column.selected).map(column => ({ source: column.source, target: column.target })),
  trim_text: trimText.value, drop_blank_rows: dropBlankRows.value, drop_duplicates: dropDuplicates.value,
  drop_invalid_system_rows: mode.value === 'system' && dropInvalidSystemRows.value,
  require_complete_system_rows: mode.value === 'system' && requireCompleteSystemRows.value,
  row_start: rowStart.value === '' ? null : Number(rowStart.value),
  row_end: rowEnd.value === '' || rowEnd.value === null ? null : Number(rowEnd.value),
  filters: filters.value.map(({ column, operator, value }) => ({ column, operator, value })),
  confirm_system_semantics: confirmSystemSemantics.value
}))
const fingerprint = computed(() => `${sourceVersion.value}:${JSON.stringify(options.value)}`)
const resultFingerprint = ref('')
const canPreview = computed(() => !!sourceInfo.value && !busy.value && outputColumnCount.value > 0 && (mode.value === 'custom' || !!schema.value))
const canDownload = computed(() => !!result.value && resultFingerprint.value === fingerprint.value && !busy.value && result.value.total_rows > 0 && (mode.value === 'custom' || (result.value.system_ready && confirmSystemSemantics.value)))
const hasInvalidSystemRows = computed(() => mode.value === 'system' && result.value?.row_quality?.checked && result.value.row_quality.invalid_rows > (result.value.row_quality.dropped_rows || 0) && !result.value.missing_required_columns?.length)

// A confirmation applies to the selected measurement/coding fields, not a future mapping.
watch(() => JSON.stringify((schema.value?.fields || []).filter(field => field.required).map(field => [field.column, systemMappings[field.column] || ''])), () => {
  confirmSystemSemantics.value = false
}, { flush: 'sync' })

// A changed source or rule set cannot reuse a preview from an older request.
watch(fingerprint, () => {
  processingGeneration += 1
  result.value = null
  resultFingerprint.value = ''
  processError.value = ''
}, { flush: 'sync' })

async function loadSchema() {
  loadingSchema.value = true
  schemaError.value = ''
  try {
    const response = await api.getCleaningSchema('blood_pressure')
    if (!response.success) { schema.value = null; schemaError.value = response.error || '无法读取后端字段规范。'; return }
    schema.value = response.data
    if (sourceInfo.value) restoreExactMappings()
  } catch { schema.value = null; schemaError.value = '字段规范读取失败，请检查后端连接。' }
  finally { loadingSchema.value = false }
}

function restoreExactMappings() {
  Object.keys(systemMappings).forEach(key => delete systemMappings[key])
  const columns = sourceInfo.value?.columns || []
  for (const field of schema.value?.fields || []) systemMappings[field.column] = columns.includes(field.column) ? field.column : ''
  confirmSystemSemantics.value = false
}

async function selectSourceFile(event) {
  const selected = event.target.files?.[0]
  if (!selected) return
  const generation = ++inspectionGeneration
  sourceVersion.value += 1
  sourceFile.value = null
  sourceInfo.value = null
  sourceError.value = ''
  filters.value = []
  dropInvalidSystemRows.value = false
  requireCompleteSystemRows.value = false
  rowStart.value = 1
  rowEnd.value = ''
  customColumns.value = []
  restoreExactMappings()
  if (!/\.(csv|xlsx)$/i.test(selected.name)) { sourceError.value = '仅支持 CSV 或 XLSX 文件；旧版 XLS 请先另存为 XLSX。'; event.target.value = ''; return }
  if (selected.size > maxUploadMb.value * 1024 * 1024) { sourceError.value = `文件超过 ${maxUploadMb.value} MB，请先拆分文件。`; event.target.value = ''; return }
  inspecting.value = true
  try {
    const response = await api.inspectCleaningFile(selected)
    if (generation !== inspectionGeneration) return
    if (!response.success) { sourceError.value = response.error || '原始文件读取失败。'; return }
    sourceFile.value = selected
    sourceInfo.value = response.data
    customColumns.value = response.data.columns.map(source => ({ source, target: source, selected: true }))
    restoreExactMappings()
  } catch { if (generation === inspectionGeneration) sourceError.value = '原始文件读取失败，请检查后端连接。' }
  finally { if (generation === inspectionGeneration) { inspecting.value = false; event.target.value = '' } }
}

function setAllColumns(selected) { customColumns.value.forEach(column => { column.selected = selected }) }
async function confirmAndRecheck(event) {
  if (busy.value) return
  confirmSystemSemantics.value = event.target.checked
  await nextTick()
  await runCleaning()
}
async function keepOnlyRequiredColumns() {
  if (busy.value || mode.value !== 'system' || result.value?.missing_required_columns?.length) return
  for (const field of schema.value?.fields || []) if (!field.required) systemMappings[field.column] = ''
  await nextTick()
  await runCleaning()
}
async function removeInvalidSystemRows() {
  if (busy.value || !hasInvalidSystemRows.value) return
  dropInvalidSystemRows.value = true
  await nextTick()
  await runCleaning()
}
function qualityReasonText(codes) {
  const reasons = result.value?.row_quality?.reasons || []
  return (codes || []).map(code => reasons.find(reason => reason.code === code)?.label || code).join('；')
}
function addFilter() {
  if (filters.value.length >= 20) { processError.value = '最多设置 20 条筛选条件。'; return }
  filters.value.push({ id: ++filterGeneration, column: '', operator: 'eq', value: '' })
}
function validateSettings() {
  const config = options.value
  if (!Number.isInteger(config.row_start) || config.row_start < 1) return '起始行必须为大于等于 1 的整数。'
  if (config.row_end !== null && (!Number.isInteger(config.row_end) || config.row_end < config.row_start)) return '结束行必须为不小于起始行的整数，或留空。'
  if (sourceInfo.value && (config.row_start > Math.max(1, sourceInfo.value.total_rows) || (config.row_end !== null && config.row_end > sourceInfo.value.total_rows))) return '行范围超出原始数据记录数，请核对起始和结束行。'
  const names = config.columns.map(column => column.target.trim())
  if (names.some(name => !name)) return '输出列名不能为空。'
  if (names.some(name => name.length > 256 || name.includes('\u0000'))) return '输出列名不能超过 256 个字符或包含空字符。'
  if (new Set(names).size !== names.length) return '输出列名存在重复，请调整自定义列名。'
  if (new Set(config.columns.map(column => column.source)).size !== config.columns.length) return '同一原始列不能映射到多个系统字段，请核对字段对应关系。'
  if (config.filters.some(filter => !filter.column)) return '请为每条筛选条件选择原始列，或删除不需要的条件。'
  if (config.filters.some(filter => filter.value.length > 1024)) return '筛选比较值不能超过 1024 个字符。'
  if (config.filters.some(filter => ['gt', 'gte', 'lt', 'lte'].includes(filter.operator) && (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(filter.value.trim()) || !Number.isFinite(Number(filter.value))))) return '数值筛选的比较值必须是有效数字。'
  return ''
}

async function runCleaning() {
  if (!canPreview.value) return
  const invalid = validateSettings()
  if (invalid) { processError.value = invalid; return }
  processError.value = ''
  result.value = null
  const capturedFingerprint = fingerprint.value
  const capturedOptions = JSON.parse(JSON.stringify(options.value))
  const capturedFile = sourceFile.value
  const generation = ++processingGeneration
  previewing.value = true
  try {
    const response = await api.previewCleanedData(capturedFile, capturedOptions)
    if (generation !== processingGeneration || capturedFingerprint !== fingerprint.value) return
    if (!response.success) { processError.value = response.error || '清洗失败，请核对字段与规则。'; return }
    result.value = response.data
    resultFingerprint.value = capturedFingerprint
    await nextTick()
    resultSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch { if (generation === processingGeneration) processError.value = '清洗请求失败，请检查后端连接。' }
  finally { previewing.value = false }
}

async function downloadResult() {
  if (!canDownload.value) return
  const capturedFingerprint = fingerprint.value
  const capturedOptions = JSON.parse(JSON.stringify(options.value))
  const capturedFile = sourceFile.value
  const generation = processingGeneration
  downloading.value = true
  processError.value = ''
  try {
    const response = await api.downloadCleanedData(capturedFile, capturedOptions)
    if (generation !== processingGeneration || capturedFingerprint !== fingerprint.value) return
    if (!response.success) { processError.value = response.error || '下载文件生成失败。'; return }
    if (!(response.data instanceof Blob)) { processError.value = '下载响应不是文件，请检查后端。'; return }
    const safeBase = capturedFile.name.replace(/\.[^.]+$/, '').replace(/[^\p{L}\p{N}_-]/gu, '_').slice(0, 100) || 'data'
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `${safeBase}_${capturedOptions.mode === 'system' ? 'system' : 'cleaned'}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    // Keep the object URL alive long enough for the browser download to start.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch { if (generation === processingGeneration) processError.value = '下载请求失败，请稍后重试。' }
  finally { downloading.value = false }
}

function displayCell(value) { return value === '' || value === null || value === undefined ? '—' : String(value) }
function formatCount(value) { return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString() : '—' }
function auditLabel(action) {
  const labels = { row_range: '按原始行范围截取', trim_text: '去除单元格两端空白', drop_blank_rows: '删除输出字段全空记录', filters: '按条件筛选', filter: '按条件筛选', column_mapping: '选择与重命名字段', select_columns: '选择与重命名字段', drop_duplicates: '删除完全重复的输出行', check_system_rows: '检查系统记录规则', drop_invalid_system_rows: '剔除不满足系统规则的行', normalize_system_numeric_for_csv: '安全数值格式规范化', formula_escape: '导出文本公式防护', csv_formula_protection: '导出文本公式防护' }
  return labels[action] || action
}
function auditDetails(entry) {
  if (entry.action === 'check_system_rows') return entry.checked ? `已检查；发现 ${formatCount(entry.invalid_rows)} 条不合格记录，此步骤不删行` : '未执行行检查：请先补齐必需列'
  if (entry.action === 'drop_invalid_system_rows') return '按当前系统记录规则剔除；未修改原文件或填补缺失值'
  if (typeof entry.changed_cells === 'number') return `调整 ${formatCount(entry.changed_cells)} 个单元格`
  if (typeof entry.protected_cells === 'number') return `防护 ${formatCount(entry.protected_cells)} 个文本值 / 列名`
  if (typeof entry.columns_before === 'number') return `${entry.columns_before} 列 → ${entry.columns_after} 列`
  if (entry.filter_index) return `条件 ${entry.filter_index}：${entry.column} ${filterOperators.find(item => item.value === entry.operator)?.label || entry.operator}`
  if (entry.row_start) return `原始第 ${entry.row_start} 行至 ${entry.row_end || '末行'}`
  return '—'
}
onMounted(loadSchema)
</script>

<style scoped>
* { box-sizing: border-box; }
.system-layout { display: flex; min-height: 100vh; background: #f7f9fc; color: #182b43; font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.system-layout :deep(.sidebar) { position: sticky; top: 0; height: 100vh; }
.main-content { flex: 1; min-width: 0; }
.page-header { display: flex; align-items: center; gap: 16px; min-height: 80px; padding: 18px 36px; border-bottom: 1px solid #e2e8f0; background: #fff; }
.page-header h1 { font-size: 20px; font-weight: 700; margin: 0; flex: 1; }
.home-link, .return-link { text-decoration: none; color: #247ebc; font-size: 13px; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.return-link { color: #60768d; }
.header-divider { color: #d0d9e4; }
.page-container { max-width: 1440px; padding: 30px 36px 16px; margin: 0 auto; }
.page-intro { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin: 2px 0 26px; }
.eyebrow { font-size: 10px; color: #4c82ac; font-weight: 800; letter-spacing: 1.4px; }
.page-intro h2 { font-size: 26px; letter-spacing: -0.5px; line-height: 1.45; margin: 10px 0 10px; }
.page-intro p { font-size: 14px; color: #64748b; line-height: 1.8; margin: 0; }
.intro-badge { color: #527da3; display: flex; gap: 12px; align-items: center; font-size: 12px; padding: 16px 20px; border: 1px solid #e0eaf5; border-radius: 12px; background: #f0f6fe; flex-shrink: 0; line-height: 1.8; }
.intro-badge .el-icon { font-size: 26px; }
.intro-badge small { font-size: 12px; color: #64748b; }
.panel { background: #fff; border: 1px solid #dce6f1; border-radius: 16px; padding: 24px; box-shadow: 0 5px 20px #254c7510; min-width: 0; }
.section-heading { display: flex; align-items: center; gap: 16px; justify-content: space-between; margin-bottom: 20px; }
.section-heading > div { display: flex; align-items: center; gap: 10px; }
.section-heading h3 { font-size: 16px; margin: 0; line-height: 1.5; }
.section-number { width: 28px; height: 28px; border-radius: 8px; display: grid; place-items: center; background: #eaf3fd; color: #2b82bf; font-size: 11px; font-weight: 800; }
.subtle { font-size: 12px; color: #64748b; text-align: right; line-height: 1.6; }
.source-upload-row { display: flex; gap: 20px; align-items: stretch; }
.upload-zone { flex: 1; display: flex; align-items: center; gap: 16px; min-width: 0; padding: 22px; border: 1px dashed #9ebfe0; border-radius: 12px; background: #f7fbff; cursor: pointer; transition: border-color .15s, background .15s; }
.upload-zone:hover { background: #f0f7ff; border-color: #2f84c7; }
.upload-zone.disabled { cursor: wait; opacity: .65; }
.upload-zone > .el-icon { flex-shrink: 0; font-size: 30px; color: #428dcc; }
.upload-zone > span:nth-child(2) { display: flex; flex-direction: column; gap: 7px; flex: 1; min-width: 0; }
.upload-zone strong { font-size: 14px; overflow-wrap: anywhere; }
.upload-zone small { font-size: 12px; color: #64748b; line-height: 1.7; }
.upload-link { font-size: 13px; color: #267cbe; white-space: nowrap; }
.file-input { width: 1px; height: 1px; position: absolute; opacity: 0; }
.upload-zone:has(+ .file-input:focus-visible) { outline: 3px solid #9cc7f0; outline-offset: 2px; }
.source-stats { display: grid; grid-template-columns: 1fr 1fr; align-items: center; border: 1px solid #e6edf5; border-radius: 12px; padding: 15px 8px; flex: 0 0 208px; background: #fbfcfe; }
.source-stats > div { padding: 0 14px; display: flex; flex-direction: column; gap: 8px; }
.source-stats > div + div { border-left: 1px solid #e5ecf4; }
.source-stats span { font-size: 12px; color: #64748b; }
.source-stats strong { font-size: 24px; color: #315d83; font-weight: 700; }
.privacy-note { font-size: 12px; color: #64748b; line-height: 1.8; margin: 14px 0 0; }
.preview-details { margin-top: 16px; border-top: 1px solid #edf2f8; padding-top: 12px; }
.preview-details summary { cursor: pointer; font-size: 13px; font-weight: 650; color: #475569; line-height: 1.8; }
.preview-details summary span { margin-left: 10px; color: #64748b; font-size: 12px; font-weight: 400; }
.table-scroll { width: 100%; max-width: 100%; overflow: auto; border: 1px solid #e1eaf4; border-radius: 10px; margin-top: 12px; }
.data-table { min-width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
.data-table th { font-size: 12px; white-space: nowrap; background: #f3f7fc; color: #475569; padding: 12px 14px; border-bottom: 1px solid #e1eaf4; font-weight: 650; }
.data-table td { font-size: 13px; padding: 11px 14px; border-bottom: 1px solid #edf2f7; max-width: 260px; white-space: nowrap; color: #475569; overflow: hidden; text-overflow: ellipsis; }
.data-table tbody tr:nth-child(even) { background: #fbfdff; }
.data-table tbody tr:last-child td { border: 0; }
.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; align-items: start; gap: 22px; margin-top: 22px; }
.rules-fieldset { padding: 0; margin: 0; border: 0; min-width: 0; }
.rules-fieldset:disabled { opacity: .6; }
.mode-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 4px; border-radius: 10px; background: #f0f4f9; }
.mode-switch button { cursor: pointer; border: 0; background: transparent; color: #64748b; font-size: 13px; font-weight: 650; padding: 12px; border-radius: 8px; }
.mode-switch button.active { background: #fff; color: #247dc2; box-shadow: 0 2px 7px #42658512; }
.format-description { padding: 18px 0 0; }
.format-description strong { font-size: 14px; color: #355b7a; }
.format-description p { color: #64748b; font-size: 13px; line-height: 1.85; margin: 7px 0 14px; }
.mapping-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 12px; color: #64748b; }
.text-button { padding: 4px 0; border: 0; background: none; font-size: 12px; color: #2d81bf; cursor: pointer; margin-left: 12px; }
.text-button:hover { color: #1c5f93; text-decoration: underline; }
.mapping-scroll { max-height: 372px; }
.mapping-table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
.mapping-table th { padding: 12px 14px; background: #f4f8fc; color: #475569; font-size: 13px; position: sticky; top: 0; z-index: 1; border-bottom: 1px solid #e0e9f2; }
.mapping-table th:first-child { width: 48%; }
.mapping-table td { border-bottom: 1px solid #edf2f7; padding: 12px 14px; font-size: 13px; }
.mapping-table tr:last-child td { border: 0; }
.mapping-table code { display: block; color: #64748b; font-size: 12px; margin-top: 5px; overflow-wrap: anywhere; line-height: 1.6; }
.mapping-table small { display: block; color: #64748b; font-size: 12px; margin-top: 4px; }
.field-label { font-size: 13px; color: #475569; }
.required-mark, .optional-mark { font-size: 12px; margin-left: 4px; color: #64748b; border-radius: 3px; padding: 2px 3px; background: #f0f4f9; white-space: nowrap; }
.required-mark { color: #5585af; background: #edf5fd; }
select, input[type='text'], input[type='number'] { font: inherit; background: #fff; border: 1px solid #d6e1ed; border-radius: 6px; min-width: 0; width: 100%; height: 36px; color: #475569; padding: 0 9px; font-size: 13px; }
select:focus-visible, input:focus-visible, button:focus-visible { outline: 2px solid #87b9e5; outline-offset: 2px; }
select:disabled, input:disabled { background: #f5f7fa; color: #9aa9bb; }
.rule-section { margin-top: 20px; padding-top: 18px; border-top: 1px solid #edf1f7; }
.rule-section h4 { font-size: 13px; color: #475569; margin: 0 0 12px; line-height: 1.8; }
.rule-section h4 span { color: #64748b; font-weight: 400; font-size: 12px; margin-left: 5px; }
.check-options { display: flex; flex-direction: column; gap: 12px; }
.checkbox-row { display: flex; align-items: flex-start; gap: 9px; font-size: 13px; color: #475569; line-height: 1.75; cursor: pointer; min-width: 0; }
.checkbox-row input[type='checkbox'] { accent-color: #2f82c3; margin: 3px 0 0; flex-shrink: 0; width: 13px; height: 13px; }
.checkbox-row span { overflow-wrap: anywhere; }
.checkbox-row small { display: inline; font-size: 12px; color: #64748b; margin-left: 5px; }
.range-row { display: flex; gap: 12px; align-items: end; }
.range-row label { flex: 1; color: #64748b; font-size: 12px; display: flex; flex-direction: column; gap: 7px; }
.range-row > span { color: #a8b4c3; height: 34px; display: flex; align-items: center; }
.filter-heading { display: flex; align-items: center; gap: 12px; justify-content: space-between; }
.filter-heading h4 { margin-bottom: 0; }
.empty-filter { color: #64748b; font-size: 12px; margin: 14px 0 0; line-height: 1.7; }
.filter-row { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 1fr) 24px; gap: 8px; margin-top: 10px; align-items: center; }
.remove-filter { font-size: 19px; color: #98a8b9; border: 0; background: none; cursor: pointer; padding: 0; }
.remove-filter:hover { color: #d17070; }
.no-filter-value { font-size: 12px; color: #64748b; }
.semantic-confirm { padding: 14px; background: #f3f8fd; border: 1px solid #deebf7; border-radius: 10px; margin-top: 22px; }
.semantic-confirm .checkbox-row { color: #4d7596; }
.semantic-confirm p { font-size: 12px; line-height: 1.85; color: #64748b; margin: 9px 0 0 22px; }
.system-quality-options { display: grid; gap: 12px; }
.system-quality-options h4 { margin-bottom: 0; }
.system-quality-options .checkbox-row small { display: block; margin: 2px 0 0; }
.recovery-panel { border: 1px solid #deebf7; background: #f7fbff; border-radius: 12px; padding: 20px; margin: 16px 0; }
.recovery-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; }
.recovery-heading h4 { margin: 0 0 7px; font-size: 14px; color: #345f83; }
.recovery-heading p { font-size: 12px; line-height: 1.85; color: #64748b; margin: 0; max-width: 700px; }
.secondary-button { border: 1px solid #c8ddec; border-radius: 8px; color: #36739e; background: #fff; padding: 10px 14px; font-size: 12px; font-weight: 650; cursor: pointer; flex-shrink: 0; }
.secondary-button:hover { border-color: #73a9d2; background: #f0f7fe; }
.result-semantic-confirm { margin: 16px 0; padding: 14px; border: 1px solid #d8e8f5; border-radius: 8px; background: #fff; }
.result-semantic-confirm small { display: block; margin: 3px 0 0; }
.quality-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
.quality-summary > div { display: flex; flex-direction: column; gap: 7px; padding-right: 12px; border-right: 1px solid #e1eaf3; }
.quality-summary > div:last-child { border-right: 0; }
.quality-summary span { font-size: 12px; color: #64748b; }
.quality-summary strong { font-size: 22px; font-weight: 700; color: #3e6688; }
.quality-reasons { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 14px 0; }
.quality-reasons > span { border: 1px solid #eee1cc; background: #fffaf3; color: #98713d; border-radius: 5px; padding: 5px 8px; font-size: 12px; line-height: 1.8; }
.quality-reasons small { flex-basis: 100%; color: #64748b; font-size: 12px; line-height: 1.8; }
.recovery-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin: 16px 0 0; }
.recovery-actions .primary-button { width: auto; padding: 11px 14px; }
.recovery-actions > span { color: #64748b; font-size: 12px; line-height: 1.8; }
.invalid-preview { margin-top: 16px; padding-top: 12px; border-top: 1px solid #e2ecf5; }
.invalid-preview summary { cursor: pointer; font-size: 12px; color: #547695; }
.invalid-preview ul { margin: 12px 0 0; padding-left: 18px; max-height: 220px; overflow: auto; color: #64748b; font-size: 12px; line-height: 1.85; }
.action-column { position: sticky; top: 22px; display: grid; gap: 18px; min-width: 0; }
.action-panel h3 { font-size: 17px; margin: 10px 0; color: #294e6e; }
.action-panel > p { font-size: 13px; color: #64748b; line-height: 1.85; margin: 0; }
.action-summary { display: flex; flex-direction: column; gap: 15px; margin: 22px 0; padding: 18px 0; border-block: 1px solid #edf2f8; }
.action-summary span { font-size: 12px; color: #64748b; display: flex; justify-content: space-between; gap: 10px; }
.action-summary strong { font-size: 12px; color: #475569; font-weight: 650; }
.primary-button { border: 0; border-radius: 8px; background: #277fc0; color: #fff; padding: 13px 16px; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; font-size: 13px; font-weight: 650; cursor: pointer; box-shadow: 0 3px 8px #247cb918; transition: background .15s; }
.primary-button:hover { background: #1e6ba4; }
button:disabled { cursor: not-allowed; opacity: .55; }
.action-panel .action-footnote { font-size: 12px; text-align: center; margin-top: 10px; }
.action-panel .action-status { color: #936d32; font-size: 12px; margin-top: 12px; }
.help-panel h4 { font-size: 13px; margin: 0 0 10px; color: #475569; }
.help-panel p, .help-panel li { color: #64748b; font-size: 12px; line-height: 1.9; overflow-wrap: anywhere; }
.help-panel ul { padding-left: 16px; margin: 12px 0; }
.help-panel li { margin: 7px 0; }
.help-link { text-decoration: none; color: #2e75a8; font-size: 12px; line-height: 1.7; display: block; padding-top: 12px; border-top: 1px solid #edf2f7; }
.help-panel .error-text { color: #bd6565; }
.process-alert { margin-top: 22px; }
.result-panel { margin-top: 24px; scroll-margin-top: 20px; }
.download-button { width: auto; flex-shrink: 0; padding: 11px 16px; }
.result-stats { display: grid; grid-template-columns: 1fr 1fr .8fr 1.5fr; gap: 12px; padding: 18px 0; margin-bottom: 16px; border-block: 1px solid #edf2f7; }
.result-stats > div { display: flex; flex-direction: column; gap: 10px; border-right: 1px solid #edf2f7; padding-right: 12px; }
.result-stats > div:last-child { border: 0; }
.result-stats span { color: #64748b; font-size: 12px; }
.result-stats strong { font-size: 25px; color: #345f83; }
.result-stats small { font-size: 12px; font-weight: 400; color: #64748b; }
.result-stats .status-text { font-size: 13px; color: #94713c; line-height: 2; }
.result-stats .status-text.ready { color: #448675; }
.result-caption { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-top: 22px; }
.result-caption h4 { margin: 0; font-size: 13px; color: #475569; }
.result-caption span { font-size: 12px; color: #64748b; line-height: 1.7; }
.result-table { max-height: 350px; }
.result-table th { position: sticky; top: 0; }
.audit-table { width: 100%; border-collapse: collapse; text-align: left; }
.audit-table th, .audit-table td { padding: 12px 15px; font-size: 13px; border-bottom: 1px solid #edf2f8; color: #475569; }
.audit-table th { background: #f7fafd; color: #475569; font-weight: 650; }
.audit-table th:not(:first-child), .audit-table td:not(:first-child) { text-align: right; }
.audit-table th:last-child, .audit-table td:last-child { text-align: left; font-size: 12px; max-width: 240px; overflow-wrap: anywhere; color: #64748b; }
.audit-table tr:last-child td { border: 0; }
.notice-list, .warning-note { font-size: 13px; color: #936b32; line-height: 1.8; background: #fffaf3; padding: 10px 14px; border-radius: 8px; margin-top: 14px; }
.notice-list p { margin: 4px 0; }
.missing-columns { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.missing-columns code { background: #ffffff8a; padding: 2px 4px; border-radius: 4px; font-size: 12px; }
.result-boundary { font-size: 12px; line-height: 1.85; color: #64748b; margin: 18px 0 0; padding-top: 14px; border-top: 1px solid #edf2f7; }
.page-footer { text-align: center; color: #64748b; font-size: 12px; letter-spacing: .5px; padding: 24px 0 12px; }
@media (max-width: 1450px) { .workspace-grid { grid-template-columns: minmax(0, 1fr) 260px; gap: 18px; } .page-container { padding: 26px 28px 16px; } .panel { padding: 22px; } .page-intro h2 { font-size: 23px; } .intro-badge { padding: 14px; } }
@media (max-width: 1240px) { .system-layout :deep(.sidebar) { width: 245px; } .workspace-grid { grid-template-columns: minmax(0, 1fr); } .action-column { position: static; grid-template-columns: 1fr 1fr; } .action-panel .action-summary { margin: 14px 0; gap: 10px; padding: 12px 0; } .source-stats { flex-basis: 170px; padding: 12px 0; } .source-stats > div { padding: 0 10px; } .page-header { padding: 18px 28px; } .intro-badge { display: none; } .recovery-heading { flex-wrap: wrap; gap: 12px; } }
@media (max-width: 1050px) { .page-container { padding: 24px 22px 16px; } .page-header { padding: 18px 22px; gap: 10px; } .page-header h1 { font-size: 17px; } .return-link { font-size: 12px; } .section-heading { align-items: flex-start; } .source-upload-row { flex-wrap: wrap; gap: 12px; } .source-stats { flex-basis: 100%; display: flex; gap: 25px; } .source-stats > div { flex: 1; flex-direction: row; align-items: center; justify-content: space-between; } .source-stats strong { font-size: 20px; } .section-heading .subtle { max-width: 230px; } }
</style>
