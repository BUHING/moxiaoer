<template>
  <section class="sales-workspace">
    <header class="sales-workspace__heading">
      <div><p>销售</p><h1>{{ isReturnMode ? '销售退货' : '销售开单' }}</h1></div>
      <div class="sales-workspace__actions">
        <el-button v-if="canCreateReturn" :type="isReturnMode ? 'primary' : 'default'" @click="switchMode(true)">退货单</el-button>
        <el-button :type="!isReturnMode ? 'primary' : 'default'" @click="switchMode(false)">销售单</el-button>
        <el-button :icon="Plus" type="primary" @click="newDocument">新增</el-button>
      </div>
    </header>

    <el-alert v-if="errorMessage" class="sales-workspace__alert" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />
    <el-alert v-if="!canCurrentAction" class="sales-workspace__alert" type="warning" title="当前账号没有此模块的开单权限。" show-icon :closable="false" />

    <div class="sales-workspace__grid">
      <section class="sales-panel">
        <div class="sales-panel__toolbar"><el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option label="草稿" value="DRAFT" /><el-option label="已完成" value="COMPLETED" /></el-select><el-button :icon="Refresh" circle title="刷新单据" @click="documentsQuery.refetch()" /></div>
        <el-table v-loading="documentsQuery.isLoading.value" :data="documents" highlight-current-row empty-text="暂无单据" @current-change="selectDocument">
          <el-table-column prop="document_no" label="单号" min-width="155" />
          <el-table-column label="客户" min-width="110"><template #default="scope">{{ partnerName(scope.row.customer_name) }}</template></el-table-column>
          <el-table-column prop="total_amount" label="金额" width="140"><template #default="scope">{{ formatPrice(scope.row.total_amount) }}</template></el-table-column>
          <el-table-column label="状态" width="82"><template #default="scope"><el-tag :type="scope.row.status === 'COMPLETED' ? 'success' : 'warning'">{{ scope.row.status === 'COMPLETED' ? '已完成' : '草稿' }}</el-tag></template></el-table-column>
        </el-table>
      </section>

      <section class="sales-panel sales-editor">
        <template v-if="selectedDocument">
          <div class="sales-editor__title"><span>{{ selectedDocument.document_no }}</span><el-tag :type="selectedDocument.status === 'COMPLETED' ? 'success' : 'warning'">{{ selectedDocument.status === 'COMPLETED' ? '已完成' : '草稿' }}</el-tag></div>
          <el-form label-position="top" :disabled="isCompleted || !canCurrentAction">
            <div class="sales-editor__details">
              <el-form-item label="客户"><div class="sales-editor__customer"><el-select v-model="form.customer_id" clearable filterable placeholder="选择客户（可选）"><el-option v-for="customer in customers" :key="customer.id" :label="customer.name" :value="customer.id" /></el-select><el-button v-if="canManageCustomers" :icon="Plus" circle title="新增客户" @click="customerDialogVisible = true" /></div></el-form-item>
              <el-form-item v-if="isReturnMode" label="原销售单" required><el-select v-model="form.sales_order_id" filterable placeholder="选择已完成销售单" @change="selectSourceOrder"><el-option v-for="order in sourceOrders" :key="order.id" :label="`${order.document_no} - ${order.customer_name}`" :value="order.id" /></el-select></el-form-item>
              <el-form-item label="业务日期" required><el-date-picker v-model="form.occurred_on" type="date" value-format="YYYY-MM-DD" /></el-form-item>
            </div>
            <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="请输入备注" /></el-form-item>
            <el-divider content-position="left">商品明细</el-divider>
            <el-table :data="form.items" empty-text="请添加商品">
              <el-table-column label="商品" min-width="210"><template #default="scope"><el-select v-model="scope.row.product_id" filterable placeholder="选择商品" :disabled="isReturnMode" @change="fillPrice(scope.$index)"><el-option v-for="product in products" :key="product.id" :label="`${product.name}（库存 ${formatQuantity(product.stock_quantity)}${product.unit_name}）`" :value="product.id" /></el-select></template></el-table-column>
              <el-table-column label="数量" width="120"><template #default="scope"><el-input v-model="scope.row.quantity" inputmode="numeric" /></template></el-table-column>
              <el-table-column label="单价" width="120"><template #default="scope"><el-input v-model="scope.row.unit_price" inputmode="decimal" :disabled="isReturnMode" /></template></el-table-column>
              <el-table-column width="54"><template #default="scope"><el-button :icon="Delete" circle title="移除明细" @click="removeItem(scope.$index)" /></template></el-table-column>
            </el-table>
            <el-button v-if="!isReturnMode" class="sales-editor__add" :icon="Plus" plain @click="addItem">添加商品</el-button>
          </el-form>
          <footer class="sales-editor__footer"><strong>合计 {{ formatPrice(selectedDocument.total_amount) }}</strong><div><el-button v-if="selectedDocument.id" :icon="Delete" type="danger" plain @click="removeDocument">删除单据</el-button><template v-if="!isCompleted"><el-button @click="saveDraft" :loading="saveMutation.isPending.value">保存草稿</el-button><el-button type="primary" :loading="completeMutation.isPending.value" @click="completeDocument">完成{{ isReturnMode ? '退货' : '销售' }}</el-button></template></div></footer>
        </template>
        <el-empty v-else description="选择或新建一张单据" />
      </section>
    </div>

    <el-dialog v-model="customerDialogVisible" title="新增客户" width="420px" destroy-on-close>
      <el-form label-position="top"><el-form-item label="客户名称" required><el-input v-model="newCustomerName" maxlength="150" /></el-form-item><el-form-item label="备注"><el-input v-model="newCustomerRemark" type="textarea" :rows="3" placeholder="请输入备注" /></el-form-item></el-form>
      <template #footer><el-button @click="customerDialogVisible = false">取消</el-button><el-button type="primary" :loading="customerMutation.isPending.value" @click="createCustomer">保存</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Delete, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, V1Service } from '../../api/generated'
