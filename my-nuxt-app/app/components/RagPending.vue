<template>
  <div class="rag-pending" role="status" aria-live="polite" aria-atomic="true">
    <div class="pending-header">
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
        <p class="pending-title">正在准备回答</p>
        <p class="pending-caption">为你呈现更完整、清晰的解答</p>
      </div>
    </div>

    <div class="pending-preview" aria-hidden="true">
      <div class="skeleton-lines">
        <span class="skeleton-line" />
        <span class="skeleton-line" />
        <span class="skeleton-line" />
      </div>
      <div class="pending-activity">
        <span class="activity-dot" /><span class="activity-dot" /><span class="activity-dot" />
        <span class="activity-track" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.rag-pending { width: 100%; max-width: 560px; padding: 6px 0 4px; box-sizing: border-box; }
.pending-header { display: flex; align-items: center; gap: 15px; }
.pending-mark { position: relative; display: grid; place-items: center; width: 56px; height: 56px; flex-shrink: 0; }
.pending-mark::before { content: ''; position: absolute; inset: -9px; border-radius: 50%; background: radial-gradient(circle, #dbeefa80, #e5f5f04d 40%, transparent 72%); pointer-events: none; }
.pending-orbit { position: absolute; inset: 0; border: 1px solid #e5edf4; border-top-color: #9bc8d7; border-right-color: #cbe6e1; border-radius: 50%; animation: pending-orbit 10s linear infinite; }
.pending-orbit::after { content: ''; position: absolute; width: 4px; height: 4px; top: 6px; right: 5px; border-radius: 50%; background: #90c4c6; box-shadow: 0 0 7px #a6d3ce66; }
.pending-symbol { position: relative; display: grid; place-items: center; width: 43px; height: 43px; border: 1px solid #dcebf2; border-radius: 14px; color: #558caf; background: linear-gradient(140deg, #eaf3ff, #edf8f4); box-shadow: inset 0 1px 0 #ffffffcc, 0 4px 12px #4d8ca40a; animation: pending-breathe 4s ease-in-out infinite; }
.pending-symbol svg { width: 29px; height: 29px; }
.pending-copy { min-width: 0; }
.pending-title { margin: 0; font-size: 15px; line-height: 1.6; font-weight: 500; letter-spacing: .035em; color: #4a6e8e; }
.pending-caption { margin: 5px 0 0; font-size: 12px; line-height: 1.7; color: #91a3b5; }
.pending-preview { position: relative; overflow: hidden; margin-top: 20px; padding: 19px 20px 15px; border: 1px solid #e8eff5; border-radius: 12px; background: radial-gradient(ellipse at 100% 0, #e4f3ef70, transparent 65%), linear-gradient(120deg, #f7faff, #fafcfd); }
.pending-preview::before { content: ''; position: absolute; height: 1px; left: 18px; right: 18px; top: 0; background: linear-gradient(90deg, transparent, #c6dfeb, #cfe8df, transparent); }
.skeleton-lines { display: flex; flex-direction: column; gap: 12px; }
.skeleton-line { position: relative; display: block; overflow: hidden; width: 88%; height: 6px; border-radius: 8px; background: linear-gradient(90deg, #dce8f3b3, #e5edf480); }
.skeleton-line:nth-child(2) { width: 72%; }
.skeleton-line:nth-child(3) { width: 81%; }
.skeleton-line::after { content: ''; position: absolute; inset: 0; background: linear-gradient(100deg, transparent 15%, #ffffffdd 49%, #d8eee980 62%, transparent 84%); transform: translateX(-110%); animation: pending-shimmer 3.2s ease-in-out infinite; }
.skeleton-line:nth-child(2)::after { animation-delay: .18s; }
.skeleton-line:nth-child(3)::after { animation-delay: .36s; }
.pending-activity { display: flex; align-items: center; gap: 4px; margin-top: 18px; height: 6px; }
.activity-dot { width: 3px; height: 3px; border-radius: 50%; background: #93b3c9; animation: pending-dot 2.4s ease-in-out infinite; }
.activity-dot:nth-child(2) { animation-delay: .25s; background: #91bcbf; }
.activity-dot:nth-child(3) { animation-delay: .5s; background: #a9c8c9; }
.activity-track { position: relative; overflow: hidden; width: 42px; height: 1px; margin-left: 5px; background: #dfebf0; }
.activity-track::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, #8fbfc5, transparent); transform: translateX(-110%); animation: pending-shimmer 3.2s ease-in-out infinite; }
@keyframes pending-orbit { to { transform: rotate(360deg); } }
@keyframes pending-breathe { 0%, 100% { box-shadow: inset 0 1px 0 #ffffffcc, 0 4px 12px #4d8ca40a; } 50% { box-shadow: inset 0 1px 0 #ffffffdd, 0 4px 16px #74b7c126; } }
@keyframes pending-shimmer { 0%, 15% { transform: translateX(-110%); } 80%, 100% { transform: translateX(110%); } }
@keyframes pending-dot { 0%, 100% { opacity: .4; } 50% { opacity: 1; } }
@media (max-width: 480px) { .rag-pending { padding-top: 3px; } .pending-header { gap: 12px; } .pending-mark { width: 48px; height: 48px; } .pending-symbol { width: 37px; height: 37px; border-radius: 12px; } .pending-symbol svg { width: 26px; height: 26px; } .pending-orbit::after { top: 5px; right: 4px; } .pending-title { font-size: 14px; } .pending-caption { font-size: 11px; margin-top: 4px; } .pending-preview { padding: 16px 15px 13px; margin-top: 17px; border-radius: 10px; } .skeleton-lines { gap: 11px; } .skeleton-line { height: 5px; } .pending-activity { margin-top: 15px; } }
@media (prefers-reduced-motion: reduce) { .pending-orbit, .pending-symbol, .skeleton-line::after, .activity-dot, .activity-track::after { animation: none; } .skeleton-line::after, .activity-track::after { transform: none; opacity: .25; } .activity-dot { opacity: .7; } }
</style>
