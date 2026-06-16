// Minimal Frappe API helper. Whitelisted GET methods don't need CSRF; the
// browser session cookie authenticates. Returns the unwrapped `message`.
export async function call(method, params = {}) {
  // Drop null/undefined so they aren't serialized as the literal strings
  // "null"/"undefined" (URLSearchParams stringifies everything) — otherwise an
  // optional filter like search=undefined silently matches nothing.
  const clean = {}
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) clean[k] = v
  }
  const qs = new URLSearchParams(clean).toString()
  const res = await fetch(`/api/method/${method}${qs ? '?' + qs : ''}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    credentials: 'include',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.exc_type || err._server_messages || `HTTP ${res.status}`)
  }
  const data = await res.json()
  return data.message
}

export async function post(method, body = {}) {
  const res = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`
    try {
      const errData = await res.json()
      if (errData._server_messages) {
        const msgs = JSON.parse(errData._server_messages).map(m => JSON.parse(m).message)
        errMsg = msgs.join(', ')
      } else if (errData.exc_type) {
        errMsg = errData.exc_type
      }
    } catch (e) {
      // ignore
    }
    throw new Error(errMsg)
  }
  const data = await res.json()
  return data.message
}