import { deleteDocument } from '../../api/account'
import type { Customer, Product, SalesDocumentWrite, SalesOrder, SalesReturn } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'
import { useAuthStore } from '../../stores/auth'
import { formatPrice, formatQuantity } from '../../utils/numberFormat'

type Document = SalesOrder | SalesReturn
type SalesFormItem = { product_id: string; quantity: string; unit_price: string; sales_order_item_id?: string }
type SalesForm = Omit<SalesDocumentWrite, 'items'> & { sales_order_id?: string; items: SalesFormItem[] }
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const isReturnMode = ref(route.path.endsWith('/returns'))
const statusFilter = ref('')
const selectedDocument = ref<Document | null>(null)
const errorMessage = ref('')
const customerDialogVisible = ref(false)
const newCustomerName = ref('')
const newCustomerRemark = ref('')
const form = reactive<SalesForm>({ customer_id: '', occurred_on: new Date().toISOString().slice(0, 10), remark: '', items: [] })
const canCreate = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('sales.create'))
const canCreateReturn = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('sales.returns.manage'))
const canManageCustomers = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('partners.manage'))
const canCurrentAction = computed(() => isReturnMode.value ? canCreateReturn.value : canCreate.value)
const isCompleted = computed(() => selectedDocument.value?.status === 'COMPLETED')
const documentsQuery = useQuery({ queryKey: computed(() => ['sales-documents', isReturnMode.value, statusFilter.value]), queryFn: () => fetchAllPages((page, pageSize) => isReturnMode.value ? V1Service.salesReturnsList(undefined, page, pageSize, statusFilter.value || undefined) : V1Service.salesOrdersList(undefined, page, pageSize, statusFilter.value || undefined)), retry: false })
const sourceOrdersQuery = useQuery({ queryKey: ['sales-return-sources'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.salesOrdersList(undefined, page, pageSize, 'COMPLETED')), retry: false })
const customersQuery = useQuery({ queryKey: ['customers', 'active'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.customersList(true, page, pageSize)), retry: false })
const productsQuery = useQuery({ queryKey: ['products', 'active'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.productsList(true, page, pageSize)), retry: false })
const documents = computed(() => documentsQuery.data.value ?? [])
const sourceOrders = computed<SalesOrder[]>(() => sourceOrdersQuery.data.value ?? [])
const customers = computed<Customer[]>(() => customersQuery.data.value ?? [])
const products = computed<Product[]>(() => productsQuery.data.value ?? [])
const saveMutation = useMutation({ mutationFn: async () => { const payload = documentPayload(); return selectedDocument.value?.id ? isReturnMode.value ? V1Service.salesReturnsPartialUpdate(selectedDocument.value.id, payload) : V1Service.salesOrdersPartialUpdate(selectedDocument.value.id, payload) : isReturnMode.value ? V1Service.salesReturnsCreate(payload) : V1Service.salesOrdersCreate(payload) }, onSuccess: async (response) => { selectedDocument.value = response.data; assignForm(response.data); await queryClient.invalidateQueries({ queryKey: ['sales-documents'] }) } })
const completeMutation = useMutation({ mutationFn: async () => { if (!selectedDocument.value) throw new Error('请先保存单据。'); const idempotencyKey = crypto.randomUUID(); return isReturnMode.value ? V1Service.salesReturnsComplete(idempotencyKey, selectedDocument.value.id) : V1Service.salesOrdersComplete(idempotencyKey, selectedDocument.value.id) }, onSuccess: async (response) => { selectedDocument.value = response.data; assignForm(response.data); await queryClient.invalidateQueries({ queryKey: ['sales-documents'] }); await queryClient.invalidateQueries({ queryKey: ['products'] }); await queryClient.invalidateQueries({ queryKey: ['dashboard'] }) } })
const customerMutation = useMutation({ mutationFn: async (payload: { name: string; remark: string }) => V1Service.customersCreate(payload), onSuccess: async (response) => { form.customer_id = response.data.id; customerDialogVisible.value = false; newCustomerName.value = ''; newCustomerRemark.value = ''; await queryClient.invalidateQueries({ queryKey: ['customers'] }) } })

