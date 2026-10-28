import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatCustomerOption, formatSupplierOption } from '../src/utils/partnerFormat.ts'

test('customer options distinguish same-name contacts and phone numbers', () => {
  const first = { name: '漳州市', contact_name: '张三', phone: '13800000000' }
  assert.equal(formatCustomerOption(first), '漳州市｜张三｜13800000000')
  assert.notEqual(formatCustomerOption(first), formatCustomerOption({ ...first, phone: '13900000000' }))
  assert.notEqual(formatCustomerOption(first), formatCustomerOption({ ...first, contact_name: '李四' }))
  assert.deepEqual(first, { name: '漳州市', contact_name: '张三', phone: '13800000000' })
})

test('supplier options include all four identity fields including the address', () => {
  const first = { name: '同名供应商', contact_name: '张三', contact_address: '示例路 1 号', phone: '13800000000' }
  assert.equal(formatSupplierOption(first), '同名供应商｜张三｜示例路 1 号｜13800000000')
  assert.notEqual(formatSupplierOption(first), formatSupplierOption({ ...first, contact_address: '示例路 2 号' }))
  assert.notEqual(formatSupplierOption(first), formatSupplierOption({ ...first, phone: '13900000000' }))
})

test('unfilled optional fields are explicit without changing existing names or source values', () => {
  assert.equal(formatCustomerOption({ name: '仅名称' }), '仅名称｜未填写联系人｜未填写电话')
  assert.equal(formatSupplierOption({ name: '仅名称', contact_name: ' ', contact_address: '', phone: '' }),
    '仅名称｜未填写联系人｜未填写联系地址｜未填写电话')
  const record = Object.freeze({ name: ' 原名称 ', contact_name: ' 联系人 ', phone: ' 138-00000000 ' })
  assert.equal(formatCustomerOption(record), ' 原名称 ｜联系人｜138-00000000')
  assert.equal(record.phone, ' 138-00000000 ')
})
