<template>
  <section class="workspace-view">
    <header class="workspace-view__title">
      <div><p>账号与权限</p><h1>你好，{{ auth.user?.display_name || auth.user?.username }}</h1></div>
      <el-tag :type="isBoss ? 'success' : 'info'">{{ isBoss ? '老板账号' : '员工账号' }}</el-tag>
    </header>
    <el-alert v-if="errorMessage" type="error" :title="errorMessage" show-icon @close="errorMessage = ''" />
    <el-tabs v-model="activeTab">
      <el-tab-pane label="我的权限" name="permissions">
        <div class="permission-grid"><el-tag v-for="permission in auth.user?.permissions" :key="permission" effect="plain">{{ permissionLabel(permission) }}</el-tag></div>
      </el-tab-pane>
      <el-tab-pane v-if="isBoss" label="员工" name="employees">
        <div class="workspace-view__actions"><el-button type="primary" @click="createDialog = true">新增员工</el-button></div>
        <el-table v-loading="employeesLoading" :data="employees" empty-text="暂无员工">
          <el-table-column prop="display_name" label="姓名" /><el-table-column prop="username" label="用户名" /><el-table-column label="最后登录"><template #default="scope">{{ formatLoginTime(scope.row.last_login) }}</template></el-table-column>
          <el-table-column label="状态"><template #default="scope"><el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column label="已授予权限"><template #default="scope"><span>{{ scope.row.permission_codes.map(permissionLabel).join('、') || '无' }}</span></template></el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="权限申请" name="requests">
        <div v-if="!isBoss" class="workspace-view__actions"><el-select v-model="requestedPermission" placeholder="选择需要申请的权限"><el-option v-for="option in permissionOptions" :key="option" :label="permissionLabel(option)" :value="option" /></el-select><el-button type="primary" :disabled="!requestedPermission" @click="submitRequest">提交申请</el-button></div>
        <el-table v-loading="requestsLoading" :data="requests" empty-text="暂无权限申请">
          <el-table-column prop="employee_name" label="员工" /><el-table-column label="权限"><template #default="scope">{{ permissionLabel(scope.row.permission_code) }}</template></el-table-column><el-table-column label="状态"><template #default="scope">{{ requestStatusLabel(scope.row.status) }}</template></el-table-column>
          <el-table-column v-if="isBoss" label="处理"><template #default="scope"><el-button v-if="scope.row.status === 'PENDING'" type="primary" link @click="review(scope.row.id, true)">批准</el-button><el-button v-if="scope.row.status === 'PENDING'" type="danger" link @click="review(scope.row.id, false)">拒绝</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <el-dialog v-model="createDialog" title="新增员工" width="440px">
      <el-form :model="employeeForm" label-position="top"><el-form-item label="姓名"><el-input v-model="employeeForm.display_name" /></el-form-item><el-form-item label="用户名"><el-input v-model="employeeForm.username" /></el-form-item><el-form-item label="找回密码邮箱"><el-input v-model="employeeForm.email" type="email" /></el-form-item><el-form-item label="初始密码"><el-input v-model="employeeForm.password" type="password" show-password /></el-form-item></el-form>
      <template #footer><el-button @click="createDialog = false">取消</el-button><el-button type="primary" :loading="creating" @click="createEmployee">创建</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { Employee, PermissionRequest } from '../../api/generated'
import { PermissionCodeEnum, V1Service } from '../../api/generated'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const isBoss = computed(() => auth.user?.role === 'BOSS')
const activeTab = ref('permissions')
const employees = ref<Array<Employee & { last_login?: string | null }>>([])
const requests = ref<PermissionRequest[]>([])
const employeesLoading = ref(false)
const requestsLoading = ref(false)
const creating = ref(false)
const createDialog = ref(false)
const errorMessage = ref('')
const requestedPermission = ref<PermissionCodeEnum | ''>('')
const permissionOptions: PermissionCodeEnum[] = [
  PermissionCodeEnum.EMPLOYEES_MANAGE,
  PermissionCodeEnum.PARTNERS_MANAGE,
  PermissionCodeEnum.PRODUCTS_MANAGE,
  PermissionCodeEnum.PURCHASES_RETURNS_MANAGE,
  PermissionCodeEnum.SALES_RETURNS_MANAGE,
  PermissionCodeEnum.SHOP_MANAGE,
]
const permissionLabels: Record<string, string> = {
  '*': '全部权限',
  'dashboard.view': '查看经营看板',
  'inventory.view': '查看库存',
  'partners.view': '查看往来单位',
  'products.view': '查看商品',
  'purchases.create': '创建进货单',
  'reports.view': '查看经营报表',
  'sales.create': '创建销售单',
  'employees.manage': '管理员工',
  'partners.manage': '管理往来单位',
  'products.manage': '管理商品',
  'purchases.returns.manage': '管理进货退货',
  'sales.returns.manage': '管理销售退货',
  'shop.manage': '管理店铺',
}
const requestStatusLabels: Record<string, string> = {
  PENDING: '待处理',
  APPROVED: '已批准',
  REJECTED: '已拒绝',
}
function permissionLabel(code: string) { return permissionLabels[code] ?? code }
function requestStatusLabel(status: string) { return requestStatusLabels[status] ?? status }
const employeeForm = reactive({ username: '', display_name: '', email: '', password: '' })

async function loadEmployees() { if (!isBoss.value) return; employeesLoading.value = true; try { employees.value = (await V1Service.employeesList()).data } finally { employeesLoading.value = false } }
async function loadRequests() { requestsLoading.value = true; try { requests.value = (await V1Service.permissionRequestsList()).data } finally { requestsLoading.value = false } }
async function createEmployee() { creating.value = true; try { await V1Service.employeesCreate({ ...employeeForm }); createDialog.value = false; employeeForm.username = ''; employeeForm.display_name = ''; employeeForm.email = ''; employeeForm.password = ''; await loadEmployees() } catch { errorMessage.value = '员工创建失败，请检查用户名、邮箱和密码。' } finally { creating.value = false } }
async function submitRequest() { if (!requestedPermission.value) return; try { await V1Service.permissionRequestsCreate({ permission_code: requestedPermission.value }); requestedPermission.value = ''; await loadRequests() } catch { errorMessage.value = '权限申请提交失败。' } }
async function review(requestId: string, approved: boolean) { try { if (approved) await V1Service.v1PermissionRequestsApproveCreate(requestId); else await V1Service.v1PermissionRequestsRejectCreate(requestId); await loadRequests() } catch { errorMessage.value = '申请处理失败，可能已被处理。' } }
function formatLoginTime(value?: string | null) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '从未登录' }

onMounted(() => { void loadEmployees(); void loadRequests() })
</script>