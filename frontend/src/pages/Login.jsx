import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

export default function Login(){
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    try {
      const r = await api().post('/api/auth/login', { email, password })
      login(r.data.access_token, r.data.user)
      nav('/quizzes')
    } catch(e){ setErr(e.response?.data?.detail || 'Error') }
  }
  return (
    <div className="card">
      <h2>Login</h2>
      {err && <p className="error">{err}</p>}
      <form onSubmit={submit}>
        <label>Email</label>
        <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required />
        <label>Contraseña</label>
        <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required />
        <button type="submit">Entrar</button>
      </form>
      <p><a href="/api/auth/google/login">Continuar con Google</a></p>
      <p>¿No tienes cuenta? <Link to="/register">Regístrate</Link></p>
    </div>
  )
}
