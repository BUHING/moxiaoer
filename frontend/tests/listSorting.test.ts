import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fetchAllPages } from '../src/api/pagination.ts'
import { isListSortOrder, listSortHelpText, listSortOptions, sortRecords } from '../src/utils/listSorting.ts'

function record(name: string, id = name, created_at = '2026-10-28T00:00:00Z', updated_at = created_at) {
  return { id, name, created_at, updated_at }
}

test('uses the six approved plain-language labels without changing stored sorting values', () => {
  assert.deepEqual(listSortOptions, [
    { value: 'name-asc', label: '名称顺着排（A → Z）' },
    { value: 'name-desc', label: '名称倒着排（Z → A）' },
    { value: 'created-asc', label: '最早添加的在前' },
    { value: 'created-desc', label: '最新添加的在前' },
    { value: 'updated-asc', label: '最早修改的在前' },
    { value: 'updated-desc', label: '最近修改的在前' },
  ])
  assert.equal(listSortHelpText, '中文按拼音排列，数字按大小排列。')
  for (const option of listSortOptions) assert.ok(isListSortOrder(option.value))
  assert.equal(isListSortOrder('name'), false)
})

test('groups numbers, Chinese, English and symbols with pinyin and natural numeric ordering', () => {
  const expected = [
    '2号商品', '3M A0213', '3M C0213', '10号商品',
    '浩源', '华恩', '台砂', '徐先生',
    'Apple', 'banana', '#其他',
  ]
  const records = expected.toReversed().map((name) => record(name))
  assert.deepEqual(sortRecords(records, 'name-asc').map((item) => item.name), expected)
  assert.deepEqual(sortRecords(records, 'name-desc').map((item) => item.name), expected.toReversed())
  assert.deepEqual(records.map((item) => item.name), expected.toReversed())
})

test('compares the full name and numeric segments, ignoring spaces and letter case for primary order', () => {
  const names = ['商品100', '商品10', '商品2', ' abc10', 'ABC2', '３M C0213', '3M A0213']
  assert.deepEqual(sortRecords(names.map((name) => record(name)), 'name-asc').map((item) => item.name), [
    '3M A0213', '３M C0213', '商品2', '商品10', '商品100', 'ABC2', ' abc10',
  ])
})

test('compares instants rather than date strings in all four time modes', () => {
  const records = [
    record('C', 'c', '2026-10-28T10:00:00+08:00', '2026-10-28T00:00:00Z'),
    record('A', 'a', '2026-10-28T01:00:00Z', '2026-10-28T03:00:00Z'),
    record('B', 'b', '2026-10-28T00:00:00Z', '2026-10-28T01:00:00Z'),
  ]
  for (const [mode, expected] of [
    ['created-asc', ['b', 'a', 'c']],
    ['created-desc', ['c', 'a', 'b']],
    ['updated-asc', ['c', 'b', 'a']],
    ['updated-desc', ['a', 'b', 'c']],
  ] as const) {
    assert.deepEqual(sortRecords(records, mode).map((item) => item.id), expected)
  }
})

test('breaks equal-name and equal-time ties deterministically without changing cached records', () => {
  const records = Object.freeze([Object.freeze(record('同名', 'b')), Object.freeze(record('同名', 'a'))])
  for (const mode of ['name-asc', 'created-asc', 'updated-asc'] as const) {
    assert.deepEqual(sortRecords(records, mode).map((item) => item.id), ['a', 'b'])
    assert.deepEqual(sortRecords([...records].reverse(), mode), sortRecords(records, mode))
  }
  assert.deepEqual(records.map((item) => item.id), ['b', 'a'])
  assert.deepEqual(sortRecords([], 'name-asc'), [])
  assert.throws(() => sortRecords([record('错误时间', 'bad', 'invalid')], 'created-asc'), /时间格式无效/)
})

test('sorts the complete filtered result across more than two API pages', async () => {
  const records = Array.from({ length: 205 }, (_, index) => record(`商品${205 - index}`))
  const calls: number[] = []
  const all = await fetchAllPages(async (page, pageSize) => {
    calls.push(page)
    return {
      data: records.slice((page - 1) * pageSize, page * pageSize),
      meta: { total: records.length },
    }
  })
  assert.deepEqual(calls, [1, 2, 3])
  assert.deepEqual(sortRecords(all, 'name-asc').map((item) => item.name),
    Array.from({ length: 205 }, (_, index) => `商品${index + 1}`))
  assert.deepEqual(sortRecords(all.filter((item) => item.name === '商品2'), 'name-desc').map((item) => item.name), ['商品2'])
})
