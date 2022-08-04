# This file contains the schemeas for all the tables in the database
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    accounts = relationship("ValoAccount")


class ValoAccount(Base):
    __tablename__ = "valoaccounts"

    owner_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    username = Column(String(16))
    tag = Column(String(5))
    note = Column(String(255))
    acctype = Column(String(1))
    region = Column(String(4))


class DisServer(Base):
    __tablename__ = "DisServer"

    id = Column(Integer, primary_key=True)
    region = Column(String(4))
    max_self_role = Column(String(20))

    roles = relationship("roles")


class Role(Base):
    __tablename__ = "roles"

    server_id = Column(Integer, ForeignKey("DisServer.id"), primary_key=True)
    role_id = Column(Integer)
    valo_name = Column(String(16))
