type NumericValue = number | string | null | undefined

const quantityFormatter = new Intl.NumberFormat('zh-CN', {
  maximumFractionDigits: 0,
})

const priceFormatter = new Intl.NumberFormat('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 20,
})

function toFiniteNumber(value: NumericValue) {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue : 0
}

export function formatQuantity(value: NumericValue) {
  return quantityFormatter.format(toFiniteNumber(value))
}

export function formatPrice(value: NumericValue) {
  return `¥${priceFormatter.format(toFiniteNumber(value))}`
}