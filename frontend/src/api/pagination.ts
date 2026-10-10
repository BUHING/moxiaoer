type PaginatedResponse<T> = {
  data: T[]
  meta: Record<string, unknown>
}

const PAGE_SIZE = 100

export async function fetchAllPages<T>(
  fetchPage: (page: number, pageSize: number) => PromiseLike<PaginatedResponse<T>>,
) {
  const items: T[] = []

  for (let page = 1; ; page += 1) {
    const response = await fetchPage(page, PAGE_SIZE)
    items.push(...response.data)
    const total = Number(response.meta.total)
    if (response.data.length < PAGE_SIZE || (Number.isFinite(total) && items.length >= total)) {
      return items
    }
  }
}