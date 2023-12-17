# -*- coding: utf-8 -*-

# Leech les report sur mirror-h via TOR et post en direct


import requests
from bs4 import BeautifulSoup
import socks
import socket
import json
from datetime import datetime
import yaml

# Charger la configuration depuis le fichier YAML
with open('config.yaml', 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

    # Récupérer la valeur du token depuis la configuration
    token = config.get('token', 'default_value_if_not_present')


# URL de la page à télécharger
url = 'https://zone-xsec.com/onhold'


# En-tête User-Agent pour simuler une requête de navigateur
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

# Set up Tor proxy
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)

# Téléchargement de la page avec l'en-tête User-Agent

response = requests.get(url, headers=headers)
html = response.text

# Analyse HTML avec BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Recherche de la table des rapports
table = soup.find('table')

reports = []
# Si la table est trouvée, itérer sur les lignes du tableau (à partir de la deuxième ligne pour éviter les en-têtes)
if table:
    # rows = table.find_all('tr')[1:]
    rows = soup.select('.mirror-table tbody tr')
    # Itérer sur chaque ligne et extraire les données
    # Loop through each row and extract information
    for row in rows:
        date_time = row.select_one('td:nth-of-type(1)').text.strip()
        attacker = row.select_one('td:nth-of-type(2) a').text.strip()
        url = row.select_one('td:nth-of-type(9)').text.strip()
        mirror_url = "https://zone-xsec.com" + row.select_one('td:nth-of-type(10) a')['href']

        response = requests.get(mirror_url, headers=headers)
        html = response.text

        # retrieve full url
        soup = BeautifulSoup(html, 'html.parser')

        # Find the h1 element within the panel title
        panel_title = soup.select_one('.panel-title')

        # Extract the URL from the h1 text
        url = panel_title.text.replace('Defacement Details of ', '').strip()

        # Imprimer les valeurs extraites
        reports.append({"date": date_time, "adversary": attacker, 'target': url, 'reference': mirror_url})

# Remove sock connections
socks.setdefaultproxy()
socks.socksocket = socket._socket
session_without_proxy = requests.Session()
del socks


for report in reports:
    print(report)
    # Convertir la date en format requis
    date_object = datetime.strptime(report.get('date'), "%Y-%m-%d %H:%M:%S")
    formatted_date = date_object.strftime("%Y-%m-%d %H:%M:%S")

    # Construire le dictionnaire avec les valeus
    data = {
        "api_key": token,
        "adversary": report.get('adversary'),
        "target": report.get('target'),
        "reference": report.get('reference'),
        "datetime": formatted_date,
        "source": 7
    }

    # URL de l'API
    # api_url = "https://xakep.in/eyetroduit/claimedvictimsview/api_claimed_victim"
    api_url = "http://127.0.0.1:5000/claimedvictimsview/api_claimed_victim"

    # Effectuer la requête POST
    response = requests.post(api_url, json=data)

    # Vérifier la reponse
    if response.status_code == 200:
        print("La requête POST a été réussie.")
    else:
        print(f"Erreur lors de la requête POST. Code de statut : {response.status_code}")
        print(response.text)
