from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)
    title = Column(String)
    service = Column(String)
    root_cause_host = Column(String, index=True)
    priority = Column(String)
    status = Column(String, default='open')
    customers_affected = Column(Integer, default=0)
    fault_started_at = Column(DateTime)
    detected_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    rca = Column(Text, default='')
    simulated = Column(Boolean, default=False)
    alarms = relationship(
        'Alarm', back_populates='incident', cascade='all, delete-orphan'
    )
    timeline = relationship(
        'TimelineEvent', back_populates='incident',
        cascade='all, delete-orphan'
    )


class Alarm(Base):
    __tablename__ = 'alarms'
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    host = Column(String)
    trigger_name = Column(String)
    severity = Column(Integer)
    event_id = Column(String)
    received_at = Column(DateTime)
    cleared = Column(Boolean, default=False)
    incident = relationship('Incident', back_populates='alarms')


class TimelineEvent(Base):
    __tablename__ = 'timeline'
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'))
    at = Column(DateTime)
    actor = Column(String)
    action = Column(String)
    note = Column(Text, default='')
    incident = relationship('Incident', back_populates='timeline')