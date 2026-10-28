<template>
  <section class="product-workspace">
    <header class="product-workspace__heading">
      <div>
        <p>商品</p>
        <h1>商品资料</h1>
      </div>
      <el-button v-if="canManage" type="primary" :icon="Plus" @click="openProductDialog()">新增商品</el-button>
    </header>

    <el-alert v-if="errorMessage" class="product-workspace__alert" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="商品" name="products">
        <div class="product-workspace__toolbar">
          <el-input v-model="search" clearable placeholder="搜索商品名称" @keyup.enter="productsQuery.refetch()" />
          <el-select v-model="activeFilter" aria-label="商品状态筛选">
            <el-option label="全部状态" value="" />
            <el-option label="仅启用" value="true" />
            <el-option label="仅停用" value="false" />
          </el-select>
          <el-button :icon="Refresh" circle title="刷新商品列表" @click="productsQuery.refetch()" />
          <el-select v-model="sortOrder" class="list-sort-select" aria-label="商品排序方式">
            <el-option v-for="option in listSortOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <span class="list-sort-help">{{ listSortHelpText }}</span>
        </div>
        <el-table v-loading="productsQuery.isLoading.value" :data="products" empty-text="暂无商品">
          <el-table-column prop="name" label="商品名称" min-width="180" />
          <el-table-column prop="supplier_name" label="默认供应商" min-width="150" />
          <el-table-column prop="unit_name" label="单位" width="100" />
          <el-table-column label="规格" min-width="170"><template #default="scope"><span>{{ formatSpecifications(scope.row) }}</span></template></el-table-column>
          <el-table-column label="库存" width="120"><template #default="scope">{{ formatQuantity(scope.row.stock_quantity) }}</template></el-table-column>
          <el-table-column label="进货价" width="130"><template #default="scope">{{ formatPrice(scope.row.purchase_price) }}</template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column v-if="canManage" label="操作" width="180" fixed="right"><template #default="scope">
            <el-button link type="primary" :icon="EditPen" @click="openProductDialog(scope.row)">编辑</el-button>
            <el-button v-if="scope.row.is_active" link type="warning" @click="deactivateProduct(scope.row.id)">停用</el-button>
            <el-button link type="danger" :icon="Delete" @click="deleteProduct(scope.row.id)">删除</el-button>
          </template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="单位" name="units">
        <div class="product-workspace__subheading"><span>商品单位</span><el-button v-if="canManage" type="primary" plain :icon="Plus" @click="openCatalogDialog('unit')">新增单位</el-button></div>
        <el-table v-loading="catalogQuery.isLoading.value" :data="catalog.units" empty-text="暂无单位"><el-table-column prop="name" label="名称" /><el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column><el-table-column v-if="canManage" label="操作" width="190"><template #default="scope"><el-button link type="primary" @click="openCatalogDialog('unit', scope.row)">编辑</el-button><el-button v-if="scope.row.is_active" link type="warning" @click="deactivateCatalog('unit', scope.row.id)">停用</el-button><el-button link type="danger" @click="deleteCatalog('unit', scope.row.id)">删除</el-button></template></el-table-column></el-table>
      </el-tab-pane>

      <el-tab-pane label="规格" name="specifications">
        <div class="product-workspace__subheading"><span>规格管理</span><el-button v-if="canManage" type="primary" plain :icon="Plus" @click="openCatalogDialog('specification')">新增规格</el-button></div>
        <el-table v-loading="catalogQuery.isLoading.value" :data="catalog.specifications" empty-text="暂无规格"><el-table-column prop="name" label="名称" /><el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column><el-table-column v-if="canManage" label="操作" width="190"><template #default="scope"><el-button link type="primary" @click="openCatalogDialog('specification', scope.row)">编辑</el-button><el-button v-if="scope.row.is_active" link type="warning" @click="deactivateCatalog('specification', scope.row.id)">停用</el-button><el-button link type="danger" @click="deleteCatalog('specification', scope.row.id)">删除</el-button></template></el-table-column></el-table>
      </el-tab-pane>

      <el-tab-pane label="商品属性" name="attributes">
        <div class="product-workspace__subheading"><span>商品属性</span><el-button v-if="canManage" type="primary" plain :icon="Plus" @click="openCatalogDialog('attribute')">新增属性</el-button></div>
        <el-table v-loading="catalogQuery.isLoading.value" :data="catalog.attributes" empty-text="暂无商品属性"><el-table-column prop="name" label="名称" /><el-table-column label="类型" width="120"><template #default="scope">{{ scope.row.input_type === InputTypeEnum.SELECT ? '选择型' : '输入型' }}</template></el-table-column><el-table-column label="选项" min-width="180"><template #default="scope"><el-tag v-for="option in scope.row.options" :key="option.id" class="product-workspace__option">{{ option.value }}</el-tag></template></el-table-column><el-table-column v-if="canManage" label="操作" width="230"><template #default="scope"><el-button v-if="scope.row.input_type === InputTypeEnum.SELECT" link type="primary" @click="openOptionDialog(scope.row)">新增选项</el-button><el-button link type="primary" @click="openCatalogDialog('attribute', scope.row)">编辑</el-button><el-button link type="danger" @click="deleteCatalog('attribute', scope.row.id)">删除</el-button></template></el-table-column></el-table>
      </el-tab-pane>

      <el-tab-pane label="价格管理" name="prices">
        <div class="product-workspace__subheading"><span>价格等级</span><el-button v-if="canManage" type="primary" plain :icon="Plus" @click="openCatalogDialog('priceLevel')">新增价格等级</el-button></div>
        <el-table v-loading="catalogQuery.isLoading.value" :data="catalog.priceLevels" empty-text="暂无价格等级"><el-table-column prop="sort_order" label="排序" width="100" /><el-table-column prop="name" label="名称" /><el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column><el-table-column v-if="canManage" label="操作" width="190"><template #default="scope"><el-button link type="primary" @click="openCatalogDialog('priceLevel', scope.row)">编辑</el-button><el-button v-if="scope.row.is_active" link type="warning" @click="deactivateCatalog('priceLevel', scope.row.id)">停用</el-button><el-button link type="danger" @click="deleteCatalog('priceLevel', scope.row.id)">删除</el-button></template></el-table-column></el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="productDialogVisible" :title="editingProductId ? '编辑商品' : '新增商品'" width="min(860px, 94vw)" destroy-on-close>
      <el-form label-position="top">
        <div class="product-form__grid">
          <el-form-item label="商品名称" required><el-input v-model="productForm.name" maxlength="200" /></el-form-item>
          <el-form-item label="默认供应商"><el-select v-model="productForm.supplier_id" clearable filterable placeholder="请选择供应商"><el-option v-for="supplier in selectableSuppliers" :key="supplier.id" :label="formatSupplierOption(supplier)" :title="formatSupplierOption(supplier)" :value="supplier.id" /></el-select></el-form-item>
          <el-form-item label="单位" required><el-select v-model="productForm.unit_id" filterable><el-option v-for="unit in activeUnits" :key="unit.id" :label="unit.name" :value="unit.id" /></el-select></el-form-item>
          <el-form-item label="进货价" required><el-input v-model="productForm.purchase_price" inputmode="decimal" placeholder="0.00" /></el-form-item>
          <el-form-item v-if="!editingProductId" label="初始库存"><el-input v-model="productForm.initial_quantity" inputmode="numeric" placeholder="0" /></el-form-item>
          <el-form-item label="规格"><el-checkbox v-model="isMultiSpecification">启用多规格</el-checkbox><el-input v-if="!isMultiSpecification" v-model="productForm.specification" maxlength="100" placeholder="请输入规格" /></el-form-item>
        </div>
        <template v-if="isMultiSpecification">
          <el-divider content-position="left">多规格</el-divider>
          <div v-for="(specificationValueItem, index) in productForm.specification_values" :key="index" class="product-form__specification-row">
            <el-select v-model="specificationValueItem.specification_id" filterable placeholder="选择规格"><el-option v-for="specification in availableSpecifications(specificationValueItem.specification_id)" :key="specification.id" :label="specification.name" :value="specification.id" /></el-select>
            <el-input v-model="specificationValueItem.value" maxlength="100" placeholder="请输入规格值" />
            <el-button :icon="Delete" circle title="移除规格" @click="removeSpecification(index)" />
          </div>
          <el-button :icon="Plus" plain @click="addSpecification">添加规格</el-button>
        </template>
        <el-divider content-position="left">备注</el-divider>
        <el-form-item><el-input v-model="productForm.remark" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="请输入备注" /></el-form-item>
        <el-divider content-position="left">商品属性</el-divider>
        <div class="product-form__grid">
          <el-form-item v-for="attribute in activeAttributes" :key="attribute.id" :label="attribute.name"><el-select v-if="attribute.input_type === InputTypeEnum.SELECT" clearable :model-value="attributeOptionValue(attribute.id)" @update:model-value="setAttributeOption(attribute.id, $event)"><el-option v-for="option in attribute.options.filter((item) => item.is_active)" :key="option.id" :label="option.value" :value="option.id" /></el-select><el-input v-else :model-value="attributeTextValue(attribute.id)" @update:model-value="setAttributeText(attribute.id, $event)" /></el-form-item>
        </div>
        <el-divider content-position="left">价格</el-divider>
        <div class="product-form__grid">
          <el-form-item v-for="priceLevel in activePriceLevels" :key="priceLevel.id" :label="priceLevel.name"><el-input :model-value="priceValue(priceLevel.id)" inputmode="decimal" placeholder="0.00" @update:model-value="setPriceValue(priceLevel.id, $event)" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="productDialogVisible = false">取消</el-button><el-button type="primary" :loading="productMutation.isPending.value" @click="saveProduct">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="catalogDialogVisible" :title="catalogDialogTitle" width="420px" destroy-on-close>
      <el-form label-position="top"><el-form-item label="名称" required><el-input v-model="catalogName" maxlength="50" /></el-form-item><el-form-item v-if="catalogKind === 'attribute'" label="属性类型"><el-radio-group v-model="attributeInputType"><el-radio-button :value="InputTypeEnum.TEXT">输入型</el-radio-button><el-radio-button :value="InputTypeEnum.SELECT">选择型</el-radio-button></el-radio-group></el-form-item><el-form-item v-if="catalogKind === 'priceLevel'" label="排序"><el-input-number v-model="priceLevelSortOrder" :min="0" :step="1" /></el-form-item></el-form>
      <template #footer><el-button @click="catalogDialogVisible = false">取消</el-button><el-button type="primary" :loading="catalogMutation.isPending.value" @click="saveCatalog">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="optionDialogVisible" :title="`新增 ${optionAttribute?.name ?? ''} 选项`" width="420px" destroy-on-close>
      <el-form label-position="top"><el-form-item label="选项值" required><el-input v-model="optionValue" maxlength="100" /></el-form-item></el-form>
      <template #footer><el-button @click="optionDialogVisible = false">取消</el-button><el-button type="primary" :loading="catalogMutation.isPending.value" @click="saveOption">保存</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Delete, EditPen, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import type { PriceLevel, Product, ProductAttribute, ProductAttributeValueInput, ProductPriceInput, ProductWrite, Specification, Supplier, Unit } from '../../api/generated'
