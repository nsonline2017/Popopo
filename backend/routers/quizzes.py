import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_admin
from models import Quiz, QuestionNode, Option, Study, User
from schemas import QuizIn, QuizOut, QuizListItem, SubmitIn, SubmitResult
from services.dicom import process_upload, MEDIA_ROOT
import json

router = APIRouter(prefix="/api", tags=["quizzes"])

def _build_tree(db, quiz):
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id == quiz.id).all()
    opts = db.query(Option).filter(Option.node_id.in_([n.id for n in nodes] or [0])).all()
    opt_by_node = {}
    for o in opts:
        opt_by_node.setdefault(o.node_id, []).append(o)
    node_map = {n.id: n for n in nodes}
    # attach options to nodes (pydantic from_orm won't auto load nested? we build manually)
    return nodes, opt_by_node

def serialize_quiz(db, quiz):
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id == quiz.id).all()
    opts = db.query(Option).filter(Option.node_id.in_([n.id for n in nodes] or [0])).all()
    opt_by_node = {}
    for o in opts:
        opt_by_node.setdefault(o.node_id, []).append(o)
    node_outs = []
    for n in nodes:
        node_outs.append({
            "id": n.id,
            "prompt": n.prompt,
            "order_index": n.order_index,
            "is_root": n.is_root,
            "parent_option_id": n.parent_option_id,
            "options": [{"id": o.id, "text": o.text, "is_correct": o.is_correct, "order_index": o.order_index} for o in sorted(opt_by_node.get(n.id, []), key=lambda x: x.order_index)],
        })
    study_out = None
    if quiz.study:
        study_out = {"id": quiz.study.id, "name": quiz.study.name, "study_type": quiz.study.study_type, "file_paths": quiz.study.file_paths or []}
    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "study_id": quiz.study_id,
        "study": study_out,
        "created_at": quiz.created_at,
        "nodes": node_outs,
    }

@router.get("/quizzes", response_model=list[QuizListItem])
def list_quizzes(db: Session = Depends(get_db)):
    return db.query(Quiz).order_by(Quiz.created_at.desc()).all()

@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    return serialize_quiz(db, quiz)

@router.post("/quizzes")
def create_quiz(data: QuizIn, user=Depends(require_admin), db: Session = Depends(get_db)):
    quiz = Quiz(title=data.title, description=data.description, study_id=data.study_id, created_by=user.id)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    # create nodes
    # map client temp ids? We'll just create recursively based on provided structure with parent_option linkage.
    # Input nodes include parent_option_id referencing option ids that may not exist yet. To handle, two-pass.
    # First create all nodes without parent, then options, then set parent_option_id? parent_option_id refers to option leading to node.
    # We'll process: create nodes first (store mapping from client id to db id), then options.
    id_map = {}  # client node id -> db node id
    # create nodes
    for n in data.nodes:
        node = QuestionNode(quiz_id=quiz.id, prompt=n.prompt, order_index=n.order_index, is_root=n.is_root, parent_option_id=None)
        db.add(node)
        db.flush()
        if n.id is not None:
            id_map[n.id] = node.id
    db.commit()
    # Now create options and set parent_option_id for child nodes.
    # Need map option client? Options have id optional. We'll create options, store map.
    option_id_map = {}
    for n in data.nodes:
        db_node_id = id_map.get(n.id) if n.id is not None else None
        # find node by prompt fallback
        if db_node_id is None:
            # find
            cand = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id, QuestionNode.prompt==n.prompt).first()
            db_node_id = cand.id if cand else None
        for o in n.options:
            opt = Option(node_id=db_node_id, text=o.text, is_correct=o.is_correct, order_index=o.order_index)
            db.add(opt)
            db.flush()
            if o.id is not None:
                option_id_map[o.id] = opt.id
    db.commit()
    # set parent_option_id for nodes
    for n in data.nodes:
        if n.parent_option_id is not None:
            # find db node
            db_node_id = id_map.get(n.id)
            if db_node_id is None:
                cand = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id, QuestionNode.prompt==n.prompt).first()
                db_node_id = cand.id if cand else None
            parent_opt_db = option_id_map.get(n.parent_option_id)
            if db_node_id and parent_opt_db:
                node = db.query(QuestionNode).filter(QuestionNode.id==db_node_id).first()
                node.parent_option_id = parent_opt_db
                db.commit()
    # ensure at least one root if none marked
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id).all()
    if nodes and not any(n.is_root for n in nodes):
        # node with no parent_option
        for n in nodes:
            if n.parent_option_id is None:
                n.is_root = True
                db.commit()
                break
    return serialize_quiz(db, quiz)

