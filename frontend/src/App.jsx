import React, { createContext, useContext, useState, useEffect } from 'react'
import { Routes, Route, Navigate, Link } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import OAuthCallback from './pages/OAuthCallback.jsx'
import QuizList from './pages/QuizList.jsx'
import QuizPlayer from './pages/QuizPlayer.jsx'
import AdminDashboard from './pages/AdminDashboard.jsx'
import QuizEditor from './pages/QuizEditor.jsx'

export const AuthContext = createContext(null)
export function useAuth(){ return useContext(AuthContext) }

export default function App(){
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(null)

  useEffect(()=>{
    if(!token) return
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(r=> r.ok ? r.json() : null)
      .then(u=> { if(u) setUser(u); else { setToken(null); localStorage.removeItem('token') } })
  }, [token])

  const login = (t, u) => { setToken(t); setUser(u); localStorage.setItem('token', t) }
  const logout = () => { setToken(null); setUser(null); localStorage.removeItem('token') }

  return (
    <AuthContext.Provider value={{token, user, login, logout}}>
      <nav className="nav">
        <Link to="/">Popopo</Link>
        <Link to="/quizzes">Quizzes</Link>
        {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
        <span style={{marginLeft:'auto'}}>
          {user ? (<>
            <span style={{marginRight:12}}>{user.email} ({user.role})</span>
            <button className="secondary" onClick={logout}>Salir</button>
          </>) : (<>
            <Link to="/login" style={{marginRight:12}}>Login</Link>
            <Link to="/register">Registro</Link>
          </>)}
        </span>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<Navigate to="/quizzes" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/oauth-callback" element={<OAuthCallback />} />
          <Route path="/quizzes" element={<QuizList />} />
          <Route path="/quizzes/:id" element={<QuizPlayer />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/quiz/new" element={<QuizEditor />} />
          <Route path="/admin/quiz/:id" element={<QuizEditor />} />
        </Routes>
      </div>
    </AuthContext.Provider>
  )
}
