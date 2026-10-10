<template>
  <section class="inventory-workspace">
    <header class="inventory-workspace__heading">
      <div>
        <p>库存</p>
        <h1>库存查询</h1>
      </div>
      <el-button :icon="Refresh" circle title="刷新库存数据" @click="refreshActiveQuery" />
    </header>

    <el-alert
      v-if="activeError"
      class="inventory-workspace__alert"
      type="error"
      title="库存数据暂时无法加载"
      show-icon
      :closable="false"
    />

    <el-tabs v-model="activeTab" @tab-change="changeTab">
      <el-tab-pane label="现有库存" name="balances">
        <div class="inventory-toolbar">
          <el-input
            v-model="balanceSearchInput"
            clearable
            placeholder="搜索商品名称"
            @keyup.enter="applyBalanceSearch"
            @clear="applyBalanceSearch"
          />
          <el-button type="primary" :icon="Search" @click="applyBalanceSearch">查询</el-button>
        </div>

        <el-table
          v-loading="balancesQuery.isLoading.value"
          :data="balancesQuery.data.value?.data ?? []"
          empty-text="暂无库存记录"
        >
          <el-table-column prop="product_name" label="商品名称" min-width="240" />
          <el-table-column prop="quantity" label="现有库存" min-width="160">
            <template #default="scope">
              <strong class="inventory-quantity">{{ formatQuantity(scope.row.quantity) }}</strong>
              <span class="inventory-unit">{{ scope.row.unit_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="最近变动" min-width="190">
            <template #default="scope">{{ formatDateTime(scope.row.updated_at) }}</template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="balanceTotal > pageSize"
          v-model:current-page="balancePage"
          class="inventory-pagination"
          background
          layout="prev, pager, next, total"
          :page-size="pageSize"
          :total="balanceTotal"
        />
      </el-tab-pane>

      <el-tab-pane label="库存流水" name="movements">
        <div class="inventory-toolbar inventory-toolbar--movements">
          <el-input
            v-model="movementSearchInput"
            clearable
            placeholder="搜索商品名称"
            @keyup.enter="applyMovementFilters"
            @clear="applyMovementFilters"
          />
          <el-select v-model="movementTypeInput" clearable placeholder="全部类型">
            <el-option v-for="option in movementTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-date-picker
            v-model="movementDatesInput"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
          <el-button type="primary" :icon="Search" @click="applyMovementFilters">查询</el-button>
          <el-button @click="resetMovementFilters">重置</el-button>
        </div>

        <el-table
          v-loading="movementsQuery.isLoading.value"
          :data="movementsQuery.data.value?.data ?? []"
          empty-text="暂无库存流水"
        >
          <el-table-column prop="occurred_at" label="发生时间" min-width="180">
            <template #default="scope">{{ formatDateTime(scope.row.occurred_at) }}</template>
          </el-table-column>
          <el-table-column prop="product_name" label="商品名称" min-width="200" />
          <el-table-column prop="movement_type" label="变动类型" min-width="130">
            <template #default="scope"><el-tag effect="plain">{{ movementTypeLabel(scope.row.movement_type) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="quantity_delta" label="数量变化" min-width="140" align="right">
            <template #default="scope">
              <strong :class="quantityClass(scope.row.quantity_delta)">{{ signedQuantity(scope.row.quantity_delta) }}</strong>
              <span class="inventory-unit">{{ scope.row.unit_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="operator_name" label="操作人" min-width="140" />
          <el-table-column prop="source_id" label="来源编号" min-width="210" show-overflow-tooltip />
        </el-table>

        <el-pagination
          v-if="movementTotal > pageSize"
          v-model:current-page="movementPage"
          class="inventory-pagination"
          background
          layout="prev, pager, next, total"
          :page-size="pageSize"
          :total="movementTotal"
        />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Refresh, Search } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MovementTypeEnum, V1Service } from '../../api/generated'
import { formatQuantity } from '../../utils/numberFormat'

const route = useRoute()
const router = useRouter()
const pageSize = 20
const balancePage = ref(1)
const movementPage = ref(1)
const balanceSearchInput = ref('')
const balanceSearch = ref('')
const movementSearchInput = ref('')
const movementSearch = ref('')
const movementTypeInput = ref<MovementTypeEnum | ''>('')
const movementType = ref<MovementTypeEnum | ''>('')
const movementDatesInput = ref<[string, string] | []>([])
const movementDates = ref<[string, string] | []>([])
const activeTab = computed(() => route.name === 'inventory-movements' ? 'movements' : 'balances')

const movementTypeOptions: Array<{ value: MovementTypeEnum; label: string }> = [
  { value: MovementTypeEnum.INITIAL, label: '初始库存' },
  { value: MovementTypeEnum.PURCHASE, label: '进货入库' },
  { value: MovementTypeEnum.PURCHASE_RETURN, label: '进货退货' },
  { value: MovementTypeEnum.SALE, label: '销售出库' },
  { value: MovementTypeEnum.SALE_RETURN, label: '销售退货' },
]

const balancesQuery = useQuery({
  queryKey: computed(() => ['inventory', 'balances', balancePage.value, balanceSearch.value]),
  queryFn: () => V1Service.inventoryBalancesList(balancePage.value, pageSize, undefined, balanceSearch.value || undefined),
  retry: false,
})
const movementsQuery = useQuery({
  queryKey: computed(() => ['inventory', 'movements', movementPage.value, movementSearch.value, movementType.value, ...movementDates.value]),
  queryFn: () => V1Service.inventoryMovementsList(
    movementDates.value[0],
    movementDates.value[1],
    movementType.value || undefined,
    movementPage.value,
    pageSize,
    undefined,
    movementSearch.value || undefined,
  ),
  retry: false,
})

const balanceTotal = computed(() => Number(balancesQuery.data.value?.meta.total ?? 0))
const movementTotal = computed(() => Number(movementsQuery.data.value?.meta.total ?? 0))
const activeError = computed(() => activeTab.value === 'balances' ? balancesQuery.isError.value : movementsQuery.isError.value)

function changeTab(name: string | number) {
  void router.push(name === 'movements' ? '/inventory/movements' : '/inventory/balances')
}

function applyBalanceSearch() {
  balancePage.value = 1
  balanceSearch.value = balanceSearchInput.value.trim()
}

function applyMovementFilters() {
  movementPage.value = 1
  movementSearch.value = movementSearchInput.value.trim()
  movementType.value = movementTypeInput.value
  movementDates.value = movementDatesInput.value
}

function resetMovementFilters() {
  movementSearchInput.value = ''
  movementTypeInput.value = ''
  movementDatesInput.value = []
  applyMovementFilters()
}

function refreshActiveQuery() {
  if (activeTab.value === 'balances') void balancesQuery.refetch()
  else void movementsQuery.refetch()
}

function movementTypeLabel(type: MovementTypeEnum) {
  return movementTypeOptions.find((option) => option.value === type)?.label ?? type
}

function signedQuantity(quantity: string) {
  const formattedQuantity = formatQuantity(quantity)
  return Number(quantity) > 0 ? `+${formattedQuantity}` : formattedQuantity
}

function quantityClass(quantity: string) {
  return Number(quantity) > 0 ? 'inventory-delta inventory-delta--positive' : 'inventory-delta inventory-delta--negative'
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
</script>

<style scoped>
.inventory-workspace { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; text-align: left; }
.inventory-workspace__heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.inventory-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }
.inventory-workspace__heading h1 { margin: 0; font-size: 28px; letter-spacing: 0; }
.inventory-workspace__alert { margin-bottom: 16px; }
.inventory-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.inventory-toolbar .el-input { width: 280px; }
.inventory-toolbar--movements .el-select { width: 150px; }
.inventory-quantity { color: #17211b; font-variant-numeric: tabular-nums; }
.inventory-unit { margin-left: 6px; color: #7a817c; font-size: 13px; }
.inventory-delta { font-variant-numeric: tabular-nums; }
.inventory-delta--positive { color: #26734d; }
.inventory-delta--negative { color: #b23a32; }
.inventory-pagination { justify-content: flex-end; margin-top: 18px; }
@media (max-width: 820px) {
  .inventory-workspace { padding: 24px 16px 36px; }
  .inventory-toolbar { align-items: stretch; flex-wrap: wrap; }
  .inventory-toolbar .el-input { width: 100%; }
  .inventory-toolbar--movements .el-select { width: calc(50% - 5px); }
  .inventory-toolbar :deep(.el-date-editor) { width: 100%; }
}
</style>