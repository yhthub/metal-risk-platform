<template>
  <section class="cohort-profile" aria-labelledby="cohort-profile-title">
    <header class="profile-heading">
      <div><span class="section-label">COHORT PROFILE</span><h3 id="cohort-profile-title">群体基本资料</h3><p>先了解本次上传的人群，再查看下方模型计算结果。</p></div>
      <span class="scope-tag">整份文件 · 原始资料统计</span>
    </header>
    <div class="profile-totals">
      <div class="total-item total-primary"><span>本次上传总人数</span><strong>{{ count(totalRecords) }}<small>人</small></strong></div>
      <div class="total-item total-ready"><span>满足模型必需输入</span><strong>{{ count(processedRecords) }}<small>人</small></strong></div>
      <div class="total-item total-skipped"><span>输入不合格 / 未计算</span><strong>{{ count(skippedRecords) }}<small>人</small></strong></div>
      <p>分类人数及比例以全部 {{ count(totalRecords) }} 人为分母，包含暂未进入模型的对象；未加抽样权重。</p>
    </div>
    <div v-if="validProfile" class="demographic-grid">
      <article class="demographic-card sex-card">
        <h4><span class="heading-mark blue"></span>男女比例</h4>
        <div class="sex-summary">
          <div class="sex-ring" :style="{ background: sexGradient }" role="img" :aria-label="sexDescription"><div><strong>{{ count(validProfile.sex.valid_count) }}</strong><span>性别已知</span></div></div>
          <ul class="category-list sex-list"><li v-for="(item, index) in validProfile.sex.categories" :key="item.key"><span class="category-name"><i :style="{ background: categoryColor('sex', item.key, index) }"></i>{{ item.label }}</span><span class="category-value">{{ count(item.count) }} 人 <small>{{ percent(item.percent) }}</small></span></li></ul>
        </div>
      </article>
      <article class="demographic-card age-card">
        <h4><span class="heading-mark green"></span>年龄分布</h4>
        <div class="age-summary"><strong>{{ number(validProfile.age.mean) }}<small>岁 · 平均年龄</small></strong><span v-if="validProfile.age.valid_count">{{ count(validProfile.age.valid_count) }} 人有效年龄 · 范围 {{ number(validProfile.age.min) }}–{{ number(validProfile.age.max) }} 岁</span><span v-else>未提供有效年龄</span></div>
        <ul class="category-list compact-list"><li v-for="(item, index) in validProfile.age.bands" :key="item.key"><div class="bar-label"><span>{{ item.label }}</span><span>{{ count(item.count) }} 人 <small>{{ percent(item.percent) }}</small></span></div><div class="proportion-track"><span :style="{ width: barWidth(item.percent), background: categoryColor('age', item.key, index) }"></span></div></li></ul>
      </article>
      <article class="demographic-card marital-card">
        <h4><span class="heading-mark orange"></span>婚姻情况</h4>
        <ul class="category-list compact-list"><li v-for="(item, index) in validProfile.marital.categories" :key="item.key"><div class="bar-label"><span>{{ item.label }}</span><span>{{ count(item.count) }} 人 <small>{{ percent(item.percent) }}</small></span></div><div class="proportion-track"><span :style="{ width: barWidth(item.percent), background: categoryColor('marital', item.key, index) }"></span></div></li></ul>
      </article>
      <article class="demographic-card education-card">
        <h4><span class="heading-mark purple"></span>学历情况</h4>
        <ul class="category-list compact-list"><li v-for="(item, index) in validProfile.education.categories" :key="item.key"><div class="bar-label"><span>{{ item.label }}</span><span>{{ count(item.count) }} 人 <small>{{ percent(item.percent) }}</small></span></div><div class="proportion-track"><span :style="{ width: barWidth(item.percent), background: categoryColor('education', item.key, index) }"></span></div></li></ul>
      </article>
    </div>
    <p v-else class="profile-unavailable">{{ totalRecords === 0 ? '尚无上传对象，暂无可统计的人口学资料。' : '本次结果尚未包含完整的原始人口学资料；请重新计算整份文件以显示性别、年龄、婚姻和学历统计，不以模型合格对象代替全体。' }}</p>
    <p v-if="validProfile" class="profile-note">缺失、无效或无法确认的分类保留为“未知 / 未提供”，不按零值填补。人口学分布不等同于风险差异；NHANES 年龄 80 岁及以上采用公开数据顶端编码。</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CohortDemographicProfile } from '~/utils/riskCohort'
