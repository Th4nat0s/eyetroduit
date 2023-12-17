from flask_appbuilder import Model
from flask import Markup as Esc
from flask import url_for
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy import func
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_appbuilder.models.decorators import renders
from .lib import util
from . import db

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
    claimedvictims = relationship("ClaimedVictims", back_populates="media")
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


class Hashts(Model):
    # Hash Tags
    id = Column(Integer, primary_key=True)
    name =  Column(String(150), unique = True, nullable=False)
    count = Column(Integer, default = 0)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    comms = relationship("Comms", secondary='hasht_comm_association', back_populates="hashts")

    def __repr__(self):
        return self.name

    def repr_links(self):
        html = ""
        for comm in self.comms:
            tag = util.lnk2tel(comm.link)
            id = comm.id
            uri = url_for("CommsView.show", pk=comm.id)
            html += f'<a href="{uri}"><span class="label label-default">{tag}</span></a> '
        return Esc(html)

class HashtcommAssociation(Model):
    __tablename__ = 'hasht_comm_association'
    hasht_id = Column(Integer, ForeignKey('hashts.id'), primary_key=True)
    comm_id = Column(Integer, ForeignKey('comms.id'), primary_key=True)

class Comms(Model):
    # Communication for a group (twitter/telegram etc.. with link
    id = Column(Integer, primary_key=True)
    link =  Column(String(4096), unique= True, nullable=False )

    comm_group_id = Column(Integer, ForeignKey('groups.id'))
    comm_group= relationship("Groups", back_populates="comm")
    media_id = Column(Integer, ForeignKey('medias.id'))
    media = relationship("Medias", back_populates="comm")
    eyetelex = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    tags = relationship("Tags", secondary='comm_tag_association', back_populates="comms")
    hashts = relationship("Hashts", secondary='hasht_comm_association', back_populates="comms")
    checkhostvictim = relationship("CheckhostVictims", back_populates="checkhostvictim_comm")

    def __repr__(self):
        return self.link

    @renders('eyetelex')
    def nice_eyetelex(self):
        if self.eyetelex:
            return Esc('<i class="fa fa-check-square-o"></i>')
        else:
            return Esc('<i class="fa fa-square-o"></i>')

    ''' render nickely telegram links '''
    @renders('link')
    def nice_link(self):
        if self.link.startswith('https://t.me/'):
            chan = self.link.split('/')[3]
            html = '<i class="fa-brands fa-telegram "></i>&nbsp;'
            html += '<a href="javascript:void(0);" onclick="openLinkInExistingTab('
            html += f"'https://web.telegram.org/k/#@{chan}')"
            html += f'">{chan}</a>&nbsp;'
            html += '<a href="javascript:void(0);" data-toggle="tooltip" title="Copy link" rel="tooltip" '
            html += 'onclick="copyToClipboard('
            html += f"'{self.link}')"
            html += '"><i class="fa-regular fa-copy"></i></a>&nbsp;'
            return Esc(html)
        elif self.link.startswith('https://twitter.com/'):
            chan = self.link.split('/')[3]
            html = '<i class="fa-brands fa-twitter "></i>&nbsp;'
            html += f'<a href="https://twitter.com{chan}" target="_blank" rel="noopener'
            html += f' noreferrer">{chan}</a>&nbsp;'
            html += '<a href="#" data-toggle="tooltip" title="Copy link" rel="tooltip" '
            html += 'onclick="copyToClipboard('
            html += f"'{self.link}')"
            html += '"><i class="fa-regular fa-copy"></i></a>&nbsp;'
            return Esc(html)
        else:
            html = '<i class="fa-solid fa-globe "></i>&nbsp;'
            html += f'<a href="{self.link}" target="_blank" rel="noopener'
            html += f' noreferrer">{self.link}</a>&nbsp;'
            html += '<a href="#" data-toggle="tooltip" title="Copy link" rel="tooltip" '
            html += 'onclick="copyToClipboard('
            html += f"'{self.link}')"
            html += '"><i class="fa-regular fa-copy"></i></a>&nbsp;'
            return Esc(html)


    def alltags(self):
        tags = []
        # Render nice html pills
        html = ""
        # Get all tag name for attached groups
        if self.comm_group:
            for tag in self.comm_group.tags:
                tags.append(tag.tname)
        for tag in tags:
            html += f'<span class="label label-default">{tag}</span> '
        tags = []
        # Get all tag name for communication channel
        for tag in self.tags:
            tags.append(tag.tname)
        # Render nice html pills
        for tag in tags:
            html += f'<span class="label label-primary">{tag}</span> '
        return Esc(html)


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

    def nice_tags(self):
        tags = []
        # Render nice html pills
        html = ""
        # Get all tag name for communication channel
        for tag in self.tags:
            tags.append(tag.tname)
        # Render nice html pills
        for tag in tags:
            html += f'<span class="label label-primary">{tag}</span> '
        return Esc(html)


    def nice_comms(self):
        html = ""
        media = db.session.query(Medias).filter(Medias.mname == "Telegram").first()
        for comm in self.comm:
            if comm.media == media:
                tag = util.lnk2tel(comm.link)
                label = "success"
            else:
                tag = comm.link
                label = "default"
            id = comm.id
            uri = url_for("CommsView.show", pk=comm.id)
            html += f'<a href="{uri}"><span class="label label-{label}">{tag}</span></a> '
        return Esc(html)


class  Victims(Model):
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



'''
    Victims Detected by checkhost report
    c'est une table de type "log".. simple listing
'''
class CheckhostVictims(Model):
    __tablename__ = 'checkhostvictims'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())  # Timestpam
    checkhost = Column(String)  # Doit t'il etre unique ??  ID checkhost
    host = Column(String)  # hostname
    domain = Column(String) # Domain pété
    country = Column(String)
    ip = Column(String)
    lat = Column(String)
    lon = Column(String)
    status = Column(Integer, default=0)  # 0 est reporté, 1 error, 2  enrichit
    checkhostvictim_comm_id = Column(Integer, ForeignKey('comms.id'))
    checkhostvictim_comm = relationship("Comms", back_populates="checkhostvictim")


'''
    Victims claimed by reporting website ( ddos, deface ).
    c'est une table de type "log".. simple listing
'''    
class ClaimedVictims(Model):
    __tablename__ = 'claimedvictims'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())  # TimeStamp
    fullurl = Column(String) # Reported URL
    reference = Column(String) # Url du claim que c'est pété
    host = Column(String)  # hostname
    domain = Column(String) # Domain pété
    country = Column(String)
    ip = Column(String)
    lat = Column(String)
    lon = Column(String)
    adversary = Column(String) # Ref du "hacker"
    status = Column(Integer, default=0)  # 0 est reporté, 1 error, 2  enrichit

    # Pour savoir d'ou que ca vient. CommSource.
    media_id = Column(Integer, ForeignKey('medias.id'))
    media = relationship("Medias", back_populates="claimedvictims")
 

    def __repr__(self):
        return self.host


class Configs(Model):
    # Collected configs
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    md5 = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)



if __name__ == "__main__":
    print (DBVERSION)
