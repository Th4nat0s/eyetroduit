import requests
import json

# Import les telegram channels "onlines" depuis deep dark cti github ressource

# URL de la page à récupérer
url = "https://raw.githubusercontent.com/fastfire/deepdarkCTI/main/telegram.md"

# URL de destination pour le POST
post_url = "https://xakep.in/eyetroduit/mediasview/api_add_media"

# Apikey to post
Apikey = ''


# Récupérer le contenu de la page
response = requests.get(url)

# Vérifier si la requête a réussi
if response.status_code == 200:
    # Diviser le contenu en lignes
    lines = response.text.split('\n')

    # Parcourir les lignes
    for line in lines:
        # Vérifier si la ligne contient des données utiles
        if "|" in line:
            # Supprimer les espaces et séparer les champs
            fields = [field.strip() for field in line.split("|")]

            # Extraire les données pertinentes
            status = fields[2]
            url = fields[1]

            # Vérifier si le statut est "ONLINE"
            if status == "ONLINE":
                # Créer et imprimer le JSON
                json_data = {
                    "api_key": Apikey,
                    "uri": url,
                    "type": "Telegram"
                }
                print(json.dumps(json_data))

                # Envoi du JSON en tant que données POST
                response = requests.post(post_url, json=json_data)

                # Afficher la réponse du serveur
                print(response.text)
else:
    print("Erreur lors de la récupération de la page:", response.status_code)

