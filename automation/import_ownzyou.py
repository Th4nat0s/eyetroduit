# -*- coding: utf-8 -*-
import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
import yaml
import socks
import socket


# Charger la configuration depuis le fichier YAML
with open('config.yaml', 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

    # Récupérer la valeur du token depuis la configuration
    token = config.get('token', 'default_value_if_not_present')



url = 'https://ownzyou.com/inc/ajax/archive.php'
headers = {
    'authority': 'ownzyou.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cookie': 'cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-functional=no; cookielawinfo-checkbox-performance=no; cookielawinfo-checkbox-analytics=no; cookielawinfo-checkbox-advertisement=no; cookielawinfo-checkbox-others=no;',
    'referer': 'https://ownzyou.com/archive',
    'sec-ch-ua': '"Opera";v="105", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
    'x-requested-with': 'XMLHttpRequest',
}

params = {
    'draw': '1',
    'columns[0][data]': '0',
    'columns[0][name]': '',
    'columns[0][searchable]': 'true',
    'columns[0][orderable]': 'true',
    'columns[0][search][value]': '',
    'columns[0][search][regex]': 'false',
    'columns[1][data]': '1',
    'columns[1][name]': '',
    'columns[1][searchable]': 'true',
    'columns[1][orderable]': 'true',
    'columns[1][search][value]': '',
    'columns[1][search][regex]': 'false',
    'columns[2][data]': '2',
    'columns[2][name]': '',
    'columns[2][searchable]': 'true',
    'columns[2][orderable]': 'true',
    'columns[2][search][value]': '',
    'columns[2][search][regex]': 'false',
    'columns[3][data]': '3',
    'columns[3][name]': '',
    'columns[3][searchable]': 'true',
    'columns[3][orderable]': 'true',
    'columns[3][search][value]': '',
    'columns[3][search][regex]': 'false',
    'columns[4][data]': '4',
    'columns[4][name]': '',
    'columns[4][searchable]': 'true',
    'columns[4][orderable]': 'true',
    'columns[4][search][value]': '',
    'columns[4][search][regex]': 'false',
    'columns[5][data]': '5',
    'columns[5][name]': '',
    'columns[5][searchable]': 'true',
    'columns[5][orderable]': 'true',
    'columns[5][search][value]': '',
    'columns[5][search][regex]': 'false',
    'columns[6][data]': '6',
    'columns[6][name]': '',
    'columns[6][searchable]': 'true',
    'columns[6][orderable]': 'true',
    'columns[6][search][value]': '',
    'columns[6][search][regex]': 'false',
    'columns[7][data]': '7',
    'columns[7][name]': '',
    'columns[7][searchable]': 'true',
    'columns[7][orderable]': 'true',
    'columns[7][search][value]': '',
    'columns[7][search][regex]': 'false',
    'order[0][column]': '0',
    'order[0][dir]': 'desc',
    'start': '0',
    'length': '35',
    'search[value]': '',
    'search[regex]': 'false'
}

# Set up Tor proxy
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)

response = requests.get(url, headers=headers, params=params)

results = []
if response.status_code == 200:
    data = response.json()
    # Extrayez les données nécessaires
    for item in data['data']:
        target_html = item[3]  # Exemple: 'https://bppd.malangkota.go.id/wp-content'
        adversary_html = item[2]  # Exemple: 'CyberzForum'
        id_number = item[0]  # Exemple: '189969'
        timestamp = item[6]  # Exemple: '27/09/2023 10:04'

        # BeautifulSoup pour extraire le texte brut des balises HTML
        target_soup = BeautifulSoup(target_html, 'html.parser')
        adversary_soup = BeautifulSoup(adversary_html, 'html.parser')

        # Obtenez le texte brut sans balises HTML
        target = target_soup.find('a')['href']
        adversary = adversary_soup.get_text()

        # Retirer les caractères spécifiques tels que "✓"
        adversary = re.sub(r'[^\w\s]', '', adversary)
        adversary = adversary.rstrip()

        id_number = "https://ownzyou.com/zone/" + item[0]
        timestamp = item[6]

        # Convertir la chaîne en objet datetime
        date_object = datetime.strptime(timestamp, "%d/%m/%Y %H:%M")
        # Formater la date dans le nouveau format
        timestamp = date_object.strftime("%Y-%m-%d %H:%M:%S")

        results.append({"target": target, "adversary": adversary, "reference": id_number, "timestamp": timestamp})

else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Remove sock connections
socks.setdefaultproxy()
socks.socksocket = socket._socket
session_without_proxy = requests.Session()
del socks

for report in results:
    print(report)
    # Convertir la date en format requis
    # Construire le dictionnaire avec les valeus
    data = {
        "api_key": token,
        "adversary": report.get('adversary'),
        "target": report.get('target'),
        "reference": report.get('reference'),
        "datetime": report.get('timestamp'),
        "source": 5
    }

    # URL de l'API
    api_url = "https://xakep.in/eyetroduit/claimedvictimsview/api_claimed_victim"
    # api_url = "http://127.0.0.1:5000/claimedvictimsview/api_claimed_victim"

    # Effectuer la requête POST
    response = requests.post(api_url, json=data)

    # Vérifier la réponse
    if response.status_code == 200:
        print("La requete POST a ete reussie.")
    else:
        print(f"Erreur lors de la requete POST. Code de statut : {response.status_code}")
        print(response.text)

