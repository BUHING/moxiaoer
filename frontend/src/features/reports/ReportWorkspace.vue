<template>
  <section class="report-workspace">
    <header class="report-workspace__heading">
      <div>
        <p>分析</p>
        <h1>经营数据</h1>
      </div>
      <el-button :icon="Refresh" circle title="刷新当前报表" @click="refreshActiveReport" />
    </header>

    <el-tabs v-model="activeReport">
      <el-tab-pane label="销售统计" name="sales" />
      <el-tab-pane label="进货统计" name="purchases" />
      <el-tab-pane label="库存统计" name="inventory" />
    </el-tabs>

    <div v-if="activeReport !== 'inventory'" class="report-toolbar">
      <el-date-picker
        v-model="dateRangeInput"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :clearable="false"
      />
      <el-button type="primary" :icon="Search" @click="applyDateRange">查询</el-button>
    </div>

    <el-alert
      v-if="activeQuery.isError.value"
      class="report-workspace__alert"
      type="error"
      title="统计数据暂时无法加载"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button text @click="refreshActiveReport">重新加载</el-button>
      </template>
    </el-alert>

    <div v-loading="activeQuery.isLoading.value" class="report-summary">
      <template v-if="activeReport === 'sales'">
        <article v-for="item in salesMetrics" :key="item.label" class="report-summary__item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </template>
      <template v-else-if="activeReport === 'purchases'">
        <article v-for="item in purchaseMetrics" :key="item.label" class="report-summary__item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </template>
      <template v-else>
        <article v-for="item in inventoryMetrics" :key="item.label" class="report-summary__item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </template>
    </div>

    <div v-if="activeReport === 'sales'" class="report-note">
      <el-icon><InfoFilled /></el-icon>
      <span>销售与退货在完成时锁定商品进货价；退货已冲减销售数量、金额与成本。</span>
    </div>
    <div v-else-if="activeReport === 'purchases'" class="report-note">
      <el-icon><InfoFilled /></el-icon>
      <span>进货退货已冲减净进货数量和金额，仅统计已完成单据。</span>
    </div>
    <div v-else class="report-note">
      <el-icon><InfoFilled /></el-icon>
      <span>库存统计为当前余额快照；商品明细和库存流水可在库存查询中查看。</span>
      <el-button text @click="router.push('/inventory/balances')">查看库存明细</el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { InfoFilled, Refresh, Search } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { V1Service } from '../../api/generated'
import { formatPrice, formatQuantity } from '../../utils/numberFormat'

type ReportName = 'sales' | 'purchases' | 'inventory'

const route = useRoute()
const router = useRouter()
const today = new Date()
const dateRangeInput = ref<[string, string]>([
  formatLocalDate(new Date(today.getFullYear(), today.getMonth(), 1)),
  formatLocalDate(today),
])
const dateRange = ref<[string, string]>([...dateRangeInput.value])
const activeReport = computed<ReportName>({
  get: () => {
    if (route.name === 'reports-purchases') return 'purchases'
    if (route.name === 'reports-inventory') return 'inventory'
    return 'sales'
  },
  set: (name) => void router.push(`/reports/${name}`),
})

const salesQuery = useQuery({
  queryKey: computed(() => ['reports', 'sales', ...dateRange.value]),
  queryFn: async () => (await V1Service.reportsSalesRetrieve(...dateRange.value)).data,
  enabled: computed(() => activeReport.value === 'sales'),
  retry: false,
})
const purchasesQuery = useQuery({
  queryKey: computed(() => ['reports', 'purchases', ...dateRange.value]),
  queryFn: async () => (await V1Service.reportsPurchasesRetrieve(...dateRange.value)).data,
  enabled: computed(() => activeReport.value === 'purchases'),
  retry: false,
})
const inventoryQuery = useQuery({
  queryKey: ['reports', 'inventory'],
  queryFn: async () => (await V1Service.reportsInventoryRetrieve()).data,
  enabled: computed(() => activeReport.value === 'inventory'),
  retry: false,
})
const activeQuery = computed(() => {
  if (activeReport.value === 'purchases') return purchasesQuery
  if (activeReport.value === 'inventory') return inventoryQuery
  return salesQuery
})