const props = defineProps<{ profile?: CohortDemographicProfile | null; totalRecords: number; processedRecords: number; skippedRecords: number }>()
const integerCount = (value: unknown, total: number): value is number => typeof value === 'number' && Number.isInteger(value) && value >= 0 && value <= total
function summaryValid(value: unknown, total: number, numeric = false): boolean {
  if (!value || typeof value !== 'object') return false
  const summary = value as Record<string, any>
  if (!Array.isArray(summary.source_columns) || !summary.source_columns.every((name: unknown) => typeof name === 'string') || typeof summary.available !== 'boolean'
    || !['valid_count', 'missing_count', 'unknown_count'].every(key => integerCount(summary[key], total))
    || summary.valid_count + summary.unknown_count !== total || summary.missing_count > summary.unknown_count) return false
  const categories = numeric ? summary.bands : summary.categories
  if (!Array.isArray(categories) || !categories.length) return false
  const keys = new Set<string>()
  let counted = 0; let unknown = 0
  for (const item of categories) {
    if (!item || typeof item.key !== 'string' || !item.key || keys.has(item.key) || typeof item.label !== 'string' || !item.label
      || !integerCount(item.count, total) || typeof item.percent !== 'number' || !Number.isFinite(item.percent)
      || item.percent < 0 || item.percent > 100 || Math.abs(item.percent - item.count / total * 100) > 0.06) return false
    keys.add(item.key); counted += item.count
    if (item.key === 'unknown') unknown += item.count
  }
  if (counted !== total || unknown !== summary.unknown_count) return false
  if (!numeric) return true
  if (!integerCount(summary.invalid_count, total) || summary.invalid_count + summary.missing_count !== summary.unknown_count) return false
  const statistics = [summary.mean, summary.median, summary.min, summary.max]
  if (!summary.valid_count) return statistics.every(value => value === null)
  return statistics.every(value => typeof value === 'number' && Number.isFinite(value))
    && summary.min <= summary.mean && summary.mean <= summary.max && summary.min <= summary.median && summary.median <= summary.max
}
const validProfile = computed(() => {
  const profile = props.profile
  if (!profile || profile.scope !== 'all_uploaded_records' || profile.denominator !== 'all_uploaded_records' || profile.weighted !== false
    || !Number.isInteger(props.totalRecords) || props.totalRecords <= 0 || profile.total_records !== props.totalRecords
    || ![profile.sex, profile.marital, profile.education].every(summary => summaryValid(summary, props.totalRecords)) || !summaryValid(profile.age, props.totalRecords, true)) return null
  return profile
})
const count = (value: unknown) => typeof value === 'number' && Number.isInteger(value) && value >= 0 ? value.toLocaleString('zh-CN') : '—'
const number = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('zh-CN', { maximumFractionDigits: 1 }) : '—'
const percent = (value: unknown) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100 ? value.toFixed(1) + '%' : '—'
const barWidth = (value: number) => Number.isFinite(value) && value >= 0 && value <= 100 ? value + '%' : '0%'
const categoryColor = (kind: string, key: string, index: number) => {
  if (key === 'unknown') return '#CBD5E1'
  if (kind === 'sex') return key === 'male' ? '#3B82F6' : '#F97316'
  const colors = kind === 'age' ? ['#10B981', '#3B82F6', '#F59E0B', '#F97316'] : kind === 'marital' ? ['#F97316', '#FBBF24', '#EF4444', '#8B5CF6', '#3B82F6', '#10B981'] : ['#3B82F6', '#10B981', '#FBBF24', '#F97316', '#8B5CF6']
  return colors[index % colors.length]
}
const sexDescription = computed(() => validProfile.value ? validProfile.value.sex.categories.map(item => item.label + ' ' + count(item.count) + ' 人，占全部对象 ' + percent(item.percent)).join('；') : '暂无性别资料')
const sexGradient = computed(() => {
  const categories = validProfile.value?.sex.categories
  if (!categories?.length) return '#E2E8F0'
  let start = 0
  const segments = categories.map((item, index) => {
    const end = start + (Number.isFinite(item.percent) ? Math.max(0, Math.min(100, item.percent)) : 0)
    const segment = categoryColor('sex', item.key, index) + ' ' + start + '% ' + Math.min(100, end) + '%'
    start = end
    return segment
  })
  if (start < 100) segments.push('#E2E8F0 ' + start + '% 100%')
  return 'conic-gradient(' + segments.join(', ') + ')'
})
</script>

