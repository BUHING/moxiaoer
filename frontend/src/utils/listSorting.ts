export const listSortOptions = [
  { value: 'name-asc', label: '名称顺着排（A → Z）' },
  { value: 'name-desc', label: '名称倒着排（Z → A）' },
  { value: 'created-asc', label: '最早添加的在前' },
  { value: 'created-desc', label: '最新添加的在前' },
  { value: 'updated-asc', label: '最早修改的在前' },
  { value: 'updated-desc', label: '最近修改的在前' },
] as const

export const listSortHelpText = '中文按拼音排列，数字按大小排列。'

export type ListSortOrder = typeof listSortOptions[number]['value']

type SortableRecord = {
  id: string
  name: string
  created_at: string
  updated_at: string
}

const nameCollator = new Intl.Collator('zh-CN-u-co-pinyin', {
  numeric: true,
  sensitivity: 'base',
})

export function isListSortOrder(value: string): value is ListSortOrder {
  return listSortOptions.some((option) => option.value === value)
}

function nameGroup(name: string) {
  if (/^\p{Decimal_Number}/u.test(name)) return 0
  if (/^\p{Script=Han}/u.test(name)) return 1
  if (/^[a-z]/i.test(name)) return 2
  return 3
}

function compareText(left: string, right: string) {
  return left < right ? -1 : left > right ? 1 : 0
}

export function sortRecords<T extends SortableRecord>(records: readonly T[], order: ListSortOrder): T[] {
  const direction = order.endsWith('-desc') ? -1 : 1
  const timeField = order.startsWith('created-') ? 'created_at' : 'updated_at'
  const byName = order.startsWith('name-')
  const entries = records.map((record) => {
    const name = record.name.trim().normalize('NFKC')
    const time = byName ? 0 : Date.parse(record[timeField])
    if (!Number.isFinite(time)) throw new Error(`资料“${record.name}”的时间格式无效，无法排序。`)
    return { record, name, group: nameGroup(name), time }
  })

  entries.sort((left, right) => direction * (
    left.time - right.time
    || left.group - right.group
    || nameCollator.compare(left.name, right.name)
    || compareText(left.record.name, right.record.name)
    || compareText(left.record.id, right.record.id)
  ))
  return entries.map(({ record }) => record)
}
