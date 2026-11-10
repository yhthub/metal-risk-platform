<script setup lang="ts">
import { computed } from 'vue'
import { renderRagMarkdown } from '../utils/ragMarkdown'

const props = withDefaults(defineProps<{
  content: string
  citationIds?: string[]
}>(), {
  citationIds: () => [],
})

const emit = defineEmits<{
  citation: [id: string]
}>()

const renderedContent = computed(() => renderRagMarkdown(props.content, props.citationIds))

function handleClick(event: MouseEvent) {
  const target = event.target
  const container = event.currentTarget
  if (!(target instanceof Element) || !(container instanceof Element)) return
  const button = target.closest<HTMLButtonElement>('button.rag-citation[data-citation-id]')
  if (!button || !container.contains(button)) return
  const id = button.dataset.citationId
  if (id && /^E[1-9]\d*$/.test(id) && props.citationIds.includes(id)) emit('citation', id)
}
</script>

<template>
  <div class="rag-answer" @click="handleClick" v-html="renderedContent" />
</template>

<style scoped>
.rag-answer { color: inherit; font-size: inherit; line-height: 1.8; overflow-wrap: anywhere; }
.rag-answer :deep(> :first-child) { margin-top: 0; }
.rag-answer :deep(> :last-child) { margin-bottom: 0; }
.rag-answer :deep(p) { margin: 0.75em 0; }
.rag-answer :deep(h1), .rag-answer :deep(h2), .rag-answer :deep(h3),
.rag-answer :deep(h4), .rag-answer :deep(h5), .rag-answer :deep(h6) {
  color: inherit; font-weight: 650; line-height: 1.5; margin: 1.25em 0 0.5em;
}
.rag-answer :deep(h1) { font-size: 1.3em; }
.rag-answer :deep(h2) { font-size: 1.18em; }
.rag-answer :deep(h3), .rag-answer :deep(h4), .rag-answer :deep(h5), .rag-answer :deep(h6) { font-size: 1.05em; }
.rag-answer :deep(strong) { font-weight: 650; }
.rag-answer :deep(ul), .rag-answer :deep(ol) { margin: 0.75em 0; padding-left: 1.6em; }
.rag-answer :deep(ul) { list-style: disc; }
.rag-answer :deep(ol) { list-style: decimal; }
.rag-answer :deep(li) { margin: 0.35em 0; padding-left: 0.15em; }
.rag-answer :deep(li > p) { margin: 0.35em 0; }
.rag-answer :deep(blockquote) {
  margin: 1em 0; padding: 0.2em 1em; border-left: 3px solid #cbd5e1; color: #64748b;
}
.rag-answer :deep(a) { color: #2563eb; text-decoration: underline; text-underline-offset: 3px; }
.rag-answer :deep(code) {
  padding: 0.15em 0.35em; border-radius: 4px; background: #f1f5f9;
  font-size: 0.9em; font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}
.rag-answer :deep(pre) { max-width: 100%; overflow-x: auto; margin: 1em 0; padding: 0.9em 1em; border-radius: 8px; background: #f1f5f9; }
.rag-answer :deep(pre code) { padding: 0; border-radius: 0; background: transparent; white-space: pre; }
.rag-answer :deep(table) { display: block; max-width: 100%; overflow-x: auto; margin: 1em 0; border-collapse: collapse; font-size: 0.94em; }
.rag-answer :deep(th), .rag-answer :deep(td) { border: 1px solid #e2e8f0; padding: 0.55em 0.8em; text-align: left; vertical-align: top; }
.rag-answer :deep(th) { background: #f8fafc; font-weight: 650; }
.rag-answer :deep(hr) { border: 0; border-top: 1px solid #e2e8f0; margin: 1.2em 0; }
.rag-answer :deep(.rag-image-alt) { color: #64748b; }
.rag-answer :deep(.rag-citation) {
  display: inline; margin: 0 0.08em; padding: 0.05em 0.2em; border: 0; border-radius: 4px;
  background: #eff6ff; color: #2563eb; font: inherit; font-size: 0.85em;
  line-height: inherit; vertical-align: baseline; cursor: pointer;
}
.rag-answer :deep(.rag-citation:hover) { background: #dbeafe; }
.rag-answer :deep(.rag-citation:focus-visible) { outline: 2px solid #2563eb; outline-offset: 2px; }
</style>
