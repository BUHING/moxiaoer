import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/auth',
      name: 'auth',
      component: () => import('../features/auth/AuthView.vue'),
      meta: { public: true },
    },
    {
      path: '/reset-password',
      name: 'password-reset',
      component: () => import('../features/auth/PasswordResetView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          redirect: { name: 'dashboard' },
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../features/reports/DashboardView.vue'),
        },
        {
          path: 'products',
          name: 'products',
          component: () => import('../features/products/ProductWorkspace.vue'),
        },
        {
          path: 'sales',
          name: 'sales',
          component: () => import('../features/sales/SalesWorkspace.vue'),
        },
        {
          path: 'sales/returns',
          name: 'sales-returns',
          component: () => import('../features/sales/SalesWorkspace.vue'),
        },
        {
          path: 'purchases',
          name: 'purchases',
          component: () => import('../features/purchases/PurchaseWorkspace.vue'),
        },
        {
          path: 'purchases/returns',
          name: 'purchase-returns',
          component: () => import('../features/purchases/PurchaseWorkspace.vue'),
        },
        {
          path: 'inventory/balances',
          name: 'inventory-balances',
          component: () => import('../features/inventory/InventoryWorkspace.vue'),
        },
        {
          path: 'inventory/movements',
          name: 'inventory-movements',
          component: () => import('../features/inventory/InventoryWorkspace.vue'),
        },
        {
          path: 'reports/sales',
          name: 'reports-sales',
          component: () => import('../features/reports/ReportWorkspace.vue'),
        },
        {
          path: 'reports/purchases',
          name: 'reports-purchases',
          component: () => import('../features/reports/ReportWorkspace.vue'),
        },
        {
          path: 'reports/inventory',
          name: 'reports-inventory',
          component: () => import('../features/reports/ReportWorkspace.vue'),
        },
        {
          path: 'customers',
          name: 'customers',
          component: () => import('../features/partners/PartnerWorkspace.vue'),
        },
        {
          path: 'price-levels',
          name: 'price-levels',
          component: () => import('../features/partners/PartnerWorkspace.vue'),
        },
        {
          path: 'suppliers',
          name: 'suppliers',
          component: () => import('../features/partners/SupplierWorkspace.vue'),
        },
        {
          path: 'settings/employees',
          name: 'account-workspace',
          component: () => import('../features/auth/AccountWorkspace.vue'),
        },
        {
          path: 'settings/label-printing',
          name: 'label-printing',
          component: () => import('../features/system/LabelPrintWorkspace.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return auth.accessToken ? '/dashboard' : true
  if (!auth.accessToken) return '/auth'
  if (!auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      auth.clearTokens()
      return '/auth'
    }
  }
  return true
})

export default router