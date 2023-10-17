from flask_appbuilder import Model
from flask import Markup as Esc
from flask import url_for
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy import func
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_appbuilder.models.decorators import renders

def dbversion():
    return DBVERSION


class ApiKeys(Model):
    # tag pour le request API
    id = Column(Integer, primary_key=True)
    key =  Column(String(150), unique = True, nullable=False)
    active = Column(Boolean, default=True)


class Medias(Model):
    # tag pour le type de media twitter etc...
    id = Column(Integer, primary_key=True)
    mname =  Column(String(150), unique = True, nullable=False)
    comm = relationship("Comms", back_populates="media")

    def __repr__(self):
        return self.mname


class GroupTagAssociation(Model):
    __tablename__ = 'group_tag_association'
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)


class Tags(Model):
    # Tag to a group (ddos, hack, propalestinian etc...)
    id = Column(Integer, primary_key=True)
    tname =  Column(String(150), unique = True, nullable=False)
    groups = relationship("Groups", secondary='group_tag_association', back_populates="tags")
    comms = relationship("Comms", secondary='comm_tag_association', back_populates="tags")

    def __repr__(self):
        return self.tname

class GroupToolAssociation(Model):
    # Join Tags pour les outils utilisés, nom de botnets
    __tablename__ = 'group_tool_association'
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    tool_id = Column(Integer, ForeignKey('tools.id'), primary_key=True)

class Tools(Model):
    # Tags pour les outils utilisés, nom de botnets
    id = Column(Integer, primary_key=True)
    toolname =  Column(String(150), unique = True, nullable=False)
    note =  Column(Text(length=4096))
    groups = relationship("Groups", secondary='group_tool_association', back_populates="tools")

    def __repr__(self):
        return self.toolname

class GroupTagAssociation(Model):
    __tablename__ = 'group_tag_association'
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

class CommTagAssociation(Model):
    __tablename__ = 'comm_tag_association'
    comm_id = Column(Integer, ForeignKey('comms.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

class Comms(Model):
    # Communication for a group (twitter/telegram etc.. with link
    id = Column(Integer, primary_key=True)
    link =  Column(String(4096), unique= True, nullable=False )
    comm_group_id = Column(Integer, ForeignKey('groups.id'))
    comm_group= relationship("Groups", back_populates="comm")
    media_id = Column(Integer, ForeignKey('medias.id'))
    media = relationship("Medias", back_populates="comm")
    eyetelex = Column(Boolean, default=True)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    tags = relationship("Tags", secondary='comm_tag_association', back_populates="comms")

    def __repr__(self):
        return self.link


class Groups(Model):
    # Group itself
    id = Column(Integer, primary_key=True)
    name =  Column(String(150), unique = True, nullable=False)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    comm = relationship("Comms", back_populates="comm_group")
    tags = relationship("Tags", secondary='group_tag_association', back_populates="groups")
    tools = relationship("Tools", secondary='group_tool_association', back_populates="groups")
    def __repr__(self):
        return self.name

class Victims(Model):
    # DDosIA
    __tablename__ = 'victim'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String)
    domain = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    country = Column(String)
    endpoint = Column(String)
    ip = Column(String)
    lat = Column(String)
    lon = Column(String)
    filename = Column(String)

    def Filename(self):
        ''' Create the download link '''
        uri = url_for("VictimsView.conf_download", filename=self.filename )
        return Esc(f'<a href="{uri}">{self.filename}</a>')

    def __repr__(self):
        return self.id

class Configs(Model):
    # Collected configs
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    md5 = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    print (DBVERSION)
