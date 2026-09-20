export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: [
    '@element-plus/nuxt'
  ],

  elementPlus: {
    importStyle: 'css',
  },

  css: [
    '~/assets/css/app.css',
  ],

  future: {
    compatibilityVersion: 4,
  },

  // 对所有路由禁用 SSR（纯 SPA 模式）
  routeRules: {
    '/**': { ssr: false },
  },

  vite: {
    optimizeDeps: {
      include: ['element-plus', 'dayjs', '@element-plus/icons-vue', 'echarts'],
    },
  }
})
