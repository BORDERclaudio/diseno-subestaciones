from sqlalchemy import Column, Integer, Float, ForeignKey
from database import Base

class ParamApantallamiento(Base):
    __tablename__ = "param_apantallamiento"
    memoria_id = Column(Integer, ForeignKey("memorias.id"), primary_key=True)
    Vnom = Column(Float, default=220.0)
    BIL = Column(Float, default=1050.0)
    h = Column(Float, default=15.0)
    n = Column(Integer, default=2)
    d_mm = Column(Float, default=25.4)
    s_cm = Column(Float, default=45.7)
    E0 = Column(Float, default=21.1)
    tipo_elemento = Column(Integer, default=1)
    modo_iter = Column(Integer, default=1)

class ResultApantallamiento(Base):
    __tablename__ = "result_apantallamiento"
    memoria_id = Column(Integer, ForeignKey("memorias.id"), primary_key=True)
    r_e = Column(Float)
    Rc = Column(Float)
    n_iter_nr = Column(Integer)
    Rc_prime = Column(Float)
    Zs = Column(Float)
    I_min = Column(Float)
    S_esfera = Column(Float)