import { ApiError, InputTypeEnum, V1Service } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'
import { useAuthStore } from '../../stores/auth'
import { formatPrice, formatQuantity } from '../../utils/numberFormat'
import { formatSupplierOption } from '../../utils/partnerFormat'
import { listSortHelpText, listSortOptions, sortRecords } from '../../utils/listSorting'
import { useListSorting } from '../../composables/useListSorting'

type CatalogKind = 'unit' | 'specification' | 'attribute' | 'priceLevel'

const auth = useAuthStore()
const queryClient = useQueryClient()
const activeTab = ref('products')
const search = ref('')
const activeFilter = ref('true')
const errorMessage = ref('')
const { sortOrder } = useListSorting('products', () => auth.user, (message) => { errorMessage.value = message })
const productDialogVisible = ref(false)
const editingProductId = ref<string | null>(null)
const catalogDialogVisible = ref(false)
const catalogKind = ref<CatalogKind>('unit')
const catalogEditingId = ref<string | null>(null)
const catalogName = ref('')
const attributeInputType = ref(InputTypeEnum.TEXT)
const priceLevelSortOrder = ref(0)
const optionDialogVisible = ref(false)
const optionAttribute = ref<ProductAttribute | null>(null)
const optionValue = ref('')
const isMultiSpecification = ref(false)
const productForm = reactive<ProductWrite>(emptyProductForm())

