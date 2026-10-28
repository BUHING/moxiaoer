<template>
  <section class="purchase-workspace">
    <header class="purchase-workspace__heading">
      <div><p>进货</p><h1>{{ isReturnMode ? '进货退货' : '进货入库' }}</h1></div>
      <div class="purchase-workspace__actions">
        <el-button v-if="canCreateReturn" :type="isReturnMode ? 'primary' : 'default'" @click="switchMode(true)">退货单</el-button>
        <el-button :type="!isReturnMode ? 'primary' : 'default'" @click="switchMode(false)">进货单</el-button>
        <el-button :icon="Plus" type="primary" @click="newDocument">新增</el-button>
      </div>
    </header>

    <el-alert v-if="errorMessage" class="purchase-workspace__alert" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />
    <el-alert v-if="!canCurrentAction" class="purchase-workspace__alert" type="warning" title="当前账号没有此模块的开单权限。" show-icon :closable="false" />

    <div class="purchase-workspace__grid">
      <section class="purchase-panel">
        <div class="purchase-panel__toolbar"><el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option label="草稿" value="DRAFT" /><el-option label="已完成" value="COMPLETED" /></el-select><el-button :icon="Refresh" circle title="刷新单据" @click="documentsQuery.refetch()" /></div>
        <el-table v-loading="documentsQuery.isLoading.value" :data="documents" highlight-current-row empty-text="暂无单据" @current-change="selectDocument">
          <el-table-column prop="document_no" label="单号" min-width="220" class-name="document-number" />
          <el-table-column label="供应商" min-width="110"><template #default="scope">{{ partnerName(scope.row.supplier_name) }}</template></el-table-column>
          <el-table-column prop="total_amount" label="金额" width="140"><template #default="scope">{{ formatPrice(scope.row.total_amount) }}</template></el-table-column>
          <el-table-column label="状态" width="82"><template #default="scope"><el-tag :type="scope.row.status === 'COMPLETED' ? 'success' : 'warning'">{{ scope.row.status === 'COMPLETED' ? '已完成' : '草稿' }}</el-tag></template></el-table-column>
        </el-table>
      </section>

      <section class="purchase-panel purchase-editor">
        <template v-if="selectedDocument">
          <div class="purchase-editor__title"><span>{{ selectedDocument.document_no }}</span><el-tag :type="selectedDocument.status === 'COMPLETED' ? 'success' : 'warning'">{{ selectedDocument.status === 'COMPLETED' ? '已完成' : '草稿' }}</el-tag></div>
          <el-form label-position="top" :disabled="isCompleted || !canCurrentAction">
            <div class="purchase-editor__details">
              <el-form-item label="供应商"><div class="purchase-editor__supplier"><el-select v-model="form.supplier_id" clearable filterable placeholder="选择供应商（可选）"><el-option v-for="supplier in suppliers" :key="supplier.id" :label="formatSupplierOption(supplier)" :title="formatSupplierOption(supplier)" :value="supplier.id" /></el-select><el-button v-if="canManageSuppliers" :icon="Plus" circle title="新增供应商" @click="supplierErrorMessage = ''; supplierDialogVisible = true" /></div></el-form-item>
              <el-form-item v-if="isReturnMode" label="原采购单（可选）"><el-select v-model="form.purchase_id" clearable filterable placeholder="选择已完成采购单" @change="selectSourcePurchase"><el-option v-for="purchase in sourcePurchases" :key="purchase.id" :label="purchase.supplier_name ? `${purchase.document_no} - ${purchase.supplier_name}` : purchase.document_no" :value="purchase.id" /></el-select></el-form-item>
              <el-form-item label="业务日期" required><el-date-picker v-model="form.occurred_on" type="date" value-format="YYYY-MM-DD" /></el-form-item>
            </div>
            <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="请输入备注" /></el-form-item>
            <el-divider content-position="left">商品明细</el-divider>
            <el-table :data="form.items" empty-text="请添加商品">
              <el-table-column label="商品" min-width="210"><template #default="scope"><el-select v-model="scope.row.product_id" filterable placeholder="选择商品" :disabled="isReturnMode && Boolean(form.purchase_id)" @change="fillPurchasePrice(scope.$index)"><el-option v-for="product in products" :key="product.id" :label="`${product.name}（库存 ${formatQuantity(product.stock_quantity)}${product.unit_name}）`" :value="product.id" /></el-select></template></el-table-column>
              <el-table-column label="数量" width="120"><template #default="scope"><el-input v-model="scope.row.quantity" inputmode="numeric" /></template></el-table-column>
              <el-table-column label="单价" width="120"><template #default="scope"><el-input v-model="scope.row.unit_price" inputmode="decimal" :disabled="isReturnMode" /></template></el-table-column>
              <el-table-column width="54"><template #default="scope"><el-button :icon="Delete" circle title="移除明细" @click="removeItem(scope.$index)" /></template></el-table-column>
            </el-table>
            <el-button v-if="!isReturnMode || !form.purchase_id" class="purchase-editor__add" :icon="Plus" plain @click="addItem">添加商品</el-button>
          </el-form>
          <footer class="purchase-editor__footer"><strong>合计 {{ formatPrice(selectedDocument.total_amount) }}</strong><div><el-button v-if="selectedDocument.id" :icon="Delete" type="danger" plain @click="removeDocument">删除单据</el-button><template v-if="!isCompleted"><el-button @click="saveDraft" :loading="saveMutation.isPending.value">保存草稿</el-button><el-button type="primary" :loading="completeMutation.isPending.value" @click="completeDocument">完成{{ isReturnMode ? '退货' : '入库' }}</el-button></template></div></footer>
        </template>
        <el-empty v-else description="选择或新建一张单据" />
      </section>
    </div>

    <el-dialog v-model="supplierDialogVisible" title="新增供应商" width="420px" destroy-on-close>
      <el-alert v-if="supplierErrorMessage" class="purchase-workspace__alert" type="error" :title="supplierErrorMessage" show-icon @close="supplierErrorMessage = ''" />
      <el-form label-position="top"><el-form-item label="供应商名称" required><el-input v-model="newSupplierName" maxlength="150" /></el-form-item><el-form-item label="联系人"><el-input v-model="newSupplierContactName" maxlength="100" /></el-form-item><el-form-item label="联系地址"><el-input v-model="newSupplierContactAddress" maxlength="255" /></el-form-item><el-form-item label="电话"><el-input v-model="newSupplierPhone" maxlength="50" /></el-form-item><el-form-item label="备注"><el-input v-model="newSupplierRemark" type="textarea" :rows="3" placeholder="请输入备注" /></el-form-item></el-form>
      <template #footer><el-button @click="supplierDialogVisible = false">取消</el-button><el-button type="primary" :loading="supplierMutation.isPending.value" @click="createSupplier">保存</el-button></template>
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
import type { Product, Purchase, PurchaseDocumentWrite, PurchaseReturn, Supplier, SupplierWrite } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'
import { useAuthStore } from '../../stores/auth'
import { formatPrice, formatQuantity } from '../../utils/numberFormat'
import { formatSupplierOption } from '../../utils/partnerFormat'

