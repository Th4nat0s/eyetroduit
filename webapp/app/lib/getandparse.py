#!/bin/env python3

import glob
import json
import os
from collections import Counter
from datetime import datetime
import tldextract
from geoip2.database import Reader
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from .. import db
#
# Chemin vers la base de données GeoIP2 Lite (City)

database_path =  db.app.config.get('GEOIP')
reader = Reader(database_path)

json_path =  db.app.config.get('DDOSIA')

def sdate2pdate(sdate):
    pdate = datetime.strptime(sdate, "%Y%m%d%H%M%S")
    return pdate

def pdate2sdate(pdate):
    sdate = datetime.strftime(pdate, "%Y%m%d%H%M%S")
    return sdate



def ip2geo(ip):
    try:
        response = reader.city(ip)
        return(response)
    except geo2ip.errors.AddressNotFoundError:
        print("L'adresse IP n'a pas été trouvée dans la base de données.")
    except Exception as e:
        print("Une erreur s'est produite lors de la géolocalisation :", str(e))

def parse_report(data,json_date):
    donnees_json = []  # a simplifir
    donnees = data  #json.loads(json)
    #now = datetime.now()
    #date = datetime.strftime(now, "%Y%m%d%H%M%S")
    fichier_json = f"{json_date}_ddosia.conf"
    donnees["metadata"] = {"name":fichier_json, "timestamp": json_date}
    donnees_json.append(donnees)

    # Chemin vers le répertoire contenant les fichiers JSON
    repertoire_json = './confs'

    # Maintenant, donnees_json contient les données JSON de tous les fichiers du répertoire
    ahost = []
    htype = []
    method = []
    event = []
    nstable = {}  


    for donnees in donnees_json:
        dhost = []
        time = donnees.get('metadata').get('timestamp') 

        for target in donnees.get('targets'):
            host = target.get('host').split("/")[0]
            ahost.append(host) # Global counter of host victim
            dhost.append(host) # Counter of this config victim
            nstable[host] = target.get('ip')  # Pierre de rosette host vs IP
            method.append(target.get('method'))
            htype.append(target.get('type'))


        time = sdate2pdate(time)
        hosts = list(set(dhost))
        for hos in hosts:
            geoinfo = ip2geo(nstable.get(hos))  # Get IP info 
            ext = tldextract.extract(hos)  # Get Domain info
            event.append({"host": hos, "timestamp": time, "endpoints": Counter(dhost).get(hos), \
                          "ip": nstable.get(hos), "country": geoinfo.country.name, \
                          "lat": geoinfo.location.latitude, "lon":geoinfo.location.longitude, \
                         "file": f'{json_date}_ddosia.json', "domain":    ext.registered_domain })
    # reader.close()
    return(event)

def file_save(data, timestamp):
    json_str = json.dumps(data, indent=4)
    nom_fichier = f"{json_path}/{timestamp}_ddosia.json"
    with open(nom_fichier, "w") as fichier_json:
        fichier_json.write(json_str)