@router.put("/quizzes/{quiz_id}")
def update_quiz(quiz_id: int, data: QuizIn, user=Depends(require_admin), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    quiz.title = data.title
    quiz.description = data.description
    quiz.study_id = data.study_id
    # delete existing nodes/options
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id == quiz.id).all()
    for n in nodes:
        db.query(Option).filter(Option.node_id == n.id).delete()
    db.query(QuestionNode).filter(QuestionNode.quiz_id == quiz.id).delete()
    db.commit()
    # reuse create logic by building a QuizIn and calling create? Just duplicate minimal:
    id_map = {}
    for n in data.nodes:
        node = QuestionNode(quiz_id=quiz.id, prompt=n.prompt, order_index=n.order_index, is_root=n.is_root, parent_option_id=None)
        db.add(node)
        db.flush()
        if n.id is not None:
            id_map[n.id] = node.id
    db.commit()
    option_id_map = {}
    for n in data.nodes:
        db_node_id = id_map.get(n.id)
        if db_node_id is None:
            cand = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id, QuestionNode.prompt==n.prompt).first()
            db_node_id = cand.id if cand else None
        for o in n.options:
            opt = Option(node_id=db_node_id, text=o.text, is_correct=o.is_correct, order_index=o.order_index)
            db.add(opt)
            db.flush()
            if o.id is not None:
                option_id_map[o.id] = opt.id
    db.commit()
    for n in data.nodes:
        if n.parent_option_id is not None:
            db_node_id = id_map.get(n.id)
            if db_node_id is None:
                cand = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id, QuestionNode.prompt==n.prompt).first()
                db_node_id = cand.id if cand else None
            parent_opt_db = option_id_map.get(n.parent_option_id)
            if db_node_id and parent_opt_db:
                node = db.query(QuestionNode).filter(QuestionNode.id==db_node_id).first()
                node.parent_option_id = parent_opt_db
                db.commit()
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id==quiz.id).all()
    if nodes and not any(n.is_root for n in nodes):
        for n in nodes:
            if n.parent_option_id is None:
                n.is_root = True
                db.commit()
                break
    db.refresh(quiz)
    return serialize_quiz(db, quiz)

@router.delete("/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    db.delete(quiz)
    db.commit()
    return {"ok": True}

@router.post("/quizzes/{quiz_id}/submit", response_model=SubmitResult)
def submit_quiz(quiz_id: int, data: SubmitIn, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    errors = []
    # map option by id
    all_opts = {}
    nodes = db.query(QuestionNode).filter(QuestionNode.quiz_id == quiz.id).all()
    opts = db.query(Option).filter(Option.node_id.in_([n.id for n in nodes] or [0])).all()
    for o in opts:
        all_opts[o.id] = o
    for sel in data.selections:
        opt = all_opts.get(sel.option_id)
        if not opt:
            errors.append({"node_id": sel.node_id, "option_id": sel.option_id, "message": "Unknown option"})
            continue
        if not opt.is_correct:
            errors.append({"node_id": sel.node_id, "option_id": sel.option_id, "message": f"Respuesta incorrecta: {opt.text}"})
    if errors:
        return SubmitResult(correct=False, errors=errors, message="Hay errores en tus respuestas. Revisa e intenta de nuevo.")
    return SubmitResult(correct=True, errors=[], message="¡Correcto! Todas las respuestas son acertadas.")

# Studies
@router.post("/studies/upload")
async def upload_study(name: str = Form(...), files: list[UploadFile] = File(...), user=Depends(require_admin), db: Session = Depends(get_db)):
    import uuid
    study_id = None
    # create study placeholder
    study = Study(name=name, study_type="image", file_paths=[])
    db.add(study)
    db.commit()
    db.refresh(study)
    study_dir = os.path.join(MEDIA_ROOT, "studies", str(study.id))
    os.makedirs(study_dir, exist_ok=True)
    file_list = []
    for f in files:
        content = await f.read()
        file_list.append((f.filename, content))
    try:
        study_type, rel_paths = process_upload(file_list, study_dir)
    except Exception as e:
        db.delete(study)
        db.commit()
        raise HTTPException(400, str(e))
    study.study_type = study_type
    study.file_paths = rel_paths
    db.commit()
    db.refresh(study)
    return {"id": study.id, "name": study.name, "study_type": study.study_type, "file_paths": study.file_paths}

@router.get("/studies")
def list_studies(user=Depends(require_admin), db: Session = Depends(get_db)):
    studies = db.query(Study).order_by(Study.created_at.desc()).all()
    return [{"id": s.id, "name": s.name, "study_type": s.study_type, "file_paths": s.file_paths or []} for s in studies]

@router.delete("/studies/{study_id}")
def delete_study(study_id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(404, "Study not found")
    db.delete(study)
    db.commit()
    return {"ok": True}
