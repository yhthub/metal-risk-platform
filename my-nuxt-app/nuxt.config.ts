export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  runtimeConfig: {
    public: {
      apiBase: '',
      // 静态构建时显式开启公开演示；本地与私有部署默认保留访问检查。
      publicDemo: process.env.NUXT_PUBLIC_PUBLIC_DEMO === 'true',
    },
  },

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
