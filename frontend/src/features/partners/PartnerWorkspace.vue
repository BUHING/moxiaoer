<template>
  <section class="partner-workspace">
    <header class="partner-workspace__heading">
      <div><p>客户</p><h1>{{ activeTab === 'customers' ? '客户资料' : '价格等级' }}</h1></div>
      <el-button v-if="canManage" type="primary" :icon="Plus" @click="openDialog()">新增{{ activeTab === 'customers' ? '客户' : '价格等级' }}</el-button>
    </header>

    <el-alert v-if="errorMessage" class="partner-workspace__alert" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="客户" name="customers">
        <div class="partner-workspace__toolbar">
          <el-input v-model="search" clearable placeholder="搜索客户名称" @keyup.enter="customersQuery.refetch()" />
          <el-select v-model="activeFilter" aria-label="客户状态筛选"><el-option label="全部状态" value="" /><el-option label="仅启用" value="true" /><el-option label="仅停用" value="false" /></el-select>
          <el-button :icon="Refresh" circle title="刷新客户列表" @click="customersQuery.refetch()" />
        </div>
        <el-table v-loading="customersQuery.isLoading.value" :data="customers" empty-text="暂无客户">
          <el-table-column prop="name" label="客户名称" min-width="160" />
          <el-table-column prop="contact_name" label="联系人" min-width="120" />
          <el-table-column prop="phone" label="电话" min-width="130" />
          <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
          <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column v-if="canManage" label="操作" width="180" fixed="right"><template #default="scope"><el-button link type="primary" :icon="EditPen" @click="openDialog(scope.row)">编辑</el-button><el-button v-if="scope.row.is_active" link type="warning" @click="deactivateCustomer(scope.row.id)">停用</el-button><el-button link type="danger" :icon="Delete" @click="deleteCustomer(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="价格等级" name="price-levels">
        <el-table v-loading="priceLevelsQuery.isLoading.value" :data="priceLevels" empty-text="暂无价格等级">
          <el-table-column prop="sort_order" label="排序" width="90" />
          <el-table-column prop="name" label="名称" min-width="180" />
          <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column v-if="canManagePrices" label="操作" width="180" fixed="right"><template #default="scope"><el-button link type="primary" :icon="EditPen" @click="openDialog(scope.row)">编辑</el-button><el-button v-if="scope.row.is_active" link type="warning" @click="deactivatePriceLevel(scope.row.id)">停用</el-button><el-button link type="danger" :icon="Delete" @click="deletePriceLevel(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="min(460px, 94vw)" destroy-on-close>
      <el-form label-position="top">
        <el-form-item :label="activeTab === 'customers' ? '客户名称' : '等级名称'" required><el-input v-model="form.name" :maxlength="activeTab === 'customers' ? 150 : 50" /></el-form-item>
        <template v-if="activeTab === 'customers'"><el-form-item label="联系人"><el-input v-model="form.contact_name" maxlength="100" /></el-form-item><el-form-item label="电话"><el-input v-model="form.phone" maxlength="50" /></el-form-item><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="3" /></el-form-item></template>
        <el-form-item v-else label="排序"><el-input-number v-model="form.sort_order" :min="0" :step="1" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saveMutation.isPending.value" @click="save">保存</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Delete, EditPen, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, V1Service } from '../../api/generated'
import type { Customer, CustomerWrite, PriceLevel, PriceLevelWrite } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'
import { useAuthStore } from '../../stores/auth'

type PartnerForm = {
  name: string
  contact_name: string
  phone: string
  remark: string
  sort_order: number
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const activeTab = ref<'customers' | 'price-levels'>(route.path === '/price-levels' ? 'price-levels' : 'customers')
const search = ref('')
const activeFilter = ref('true')
const errorMessage = ref('')
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const form = reactive<PartnerForm>(emptyForm())
const canManage = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('partners.manage'))
const canManagePrices = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('products.manage'))
const dialogTitle = computed(() => `${editingId.value ? '编辑' : '新增'}${activeTab.value === 'customers' ? '客户' : '价格等级'}`)
const customersQuery = useQuery({ queryKey: computed(() => ['customers', search.value, activeFilter.value]), queryFn: () => fetchAllPages((page, pageSize) => V1Service.customersList(activeFilter.value === '' ? undefined : activeFilter.value === 'true', page, pageSize, search.value || undefined)), retry: false })
const priceLevelsQuery = useQuery({ queryKey: ['price-levels'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.priceLevelsList(page, pageSize)), retry: false })
const customers = computed<Customer[]>(() => customersQuery.data.value ?? [])
const priceLevels = computed<PriceLevel[]>(() => priceLevelsQuery.data.value ?? [])
const saveMutation = useMutation({ mutationFn: async () => activeTab.value === 'customers' ? saveCustomer() : savePriceLevel(), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: activeTab.value === 'customers' ? ['customers'] : ['price-levels'] }); dialogVisible.value = false } })

