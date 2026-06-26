import os
from datetime import datetime
from sqlalchemy import create_engine, ForeignKey, Text, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# Configuração do banco de dados SQLite interno do GitIDE.
# Por padrão, os metadados são salvos em um banco de dados global em ~/.gitide/gitide.db
# ou no diretório de dados do aplicativo. Vamos usar um diretório padrão ~/.gitide
DATABASE_DIR = os.path.expanduser("~/.gitide")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DATABASE_DIR, "gitide.db")

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

class Base(DeclarativeBase):
    pass

from sqlalchemy.ext.hybrid import hybrid_property

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Mapeia a coluna 'path' para o atributo interno '_path'
    _path: Mapped[str] = mapped_column("path", String(500), nullable=False)
    
    git_remote: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @hybrid_property
    def path(self) -> str:
        val = self._path
        # Se for Linux (POSIX) mas o caminho cadastrado no banco for do Windows, mapeia para /workspace
        if os.name != 'nt':
            if '\\' in val or (len(val) > 1 and val[1] == ':'):
                normalized = val.replace('\\', '/')
                project_name = normalized.split('/')[-1]
                if project_name.lower() == '.workspace':
                    return "/workspace"
                
                possible_path = f"/workspace/{project_name}"
                if os.path.exists(possible_path):
                    return possible_path
                
                # Fallback para caminho relativo
                relative = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", project_name))
                if os.path.exists(relative):
                    return relative
                    
                return possible_path
        return val

    @path.expression
    def path(cls):
        return cls._path

    @path.setter
    def path(self, value: str):
        self._path = value

    # Relacionamentos
    logs: Mapped[list["ActivityLog"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    snapshots: Mapped[list["FileSnapshot"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # FILE_WRITE, FILE_DELETE, SHELL_EXEC, GIT_DEPLOY, etc.
    details: Mapped[str] = mapped_column(Text, nullable=True)  # Informações extras (ex: comando, commit, etc.)

    # Relacionamentos
    project: Mapped["Project"] = relationship(back_populates="logs")
    snapshots: Mapped[list["FileSnapshot"]] = relationship(back_populates="activity_log")

class FileSnapshot(Base):
    __tablename__ = "file_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)  # Caminho relativo dentro do projeto
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Conteúdo completo do arquivo
    hash: Mapped[str] = mapped_column(String(64), nullable=False)  # Hash SHA256 do conteúdo para deduplicação
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activity_log_id: Mapped[int | None] = mapped_column(ForeignKey("activity_logs.id", ondelete="SET NULL"), nullable=True)

    # Relacionamentos
    project: Mapped["Project"] = relationship(back_populates="snapshots")
    activity_log: Mapped["ActivityLog | None"] = relationship(back_populates="snapshots")

class PendingCommand(Base):
    __tablename__ = "pending_commands"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected, executed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamento
    project: Mapped["Project"] = relationship()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
