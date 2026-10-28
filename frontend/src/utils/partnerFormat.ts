type CustomerContact = {
  name: string
  contact_name?: string
  phone?: string
}

type SupplierContact = CustomerContact & {
  contact_address?: string
}

export function formatCustomerOption(customer: CustomerContact) {
  return [
    customer.name,
    customer.contact_name?.trim() || '未填写联系人',
    customer.phone?.trim() || '未填写电话',
  ].join('｜')
}

export function formatSupplierOption(supplier: SupplierContact) {
  return [
    supplier.name,
    supplier.contact_name?.trim() || '未填写联系人',
    supplier.contact_address?.trim() || '未填写联系地址',
    supplier.phone?.trim() || '未填写电话',
  ].join('｜')
}
