export function apiFetch(url, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  return fetch(url, { ...options, headers }).then((res) => {
    if (res.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return res
  })
}

export const getToken = () => localStorage.getItem('token')
export const setToken = (t) => localStorage.setItem('token', t)
export const removeToken = () => localStorage.removeItem('token')
