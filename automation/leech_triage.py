import requests
from bs4 import BeautifulSoup
import json

# Fonction pour extraire les informations de la section "Malware Config"
def extract_malware_config(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche de la section "Malware Config"
        malware_config_container = soup.find('div', id='malware-config-container')

        # Vérification si la section "Malware Config" est présente
        if malware_config_container and 'data-collapsable-closed' not in malware_config_container.attrs:
            malware_config_section = soup.find('div', id='malware-config')

            if malware_config_section:
                # Extraction des informations de la section "Malware Config"
                family = malware_config_section.find('div', class_='config-entry-heading', text='Family').find_next('p').get_text(strip=True)

                # Vérification s'il y a une entrée "C2"
                c2_entry = malware_config_section.find('div', class_='config-entry-heading', text='C2')
                if c2_entry:
                    c2_value = c2_entry.find_next('p').get_text(strip=True)
                    return {
                        'ID': url.split('/')[-1],
                        'Family': family,
                        'Type': 'Telegram',
                        'Value': c2_value
                    }
                
                # Vérification s'il y a une entrée "Credentials"
                credentials_entry = malware_config_section.find('div', class_='config-entry-heading', text='Credentials')
                if credentials_entry:
                    credentials = {}
                    for item in credentials_entry.find_next('ul', class_='list').find_all('li', class_='nano'):
                        key = item.find('b').get_text(strip=True)
                        value = item.get_text(strip=True).replace(key, '').strip()
                        credentials[key] = value

                    # Vérification du type (SMTP ou FTP)
                    config_type = 'SMTP' if 'Protocol:' in credentials and credentials['Protocol:'].lower() == 'smtp' else 'FTP'

                    return {
                        'ID': url.split('/')[-1],
                        'Family': family,
                        'Type': config_type,
                        'Credentials': credentials
                    }
                
                # Si aucune entrée spécifique n'est trouvée, retourner la famille uniquement
                return {
                    'ID': url.split('/')[-1],
                    'Family': family,
                    'Type': 'Not_extracted'
                }
            else:
                print(f"La section 'Malware Config' n'a pas été trouvée sur la page {url}")
                return None
        else:
            print(f"La section 'Malware Config' n'est pas disponible sur la page {url}")
            return None
    else:
        print(f"La requête a échoué avec le code d'état {response.status_code}")
        return None

# Liste des familles à rechercher
families = ['snakekeylogger', 'agenttesla']

# URL de la page principale
main_url_template = "https://tria.ge/s?q=family%3A{}"

# Récupération des informations pour chaque famille
malware_configs = []
for family in families:
    main_url = main_url_template.format(family)

    # Récupération des valeurs de "data-sample-id" à partir de la page principale
    response_main = requests.get(main_url)
    if response_main.status_code == 200:
        soup_main = BeautifulSoup(response_main.text, 'html.parser')
        samples = soup_main.find_all('a', class_='row', attrs={'data-sample-id': True})

        for sample in samples:
            sample_id = sample['data-sample-id']
            sample_url = f"https://tria.ge/{sample_id}"

            # Extraction des informations de la section "Malware Config"
            malware_config_info = extract_malware_config(sample_url)

            if malware_config_info:
                malware_configs.append(malware_config_info)

# Écriture des informations dans un fichier JSON
with open('malware_configs.json', 'w') as json_file:
    json.dump(malware_configs, json_file, indent=2)

