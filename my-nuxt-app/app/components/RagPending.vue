<template>
  <div class="rag-pending" role="status" aria-live="polite" aria-atomic="true">
    <div class="pending-mark" aria-hidden="true">
      <span class="pending-orbit" />
      <span class="pending-symbol">
        <svg viewBox="0 0 32 32" fill="none" focusable="false">
          <path d="M16 11.5c-3-2-6.3-2.4-10-1.3v14c3.7-1.1 7-.7 10 1.3m0-14c2.6-1.7 5.6-2.3 9-1.6m-9 1.6v14m0 0c3-2 6.3-2.4 10-1.3V16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M9.5 14.4c1.2-.1 2.4.1 3.5.6m-3.5 3.4c1.2-.1 2.4.1 3.5.6" stroke="currentColor" stroke-opacity=".55" stroke-width="1.3" stroke-linecap="round" />
          <path d="m24 3 1.4 4.1L29.5 8.5l-4.1 1.4L24 14l-1.4-4.1-4.1-1.4 4.1-1.4L24 3Z" fill="currentColor" fill-opacity=".15" stroke="currentColor" stroke-width="1.15" stroke-linejoin="round" />
        </svg>
      </span>
    </div>
    <div class="pending-copy">
      <span class="pending-label">医学知识助手</span>
      <p class="pending-title">
        正在准备回答
        <span class="pending-activity" aria-hidden="true">
          <i class="activity-dot" /><i class="activity-dot" /><i class="activity-dot" />
        </span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.rag-pending { display: flex; align-items: center; gap: 13px; }
.pending-mark { position: relative; display: grid; place-items: center; width: 44px; height: 44px; flex-shrink: 0; }
.pending-mark::before { content: ''; position: absolute; inset: -9px; border-radius: 50%; background: radial-gradient(circle, #dbeefa80, #e5f5f04d 40%, transparent 72%); pointer-events: none; }
.pending-orbit { position: absolute; inset: 0; border: 1px solid #e5edf4; border-top-color: #9bc8d7; border-right-color: #cbe6e1; border-radius: 50%; animation: pending-orbit 10s linear infinite; }
.pending-orbit::after { content: ''; position: absolute; width: 4px; height: 4px; top: 6px; right: 5px; border-radius: 50%; background: #90c4c6; box-shadow: 0 0 7px #a6d3ce66; }
.pending-symbol { position: relative; display: grid; place-items: center; width: 34px; height: 34px; border: 1px solid #dcebf2; border-radius: 11px; color: #558caf; background: linear-gradient(140deg, #eaf3ff, #edf8f4); box-shadow: inset 0 1px 0 #ffffffcc; }
.pending-symbol svg { width: 25px; height: 25px; }
.pending-copy { min-width: 0; }
.pending-label { display: block; margin-bottom: 2px; font-size: 11px; line-height: 1.4; color: #61788d; }
.pending-title { margin: 0; font-size: 15px; line-height: 1.5; font-weight: 500; color: #395d78; }
.pending-activity { display: inline-flex; align-items: center; gap: 3px; margin-inline-start: 3px; vertical-align: middle; }
.activity-dot { width: 4px; height: 4px; border-radius: 50%; background: #6c9fbc; animation: pending-dot 2.4s ease-in-out infinite; }
.activity-dot:nth-child(2) { animation-delay: .25s; background: #91bcbf; }
.activity-dot:nth-child(3) { animation-delay: .5s; background: #a9c8c9; }
@keyframes pending-orbit { to { transform: rotate(360deg); } }
@keyframes pending-dot { 0%, 100% { opacity: .4; } 50% { opacity: 1; } }
@media (max-width: 480px) { .rag-pending { gap: 10px; } .pending-mark { width: 39px; height: 39px; } .pending-symbol { width: 30px; height: 30px; } .pending-symbol svg { width: 22px; height: 22px; } .pending-title { font-size: 14px; } }
@media (prefers-reduced-motion: reduce) { .pending-orbit, .activity-dot { animation: none; } }
</style>
