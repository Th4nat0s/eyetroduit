#-*- coding: utf-8 -*-

# Leech les report sur mirror-h via TOR et post en direct

import requests
from bs4 import BeautifulSoup
import socks
import socket
import json
from datetime import datetime
import yaml
import sys


def get_api_token():
    # Charger la configuration depuis le fichier YAML
    with open('./config.yaml', 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Récupérer la valeur du token depuis la configuration
    token = config.get('token', 'default_value_if_not_present')
    return token


def get_api_url():
    # Charger la configuration depuis le fichier YAML
    with open('./config.yaml', 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Récupérer la valeur du token depuis la configuration
    url = config.get('api_url', 'default_value_if_not_present')
    return url


def post_victims(reports, source):
    '''
    Post to eyetroduit victims collected, without TOR
    reports array of reports
    source integer communication source type ( mediaviews )
    '''
    # Remove sock connections, in case of TOR usage before.
    #socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
    #socks.setdefaultproxy()
    #socks.socksocket = socket._socket
    #session_without_proxy = requests.Session()
    #del socks

    for report in reports:
        # Convertir la date en format requis
        #date_object = datetime.strptime(report.get('date'), "%Y-%m-%d %H:%M:%S")
        #formatted_date = date_object.strftime("%Y-%m-%d %H:%M:%S")

        # Construire le dictionnaire avec les valeus
        data = {
            "api_key": get_api_token(),
            "adversary": report.get('adversary'),
            "target": report.get('target'),
            "reference": report.get('reference'),
            "datetime": report.get('datetime'), # formatted_date,
            "source": source
        }
        sys.stdout.buffer.write(str(data).encode('utf-8'))

        # URL de l'API
        api_url = get_api_url() + "/claimedvictimsview/api_claimed_victim"
        # "https://xakep.in/eyetroduit/claimedvictimsview/api_claimed_victim"
        # api_url = "http://127.0.0.1:5000/claimedvictimsview/api_claimed_victim"

        # Effectuer la requête POST
        response = requests.post(api_url, json=data)

        # Vérifier la reponse
        if response.status_code == 200:
            print("La requete POST a ete reussie.")
        else:
            print(f"Erreur lors de la requete POST. Code de statut : {response.status_code}")
            print(response.text)
