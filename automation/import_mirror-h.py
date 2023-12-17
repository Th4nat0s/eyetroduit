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
url = 'https://mirror-h.org'



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
    rows = table.find_all('tr')[1:]

    # Itérer sur chaque ligne et extraire les données
    for row in rows:
        cells = row.find_all('td')

        # Extraction des valeurs
        attacker_name = cells[0].text.strip()
        web_url = cells[2].find('a')['href'].strip()
        date = cells[4].text.strip()
        victim_site = cells[2].text.strip()

        # Imprimer les valeurs extraites
        reports.append({"date": date, "adversary": attacker_name, 'target': victim_site, 'reference': web_url})

# Remove sock connections
socks.setdefaultproxy()
socks.socksocket = socket._socket
session_without_proxy = requests.Session()
del socks


for report in reports:
    print(report)
    # Convertir la date en format requis
    date_object = datetime.strptime(report.get('date'), "%d/%m/%Y")
    formatted_date = date_object.strftime("%Y-%m-%d %H:%M:%S")

    # Construire le dictionnaire avec les valeus
    data = {
        "api_key": token,
        "adversary": report.get('adversary'),
        "target": report.get('target'),
        "reference": report.get('reference'),
        "datetime": formatted_date,
        "source": 6
    }

    # URL de l'API
    api_url = "https://xakep.in/eyetroduit/claimedvictimsview/api_claimed_victim"

    # Effectuer la requête POST
    response = requests.post(api_url, json=data)

    # Vérifier la réponse
    if response.status_code == 200:
        print("La requête POST a été réussie.")
    else:
        print(f"Erreur lors de la requête POST. Code de statut : {response.status_code}")
        print(response.text)

