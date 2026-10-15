import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

export default function Register(){
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [err, setErr] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    try {
      const r = await api().post('/api/auth/register', { email, password, name })
      login(r.data.access_token, r.data.user)
      nav('/quizzes')
    } catch(e){ setErr(e.response?.data?.detail || 'Error') }
  }
  return (
    <div className="card">
      <h2>Registro</h2>
      {err && <p className="error">{err}</p>}
      <form onSubmit={submit}>
        <label>Nombre</label>
        <input value={name} onChange={e=>setName(e.target.value)} />
        <label>Email</label>
        <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required />
        <label>Contraseña</label>
        <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required />
        <button type="submit">Crear cuenta</button>
      </form>
      <p><Link to="/login">Ya tengo cuenta</Link></p>
    </div>
  )
}
