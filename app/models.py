from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base


class ImageOptimization(Base):
    """Stores records of media image optimization operations."""

    __tablename__ = "image_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_size_kb = Column(Float, nullable=False)
    optimized_size_kb = Column(Float, nullable=False)
    saved_bytes_kb = Column(Float, nullable=False)
    reduction_percent = Column(Float, nullable=False)
    format = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_size_kb": round(self.original_size_kb, 2),
            "optimized_size_kb": round(self.optimized_size_kb, 2),
            "saved_bytes_kb": round(self.saved_bytes_kb, 2),
            "reduction_percent": round(self.reduction_percent, 2),
            "format": self.format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
