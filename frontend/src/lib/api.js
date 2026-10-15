import axios from 'axios'

export function api(token){
  const instance = axios.create({ baseURL: '' })
  if(token) instance.defaults.headers.common['Authorization'] = `Bearer ${token}`
  return instance
}

export function authHeaders(token){
  return token ? { Authorization: `Bearer ${token}` } : {}
}
