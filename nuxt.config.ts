export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: [
    '@element-plus/nuxt'
  ],

  elementPlus: {
    icon: 'ElIcon',
    importStyle: 'css',
  },

  css: [
    '~/assets/css/app.css',
    'element-plus/dist/index.css'
  ],

  future: {
    compatibilityVersion: 4,
  },

  vite: {
    ssr: {
      noExternal: ['element-plus']
    }
  }
})
// https://nuxt.com/docs/api/configuration/nuxt-config
// export default defineNuxtConfig({
//   compatibilityDate: '2024-11-01',
//   devtools: { enabled: true },
//   modules: ['@nuxt/ui'],
//   css: ['~/assets/css/app.css'],
//   future: {
//     compatibilityVersion: 4, // 开启 Nuxt 4 目录规范
//   },
//   ui: {
//     fonts: false
//   }
// })
// cd my-nuxt-app  pnpm dev 
// Nuxt4 + Vue3 + Vite7 + Tailwind4 + Element plus + ECharts6 + pnpm
