<template>
  <section class="supplier-workspace">
    <header class="supplier-workspace__heading">
      <div>
        <p>进货资料</p>
        <h1>供应商资料</h1>
      </div>
      <el-button v-if="canManage" type="primary" :icon="Plus" @click="openDialog()">新增供应商</el-button>
    </header>

    <el-alert
      v-if="errorMessage"
      class="supplier-workspace__alert"
      type="error"
      :title="errorMessage"
      show-icon
      @close="errorMessage = ''"
    />

    <div class="supplier-workspace__toolbar">
      <el-input
        v-model="search"
        clearable
        placeholder="搜索供应商名称"
        @keyup.enter="suppliersQuery.refetch()"
      />
      <el-select v-model="activeFilter" aria-label="供应商状态筛选">
        <el-option label="全部状态" value="" />
        <el-option label="仅启用" value="true" />
        <el-option label="仅停用" value="false" />
      </el-select>
      <el-button :icon="Refresh" circle title="刷新供应商列表" @click="suppliersQuery.refetch()" />
    </div>

    <el-table v-loading="suppliersQuery.isLoading.value" :data="suppliers" empty-text="暂无供应商">
      <el-table-column prop="name" label="供应商名称" min-width="180" />
      <el-table-column prop="contact_name" label="联系人" min-width="120" />
      <el-table-column prop="contact_address" label="联系人地址" min-width="220" show-overflow-tooltip />
      <el-table-column prop="phone" label="电话" min-width="130" />
      <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">
            {{ scope.row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="canManage" label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button link type="primary" :icon="EditPen" @click="openDialog(scope.row)">编辑</el-button>
          <el-button v-if="scope.row.is_active" link type="warning" @click="deactivateSupplier(scope.row.id)">停用</el-button>
          <el-button link type="danger" :icon="Delete" @click="deleteSupplier(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="min(680px, 94vw)" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="save">
        <div class="supplier-workspace__form-grid">
          <el-form-item label="供应商名称" prop="name" required>
            <el-input v-model="form.name" maxlength="150" show-word-limit />
          </el-form-item>
          <el-form-item label="联系人" prop="contact_name">
            <el-input v-model="form.contact_name" maxlength="100" />
          </el-form-item>
          <el-form-item class="supplier-workspace__form-wide" label="联系人地址" prop="contact_address">
            <el-input v-model="form.contact_address" type="textarea" :rows="2" maxlength="255" show-word-limit />
          </el-form-item>
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="form.phone" maxlength="50" />
          </el-form-item>
          <el-form-item label="备注" prop="remark">
            <el-input v-model="form.remark" type="textarea" :rows="2" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saveMutation.isPending.value" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Delete, EditPen, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { ApiError, V1Service } from '../../api/generated'
import type { Supplier, SupplierWrite } from '../../api/generated'
import { fetchAllPages } from '../../api/pagination'
import { useAuthStore } from '../../stores/auth'

type SupplierForm = {
  name: string
  contact_name: string
  contact_address: string
  phone: string
  remark: string
}

const auth = useAuthStore()
const queryClient = useQueryClient()
const formRef = ref<FormInstance>()
const search = ref('')
const activeFilter = ref('true')
const errorMessage = ref('')
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const form = reactive<SupplierForm>(emptyForm())
const rules: FormRules<SupplierForm> = {
  name: [{ required: true, message: '请填写供应商名称。', trigger: 'blur' }],
}
const canManage = computed(
  () => auth.user?.permissions.includes('*') || auth.user?.permissions.includes('partners.manage'),
)
const dialogTitle = computed(() => `${editingId.value ? '编辑' : '新增'}供应商`)
const suppliersQuery = useQuery({
  queryKey: computed(() => ['suppliers', search.value, activeFilter.value]),
  queryFn: () =>
    fetchAllPages((page, pageSize) =>
      V1Service.suppliersList(
        activeFilter.value === '' ? undefined : activeFilter.value === 'true',
        page,
        pageSize,
        search.value || undefined,
      ),
    ),
  retry: false,
})
const suppliers = computed<Supplier[]>(() => suppliersQuery.data.value ?? [])
const saveMutation = useMutation({
  mutationFn: saveSupplier,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: ['suppliers'] })
    dialogVisible.value = false
  },
})

