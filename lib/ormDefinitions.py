# This file contains the schemeas for all the tables in the database
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ValoAccount(Base):
    __tablename__ = "valoaccounts"

    id = Column(Integer, primary_key=True)
    owner_id = Column(String(19))
    username = Column(String(16))
    tag = Column(String(5))
    note = Column(String(255))
    acctype = Column(String(1))
    region = Column(String(4))


class DisServer(Base):
    __tablename__ = "Servers"

    server_id = Column(String(19), primary_key=True)
    region = Column(String(4))
    max_self_role = Column(String(20))

    roles = relationship("Role")


class Role(Base):
    __tablename__ = "roles"

    server_id = Column(String(19), ForeignKey("Servers.server_id"), primary_key=True)
    role_id = Column(String(19))
    valo_name = Column(String(16))
