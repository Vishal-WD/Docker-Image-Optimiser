from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base


class DockerOptimizationRecord(Base):
    """Stores records of Docker container optimization operations in PostgreSQL."""

    __tablename__ = "docker_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, default="python-app")
    original_dockerfile = Column(Text, nullable=False)
    optimized_dockerfile = Column(Text, nullable=False)
    dockerignore_content = Column(Text, nullable=False)
    original_size_mb = Column(Float, nullable=False)
    optimized_size_mb = Column(Float, nullable=False)
    saved_mb = Column(Float, nullable=False)
    reduction_percent = Column(Float, nullable=False)
    issues_found_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_name": self.project_name,
            "original_dockerfile": self.original_dockerfile,
            "optimized_dockerfile": self.optimized_dockerfile,
            "dockerignore_content": self.dockerignore_content,
            "original_size_mb": round(self.original_size_mb, 1),
            "optimized_size_mb": round(self.optimized_size_mb, 1),
            "saved_mb": round(self.saved_mb, 1),
            "reduction_percent": round(self.reduction_percent, 1),
            "issues_found_count": self.issues_found_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "type": "docker"
        }
