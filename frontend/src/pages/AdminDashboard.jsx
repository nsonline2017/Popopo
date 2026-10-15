import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

export default function AdminDashboard(){
  const { token, user } = useAuth()
  const nav = useNavigate()
  const [quizzes, setQuizzes] = useState([])
  const [studies, setStudies] = useState([])

  const load = () => {
    api(token).get('/api/quizzes').then(r=>setQuizzes(r.data))
    api(token).get('/api/studies').then(r=>setStudies(r.data)).catch(()=>{})
  }
  useEffect(()=>{ if(user?.role==='admin') load() }, [token, user])

  if(user?.role !== 'admin') return <p>Acceso denegado.</p>

  const delQuiz = async (id) => {
    if(!confirm('Eliminar quiz?')) return
    await api(token).delete(`/api/quizzes/${id}`)
    load()
  }

  return (
    <div>
      <h2>Dashboard Admin</h2>
      <div style={{marginBottom:12}}>
        <Link to="/admin/quiz/new"><button>Crear Quiz</button></Link>
      </div>
      <h3>Quizzes</h3>
      {quizzes.map(q=>(
        <div className="card" key={q.id}>
          <strong>{q.title}</strong> <span style={{color:'#94a3b8'}}>({q.id})</span>
          <div style={{marginTop:8}}>
            <Link to={`/admin/quiz/${q.id}`}><button className="secondary">Editar</button></Link>
            <button className="danger" style={{marginLeft:8}} onClick={()=>delQuiz(q.id)}>Eliminar</button>
          </div>
        </div>
      ))}
      <h3>Estudios</h3>
      {studies.map(s=>(
        <div className="card" key={s.id}>
          {s.name} ({s.study_type}) - {s.file_paths?.length} imágenes
        </div>
      ))}
    </div>
  )
}