watch(() => route.path, (path) => { activeTab.value = path === '/price-levels' ? 'price-levels' : 'customers' })
watch(activeTab, (tab) => {
  const path = tab === 'price-levels' ? '/price-levels' : '/customers'
  if (route.path !== path) void router.push(path)
})
function emptyForm(): PartnerForm { return { name: '', contact_name: '', phone: '', remark: '', sort_order: 0 } }
function resetForm() { Object.assign(form, emptyForm()) }
function openDialog(item?: Customer | PriceLevel) { resetForm(); editingId.value = item?.id ?? null; if (item) { form.name = item.name ?? ''; if ('contact_name' in item) { form.contact_name = item.contact_name ?? ''; form.phone = item.phone ?? ''; form.remark = item.remark ?? '' } else if ('sort_order' in item) form.sort_order = item.sort_order ?? 0 } else if (activeTab.value === 'price-levels') form.sort_order = priceLevels.value.length; dialogVisible.value = true }
function apiMessage(error: unknown) { if (error instanceof ApiError && typeof error.body === 'object' && error.body !== null && 'message' in error.body) return String(error.body.message); return error instanceof Error ? error.message : '操作未完成，请检查输入或稍后重试。' }
function saveCustomer() { const payload: CustomerWrite = { name: form.name.trim(), contact_name: form.contact_name, phone: form.phone, remark: form.remark }; return editingId.value ? V1Service.customersPartialUpdate(editingId.value, payload) : V1Service.customersCreate(payload) }
function savePriceLevel() { const payload: PriceLevelWrite = { name: form.name.trim(), sort_order: form.sort_order }; return editingId.value ? V1Service.priceLevelsPartialUpdate(editingId.value, payload) : V1Service.priceLevelsCreate(payload) }
async function save() { if (!form.name.trim()) { errorMessage.value = '请填写名称。'; return } try { await saveMutation.mutateAsync() } catch (error) { errorMessage.value = apiMessage(error) } }
async function deactivateCustomer(id: string) { await runConfirmed('停用后不能用于新建销售单，确定继续吗？', () => V1Service.customersDeactivate(id), ['customers']) }
async function deleteCustomer(id: string) { await runConfirmed('删除后无法恢复；已被销售单引用的客户不可删除。', () => V1Service.customersDestroy(id), ['customers']) }
async function deactivatePriceLevel(id: string) { await runConfirmed('停用后不能用于新建商品，确定继续吗？', () => V1Service.v1PriceLevelsDeactivateCreate(id), ['price-levels']) }
async function deletePriceLevel(id: string) { await runConfirmed('删除后无法恢复，确定继续吗？', () => V1Service.priceLevelsDestroy(id), ['price-levels']) }
async function runConfirmed(message: string, action: () => Promise<unknown>, queryKey: string[]) { try { await ElMessageBox.confirm(message, '确认操作', { type: 'warning' }); await action(); await queryClient.invalidateQueries({ queryKey }) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
</script>

<style scoped>
.partner-workspace { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; }.partner-workspace__heading, .partner-workspace__toolbar { display: flex; align-items: center; gap: 12px; }.partner-workspace__heading { justify-content: space-between; margin-bottom: 24px; }.partner-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }.partner-workspace__heading h1 { margin: 0; font-size: 28px; }.partner-workspace__alert { margin-bottom: 16px; }.partner-workspace__toolbar { margin-bottom: 16px; }.partner-workspace__toolbar .el-input { width: 280px; }.partner-workspace__toolbar .el-select { width: 130px; } @media (max-width: 600px) { .partner-workspace { padding: 24px 16px 36px; }.partner-workspace__heading { align-items: flex-start; }.partner-workspace__toolbar { flex-wrap: wrap; }.partner-workspace__toolbar .el-input { width: calc(100% - 52px); } }
</style>