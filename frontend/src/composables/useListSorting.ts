import { computed, ref, watch } from 'vue'
import { isListSortOrder, listSortOptions, type ListSortOrder } from '../utils/listSorting.ts'

type SortingUser = { id: string; organization_id: string }
const defaultSortLabel = listSortOptions[0].label

export function useListSorting(
  page: 'products' | 'customers' | 'suppliers',
  getUser: () => SortingUser | null,
  reportError: (message: string) => void,
) {
  const sortOrder = ref<ListSortOrder>('name-asc')
  const storageKey = computed(() => {
    const user = getUser()
    return user ? `grindbuddy.list-sort.${user.organization_id}.${user.id}.${page}` : null
  })

  watch(storageKey, (key) => {
    let order: ListSortOrder = 'name-asc'
    if (key) {
      try {
        const saved = localStorage.getItem(key)
        if (saved !== null) {
          if (isListSortOrder(saved)) order = saved
          else reportError(`保存的排序方式无效，已恢复为“${defaultSortLabel}”，请重新选择。`)
        }
      } catch (error) {
        reportError(`无法读取排序偏好，已使用“${defaultSortLabel}”：${error instanceof Error ? error.message : String(error)}`)
      }
    }
    sortOrder.value = order
  }, { immediate: true, flush: 'sync' })

  watch(sortOrder, (order) => {
    if (!storageKey.value) return
    try {
      localStorage.setItem(storageKey.value, order)
    } catch (error) {
      reportError(`本次排序已生效，但无法保存排序偏好：${error instanceof Error ? error.message : String(error)}`)
    }
  }, { flush: 'sync' })

  return { sortOrder }
}
