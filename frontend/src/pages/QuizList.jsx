import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

export default function QuizList(){
  const { token } = useAuth()
  const [quizzes, setQuizzes] = useState([])
  useEffect(()=>{
    api(token).get('/api/quizzes').then(r=>setQuizzes(r.data)).catch(()=>{})
  }, [token])
  return (
    <div>
      <h2>Quizzes de Radiología</h2>
      {quizzes.map(q=>(
        <div className="card" key={q.id}>
          <h3>{q.title}</h3>
          <p>{q.description}</p>
          <Link to={`/quizzes/${q.id}`}><button>Resolver</button></Link>
        </div>
      ))}
      {quizzes.length===0 && <p>No hay quizzes disponibles.</p>}
    </div>
  )
}
