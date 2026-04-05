import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Vuetify
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import App from './App.vue'

const vuetify = createVuetify({
  components,
  directives,
  defaults: {
    VBtn:      { ripple: false },      // 关闭水波纹，避免点击蒙层残留
    VListItem: { ripple: false },
    VTab:      { ripple: false },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary:   '#1565C0',
          secondary: '#455A64',
          success:   '#2E7D32',
          warning:   '#F57F17',
          error:     '#C62828',
          info:      '#0277BD',
          surface:   '#FFFFFF',
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi',
  },
})

createApp(App)
  .use(createPinia())
  .use(vuetify)
  .mount('#app')