type Document = Purchase | PurchaseReturn
type PurchaseFormItem = { product_id: string; quantity: string; unit_price: string; purchase_item_id?: string }
type PurchaseForm = Omit<PurchaseDocumentWrite, 'items'> & { purchase_id?: string | null; items: PurchaseFormItem[] }
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const isReturnMode = ref(route.path.endsWith('/returns'))
const statusFilter = ref('')
const selectedDocument = ref<Document | null>(null)
const errorMessage = ref('')
const supplierDialogVisible = ref(false)
const supplierErrorMessage = ref('')
const newSupplierName = ref('')
const newSupplierContactName = ref('')
const newSupplierContactAddress = ref('')
const newSupplierPhone = ref('')
const newSupplierRemark = ref('')
const form = reactive<PurchaseForm>({ supplier_id: '', occurred_on: new Date().toISOString().slice(0, 10), remark: '', items: [] })
const canCreate = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('purchases.create'))
const canCreateReturn = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('purchases.returns.manage'))
const canManageSuppliers = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('partners.manage'))
const canCurrentAction = computed(() => isReturnMode.value ? canCreateReturn.value : canCreate.value)
const isCompleted = computed(() => selectedDocument.value?.status === 'COMPLETED')
const documentsQuery = useQuery({ queryKey: computed(() => ['purchase-documents', isReturnMode.value, statusFilter.value]), queryFn: () => fetchAllPages((page, pageSize) => isReturnMode.value ? V1Service.purchaseReturnsList(page, pageSize, statusFilter.value || undefined) : V1Service.purchasesList(page, pageSize, statusFilter.value || undefined)), retry: false })
const sourcePurchasesQuery = useQuery({ queryKey: ['purchase-return-sources'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.purchasesList(page, pageSize, 'COMPLETED')), retry: false })
const suppliersQuery = useQuery({ queryKey: ['suppliers', 'active'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.suppliersList(true, page, pageSize)), retry: false })
const productsQuery = useQuery({ queryKey: ['products', 'active'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.productsList(true, page, pageSize)), retry: false })
const documents = computed(() => documentsQuery.data.value ?? [])
const sourcePurchases = computed<Purchase[]>(() => sourcePurchasesQuery.data.value ?? [])
const suppliers = computed<Supplier[]>(() => suppliersQuery.data.value ?? [])
const products = computed<Product[]>(() => productsQuery.data.value ?? [])
const saveMutation = useMutation({ mutationFn: async () => { const payload = documentPayload(); return selectedDocument.value?.id ? isReturnMode.value ? V1Service.purchaseReturnsPartialUpdate(selectedDocument.value.id, payload) : V1Service.purchasesPartialUpdate(selectedDocument.value.id, payload) : isReturnMode.value ? V1Service.purchaseReturnsCreate(payload) : V1Service.purchasesCreate(payload) }, onSuccess: async (response) => { selectedDocument.value = response.data; assignForm(response.data); await queryClient.invalidateQueries({ queryKey: ['purchase-documents'] }) } })
const completeMutation = useMutation({ mutationFn: async () => { if (!selectedDocument.value) throw new Error('请先保存单据。'); const idempotencyKey = crypto.randomUUID(); return isReturnMode.value ? V1Service.purchaseReturnsComplete(idempotencyKey, selectedDocument.value.id) : V1Service.purchasesComplete(idempotencyKey, selectedDocument.value.id) }, onSuccess: async (response) => { selectedDocument.value = response.data; assignForm(response.data); await queryClient.invalidateQueries({ queryKey: ['purchase-documents'] }); await queryClient.invalidateQueries({ queryKey: ['products'] }) } })
const supplierMutation = useMutation({ mutationFn: async (payload: SupplierWrite) => V1Service.suppliersCreate(payload), onSuccess: async (response) => { form.supplier_id = response.data.id; supplierDialogVisible.value = false; newSupplierName.value = ''; newSupplierContactName.value = ''; newSupplierContactAddress.value = ''; newSupplierPhone.value = ''; newSupplierRemark.value = ''; supplierErrorMessage.value = ''; await queryClient.invalidateQueries({ queryKey: ['suppliers'] }) } })

