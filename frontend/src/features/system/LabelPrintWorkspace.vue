<template>
  <section class="label-print">
    <header><div><p>系统工具</p><h1>标签打印</h1></div><el-button type="primary" :icon="Printer" @click="printLabels">打印预览</el-button></header>
    <el-alert v-if="errorMessage" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />
    <div class="label-print__layout">
      <section class="label-print__controls">
        <el-form label-position="top">
          <el-form-item label="商品"><el-select v-model="productId" filterable placeholder="选择商品"><el-option v-for="product in products" :key="product.id" :label="product.name" :value="product.id" /></el-select></el-form-item>
          <el-form-item label="模板"><el-select v-model="templateId" placeholder="选择模板"><el-option v-for="item in templates" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
          <el-form-item label="打印份数"><el-input-number v-model="copies" :min="1" :max="200" /></el-form-item>
          <el-form-item label="模板文件"><input type="file" accept="application/json" @change="importTemplate" /></el-form-item>
          <el-button :loading="saveMutation.isPending.value" @click="saveTemplate">保存导入模板</el-button>
        </el-form>
        <p class="label-print__hint">模板 JSON 必须包含 <code>elements</code> 数组。元素可使用 <code>field</code> 绑定商品字段或 <code>text</code> 固定文字，并以毫米坐标定位。</p>
      </section>
      <section class="label-print__preview-wrap"><div v-if="activeTemplate && selectedProduct" id="label-print-area" class="label-print__sheet"><article v-for="copyIndex in copies" :key="copyIndex" class="label-print__card" :style="cardStyle"><template v-for="(element, index) in activeTemplate.template.elements" :key="index"><span v-if="element.type !== 'barcode'" class="label-print__element" :style="elementStyle(element)">{{ element.text || fieldValue(element.field) }}</span><span v-else class="label-print__barcode" :style="elementStyle(element)">||| {{ fieldValue(element.field) }} |||</span></template></article></div><el-empty v-else description="选择商品和打印模板" /></section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Printer } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { ApiError, V1Service } from '../../api/generated'
import type { LabelTemplate, LabelTemplateWrite, Product } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'

type TemplateElement = { type?: string; field?: string; text?: string; x?: number; y?: number; width?: number; height?: number; font_size?: number }
const queryClient = useQueryClient()
const productId = ref('')
const templateId = ref('')
const copies = ref(1)
const importedTemplate = ref<LabelTemplateWrite | null>(null)
const errorMessage = ref('')
const productsQuery = useQuery({ queryKey: ['products', 'label-print'], queryFn: () => fetchAllPages((page, pageSize) => V1Service.productsList(true, page, pageSize)), retry: false })
const templatesQuery = useQuery({ queryKey: ['label-templates'], queryFn: () => fetchAllPages(() => V1Service.labelTemplatesList()), retry: false })
const products = computed<Product[]>(() => productsQuery.data.value ?? [])
const templates = computed<LabelTemplate[]>(() => templatesQuery.data.value ?? [])
const selectedProduct = computed(() => products.value.find((product) => product.id === productId.value))
const activeTemplate = computed(() => templates.value.find((item) => item.id === templateId.value))
const cardStyle = computed(() => activeTemplate.value ? { width: `${activeTemplate.value.width_mm}mm`, height: `${activeTemplate.value.height_mm}mm`, '--orientation': activeTemplate.value.orientation === 'LANDSCAPE' ? 'landscape' : 'portrait' } : {})
const saveMutation = useMutation({ mutationFn: (payload: LabelTemplateWrite) => V1Service.labelTemplatesCreate(payload), onSuccess: async (response) => { templateId.value = response.data.id; await queryClient.invalidateQueries({ queryKey: ['label-templates'] }) } })

function fieldValue(field?: string) { const product = selectedProduct.value; if (!product || !field) return ''; const values: Record<string, string> = { name: product.name, unit_name: product.unit_name, purchase_price: product.purchase_price ?? '', barcode: product.id }; return values[field] ?? '' }
function elementStyle(element: TemplateElement) { return { left: `${element.x ?? 0}mm`, top: `${element.y ?? 0}mm`, width: `${element.width ?? 30}mm`, height: `${element.height ?? 8}mm`, fontSize: `${element.font_size ?? 10}pt` } }
function importTemplate(event: Event) { const file = (event.target as HTMLInputElement).files?.[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => { try { const parsed = JSON.parse(String(reader.result)) as LabelTemplateWrite; if (!parsed.name || !Array.isArray(parsed.template?.elements)) throw new Error('模板缺少名称或 elements 数组。'); importedTemplate.value = parsed; errorMessage.value = '' } catch (error) { errorMessage.value = error instanceof Error ? error.message : '模板文件无效。' } }; reader.readAsText(file) }
async function saveTemplate() { if (!importedTemplate.value) { errorMessage.value = '请先导入模板 JSON 文件。'; return } try { await saveMutation.mutateAsync(importedTemplate.value) } catch (error) { errorMessage.value = error instanceof ApiError ? '模板保存失败。' : '模板保存失败。' } }
function printLabels() { if (!activeTemplate.value || !selectedProduct.value) { errorMessage.value = '请先选择商品和打印模板。'; return } document.title = activeTemplate.value.name; window.print() }
</script>

<style scoped>
.label-print { max-width: 1200px; margin: 0 auto; padding: 28px 24px 48px; }.label-print header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }.label-print header p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }.label-print h1 { margin: 0; font-size: 28px; }.label-print__layout { display: grid; grid-template-columns: 310px minmax(0, 1fr); gap: 18px; }.label-print__controls, .label-print__preview-wrap { padding: 18px; border: 1px solid #dce5df; border-radius: 8px; background: #fff; }.label-print__hint { color: #687873; font-size: 13px; line-height: 1.6; }.label-print__sheet { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 12px; }.label-print__card { position: relative; overflow: hidden; border: 1px dashed #82938e; background: #fff; transform: rotate(0deg); }.label-print__element, .label-print__barcode { position: absolute; overflow: hidden; color: #111; line-height: 1.25; white-space: nowrap; }.label-print__barcode { font-family: monospace; letter-spacing: 1px; }@media (max-width: 800px) { .label-print { padding: 24px 16px 36px; }.label-print__layout { grid-template-columns: 1fr; }}
</style>

<style>
@media print { body * { visibility: hidden; } #label-print-area, #label-print-area * { visibility: visible; } #label-print-area { position: absolute; top: 0; left: 0; gap: 0; } .label-print__card { border: 0; break-after: page; page-break-after: always; } }
</style>