const salesMetrics = computed(() => {
  const data = salesQuery.data.value
  return [
    { label: '完成销售单', value: `${data?.sales_order_count ?? 0} 单` },
    { label: '销售数量', value: formatQuantity(data?.sales_quantity) },
    { label: '销售金额', value: formatPrice(data?.sales_amount) },
    { label: '退货数量', value: formatQuantity(data?.sales_return_quantity) },
    { label: '退货金额', value: formatPrice(data?.sales_return_amount) },
    { label: '净销售额', value: formatPrice(data?.net_sales_amount) },
    { label: '销售成本', value: formatPrice(data?.sales_cost) },
    { label: '退货成本', value: formatPrice(data?.sales_return_cost) },
    { label: '净销售成本', value: formatPrice(data?.net_sales_cost) },
    { label: '销售毛利', value: formatPrice(data?.gross_profit) },
  ]
})
const purchaseMetrics = computed(() => {
  const data = purchasesQuery.data.value
  return [
    { label: '完成进货单', value: `${data?.purchase_count ?? 0} 单` },
    { label: '进货数量', value: formatQuantity(data?.purchase_quantity) },
    { label: '进货金额', value: formatPrice(data?.purchase_amount) },
    { label: '退货数量', value: formatQuantity(data?.purchase_return_quantity) },
    { label: '退货金额', value: formatPrice(data?.purchase_return_amount) },
    { label: '净进货额', value: formatPrice(data?.net_purchase_amount) },
  ]
})
const inventoryMetrics = computed(() => {
  const data = inventoryQuery.data.value
  return [
    { label: '商品总数', value: `${data?.product_count ?? 0} 种` },
    { label: '有库存商品', value: `${data?.in_stock_product_count ?? 0} 种` },
    { label: '无库存商品', value: `${data?.out_of_stock_product_count ?? 0} 种` },
    { label: '库存总数量', value: formatQuantity(data?.total_quantity) },
    { label: '库存总金额', value: formatPrice(data?.total_amount) },
  ]
})

function applyDateRange() {
  dateRange.value = [...dateRangeInput.value]
}

function refreshActiveReport() {
  void activeQuery.value.refetch()
}

function formatLocalDate(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

</script>

<style scoped>
.report-workspace { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; text-align: left; }
.report-workspace__heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.report-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }
.report-workspace__heading h1 { margin: 0; font-size: 28px; letter-spacing: 0; }
.report-toolbar { display: flex; align-items: center; gap: 10px; margin: 20px 0; }
.report-workspace__alert { margin: 16px 0; }
.report-summary { display: grid; min-height: 220px; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid #dce5df; border-left: 1px solid #dce5df; background: #ffffff; }
.report-summary__item { min-width: 0; padding: 26px 22px; border-right: 1px solid #dce5df; border-bottom: 1px solid #dce5df; }
.report-summary__item span { display: block; margin-bottom: 12px; color: #68756f; font-size: 13px; }
.report-summary__item strong { display: block; overflow: hidden; color: #17211b; font-size: 25px; font-variant-numeric: tabular-nums; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.report-note { display: flex; align-items: center; gap: 8px; margin-top: 18px; color: #68756f; font-size: 13px; }
.report-note .el-button { margin-left: auto; }
@media (max-width: 760px) {
  .report-workspace { padding: 24px 16px 36px; }
  .report-toolbar { align-items: stretch; flex-direction: column; }
  .report-toolbar :deep(.el-date-editor), .report-toolbar .el-button { width: 100%; }
  .report-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-summary__item strong { font-size: 20px; }
  .report-note { align-items: flex-start; flex-wrap: wrap; }
  .report-note .el-button { margin-left: 0; }
}
</style>