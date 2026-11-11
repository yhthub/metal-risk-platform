<template>
  <div class="feature-art" :data-feature-preview="kind">
    <img
      :src="illustrations[kind]"
      alt=""
      width="900"
      height="600"
      loading="lazy"
      decoding="async"
    >
  </div>
</template>

<script setup lang="ts">
import riskArt from '~/assets/illustrations/features/risk.svg?no-inline'
import cleaningArt from '~/assets/illustrations/features/cleaning.svg?no-inline'
import knowledgeArt from '~/assets/illustrations/features/knowledge.svg?no-inline'

type Feature = 'risk' | 'cleaning' | 'knowledge'
defineProps<{ kind: Feature }>()

const illustrations: Record<Feature, string> = {
  risk: riskArt,
  cleaning: cleaningArt,
  knowledge: knowledgeArt,
}
</script>

<style scoped>
.feature-art {
  --art-tint: #f0f5fc;
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  aspect-ratio: 3 / 2;
  padding: clamp(12px, 1.5vw, 22px);
  overflow: hidden;
  border: 1px solid #e5ebf1;
  border-radius: 24px;
  background: radial-gradient(ellipse at 18% 12%, var(--art-tint), transparent 70%), #fff;
  box-shadow: 0 18px 42px -30px #284b6b40;
}

.feature-art[data-feature-preview="cleaning"] { --art-tint: #eff7f4; }
.feature-art[data-feature-preview="knowledge"] { --art-tint: #f0f3fb; }

.feature-art img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

@media (max-width: 600px) {
  .feature-art { padding: 10px; border-radius: 20px; }
}
</style>
