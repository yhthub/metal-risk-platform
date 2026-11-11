<template>
  <svg class="sidebar-icon" :data-sidebar-icon="name" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"
    stroke-linejoin="round" aria-hidden="true" focusable="false">
    <g v-if="name === 'intake'">
      <path class="tint" d="M5.3 9 2.7 15.3v3.1c0 1.1.9 2 2 2h14.6c1.1 0 2-.9 2-2v-3.1L18.7 9"/>
      <path d="M5.3 9 2.7 15.3v3.1c0 1.1.9 2 2 2h14.6c1.1 0 2-.9 2-2v-3.1L18.7 9M3.1 15h5l1.5 2.4h4.8l1.5-2.4h5"/>
      <path d="M12 2.6v9.1m-3.5-3.3L12 12l3.5-3.6"/>
    </g>
    <g v-else-if="name === 'organize'">
      <rect class="tint" x="2.8" y="3.8" width="18.4" height="4.6" rx="1.4"/>
      <rect x="2.8" y="3.8" width="18.4" height="4.6" rx="1.4"/>
      <path d="M4.3 12.5h5.2m-5.2 4.1h3.4"/>
      <path class="wash" d="M11.5 11.5h10l-3.7 4.7v3.2l-2.6 1.4v-4.6z"/>
    </g>
    <g v-else-if="name === 'risk'">
      <path class="wash" d="M3.2 17.4a9.4 9.4 0 1 1 17.6 0l-.6 1.3H3.8z"/>
      <path d="m5.4 11.6 1.5.6M8.2 7.5l1 1.3M12 6.5v1.6m6.6 3.5-1.4.6M12 15l4.3-6"/>
      <circle cx="12" cy="15" r="1.5" fill="currentColor" stroke="none"/>
    </g>
    <g v-else-if="name === 'causal'">
      <path d="m6.1 11.1 4.6-5m-4.6 7 4.6 5m2.4-12 4.9 5m-4.9 7 4.9-5"/>
      <circle class="wash" cx="4.6" cy="12.1" r="2.2"/>
      <circle class="wash" cx="12" cy="4.5" r="2.2"/>
      <circle class="wash" cx="12" cy="19.6" r="2.2"/>
      <circle cx="19.4" cy="12.1" r="2.5" fill="currentColor" stroke="none"/>
    </g>
    <g v-else-if="name === 'plan'">
      <path class="wash" d="M8.4 4.3h-2c-1.1 0-2 .9-2 2v13c0 1.1.9 2 2 2h11.2c1.1 0 2-.9 2-2v-13c0-1.1-.9-2-2-2h-2"/>
      <rect x="8.5" y="2.4" width="7" height="4.2" rx="1.4"/>
      <path d="m8.4 12.8 2.1 2.1 4.8-4.9M8.5 17.5h7"/>
    </g>
    <g v-else>
      <path class="wash" d="M7.2 3.8h9.6a4.7 4.7 0 0 1 4.7 4.7v5.1a4.7 4.7 0 0 1-4.7 4.7h-6.2l-4.7 3v-3.2a4.7 4.7 0 0 1-3.4-4.5V8.5a4.7 4.7 0 0 1 4.7-4.7Z"/>
      <path d="M12 7.3v6.9m-3.4-3.4h6.8"/>
    </g>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ name: 'intake' | 'organize' | 'risk' | 'causal' | 'plan' | 'qa' }>()
</script>

<style scoped>
.sidebar-icon {
  --ink: #385f86;
  --surface: #eaf1fa;
  box-sizing: border-box;
  display: block;
  flex: none;
  width: 32px;
  height: 32px;
  padding: 5px;
  border-radius: 9px;
  background-color: var(--nav-icon-bg, var(--surface));
  color: var(--nav-icon-ink, var(--ink));
}
.sidebar-icon[data-sidebar-icon="organize"] { --ink: #386c71; --surface: #e8f2f2; }
.sidebar-icon[data-sidebar-icon="risk"] { --ink: #86602c; --surface: #f7f1e6; }
.sidebar-icon[data-sidebar-icon="causal"] { --ink: #585e92; --surface: #eeeef8; }
.sidebar-icon[data-sidebar-icon="plan"] { --ink: #346c5c; --surface: #e8f2ec; }
.sidebar-icon[data-sidebar-icon="qa"] { --ink: #466c97; --surface: #eaf2fa; }
.tint, .wash { fill: currentColor; fill-opacity: .14; }
.tint { stroke: none; }
</style>
