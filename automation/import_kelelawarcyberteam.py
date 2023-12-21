# -*- coding: utf-8 -*-

# Leech les report sur mirror-h via TOR et post en direct

import requests
from bs4 import BeautifulSoup
import socks
import socket
import json
from datetime import datetime
import yaml
import re
import sys
from lib import troduitlib



# URL de la page à télécharger
url = 'https://mirror.kelelawarcyberteam.com/archive'


# En-tête User-Agent pour simuler une requête de navigateur
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }



def scrap():
    # Set up Tor proxy
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)

    # Téléchargement de la page avec l'en-tête User-Agent

    response = requests.get(url, headers=headers)
    html = response.text


    soup = BeautifulSoup(html, 'html.parser')

    # Trouver la balise <h6 class="card-title">Archives</h6>
    archives_title = soup.find('h6', {'class': 'card-title'})

    reports= []

    # Vérifier si la balise existe
    if archives_title:
        # Trouver le conteneur suivant la balise h6 (div.table-responsive)
        table_container = archives_title.find_next('div', {'class': 'table-responsive'})

        # Trouver toutes les lignes du tableau dans le conteneur table-responsive
        table_rows = table_container.find_all('tr')

        # Parcourir les lignes pour extraire les informations nécessaires
        for row in table_rows:
            columns = row.find_all('td')
            if len(columns) >= 3:  # Assurez-vous qu'il y a suffisamment de colonnes
                defacer = columns[0].find('a').text.strip()
                timestamp = columns[2].text.strip()
                mirror_link = columns[-1].find('a')['href'].strip()
                mirror_link = "https://mirror.kelelawarcyberteam.com" + mirror_link

                response = requests.get(mirror_link, headers=headers)
                html = response.text

                soup = BeautifulSoup(html, 'html.parser')

                # Trouver la div contenant l'URL du domaine
                domain_info_div = soup.find('div', {'class': 'col-md-12 mt-2'})

                # Vérifier si la div existe
                if domain_info_div:
                    # Extraire l'URL du domaine
                    url_pattern = re.compile(r'Domain : (http[s]?://[^\s<>"]+)')
                    match = url_pattern.search(domain_info_div.text)
                    if match:
                        domain_url = match.group(1)

                else:
                    print("Balise <div class='col-md-12 mt-2'> non trouvee.")

                reports.append({"datetime": timestamp, "adversary": defacer, 'target': domain_url, 'reference': mirror_link})
    else:
        print("Balise <h6 class='card-title'>Archives</h6> non trouvee.")
    return(reports)


if __name__ == '__main__':
    results = scrap()
    troduitlib.post_victims(results, 8)
