<template>
  <section v-if="reviews.length" class="exposure-review" aria-label="暴露现场核查与资料依据">
    <h2>暴露现场核查</h2>
    <p class="review-intro">按实际工序核对接触途径，将现场记录与相应的暴露因素对应。</p>
    <article v-for="item in reviews" :key="item.symbol" class="review-row">
      <header class="review-heading">
        <h3><span class="symbol">{{ item.symbol }}</span>{{ item.name }}</h3>
        <a :href="item.url" target="_blank" rel="noopener noreferrer">
          {{ item.source }}<span aria-hidden="true">↗</span>
        </a>
      </header>
      <dl class="review-fields">
        <div><dt>现场核查</dt><dd>{{ item.check }}</dd></div>
        <div><dt>留存资料</dt><dd>{{ item.record }}</dd></div>
      </dl>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ factors: string }>()

interface ExposureReview {
  symbol: string
  name: string
  check: string
  record: string
  source: string
  url: string
}

const reviewBySymbol: Record<string, ExposureReview> = {
  PB: {
    symbol: 'Pb', name: '铅',
    check: '沿投料、加工和清扫路线查看含铅颗粒在哪里产生，排风罩能否在源头捕集。核对工作服与生活衣物的存放、清洗位置。',
    record: '标出产尘点和排风罩位置，记录排风巡检结果、表面清洁方式及工作服清洗流程。',
    source: '美国 OSHA · 铅暴露评估与控制', url: 'https://www.osha.gov/lead/evaluating-controlling-exposure',
  },
  AS: {
    symbol: 'As', name: '砷',
    check: '核对原料成分和检测项目，区分总砷与无机砷。若工序涉及无机砷，核查采样是否覆盖清灰、检修等实际接触时段。',
    record: '收集注明砷形态的原料资料、对应工种和班次的个人空气采样报告，以及除尘设备清理记录。',
    source: '美国 OSHA · 无机砷职业暴露', url: 'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1018',
  },
  CD: {
    symbol: 'Cd', name: '镉',
    check: '按工序区分含镉粉尘、烟或雾，核对采样时设备的运行状态；若已采取密闭或排风措施，现场确认其覆盖的工位。',
    record: '按工位收集物料清单、标明采样任务和时段的空气检测结果，以及密闭设备或排风系统的巡检记录。',
    source: '美国 OSHA · 镉暴露与控制', url: 'https://www.osha.gov/cadmium/exposure-controls',
  },
  HG: {
    symbol: 'Hg', name: '汞',
    check: '从物料资料确认汞的形态。若涉及金属汞，排查敞口、溢洒及残留液滴的位置，并核查这些位置的蒸气监测情况。',
    record: '记录物料所列汞形态。对金属汞工序，留存溢洒位置、处置记录和汞蒸气监测结果；生物检测记录应标明测的是总汞还是特定形态。',
    source: '美国 NIOSH · 金属汞与汞蒸气', url: 'https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750021.html',
  },
  CR: {
    symbol: 'Cr', name: '铬',
    check: '核对材料、工艺和检测报告中的铬价态。若涉及不锈钢热作业或镀铬，确认空气检测项目是否专门测定六价铬。',
    record: '并列保留材料成分、工序和采样报告，标明每份结果测的是总铬、三价铬还是六价铬。',
    source: '美国 OSHA · 铬的形态与接触工序', url: 'https://www.osha.gov/chromium',
  },
  NI: {
    symbol: 'Ni', name: '镍',
    check: '查明工序使用的是金属镍还是镍化合物，分别核查含镍物料进入呼吸带、接触皮肤的操作环节。',
    record: '留存原料安全数据表和岗位空气采样方法，另记直接接触含镍物料的操作及皮肤防护措施。',
    source: '美国 NIOSH · 金属镍及其他镍化合物', url: 'https://www.cdc.gov/niosh/npg/npgd0445.html',
  },
}

const reviews = computed(() => {
  const symbols = props.factors.split(/[,，、]/).map(value => value.trim().toUpperCase())
  return Array.from(new Set(symbols)).filter(symbol => Object.hasOwn(reviewBySymbol, symbol))
    .map(symbol => reviewBySymbol[symbol]!)
})
</script>

<style scoped>
.exposure-review { padding: 22px; border: 1px solid #dce5e9; border-radius: 12px; background: #fff; color: #273c50; }
.exposure-review h2 { margin: 0; font-size: 18px; line-height: 1.4; font-weight: 700; }
.review-intro { margin: 5px 0 16px; color: #52697a; font-size: 13px; line-height: 1.7; }
.review-row { padding: 15px 0; border-top: 1px solid #e0e9ec; }
.review-row:last-child { padding-bottom: 0; }
.review-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.review-heading h3 { display: inline-flex; align-items: center; gap: 8px; margin: 0; font-size: 15px; font-weight: 700; }
.symbol { display: inline-grid; place-items: center; min-width: 30px; height: 28px; padding: 0 4px; border-radius: 6px; background: #e6f3f1; color: #18665e; font-size: 13px; }
.review-heading a { display: inline-flex; align-items: center; gap: 5px; color: #345e82; font-size: 12px; line-height: 1.6; text-underline-offset: 3px; text-decoration: underline; text-decoration-color: #a5bdce; }
.review-heading a:hover { color: #153c66; text-decoration-color: currentColor; }
.review-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 11px 0 0; }
.review-fields dt { margin: 0; color: #475f71; font-size: 12px; font-weight: 650; }
.review-fields dd { margin: 3px 0 0; color: #2e4658; font-size: 13px; line-height: 1.75; overflow-wrap: anywhere; }
@media (max-width: 680px) {
  .exposure-review { padding: 16px; }
  .review-fields { grid-template-columns: minmax(0, 1fr); gap: 9px; }
  .review-heading a { min-height: 32px; }
}
</style>
