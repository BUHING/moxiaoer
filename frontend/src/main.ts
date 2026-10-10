import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { configureApi } from './api/configure'
import router from './router'
import './styles/base.css'

configureApi()
createApp(App).use(createPinia()).use(router).use(VueQueryPlugin).use(ElementPlus, { locale: zhCn }).mount('#app')