function emptyForm(): SupplierForm {
  return { name: '', contact_name: '', contact_address: '', phone: '', remark: '' }
}

function resetForm() {
  Object.assign(form, emptyForm())
}

function openDialog(supplier?: Supplier) {
  resetForm()
  editingId.value = supplier?.id ?? null
  if (supplier) {
    form.name = supplier.name ?? ''
    form.contact_name = supplier.contact_name ?? ''
    form.contact_address = supplier.contact_address ?? ''
    form.phone = supplier.phone ?? ''
    form.remark = supplier.remark ?? ''
  }
  errorMessage.value = ''
  dialogVisible.value = true
}

function apiMessage(error: unknown) {
  if (error instanceof ApiError && typeof error.body === 'object' && error.body !== null && 'message' in error.body) {
    return String(error.body.message)
  }
  return error instanceof Error ? error.message : '操作未完成，请检查输入或稍后重试。'
}

function saveSupplier() {
  const payload: SupplierWrite = {
    name: form.name.trim(),
    contact_name: form.contact_name.trim(),
    contact_address: form.contact_address.trim(),
    phone: form.phone.trim(),
    remark: form.remark.trim(),
  }
  return editingId.value
    ? V1Service.suppliersPartialUpdate(editingId.value, payload)
    : V1Service.suppliersCreate(payload)
}

async function save() {
  const isValid = await formRef.value?.validate()
  if (!isValid) return
  try {
    await saveMutation.mutateAsync()
  } catch (error) {
    errorMessage.value = apiMessage(error)
  }
}

async function deactivateSupplier(id: string) {
  await runConfirmed('停用后不能用于新建进货单，确定继续吗？', () => V1Service.suppliersDeactivate(id))
}

async function deleteSupplier(id: string) {
  await runConfirmed('删除后无法恢复；已被进货单引用的供应商不可删除。', () => V1Service.suppliersDestroy(id))
}

async function runConfirmed(message: string, action: () => Promise<unknown>) {
  try {
    await ElMessageBox.confirm(message, '确认操作', { type: 'warning' })
    await action()
    await queryClient.invalidateQueries({ queryKey: ['suppliers'] })
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') errorMessage.value = apiMessage(error)
  }
}
</script>

<style scoped>
.supplier-workspace { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; }
.supplier-workspace__heading, .supplier-workspace__toolbar { display: flex; align-items: center; gap: 12px; }
.supplier-workspace__heading { justify-content: space-between; margin-bottom: 24px; }
.supplier-workspace__heading p { margin: 0 0 6px; color: #6b7780; font-size: 14px; }
.supplier-workspace__heading h1 { margin: 0; font-size: 28px; }
.supplier-workspace__alert { margin-bottom: 16px; }
.supplier-workspace__toolbar { margin-bottom: 16px; }
.supplier-workspace__toolbar .el-input { width: 280px; }
.supplier-workspace__toolbar .el-select { width: 130px; }
.supplier-workspace__form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 18px; }
.supplier-workspace__form-wide { grid-column: 1 / -1; }
@media (max-width: 600px) {
  .supplier-workspace { padding: 24px 16px 36px; }
  .supplier-workspace__heading { align-items: flex-start; }
  .supplier-workspace__toolbar { flex-wrap: wrap; }
  .supplier-workspace__toolbar .el-input { width: calc(100% - 52px); }
  .supplier-workspace__form-grid { grid-template-columns: 1fr; }
  .supplier-workspace__form-wide { grid-column: auto; }
}
</style>