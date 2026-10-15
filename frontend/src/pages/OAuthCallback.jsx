import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App.jsx'

export default function OAuthCallback(){
  const { login } = useAuth()
  const nav = useNavigate()
  useEffect(()=>{
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if(token){
      fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r=>r.json()).then(u=>{ login(token,u); nav('/quizzes') })
    } else {
      nav('/login')
    }
  }, [])
  return <p>Procesando...</p>
}
