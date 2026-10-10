<template>
  <section class="dashboard-view">
    <header class="dashboard-view__heading">
      <div>
        <p>首页</p>
        <h1>{{ greeting }}，{{ displayName }}</h1>
      </div>
      <span class="dashboard-view__date">{{ currentDate }}</span>
    </header>

    <el-alert
      v-if="dashboardQuery.isError.value"
      class="dashboard-view__alert"
      type="error"
      title="关键数据暂时无法加载"
      show-icon
      :closable="false"
    />

    <section class="dashboard-section" aria-labelledby="key-metrics-title">
      <div class="dashboard-section__heading">
        <h2 id="key-metrics-title">关键数据</h2>
        <el-button text :loading="dashboardQuery.isFetching.value" @click="dashboardQuery.refetch()">
          刷新
        </el-button>
      </div>
      <div v-loading="dashboardQuery.isLoading.value" class="dashboard-metrics">
        <article v-for="metric in metrics" :key="metric.key" class="dashboard-metric">
          <div class="dashboard-metric__header">
            <h3>{{ metric.label }}</h3>
            <span>{{ metric.comparisonLabel }}</span>
          </div>
          <div class="dashboard-metric__values">
            <div>
              <span>销售单</span>
              <strong>{{ metric.data.sales_order_count }}</strong>
            </div>
            <div>
              <span>销售额</span>
              <strong>{{ formatPrice(metric.data.sales_amount) }}</strong>
            </div>
            <div>
              <span>销售毛利</span>
              <strong>{{ formatPrice(metric.data.gross_profit) }}</strong>
            </div>
          </div>
          <p>上月销售额 {{ formatPrice(metric.comparison.sales_amount) }}</p>
        </article>
      </div>
    </section>

    <section class="dashboard-section" aria-labelledby="quick-actions-title">
      <div class="dashboard-section__heading">
        <h2 id="quick-actions-title">常用功能</h2>
      </div>
      <div class="dashboard-actions">
        <button
          v-for="action in quickActions"
          :key="action.label"
          class="dashboard-action"
          type="button"
          :disabled="action.disabled"
          :aria-label="action.label"
          @click="action.route && router.push(action.route)"
        >
          <el-icon><component :is="action.icon" /></el-icon>
          <span>{{ action.label }}</span>
        </button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Box, DataAnalysis, DocumentAdd, PriceTag, ShoppingBag, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Component } from 'vue'
import type { DashboardMetric } from '../../api/generated'
import { V1Service } from '../../api/generated'
import { useAuthStore } from '../../stores/auth'
import { formatPrice } from '../../utils/numberFormat'

const auth = useAuthStore()
const router = useRouter()
const emptyMetric: DashboardMetric = { sales_order_count: 0, sales_amount: '0.00', gross_profit: '0.00' }
const dashboardQuery = useQuery({
  queryKey: ['dashboard'],
  queryFn: async () => (await V1Service.dashboardRetrieve()).data,
  retry: false,
})
const dashboard = computed(() => dashboardQuery.data.value)
const displayName = computed(() => auth.user?.display_name || auth.user?.username || '你好')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
const currentDate = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date())

const metrics = computed(() => [
  {
    key: 'today',
    label: '今日',
    comparisonLabel: '较上月同期',
    data: dashboard.value?.today ?? emptyMetric,
    comparison: dashboard.value?.last_month ?? emptyMetric,
  },
  {
    key: 'week',
    label: '本周',
    comparisonLabel: '较上月同期',
    data: dashboard.value?.week ?? emptyMetric,
    comparison: dashboard.value?.last_month ?? emptyMetric,
  },
  {
    key: 'month',
    label: '本月',
    comparisonLabel: '上月',
    data: dashboard.value?.month ?? emptyMetric,
    comparison: dashboard.value?.last_month ?? emptyMetric,
  },
])

const quickActions: Array<{ label: string; icon: Component; route?: string; disabled: boolean }> = [
  { label: '销售开单', icon: DocumentAdd, route: '/sales', disabled: false },
  { label: '商品列表', icon: Box, route: '/products', disabled: false },
  { label: '进货', icon: ShoppingBag, route: '/purchases', disabled: false },
  { label: '客户', icon: User, route: '/customers', disabled: false },
  { label: '价格查询', icon: PriceTag, route: '/price-levels', disabled: false },
  { label: '库存查询', icon: DataAnalysis, route: '/inventory/balances', disabled: false },
]

</script>