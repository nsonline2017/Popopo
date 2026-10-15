import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    name = Column(String, nullable=True)
    role = Column(String, default="guest")  # admin | guest
    google_sub = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    study_type = Column(String, default="image")  # image | series
    file_paths = Column(JSON, default=list)  # list of relative media paths
    created_at = Column(DateTime, default=datetime.utcnow)

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    study = relationship("Study")
    nodes = relationship("QuestionNode", back_populates="quiz", cascade="all, delete-orphan")

class QuestionNode(Base):
    __tablename__ = "question_nodes"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    parent_option_id = Column(Integer, ForeignKey("options.id"), nullable=True)
    prompt = Column(Text, nullable=False)
    order_index = Column(Integer, default=0)
    is_root = Column(Boolean, default=False)
    quiz = relationship("Quiz", back_populates="nodes")
    options = relationship("Option", back_populates="node", cascade="all, delete-orphan", foreign_keys="Option.node_id")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("question_nodes.id"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    node = relationship("QuestionNode", back_populates="options", foreign_keys=[node_id])
