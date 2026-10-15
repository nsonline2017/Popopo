import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

export default function QuizPlayer(){
  const { id } = useParams()
  const { token } = useAuth()
  const nav = useNavigate()
  const [quiz, setQuiz] = useState(null)
  const [slice, setSlice] = useState(0)
  const [currentNodeId, setCurrentNodeId] = useState(null)
  const [selections, setSelections] = useState([]) // {node_id, option_id}
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(()=>{
    api(token).get(`/api/quizzes/${id}`).then(r=>{
      setQuiz(r.data)
      const root = (r.data.nodes||[]).find(n=>n.is_root) || (r.data.nodes||[]).find(n=>!n.parent_option_id)
      setCurrentNodeId(root?.id)
      setSelections([])
      setResult(null)
      setSlice(0)
    })
  }, [id, token])

  if(!quiz) return <p>Cargando...</p>

  const nodeById = Object.fromEntries((quiz.nodes||[]).map(n=>[n.id,n]))
  const childrenOfOption = (optId) => (quiz.nodes||[]).find(n=>n.parent_option_id===optId)
  const current = currentNodeId ? nodeById[currentNodeId] : null

  const selectOption = (opt) => {
    if(result) return
    // remove any selections after current node? simple: append
    const newSel = [...selections.filter(s=>s.node_id!==currentNodeId), { node_id: currentNodeId, option_id: opt.id }]
    setSelections(newSel)
    const child = childrenOfOption(opt.id)
    if(child){ setCurrentNodeId(child.id) }
    else { setCurrentNodeId(null) } // terminal
  }

  const submit = async () => {
    setSubmitting(true)
    try {
      const r = await api(token).post(`/api/quizzes/${id}/submit`, { selections })
      setResult(r.data)
    } catch(e){ setResult({correct:false, errors:[], message: e.response?.data?.detail || 'Error' }) }
    setSubmitting(false)
  }

  const restart = () => {
    const root = (quiz.nodes||[]).find(n=>n.is_root) || (quiz.nodes||[]).find(n=>!n.parent_option_id)
    setCurrentNodeId(root?.id)
    setSelections([])
    setResult(null)
    setSlice(0)
  }

  const study = quiz.study
  const paths = study?.file_paths || []

  return (
    <div>
      <h2>{quiz.title}</h2>
      <p>{quiz.description}</p>
      <div className="card img-viewer">
        {study?.study_type === 'series' && paths.length>0 ? (
          <>
            <img src={`/media/${paths[slice]}`} alt="slice" />
            <div className="series-nav">
              <button className="secondary" onClick={()=>setSlice(s=>Math.max(0,s-1))} disabled={slice===0}>Anterior</button>
              <span>Slice {slice+1} / {paths.length}</span>
              <button className="secondary" onClick={()=>setSlice(s=>Math.min(paths.length-1,s+1))} disabled={slice===paths.length-1}>Siguiente</button>
            </div>
          </>
        ) : paths.length>0 ? (
          <img src={`/media/${paths[0]}`} alt="study" />
        ) : <p>Sin estudio.</p>}
      </div>

      <div className="card">
        <h3>Preguntas</h3>
        {selections.length>0 && (
          <div style={{marginBottom:12}}>
            <strong>Selecciones:</strong>
            <ul>
              {selections.map((s,i)=>{
                const n = nodeById[s.node_id]
                const o = (n?.options||[]).find(x=>x.id===s.option_id)
                return <li key={i}>{n?.prompt} → {o?.text}</li>
              })}
            </ul>
          </div>
        )}

        {current && !result && (
          <div>
            <p><strong>{current.prompt}</strong></p>
            <div style={{display:'flex', flexDirection:'column', gap:8}}>
              {(current.options||[]).map(o=>(
                <button key={o.id} className="secondary" onClick={()=>selectOption(o)}>{o.text}</button>
              ))}
            </div>
          </div>
        )}
        {!current && !result && selections.length>0 && (
          <p>Fin de la rama. Puedes enviar.</p>
        )}

        {!result && selections.length>0 && (
          <div style={{marginTop:12}}>
            <button onClick={submit} disabled={submitting}>Submit</button>
          </div>
        )}

        {result && (
          <div style={{marginTop:12}}>
            <p className={result.correct ? 'success' : 'error'}>{result.message}</p>
            {!result.correct && result.errors?.length>0 && (
              <ul>
                {result.errors.map((e,i)=>(<li key={i} className="error">{e.message}</li>))}
              </ul>
            )}
            <button onClick={restart}>Volver a comenzar</button>
          </div>
        )}
      </div>
    </div>
  )
}
