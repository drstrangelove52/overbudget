export function apiFetch(url, options = {}) {
  return fetch(url, options).then((res) => {
    if (res.status === 401) {
      setLoggedIn(false)
      window.location.href = '/login'
    }
    return res
  })
}

export const isLoggedIn = () => localStorage.getItem('loggedIn') === '1'
export const setLoggedIn = (v) => {
  if (v) localStorage.setItem('loggedIn', '1')
  else localStorage.removeItem('loggedIn')
}
