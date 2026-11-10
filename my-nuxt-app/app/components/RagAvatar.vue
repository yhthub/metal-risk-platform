<script setup lang="ts">
defineProps<{
  role: 'assistant' | 'user'
}>()
</script>

<template>
  <span class="rag-avatar" :class="`rag-avatar--${role}`" aria-hidden="true">
    <svg v-if="role === 'assistant'" viewBox="0 0 32 32" fill="none" focusable="false">
      <path d="m15 5 2.7 6.8 6.8 2.7-6.8 2.7L15 24l-2.7-6.8-6.8-2.7 6.8-2.7L15 5Z" fill="currentColor" fill-opacity=".12" stroke="currentColor" stroke-width="1.45" stroke-linejoin="round" />
      <path d="m15 10.2 1.3 3 3 1.3-3 1.3-1.3 3-1.3-3-3-1.3 3-1.3 1.3-3Z" fill="currentColor" fill-opacity=".72" />
      <path d="M25 4.5v4m-2-2h4M7 25.5c2.6.1 5.2.7 8 2 2.8-1.3 5.4-1.9 8-2" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" opacity=".55" />
    </svg>
    <svg v-else viewBox="0 0 32 32" fill="none" focusable="false">
      <circle cx="16" cy="11" r="4.25" fill="currentColor" fill-opacity=".12" stroke="currentColor" stroke-width="1.45" />
      <path d="M7.5 25v-1.2a8.5 8.5 0 0 1 17 0V25c-2.6 1.2-5.5 1.8-8.5 1.8s-5.9-.6-8.5-1.8Z" fill="currentColor" fill-opacity=".09" stroke="currentColor" stroke-width="1.45" stroke-linejoin="round" />
      <path d="M11.5 23.3a4.5 4.5 0 0 1 1.2-3" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" opacity=".35" />
    </svg>
  </span>
</template>

<style scoped>
.rag-avatar {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  width: var(--rag-avatar-size, 36px);
  height: var(--rag-avatar-size, 36px);
  box-sizing: border-box;
  border: 1px solid;
  border-radius: var(--rag-avatar-radius, 12px);
  vertical-align: middle;
  box-shadow: inset 0 1px 0 #ffffffcc, 0 2px 6px #4b719508;
}
.rag-avatar svg { display: block; width: 75%; height: 75%; }
.rag-avatar--assistant { color: #377fb7; border-color: #d5e7f2; background: linear-gradient(145deg, #edf5ff 8%, #e1f1fb 55%, #e6f6f4); }
.rag-avatar--user { color: #6c829c; border-color: #dfe7ef; background: linear-gradient(145deg, #f7faff, #edf2f8); }
</style>
