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
  ],

  future: {
    compatibilityVersion: 4,
  },

  vite: {
    ssr: {
      noExternal: ['element-plus']
    },
    server: {
      fs: {
        allow: [
          'D:/gradstu/gard1/vite+vue3/my-nuxt-app',
          'D:/gradstu/gard1/vite+vue3/node_modules',
        ]
      }
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

