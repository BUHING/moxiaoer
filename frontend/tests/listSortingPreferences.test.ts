import assert from 'node:assert/strict'
import { afterEach, beforeEach, test } from 'node:test'
import { effectScope, ref, type EffectScope } from 'vue'
import { useListSorting } from '../src/composables/useListSorting.ts'
import { listSortOptions } from '../src/utils/listSorting.ts'

const originalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
const scopes: EffectScope[] = []
let values: Map<string, string>
let errors: string[]

beforeEach(() => {
  values = new Map()
  errors = []
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => { values.set(key, value) },
    },
  })
})

afterEach(() => {
  for (const scope of scopes.splice(0)) scope.stop()
  if (originalStorage) Object.defineProperty(globalThis, 'localStorage', originalStorage)
  else Reflect.deleteProperty(globalThis, 'localStorage')
})

function setup(page: 'products' | 'customers' | 'suppliers' = 'products') {
  const user = ref<{ id: string; organization_id: string } | null>({ id: 'alice', organization_id: 'shop' })
  const scope = effectScope()
  scopes.push(scope)
  const sorting = scope.run(() => useListSorting(page, () => user.value, (message) => errors.push(message)))
  assert.ok(sorting)
  return { user, ...sorting }
}

test('defaults to name ascending and restores the selected mode on revisiting', () => {
  const first = setup()
  assert.equal(first.sortOrder.value, 'name-asc')
  first.sortOrder.value = 'updated-desc'
  assert.equal(setup().sortOrder.value, 'updated-desc')
  assert.deepEqual(errors, [])
})

test('restores every previously saved sorting value after changing display labels', () => {
  for (const option of listSortOptions) {
    values.set('grindbuddy.list-sort.shop.alice.products', option.value)
    assert.equal(setup().sortOrder.value, option.value)
  }
  assert.deepEqual(errors, [])
})

test('keeps preferences separate for every page, user and organization', () => {
  const sorting = setup()
  sorting.sortOrder.value = 'created-desc'
  assert.equal(setup('customers').sortOrder.value, 'name-asc')
  assert.equal(setup('suppliers').sortOrder.value, 'name-asc')
  sorting.user.value = { id: 'bob', organization_id: 'shop' }
  assert.equal(sorting.sortOrder.value, 'name-asc')
  sorting.sortOrder.value = 'updated-asc'
  sorting.user.value = { id: 'alice', organization_id: 'other-shop' }
  assert.equal(sorting.sortOrder.value, 'name-asc')
  sorting.user.value = { id: 'alice', organization_id: 'shop' }
  assert.equal(sorting.sortOrder.value, 'created-desc')
  sorting.user.value = null
  assert.equal(sorting.sortOrder.value, 'name-asc')
  assert.equal(values.get('grindbuddy.list-sort.shop.alice.products'), 'created-desc')
  assert.equal(values.get('grindbuddy.list-sort.shop.bob.products'), 'updated-asc')
})

test('reports invalid saved values instead of silently accepting them', () => {
  values.set('grindbuddy.list-sort.shop.alice.products', 'not-a-mode')
  assert.equal(setup().sortOrder.value, 'name-asc')
  assert.match(errors[0]!, /保存的排序方式无效/)
  assert.ok(errors[0]!.includes('名称顺着排（A → Z）'))
  assert.doesNotMatch(errors[0]!, /升序|降序/)
})

test('reports storage read and write failures while retaining the current sorting choice', () => {
  localStorage.getItem = () => { throw new Error('read denied') }
  localStorage.setItem = () => { throw new Error('write denied') }
  const sorting = setup()
  assert.match(errors[0]!, /无法读取排序偏好/)
  assert.ok(errors[0]!.includes('名称顺着排（A → Z）'))
  assert.doesNotMatch(errors[0]!, /升序|降序/)
  sorting.sortOrder.value = 'name-desc'
  assert.equal(sorting.sortOrder.value, 'name-desc')
  assert.match(errors[1]!, /本次排序已生效，但无法保存/)
})