const canManage = computed(() => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('products.manage'))
const productsQuery = useQuery({
  queryKey: computed(() => ['products', search.value, activeFilter.value]),
  queryFn: () => fetchAllPages((page, pageSize) => V1Service.productsList(activeFilter.value === '' ? undefined : activeFilter.value === 'true', page, pageSize, undefined, search.value || undefined)),
  retry: false,
})
const catalogQuery = useQuery({
  queryKey: ['product-catalog'],
  queryFn: async () => {
    const [units, specifications, attributes, priceLevels] = await Promise.all([
      fetchAllPages((page, pageSize) => V1Service.unitsList(page, pageSize)),
      fetchAllPages((page, pageSize) => V1Service.specificationsList(page, pageSize)),
      fetchAllPages((page, pageSize) => V1Service.productAttributesList(page, pageSize)),
      fetchAllPages((page, pageSize) => V1Service.priceLevelsList(page, pageSize)),
    ])
    return { units, specifications, attributes, priceLevels }
  },
  retry: false,
})
const suppliersQuery = useQuery({
  queryKey: ['suppliers', 'active-options'],
  queryFn: () => fetchAllPages((page, pageSize) => V1Service.suppliersList(true, page, pageSize)),
  retry: false,
})
const products = computed(() => sortRecords(productsQuery.data.value ?? [], sortOrder.value))
const catalog = computed(() => catalogQuery.data.value ?? { units: [] as Unit[], specifications: [] as Specification[], attributes: [] as ProductAttribute[], priceLevels: [] as PriceLevel[] })
const activeUnits = computed(() => catalog.value.units.filter((item) => item.is_active))
const activeSpecifications = computed(() => catalog.value.specifications.filter((item) => item.is_active))
const activeAttributes = computed(() => catalog.value.attributes.filter((item) => item.is_active))
const activePriceLevels = computed(() => catalog.value.priceLevels.filter((item) => item.is_active))
const suppliers = computed<Supplier[]>(() => suppliersQuery.data.value ?? [])
const selectableSuppliers = computed(() => {
  const selectedSupplierId = productForm.supplier_id
  return suppliers.value.filter((supplier) => supplier.is_active || supplier.id === selectedSupplierId)
})
const catalogDialogTitle = computed(() => `${catalogEditingId.value ? '编辑' : '新增'}${{ unit: '单位', specification: '规格', attribute: '商品属性', priceLevel: '价格等级' }[catalogKind.value]}`)

