#!/bin/env python3
import sqlite3
import datetime
import hashlib
import json
from .getandparse import pdate2sdate, sdate2pdate
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .. import db
from ..models import Victims

conf_path = db.app.config.get('DDOSIA')

def db_open():
    # ouvre une sessin sqlite
    conn = sqlite3.connect(db.app.config.get('DBASE'))
    return(conn.cursor(), conn)

def last_geoloc():
    # Extrait les lat lon de l'attaque en cours pour faire la mapmonde.
    current_date = last_report()
    cursor, conn = db_open()
    query = f'select lat,lon from victim where  strftime("%Y-%m-%d %H:%M:%S", timestamp) = "{current_date}"'
    cursor.execute(query)
    results =  cursor.fetchall()
    json = []
    for item in results:
        try:
            json.append({"latitude":float(item[0]), "longitude": float(item[1]) }) 
        except TypeError:
            pass
    conn.close
    return(json)

def md5it(data):
    # dump a json ident and hash it
    json_str = json.dumps(data, indent=4)
    md5_hasher = hashlib.md5()
    # Mettre le hasher avec la chaîne (convertie en bytes)
    md5_hasher.update(json_str.encode('utf', errors="replace"))
    # Obtenir la somme de contrôle MD5 sous forme de chaîne hexadécimale
    md5_sum = md5_hasher.hexdigest()
    return md5_sum

def savemd5(data, time_json):
    # Save le tuple config = une date unique et un hash.
    md5_sum = md5it(data)
    cursor, conn = db_open()
    query = f"INSERT INTO config (md5, timestamp) VALUES ('{md5_sum}', '{sdate2pdate(time_json)}')"
    cursor.execute(query)
    conn.commit()
    conn.close


def notindb(data, last):
    # Check si un rapport est deja dans la db
    # Return True si ce n'est PAS dans la db
    # il ne prends pas si le md5 qu'on lui file c'est le dernier rentré
    md5_sum = md5it(data)
    # last = last_report() # sdate2pdate( last_report())  # récupère la date du dernier rapport
    cursor, conn = db_open()
    query = f"select id from config where md5 = '{md5_sum}' and strftime('%Y%m%d%H%M%S', timestamp) = '{last}';"
    cursor.execute(query)
    results =  cursor.fetchall()
    conn.close()
    if len(results) == 0:
        return True
    return False

def last_report():
    cursor,conn = db_open()
    # cherche le dernier config file
    query = f'select strftime("%Y%m%d%H%M%S", timestamp) from victim order by timestamp desc limit 1;'
    cursor.execute(query)
    data="1976090100000"
    result = cursor.fetchone()
    if result: 
        data = result[0]
    conn.close()
    return sdate2pdate(data)

def lookfor(domain):
    cursor, conn = db_open()
    query = f'select host, STRFTIME("%d/%m/%Y, %H:%M", timestamp) from victim where domain like "%{domain}%" order by timestamp desc limit 500;'
    cursor.execute(query)
    results =  cursor.fetchall()
    conn.close()
    json = []
    for item in results:
        json.append({"host":item[0], "timestamp": item[1] }) 
    return(json)


def daily_victims():
    cursor, conn = db_open()
    current_date = last_report()
    # Requête SQL pour sélectionner les hôtes avec le timestamp égal à la date courante
    query = f"select distinct host,filename,endpoint from victim where strftime('%Y-%m-%d %H:%M:%S', timestamp) = '{current_date}' order by domain"
    # Exécutez la requête SQL
    cursor.execute(query)
    # Récupérez tous les résultats
    hosts = cursor.fetchall()
    conn.close()
    # Fermez la connexion à la base de données
    # conn.close()
    # Imprimez les hôtes
    ostring = ""
    if hosts:
        for host in hosts:
            ostring += f'<li>{host[0]}<span title="Path targeted">&nbsp;{host[2]}<i class="fa fa-crosshairs">&nbsp;</i></spam><a href="{conf_path}/{host[1]}" target="_blank"><i class="fa fa-file-code-o"></i></a></li>'
    else:
        ostring = ("No Active attack")
    return(ostring)

def save(data, json_timestamp):
    # Save a list of parsed victim into the database
    # Créez un moteur SQLite pour la base de données
    engine = create_engine((db.app.config.get('SQLALCHEMY_DATABASE_URI')))

    # Déclarer une classe de modèle pour la table "victime"
    Base = declarative_base()

    # Créez une session SQLAlchemy pour interagir avec la base de données
    Session = sessionmaker(bind=engine)
    session = Session()
    for element in data:
        new_victim = Victims(
            host= element.get("host"),
            domain = element.get("domain"),
            ip=element.get("ip"),
            country=element.get("country"),
            # timestamp = datetime.datetime.strptime(element.get("timestamp"),  "%Y%m%d%H%M%S"),
            timestamp = datetime.datetime.strptime(json_timestamp,  "%Y%m%d%H%M%S"),
            # timestamp = json_timestamp, 
            endpoint=element.get("endpoints"),
            lat=element.get("lat"),
            lon=element.get("lon"),
            filename=element.get("file")
        )
        # Ajoutez l'entrée à la session et effectuez la transaction
        session.add(new_victim)
    session.commit()

    # Fermez la session
    session.close()

def valid_key_push(key):
    cursor, conn = db_open()
    query = f'select id from api_keys where key = "{key}" and active = True;'
    cursor.execute(query)
    result =  cursor.fetchone()
    if result:
        return True
    return False
