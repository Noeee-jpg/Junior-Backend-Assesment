from sqlalchemy import Column, String, BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Nasabah(Base):
    __tablename__ = 'nasabah'
    id = Column(BigInteger, primary_key=True)
    nik = Column(String(50), unique=True, nullable=False)
    nama = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    no_hp = Column(String(13), unique=True, nullable=False)
    no_rekening = Column(String(16), unique=True, nullable=False)
    saldo = Column(Float, default=0.0)
    password = Column(String(100), nullable=False) 
    created_at = Column(DateTime, default=func.now())

    # Relationship to Mutasi
    mutasi = relationship("Mutasi", back_populates="nasabah")

class Mutasi(Base):
    __tablename__ = 'mutasi'
    id = Column(BigInteger, primary_key=True)
    no_rekening = Column(String(16), ForeignKey('nasabah.no_rekening'), nullable=False)
    jenis_transaksi = Column(String(50), nullable=False)
    tanggal_transaksi = Column(DateTime, default=func.now())
    saldo = Column(Float, nullable=False)
    keterangan = Column(String(255))  # Mengatur panjang kolom keterangan
    
    # Relationship to Nasabah
    nasabah = relationship("Nasabah", back_populates="mutasi")
