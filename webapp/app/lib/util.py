def lnk2tel(link):
    # Convertis une URL Telegram en Nom court télégram
    index = str(link).rstrip('/').rfind('/')  # vire le last / et trouve le / d'après.
    tel = link[index + 1:]
    return tel