watch(() => route.path, (path) => { const returnMode = path.endsWith('/returns'); if (isReturnMode.value !== returnMode) { isReturnMode.value = returnMode; selectedDocument.value = null; resetForm() } })
function switchMode(returnMode: boolean) { if (returnMode && !canCreateReturn.value) return; void router.push(returnMode ? '/purchases/returns' : '/purchases') }
function resetForm() { Object.assign(form, { supplier_id: '', purchase_id: undefined, occurred_on: new Date().toISOString().slice(0, 10), remark: '', items: [] }) }
function assignForm(document: Document) { form.supplier_id = document.supplier_id ?? ''; form.purchase_id = 'purchase_id' in document ? document.purchase_id ?? undefined : undefined; form.occurred_on = document.occurred_on; form.remark = document.remark ?? ''; form.items = document.items.map((item) => ({ product_id: item.product_id, quantity: integerQuantity(item.quantity), unit_price: item.unit_price, ...('purchase_item_id' in item && item.purchase_item_id ? { purchase_item_id: item.purchase_item_id } : {}) })) }
function selectDocument(document: Document | undefined) { if (!document) return; selectedDocument.value = document; assignForm(document) }
function newDocument() { selectedDocument.value = { id: '', document_no: '新建草稿', supplier_id: '', supplier_name: '', status: 'DRAFT', occurred_on: form.occurred_on ?? '', total_amount: '0.00', remark: '', completed_by_user_id: null, completed_at: null, created_at: '', updated_at: '', items: [] } as Document; resetForm(); if (!isReturnMode.value) addItem() }
function addItem() { form.items = [...(form.items ?? []), { product_id: '', quantity: '1', unit_price: '0.00' }] }
function removeItem(index: number) { form.items = (form.items ?? []).filter((_, itemIndex) => itemIndex !== index) }
function fillPurchasePrice(index: number) { const item = form.items?.[index]; const product = products.value.find((candidate) => candidate.id === item?.product_id); if (item && product) item.unit_price = product.purchase_price ?? '0.00' }
function selectSourcePurchase(purchaseId?: string) { const purchase = sourcePurchases.value.find((candidate) => candidate.id === purchaseId); if (!purchase) { form.items = []; return }; form.supplier_id = purchase.supplier_id ?? ''; form.items = purchase.items.map((item) => ({ product_id: item.product_id, purchase_item_id: item.id, quantity: integerQuantity(item.quantity), unit_price: item.unit_price })) }
function integerQuantity(value: string) { const quantity = Number(value); return Number.isFinite(quantity) ? String(Math.trunc(quantity)) : '0' }
function partnerName(name: string | null | undefined) { return name || '未指定' }
function documentPayload(): PurchaseForm { if (!form.occurred_on || !(form.items?.length)) throw new Error('请选择业务日期并至少添加一条商品明细。'); form.items = form.items.map((item) => ({ ...item, quantity: integerQuantity(item.quantity) })); if (form.items.some((item) => !item.product_id || !(Number(item.quantity) > 0) || !(Number(item.unit_price) >= 0))) throw new Error('请填写有效的商品、数量和单价。'); if (isReturnMode.value && form.purchase_id && form.items.some((item) => !item.purchase_item_id)) throw new Error('请选择原采购单后，请从原单明细填写退货数量。'); return { supplier_id: form.supplier_id || null, ...(isReturnMode.value ? { purchase_id: form.purchase_id ?? null } : {}), occurred_on: form.occurred_on, remark: form.remark ?? '', items: form.items } }
function apiMessage(error: unknown) { if (error instanceof ApiError && typeof error.body === 'object' && error.body !== null && 'message' in error.body) return String(error.body.message); return error instanceof Error ? error.message : '操作未完成，请稍后重试。' }
async function saveDraft() { try { await saveMutation.mutateAsync() } catch (error) { errorMessage.value = apiMessage(error) } }
async function createSupplier() { if (!newSupplierName.value.trim()) { supplierErrorMessage.value = '请填写供应商名称。'; return } try { await supplierMutation.mutateAsync({ name: newSupplierName.value.trim(), contact_name: newSupplierContactName.value.trim(), contact_address: newSupplierContactAddress.value.trim(), phone: newSupplierPhone.value.trim(), remark: newSupplierRemark.value }) } catch (error) { supplierErrorMessage.value = apiMessage(error) } }
async function completeDocument() { try { await ElMessageBox.confirm(`完成后将${isReturnMode.value ? '扣减' : '增加'}库存且不可编辑，确定继续吗？`, `确认完成${isReturnMode.value ? '退货' : '入库'}`, { type: 'warning' }); await saveMutation.mutateAsync(); if (!selectedDocument.value?.id) return; await completeMutation.mutateAsync() } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
async function removeDocument() { if (!selectedDocument.value?.id) return; try { await ElMessageBox.confirm('删除后会同步清理单据明细和库存流水，且无法恢复。', '确认删除单据', { type: 'warning' }); const path = isReturnMode.value ? `/purchase-returns/${selectedDocument.value.id}/` : `/purchases/${selectedDocument.value.id}/`; await deleteDocument(path); selectedDocument.value = null; resetForm(); await queryClient.invalidateQueries({ queryKey: ['purchase-documents'] }); await queryClient.invalidateQueries({ queryKey: ['products'] }) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
</script>

<style scoped>
.purchase-panel :deep(.document-number .cell) { white-space: nowrap; }
.purchase-editor__title > span { min-width: 0; overflow-wrap: anywhere; }
.purchase-editor__title > .el-tag { flex-shrink: 0; }
.purchase-workspace { max-width: 1360px; margin: 0 auto; padding: 28px 24px 48px; }.purchase-workspace__heading, .purchase-workspace__actions, .purchase-panel__toolbar, .purchase-editor__title, .purchase-editor__footer, .purchase-editor__supplier { display: flex; align-items: center; gap: 10px; }.purchase-workspace__heading { justify-content: space-between; margin-bottom: 22px; }.purchase-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }.purchase-workspace__heading h1 { margin: 0; font-size: 28px; }.purchase-workspace__alert { margin-bottom: 16px; }.purchase-workspace__grid { display: grid; grid-template-columns: minmax(420px, .95fr) minmax(500px, 1.35fr); gap: 18px; }.purchase-panel { min-width: 0; padding: 18px; border: 1px solid #dce5df; border-radius: 8px; background: #fff; }.purchase-panel__toolbar { justify-content: space-between; margin-bottom: 14px; }.purchase-panel__toolbar .el-select { width: 150px; }.purchase-editor__title { justify-content: space-between; padding-bottom: 12px; font-weight: 650; }.purchase-editor__details { display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; }.purchase-editor__details .el-form-item { margin-bottom: 0; }.purchase-editor__supplier .el-select { min-width: 0; flex: 1; }.purchase-editor__add { margin-top: 12px; }.purchase-editor__footer { justify-content: space-between; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e9e6; }.purchase-editor__footer strong { color: #176b5b; font-size: 18px; }@media (max-width: 920px) { .purchase-workspace__grid { grid-template-columns: 1fr; }.purchase-editor__details { grid-template-columns: 1fr; }}@media (max-width: 600px) { .purchase-workspace { padding: 24px 16px 36px; }.purchase-workspace__heading { align-items: flex-start; flex-direction: column; }.purchase-workspace__actions { flex-wrap: wrap; }.purchase-panel { padding: 14px; }.purchase-editor__footer { align-items: flex-start; flex-direction: column; }}
</style>