const productMutation = useMutation({
  mutationFn: async (payload: ProductWrite) => editingProductId.value ? V1Service.productsPartialUpdate(editingProductId.value, payload) : V1Service.productsCreate(payload),
  onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['products'] }); productDialogVisible.value = false },
})
const catalogMutation = useMutation({
  mutationFn: async (action: () => Promise<unknown>) => action(),
  onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['product-catalog'] }); await queryClient.invalidateQueries({ queryKey: ['products'] }) },
})

function emptyProductForm(): ProductWrite { return { name: '', unit_id: '', supplier_id: null, purchase_price: '0.00', specification: '', remark: '', initial_quantity: '0', specification_values: [], attribute_values: [], prices: [] } }
function formatSpecifications(product: Product) { return product.specification_values.map((item) => `${item.specification_name}: ${item.value}`).join('；') || product.specification || '-' }
function apiMessage(error: unknown) { if (error instanceof ApiError && typeof error.body === 'object' && error.body !== null && 'message' in error.body) return String(error.body.message); return '操作未完成，请检查输入或稍后重试。' }
function resetProductForm() { Object.assign(productForm, emptyProductForm()) }
function openProductDialog(product?: Product) { resetProductForm(); editingProductId.value = product?.id ?? null; isMultiSpecification.value = Boolean(product?.specification_values.length); if (product) { productForm.name = product.name; productForm.unit_id = product.unit_id; productForm.supplier_id = product.supplier_id; productForm.purchase_price = product.purchase_price ?? '0.00'; productForm.specification = product.specification ?? ''; productForm.remark = product.remark ?? ''; productForm.is_active = product.is_active; productForm.specification_values = product.specification_values.map((item) => ({ specification_id: item.specification_id, value: item.value })); productForm.attribute_values = product.attribute_values.map((item) => item.option_id ? { attribute_id: item.attribute_id, option_id: item.option_id } : { attribute_id: item.attribute_id, text_value: item.text_value ?? '' }); productForm.prices = product.prices.map((item) => ({ price_level_id: item.price_level_id, amount: item.amount })); delete productForm.initial_quantity }; productDialogVisible.value = true }
function availableSpecifications(selectedId: string) { return activeSpecifications.value.filter((item) => item.id === selectedId || !productForm.specification_values?.some((value) => value.specification_id === item.id)) }
function addSpecification() { productForm.specification_values = [...(productForm.specification_values ?? []), { specification_id: '', value: '' }] }
function removeSpecification(index: number) { productForm.specification_values = (productForm.specification_values ?? []).filter((_, itemIndex) => itemIndex !== index) }
function attributeTextValue(attributeId: string) { return productForm.attribute_values?.find((item) => item.attribute_id === attributeId)?.text_value ?? '' }
function attributeOptionValue(attributeId: string) { return productForm.attribute_values?.find((item) => item.attribute_id === attributeId)?.option_id }
function setAttributeText(attributeId: string, value: string) { setAttributeValue(attributeId, value ? { attribute_id: attributeId, text_value: value } : undefined) }
function setAttributeOption(attributeId: string, optionId: string | undefined) { setAttributeValue(attributeId, optionId ? { attribute_id: attributeId, option_id: optionId } : undefined) }
function setAttributeValue(attributeId: string, value: ProductAttributeValueInput | undefined) { const values = productForm.attribute_values ?? []; productForm.attribute_values = value ? [...values.filter((item) => item.attribute_id !== attributeId), value] : values.filter((item) => item.attribute_id !== attributeId) }
function priceValue(priceLevelId: string) { return productForm.prices?.find((item) => item.price_level_id === priceLevelId)?.amount ?? '' }
function setPriceValue(priceLevelId: string, amount: string) { const prices = productForm.prices ?? []; productForm.prices = amount ? [...prices.filter((item) => item.price_level_id !== priceLevelId), { price_level_id: priceLevelId, amount } as ProductPriceInput] : prices.filter((item) => item.price_level_id !== priceLevelId) }
async function saveProduct() { if (!productForm.name?.trim() || !productForm.unit_id) { errorMessage.value = '请填写商品名称并选择单位。'; return }; if (isMultiSpecification.value && productForm.specification_values?.some((item) => !item.specification_id || !item.value.trim())) { errorMessage.value = '请选择规格并填写规格值。'; return }; try { await productMutation.mutateAsync({ ...productForm, name: productForm.name.trim(), specification: isMultiSpecification.value ? '' : productForm.specification?.trim(), specification_values: isMultiSpecification.value ? productForm.specification_values : [] }) } catch (error) { errorMessage.value = apiMessage(error) } }

