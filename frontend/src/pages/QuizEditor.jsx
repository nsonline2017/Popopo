import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../App.jsx'
import { api } from '../lib/api.js'

let cidCounter = -1
const newCid = () => cidCounter--

export default function QuizEditor(){
  const { id } = useParams()
  const isNew = !id || id === 'new'
  const quizId = isNew ? null : id
  const { token } = useAuth()
  const nav = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [studyId, setStudyId] = useState(null)
  const [studies, setStudies] = useState([])
  const [nodes, setNodes] = useState([])
  const [uploadName, setUploadName] = useState('')
  const [uploadFiles, setUploadFiles] = useState(null)
  const [err, setErr] = useState('')

  useEffect(()=>{
    api(token).get('/api/studies').then(r=>setStudies(r.data)).catch(()=>{})
    if(!isNew){
      api(token).get(`/api/quizzes/${quizId}`).then(r=>{
        const q = r.data
        setTitle(q.title); setDescription(q.description||''); setStudyId(q.study_id)
        // convert to client nodes
        const optsByNode = {}
        // map db option id -> client cid
        const optionCidMap = {}
        const nodeCidMap = {}
        const clientNodes = (q.nodes||[]).map(n=>{
          const cid = newCid()
          nodeCidMap[n.id] = cid
          const opts = (n.options||[]).map(o=>{
            const ocid = newCid()
            optionCidMap[o.id] = ocid
            return { cid: ocid, text: o.text, is_correct: o.is_correct }
          })
          optsByNode[cid] = opts
          return { cid, prompt: n.prompt, is_root: n.is_root, parent_option_id: n.parent_option_id, options: opts }
        })
        // convert parent_option_id (db) to client cid
        clientNodes.forEach(n=>{
          if(n.parent_option_id != null){
            n.parent_option_id = optionCidMap[n.parent_option_id] ?? n.parent_option_id
          }
        })
        setNodes(clientNodes)
      })
    } else {
      // start with one root node
      setNodes([{ cid: newCid(), prompt: '', is_root: true, parent_option_id: null, options: [] }])
    }
  }, [id, token])

  const addNode = () => setNodes(prev=>[...prev, { cid: newCid(), prompt:'', is_root:false, parent_option_id: null, options: [] }])
  const removeNode = (cid) => setNodes(prev=>prev.filter(n=>n.cid!==cid))
  const updateNode = (cid, patch) => setNodes(prev=>prev.map(n=> n.cid===cid ? {...n, ...patch} : n))
  const addOption = (nodeCid) => setNodes(prev=>prev.map(n=> n.cid===nodeCid ? {...n, options:[...n.options, {cid:newCid(), text:'', is_correct:false}]} : n))
  const removeOption = (nodeCid, optCid) => setNodes(prev=>prev.map(n=> n.cid===nodeCid ? {...n, options:n.options.filter(o=>o.cid!==optCid)} : n))
  const updateOption = (nodeCid, optCid, patch) => setNodes(prev=>prev.map(n=> n.cid===nodeCid ? {...n, options:n.options.map(o=> o.cid===optCid ? {...o,...patch} : o)} : n))

  const handleUpload = async () => {
    if(!uploadFiles || uploadFiles.length===0) return
    const fd = new FormData()
    fd.append('name', uploadName || 'Estudio')
    for(const f of uploadFiles) fd.append('files', f)
    try {
      const r = await api(token).post('/api/studies/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setStudies(prev=>[r.data, ...prev])
      setStudyId(r.data.id)
      setUploadFiles(null)
      setUploadName('')
    } catch(e){ setErr(e.response?.data?.detail || 'Error upload') }
  }

  const save = async () => {
    setErr('')
    // map client cid -> node payload with parent_option_id as client cid (backend maps? backend expects client ids in id fields)
    // We need pass id as client cid for mapping. Backend uses n.id if provided. Let's set id=cid.
    const payloadNodes = nodes.map(n=>({
      id: n.cid,
      prompt: n.prompt,
      is_root: n.is_root,
      order_index: 0,
      parent_option_id: n.parent_option_id,
      options: n.options.map((o, idx)=>({ id: o.cid, text: o.text, is_correct: o.is_correct, order_index: idx }))
    }))
    const payload = { title, description, study_id: studyId, nodes: payloadNodes }
    try {
      if(isNew){
        const r = await api(token).post('/api/quizzes', payload)
        nav(`/admin/quiz/${r.data.id}`)
      } else {
        await api(token).put(`/api/quizzes/${quizId}`, payload)
        nav('/admin')
      }
    } catch(e){ setErr(e.response?.data?.detail || 'Error guardando') }
  }

  // all options flat for parent selector
  const allOptions = nodes.flatMap(n=> n.options.map(o=>({nodeCid:n.cid, optCid:o.cid, label: `${n.prompt?.slice(0,30) || 'Nodo'} → ${o.text}`})))

  return (
    <div>
      <h2>{isNew ? 'Crear Quiz' : 'Editar Quiz'}</h2>
      {err && <p className="error">{err}</p>}
      <div className="card">
        <label>Título</label>
        <input value={title} onChange={e=>setTitle(e.target.value)} />
        <label>Descripción</label>
        <textarea value={description} onChange={e=>setDescription(e.target.value)} />
        <label>Estudio</label>
        <select value={studyId ?? ''} onChange={e=>setStudyId(e.target.value ? parseInt(e.target.value) : null)}>
          <option value="">-- seleccionar --</option>
          {studies.map(s=><option key={s.id} value={s.id}>{s.name} ({s.study_type})</option>)}
        </select>

        <div style={{marginTop:12, padding:12, background:'#0f172a', borderRadius:8}}>
          <h4>Subir nuevo estudio DICOM</h4>
          <label>Nombre</label>
          <input value={uploadName} onChange={e=>setUploadName(e.target.value)} />
          <input type="file" multiple onChange={e=>setUploadFiles(e.target.files)} />
          <button className="secondary" onClick={handleUpload} style={{marginTop:8}}>Subir</button>
        </div>
      </div>

      <h3>Preguntas / Ramas</h3>
      {nodes.map(n=>(
        <div className="card" key={n.cid}>
          <div style={{display:'flex', justifyContent:'space-between'}}>
            <strong>Nodo</strong>
            <button className="danger" onClick={()=>removeNode(n.cid)}>Eliminar nodo</button>
          </div>
          <label>Pregunta</label>
          <textarea value={n.prompt} onChange={e=>updateNode(n.cid, {prompt:e.target.value})} />
          <label>
            <input type="checkbox" checked={n.is_root} onChange={e=>updateNode(n.cid, {is_root:e.target.checked})} /> Es raíz
          </label>
          <label>Padre (opción que lleva a este nodo)</label>
          <select value={n.parent_option_id ?? ''} onChange={e=>updateNode(n.cid, {parent_option_id: e.target.value ? parseInt(e.target.value) : null})}>
            <option value="">-- ninguno (raíz) --</option>
            {allOptions.filter(o=>o.optCid !== undefined).map(o=>(
              <option key={o.optCid} value={o.optCid}>{o.label}</option>
            ))}
          </select>
          <h4>Respuestas (opciones)</h4>
          {n.options.map(o=>(
            <div key={o.cid} style={{display:'flex', gap:8, alignItems:'center', marginBottom:6}}>
              <input style={{flex:1}} value={o.text} onChange={e=>updateOption(n.cid, o.cid, {text:e.target.value})} placeholder="Texto respuesta" />
              <label style={{display:'flex', alignItems:'center', gap:4}}>
                <input type="checkbox" checked={o.is_correct} onChange={e=>updateOption(n.cid, o.cid, {is_correct:e.target.checked})} /> Correcta
              </label>
              <button className="danger" onClick={()=>removeOption(n.cid, o.cid)}>x</button>
            </div>
          ))}
          <button className="secondary" onClick={()=>addOption(n.cid)}>+ Respuesta</button>
        </div>
      ))}
      <div style={{marginBottom:12}}>
        <button className="secondary" onClick={addNode}>+ Nodo</button>
      </div>
      <button onClick={save}>Guardar</button>
      <button className="secondary" style={{marginLeft:8}} onClick={()=>nav('/admin')}>Cancelar</button>
    </div>
  )
}
