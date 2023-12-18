from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class MotorSport(Base):
    __tablename__ = "pilihanmotor"
    id: Mapped[int] = mapped_column(primary_key=True)
    cc: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    speed: Mapped[int] = mapped_column()
    berat: Mapped[int] = mapped_column()
    kapasitas_tangkibensin: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"MotorSport(id={self.id!r}, cc={self.cc!r}, harga={self.harga!r}, speed={self.speed!r}, berat={self.berat!r}, kapasitas_tangkibensin={self.kapasitas_tangkibensin!r})"
    