function openCatalogDialog(kind: CatalogKind, item?: Unit | Specification | ProductAttribute | PriceLevel) { catalogKind.value = kind; catalogEditingId.value = item?.id ?? null; catalogName.value = item?.name ?? ''; attributeInputType.value = item && 'input_type' in item ? item.input_type : InputTypeEnum.TEXT; priceLevelSortOrder.value = item && 'sort_order' in item ? item.sort_order ?? 0 : catalog.value.priceLevels.length; catalogDialogVisible.value = true }
async function saveCatalog() { if (!catalogName.value.trim()) { errorMessage.value = '请填写名称。'; return }; const request = catalogEditingId.value ? updateCatalog(catalogKind.value, catalogEditingId.value) : createCatalog(catalogKind.value); try { await catalogMutation.mutateAsync(request); catalogDialogVisible.value = false } catch (error) { errorMessage.value = apiMessage(error) } }
function createCatalog(kind: CatalogKind) { const name = catalogName.value.trim(); if (kind === 'unit') return () => V1Service.unitsCreate({ name }); if (kind === 'specification') return () => V1Service.specificationsCreate({ name }); if (kind === 'attribute') return () => V1Service.productAttributesCreate({ name, input_type: attributeInputType.value }); return () => V1Service.priceLevelsCreate({ name, sort_order: priceLevelSortOrder.value }) }
function updateCatalog(kind: CatalogKind, id: string) { const name = catalogName.value.trim(); if (kind === 'unit') return () => V1Service.unitsPartialUpdate(id, { name }); if (kind === 'specification') return () => V1Service.specificationsPartialUpdate(id, { name }); if (kind === 'attribute') return () => V1Service.productAttributesPartialUpdate(id, { name, input_type: attributeInputType.value }); return () => V1Service.priceLevelsPartialUpdate(id, { name, sort_order: priceLevelSortOrder.value }) }
async function deactivateCatalog(kind: CatalogKind, id: string) { try { await ElMessageBox.confirm('停用后不能用于新建商品，确定继续吗？', '确认停用', { type: 'warning' }); const actions = { unit: () => V1Service.v1UnitsDeactivateCreate(id), specification: () => V1Service.v1SpecificationsDeactivateCreate(id), attribute: () => V1Service.v1ProductAttributesDeactivateCreate(id), priceLevel: () => V1Service.v1PriceLevelsDeactivateCreate(id) }; await catalogMutation.mutateAsync(actions[kind]) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
async function deleteCatalog(kind: CatalogKind, id: string) { try { await ElMessageBox.confirm('删除后无法恢复，确定继续吗？', '确认删除', { type: 'warning' }); const actions = { unit: () => V1Service.unitsDestroy(id), specification: () => V1Service.specificationsDestroy(id), attribute: () => V1Service.productAttributesDestroy(id), priceLevel: () => V1Service.priceLevelsDestroy(id) }; await catalogMutation.mutateAsync(actions[kind]) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
function openOptionDialog(attribute: ProductAttribute) { optionAttribute.value = attribute; optionValue.value = ''; optionDialogVisible.value = true }
async function saveOption() { if (!optionAttribute.value || !optionValue.value.trim()) { errorMessage.value = '请填写选项值。'; return }; try { await catalogMutation.mutateAsync(() => V1Service.productAttributeOptionsCreate(optionAttribute.value!.id, { value: optionValue.value.trim() })); optionDialogVisible.value = false } catch (error) { errorMessage.value = apiMessage(error) } }
async function deactivateProduct(id: string) { try { await ElMessageBox.confirm('停用后不能用于新单据，确定继续吗？', '确认停用', { type: 'warning' }); await catalogMutation.mutateAsync(() => V1Service.v1ProductsDeactivateCreate(id)) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
async function deleteProduct(id: string) { try { await ElMessageBox.confirm('删除后无法恢复；已有库存流水的商品不可删除。', '确认删除', { type: 'warning' }); await catalogMutation.mutateAsync(() => V1Service.productsDestroy(id)) } catch (error) { if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error) } }
</script>

<style scoped>
.list-sort-help { color: #6b7780; font-size: 12px; }
.product-workspace { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; }
.product-workspace__heading, .product-workspace__subheading, .product-workspace__toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.product-workspace__toolbar { flex-wrap: wrap; }
.product-workspace__toolbar .el-select.list-sort-select { width: 200px; }
.product-workspace__heading { margin-bottom: 24px; }.product-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }.product-workspace__heading h1 { margin: 0; font-size: 28px; }.product-workspace__alert { margin-bottom: 16px; }.product-workspace__subheading { margin: 0 0 16px; font-size: 16px; font-weight: 650; }.product-workspace__toolbar { justify-content: flex-start; margin-bottom: 16px; }.product-workspace__toolbar .el-input { width: 280px; }.product-workspace__toolbar .el-select { width: 130px; }.product-workspace__option { margin-right: 6px; }.product-form__grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 16px; }.product-form__specification-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 40px; gap: 12px; margin-bottom: 12px; }
@media (max-width: 720px) { .product-workspace { padding: 24px 16px 36px; }.product-workspace__heading { align-items: flex-start; }.product-workspace__toolbar { align-items: stretch; flex-wrap: wrap; }.product-workspace__toolbar .el-input { width: calc(100% - 52px); }.product-form__grid { grid-template-columns: 1fr; }.product-form__specification-row { grid-template-columns: minmax(0, 1fr) 40px; }.product-form__specification-row .el-input { grid-column: 1 / -1; grid-row: 2; } }
</style>