watch(() => route.path, (path) => { const returnMode = path.endsWith('/returns'); if (isReturnMode.value !== returnMode) { isReturnMode.value = returnMode; selectedDocument.value = null; resetForm() } })
function switchMode(returnMode: boolean) { if (returnMode && !canCreateReturn.value) return; void router.push(returnMode ? '/sales/returns' : '/sales') }
function resetForm() { Object.assign(form, { customer_id: '', sales_order_id: undefined, occurred_on: new Date().toISOString().slice(0, 10), remark: '', items: [] }) }
function assignForm(document: Document) { form.customer_id = document.customer_id ?? ''; form.sales_order_id = 'sales_order_id' in document ? document.sales_order_id : undefined; form.occurred_on = document.occurred_on; form.remark = document.remark ?? ''; form.items = document.items.map((item) => ({ product_id: item.product_id, quantity: integerQuantity(item.quantity), unit_price: item.unit_price, ...('sales_order_item_id' in item ? { sales_order_item_id: item.sales_order_item_id } : {}) })) }
function selectDocument(document: Document | undefined) { if (!document) return; selectedDocument.value = document; assignForm(document) }
function newDocument() { selectedDocument.value = { id: '', document_no: '新建草稿', customer_id: '', customer_name: '', status: 'DRAFT', occurred_on: form.occurred_on ?? '', total_amount: '0.00', remark: '', completed_by_user_id: null, completed_at: null, created_at: '', updated_at: '', items: [] } as Document; resetForm(); if (!isReturnMode.value) addItem() }
function addItem() { form.items = [...(form.items ?? []), { product_id: '', quantity: '1', unit_price: '0.00' }] }
function removeItem(index: number) { form.items = (form.items ?? []).filter((_, itemIndex) => itemIndex !== index) }
function fillPrice(index: number) { const item = form.items?.[index]; const product = products.value.find((candidate) => candidate.id === item?.product_id); if (item && product?.prices[0]) item.unit_price = product.prices[0].amount }
function selectSourceOrder(orderId: string) { const order = sourceOrders.value.find((candidate) => candidate.id === orderId); if (!order) return; form.customer_id = order.customer_id ?? ''; form.items = order.items.map((item) => ({ product_id: item.product_id, sales_order_item_id: item.id, quantity: integerQuantity(item.quantity), unit_price: item.unit_price })) }
function integerQuantity(value: string) { const quantity = Number(value); return Number.isFinite(quantity) ? String(Math.trunc(quantity)) : '0' }
function partnerName(name: string | null | undefined) { return name || '未指定' }
function documentPayload(): SalesForm { if (!form.occurred_on || !(form.items?.length)) throw new Error('请选择业务日期并至少添加一条商品明细。'); form.items = form.items.map((item) => ({ ...item, quantity: integerQuantity(item.quantity) })); if (form.items.some((item) => !item.product_id || !(Number(item.quantity) > 0) || !(Number(item.unit_price) >= 0))) throw new Error('请填写有效的商品、数量和单价。'); if (isReturnMode.value && (!form.sales_order_id || form.items.some((item) => !item.sales_order_item_id))) throw new Error('请选择原销售单，并从原单明细填写退货数量。'); return { customer_id: form.customer_id || null, sales_order_id: form.sales_order_id, occurred_on: form.occurred_on, remark: form.remark ?? '', items: form.items } }
function apiMessage(error: unknown) { if (error instanceof ApiError && typeof error.body === 'object' && error.body !== null && 'message' in error.body) return String(error.body.message); return error instanceof Error ? error.message : '操作未完成，请稍后重试。' }
async function saveDraft() { try { await saveMutation.mutateAsync() } catch (error) { errorMessage.value = apiMessage(error) } }
async function createCustomer() { if (!newCustomerName.value.trim()) { errorMessage.value = '请填写客户名称。'; return } try { await customerMutation.mutateAsync({ name: newCustomerName.value.trim(), remark: newCustomerRemark.value }) } catch (error) { errorMessage.value = apiMessage(error) } }
async function completeDocument() { try { await ElMessageBox.confirm(`完成后将${isReturnMode.value ? '增加' : '扣减'}库存且不可编辑，确定继续吗？`, `确认完成${isReturnMode.value ? '退货' : '销售'}`, { type: 'warning' }); await saveMutation.mutateAsync(); if (!selectedDocument.value?.id) return; await completeMutation.mutateAsync() } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
async function removeDocument() { if (!selectedDocument.value?.id) return; try { await ElMessageBox.confirm('删除后会同步清理单据明细和库存流水，且无法恢复。', '确认删除单据', { type: 'warning' }); const path = isReturnMode.value ? `/sales-returns/${selectedDocument.value.id}/` : `/sales-orders/${selectedDocument.value.id}/`; await deleteDocument(path); selectedDocument.value = null; resetForm(); await queryClient.invalidateQueries({ queryKey: ['sales-documents'] }); await queryClient.invalidateQueries({ queryKey: ['products'] }); await queryClient.invalidateQueries({ queryKey: ['dashboard'] }) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
</script>

<style scoped>
.sales-workspace { max-width: 1360px; margin: 0 auto; padding: 28px 24px 48px; }.sales-workspace__heading, .sales-workspace__actions, .sales-panel__toolbar, .sales-editor__title, .sales-editor__footer, .sales-editor__customer { display: flex; align-items: center; gap: 10px; }.sales-workspace__heading { justify-content: space-between; margin-bottom: 22px; }.sales-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }.sales-workspace__heading h1 { margin: 0; font-size: 28px; }.sales-workspace__alert { margin-bottom: 16px; }.sales-workspace__grid { display: grid; grid-template-columns: minmax(420px, .95fr) minmax(500px, 1.35fr); gap: 18px; }.sales-panel { min-width: 0; padding: 18px; border: 1px solid #dce5df; border-radius: 8px; background: #fff; }.sales-panel__toolbar { justify-content: space-between; margin-bottom: 14px; }.sales-panel__toolbar .el-select { width: 150px; }.sales-editor__title { justify-content: space-between; padding-bottom: 12px; font-weight: 650; }.sales-editor__details { display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; }.sales-editor__details .el-form-item { margin-bottom: 0; }.sales-editor__customer .el-select { min-width: 0; flex: 1; }.sales-editor__add { margin-top: 12px; }.sales-editor__footer { justify-content: space-between; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e9e6; }.sales-editor__footer strong { color: #176b5b; font-size: 18px; }@media (max-width: 920px) { .sales-workspace__grid { grid-template-columns: 1fr; }.sales-editor__details { grid-template-columns: 1fr; }}@media (max-width: 600px) { .sales-workspace { padding: 24px 16px 36px; }.sales-workspace__heading { align-items: flex-start; flex-direction: column; }.sales-workspace__actions { flex-wrap: wrap; }.sales-panel { padding: 14px; }.sales-editor__footer { align-items: flex-start; flex-direction: column; }}
</style>