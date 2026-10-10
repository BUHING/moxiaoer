<template>
  <div class="app-layout">
    <aside class="app-layout__sidebar">
      <div class="app-layout__brand">磨小二</div>
      <div class="app-layout__organization">{{ auth.user?.organization_name || '系统管理' }}</div>
      <nav class="app-layout__nav" aria-label="主导航">
        <el-button
          v-for="item in navigationItems"
          :key="item.path"
          text
          class="app-layout__nav-button"
          :class="{ 'app-layout__nav-button--active': isActive(item.path) }"
          @click="router.push(item.path)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-button>
      </nav>
      <el-button text class="app-layout__logout" @click="logout">
        <el-icon><SwitchButton /></el-icon>
        <span>退出登录</span>
      </el-button>
    </aside>

    <main class="app-layout__workspace">
      <header class="app-layout__topbar">
        <span>{{ auth.user?.display_name || auth.user?.username }}</span>
        <span class="app-layout__role">{{ auth.user?.role === 'BOSS' ? '老板账号' : '员工账号' }}</span>
      </header>
      <nav class="app-layout__tabs" aria-label="已打开页面">
        <button
          v-for="tab in openTabs"
          :key="tab.path"
          class="app-layout__tab"
          :class="{ 'app-layout__tab--active': route.path === tab.path }"
          type="button"
          @click="router.push(tab.path)"
        >
          <span>{{ tab.label }}</span>
          <el-icon
            v-if="tab.closable"
            class="app-layout__tab-close"
            role="button"
            :aria-label="`关闭${tab.label}`"
            @click.stop="closeTab(tab.path)"
          >
            <Close />
          </el-icon>
        </button>
      </nav>
      <section class="app-layout__content">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { Box, Close, DataAnalysis, DocumentAdd, House, Printer, Setting, ShoppingBag, SwitchButton, TrendCharts, User, UserFilled } from '@element-plus/icons-vue'
import { computed, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

interface NavigationItem {
  label: string
  path: string
  icon: Component
}

interface OpenTab {
  label: string
  path: string
  closable: boolean
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const canViewReports = computed(() => auth.user?.permissions.some((code) => code === '*' || code === 'reports.view'))
const navigationItems = computed<NavigationItem[]>(() => [
  { label: '首页', path: '/dashboard', icon: House },
  { label: '商品', path: '/products', icon: Box },
  { label: '销售', path: '/sales', icon: DocumentAdd },
  { label: '客户', path: '/customers', icon: User },
  { label: '供应商', path: '/suppliers', icon: UserFilled },
  { label: '进货', path: '/purchases', icon: ShoppingBag },
  { label: '库存', path: '/inventory/balances', icon: DataAnalysis },
  ...(canViewReports.value ? [{ label: '分析', path: '/reports/sales', icon: TrendCharts }] : []),
  { label: '标签打印', path: '/settings/label-printing', icon: Printer },
  { label: '设置', path: '/settings/employees', icon: Setting },
])
const tabDefinitions: Record<string, string> = {
  dashboard: '首页',
  products: '商品',
  sales: '销售开单',
  'sales-returns': '销售退货',
  purchases: '进货入库',
  'purchase-returns': '进货退货',
  'inventory-balances': '库存查询',
  'inventory-movements': '库存流水',
  'reports-sales': '销售统计',
  'reports-purchases': '进货统计',
  'reports-inventory': '库存统计',
  customers: '客户',
  'price-levels': '价格等级',
  suppliers: '供应商',
  'account-workspace': '设置',
  'label-printing': '标签打印',
}
const openTabs = ref<OpenTab[]>([{ label: '首页', path: '/dashboard', closable: false }])

watch(() => route.path, () => {
  const label = tabDefinitions[String(route.name)]
  if (!label || openTabs.value.some((tab) => tab.path === route.path)) return
  openTabs.value = [...openTabs.value, { label, path: route.path, closable: route.path !== '/dashboard' }]
}, { immediate: true })

function isActive(path: string) {
  if (path === '/customers') return route.path === path || route.path === '/price-levels'
  return route.path === path || route.path.startsWith(`${path}/`)
}

function closeTab(path: string) {
  const tabIndex = openTabs.value.findIndex((tab) => tab.path === path)
  if (tabIndex < 0 || !openTabs.value[tabIndex].closable) return
  const wasActive = route.path === path
  const remainingTabs = openTabs.value.filter((tab) => tab.path !== path)
  openTabs.value = remainingTabs
  if (wasActive) void router.push(remainingTabs[Math.max(0, tabIndex - 1)].path)
}

function logout() {
  auth.clearTokens()
  void router.replace('/auth')
}
</script>