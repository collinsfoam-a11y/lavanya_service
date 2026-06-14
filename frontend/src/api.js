// Minimal Frappe API helper. Whitelisted GET methods don't need CSRF; the
// browser session cookie authenticates. Returns the unwrapped `message`.
export async function call(method, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`/api/method/${method}${qs ? '?' + qs : ''}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    credentials: 'include',
  })
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
  const data = await res.json()
  return data.message
}