<style scoped>
*{box-sizing:border-box}.cohort-profile{color:#0F172A;background:#fff;border:1px solid #DBE7F4;border-top:4px solid #3B82F6;border-radius:12px;padding:23px 24px 15px;margin:0 0 24px;box-shadow:0 4px 12px #102A4305}.profile-heading{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:20px}.section-label{font-size:10px;letter-spacing:1.5px;font-weight:700;color:#3B82F6}.profile-heading h3{font-size:19px;margin:6px 0 7px}.profile-heading p{font-size:12px;color:#64748B;margin:0;line-height:1.8}.scope-tag{color:#2563EB;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:16px;padding:6px 11px;font-size:11px;white-space:nowrap}.profile-totals{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) 1.3fr;align-items:center;gap:18px;background:#F7FAFE;border:1px solid #E7EEF7;border-radius:9px;padding:16px 18px;margin-bottom:22px}.total-item{min-width:0;border-right:1px solid #DFE8F3}.total-item>span{font-size:11px;color:#64748B}.total-item strong{display:block;font-size:29px;line-height:1.3;margin-top:6px;font-variant-numeric:tabular-nums}.total-item small{font-size:11px;font-weight:400;color:#8192A8;margin-left:7px}.total-primary strong{color:#2563EB}.total-ready strong{color:#059669}.total-skipped strong{color:#B7790C}.profile-totals>p{font-size:11px;line-height:1.9;color:#8192A8;margin:0}.demographic-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px}.demographic-card{min-width:0;padding-right:20px;border-right:1px solid #EDF2F8}.demographic-card:last-child{padding-right:0;border-right:0}.demographic-card h4{font-size:13px;margin:0 0 16px;display:flex;align-items:center;gap:7px}.heading-mark{display:inline-block;width:4px;height:13px;border-radius:2px}.blue{background:#3B82F6}.green{background:#10B981}.orange{background:#F97316}.purple{background:#8B5CF6}.sex-summary{display:grid;justify-items:center;gap:14px}.sex-ring{width:108px;height:108px;border-radius:50%;padding:11px;flex-shrink:0}.sex-ring>div{height:100%;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:3px}.sex-ring strong{font-size:24px;color:#334E68;font-variant-numeric:tabular-nums}.sex-ring>div>span{font-size:10px;color:#8192A8}.category-list{list-style:none;margin:0;padding:0;width:100%}.sex-list{display:grid;gap:10px}.sex-list li{display:flex;justify-content:space-between;gap:8px;font-size:11px;line-height:1.8}.category-name{display:flex;gap:6px;align-items:center;min-width:0}.category-name i{width:7px;height:7px;border-radius:50%;flex-shrink:0}.category-value{white-space:nowrap;font-variant-numeric:tabular-nums}.category-list small{font-size:10px;color:#94A3B8;margin-left:4px}.age-summary{margin:0 0 17px;display:grid;gap:6px}.age-summary strong{font-size:23px;color:#059669;line-height:1.3;font-variant-numeric:tabular-nums}.age-summary small{font-size:10px;font-weight:400;color:#8192A8;margin-left:7px}.age-summary>span{font-size:10px;color:#8192A8}.compact-list{display:grid;gap:9px}.bar-label{display:flex;align-items:flex-start;justify-content:space-between;gap:6px;font-size:10px;line-height:1.6;margin-bottom:4px}.bar-label>span:first-child{color:#536A84;min-width:0;overflow-wrap:anywhere}.bar-label>span:last-child{white-space:nowrap;font-variant-numeric:tabular-nums}.proportion-track{height:4px;border-radius:3px;background:#F1F5F9;overflow:hidden}.proportion-track>span{display:block;height:100%;border-radius:3px}.profile-note{font-size:10px;color:#94A3B8;line-height:1.9;border-top:1px dashed #E8EEF7;margin:19px 0 0;padding-top:11px}.profile-unavailable{font-size:12px;line-height:1.9;color:#8192A8;background:#F8FAFC;border:1px dashed #DCE5F1;padding:17px;border-radius:8px;margin:0}@media(max-width:1250px){.demographic-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.demographic-card:nth-child(2){padding-right:0;border-right:0}.sex-summary{grid-template-columns:108px minmax(0,1fr);align-items:center;gap:20px}.profile-totals{grid-template-columns:repeat(3,minmax(0,1fr))}.profile-totals>p{grid-column:1/-1}.total-item:last-of-type{border-right:0}}@media print{.cohort-profile{break-inside:avoid;box-shadow:none}.demographic-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.scope-tag{display:none}}
</style>
