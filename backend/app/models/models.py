# PATH: backend/app/models/models.py

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, event, DateTime
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Imputaciones(Base):
    __tablename__ = 'Imputaciones'
    
    ID = Column(BIGINT, primary_key=True, index=True)
    FechaImp = Column(Date)
    CodEmpleado = Column(String)
    Timpu = Column(String)
    Horas = Column(Float)
    Proyecto = Column(String(255), ForeignKey('Projects_Dictionary.ProyectoBaan'))
    TipoCoche = Column(String)
    NumCoche = Column(String)
    CentroTrabajo = Column(String(32))
    Tarea = Column(String)
    TareaAsoc = Column(String)
    TipoIndirecto = Column(String)
    TipoMotivo = Column(String)
    TimestampInput = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    TipoImput = Column(String(2), ForeignKey("TiposOrdenes.TipoOrden"), nullable=True)
    AreaTarea = Column(String(64), ForeignKey('Extraciclos.AreaTarea'), nullable=True)
    area_id = Column(String(32), ForeignKey('Areas.CentroTrabajo'))

    # Relaciones
    tabla_central = relationship("TablaCentral", uselist=False, back_populates="imputacion")
    project_dict = relationship("ProjectsDictionary", back_populates="imputacion", uselist=False)
    area = relationship("Areas", back_populates="imputacion", uselist=False)
    extraciclo = relationship("Extraciclos", backref="imputaciones")

    # Relación con TiposOrdenes
    tipo_orden = relationship("TiposOrdenes", back_populates="imputaciones", lazy="select")

class SapOrders(Base):
    __tablename__ = 'Sap_Orders'

    ID = Column(BIGINT, primary_key=True, index=True)
    OperationActivityFull = Column(String)
    EffectivityFull = Column(String)
    Order = Column(String)
    Operation = Column(String)
    OperationActivity = Column(String)
    Description = Column(String)
    Project = Column(String)
    Area = Column(String)
    Vertice = Column(String)
    CarNumber = Column(Integer)
    TipoIndirecto = Column(String)
    TipoMotivo = Column(String)
    ActiveOrder = Column(Boolean, default=True)
    TimestampInput = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    TipoTarea = Column(String(2), ForeignKey("TiposOrdenes.TipoOrden"), nullable=True)
    tablas_centrales = relationship("TablaCentral", back_populates="sap_order")
    tipo_orden = relationship("TiposOrdenes", back_populates="sap_orders", lazy="select")


class TablaCentral(Base):
  __tablename__ = 'Tabla_Central'
  
  ID = Column(BIGINT, primary_key=True, index=True)
  Employee_Number = Column(String)
  Date = Column(Date)
  HourType = Column(String)
  ProductionOrder = Column(BIGINT)
  Operation = Column(String)
  OperationActivity = Column(String)
  Hours = Column(Float)
  Cargado_SAP = Column(Boolean, default=False)  
  cargadoEnTareaReal = Column(Boolean, default=True)
  TimestampInput = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

  # Clave foránea para la relación 1:1 con Imputaciones
  imputacion_id = Column(BIGINT, ForeignKey('Imputaciones.ID'))
  # Clave foránea para la relación 1:N con SapOrders
  sap_order_id = Column(BIGINT, ForeignKey('Sap_Orders.ID'))
  # Definir las relaciones
  imputacion = relationship("Imputaciones", back_populates="tabla_central")
  sap_order = relationship("SapOrders", back_populates="tablas_centrales")

class ProjectsDictionary(Base):
  __tablename__ = 'Projects_Dictionary'
  ProyectoBaan = Column(String(255), primary_key=True, index=True)  # Asegúrate de que la longitud coincida
  ProyectoSap = Column(String(255))

  # Agregar la relación 1:1 con Imputaciones
  imputacion = relationship("Imputaciones", back_populates="project_dict", uselist=False)

class Areas(Base):
  __tablename__ = 'Areas'

  CentroTrabajo = Column(String(32), primary_key=True, index=True)
  Area = Column(String)
  OpMinC = Column(String)
  OpGG = Column(String)

  # Relación 1:1 con Imputaciones
  imputacion = relationship("Imputaciones", back_populates="area", uselist=False)

class Extraciclos(Base):
  __tablename__ = 'Extraciclos'

  AreaTarea = Column(String(64), primary_key=True, index=True)
  CentroTrabajo = Column(String(32), nullable=False)
  TareaBaan = Column(String(32), nullable=False)
  TipoCNC = Column(String(32))
  OASAP = Column(String(32))

class TiposOrdenes(Base):
    __tablename__ = "TiposOrdenes"

    TipoOrden = Column(String(2), primary_key=True, index=True)  # Ej: 'GG', 'XX', 'C0', etc.
    Nombre = Column(String(50))
    Grupo = Column(Integer)      # Ej: 4 para 'Gasto General', 3 para 'Productivas', 5 para 'Extraciclos'...
    NombreGrupo = Column(String(50))

    # Relación con Imputaciones (1:N)
    imputaciones = relationship("Imputaciones", back_populates="tipo_orden", lazy="select")

    # Relación con SapOrders (1:N)
    sap_orders = relationship("SapOrders", back_populates="tipo_orden", lazy="select")

