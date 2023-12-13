#!/usr/bin/env python3
# coding=utf-8
import sys

import requests
from bs4 import BeautifulSoup
import re
import socket
# import adb

# UA Chrome
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
}

'''  Sample of victims types.
<h1>Check website <div class="inline-block"><span class="break-all bg-neutral-200 px-1">https://ftp.prg.aero/WebInterface/login.html</span></div></h1>
<h1>Check website <div class="inline-block"><span class="break-all bg-neutral-200 px-1">http://www.google.com:80</span></div></h1>
<h1>Ping server <div class="inline-block"><span class="break-all bg-neutral-200 px-1">www.premier.be</span></div></h1>
<h1>DNS <div class="inline-block"><span class="break-all bg-neutral-200 px-1" id="dns_host">ec.europa.eu</span></div></h1>
<h1>UDP connect <div class="inline-block"><span id="udp_host" class="break-all bg-neutral-200 px-1">perdu.com:80</span></div></h1>
'''

def testme():
    uri = ['check-host.net/check-report/12d0f5efkec8',
           'check-host.net/check-report/12d0f6c9k415',
           'check-host.net/check-report/12d0f7dekc07',
           'check-host.net/check-report/12d0f8bdkcb7',
           'check-host.net/check-report/12d0f983k665',
           'check-host.net/check-report/12d0fb2fk21b',
           'check-host.net/check-report/12d0fc47k10f',
           'check-host.net/check-report/12d0fd3dk771',
           'check-host.net/check-report/12d0fe04k99b',
           'check-host.net/check-report/12d104abkc75',
           'check-host.net/check-report/12d10177k1bb',
           'check-host.net/check-report/12d0fef1kfad',
           'check-host.net/check-report/12d0ffe4kca3',
           'check-host.net/check-report/12d100b3k947',
           'check-host.net/check-report/12d102fbk5bc',
           'check-host.net/check-report/12d10590k7a8']


def resolve(fqdn):
    try:
        ip_address = socket.gethostbyname(fqdn)
        return(ip_address)
    except socket.gaierror:
        return(None)

def resolveall(fqdn):
    try:
        address_info = socket.getaddrinfo(fqdn, None)
        ips = []
        for info in address_info:
            family, _, _, _, address = info
            ip = address[0] if family == socket.AF_INET else address[0]
            ips.append(ip)
        ips.append(resolve(fqdn))
        return (list(set(ips)))

    except socket.gaierror:
        # Ca arrive quand il n'y a pas de domain
        return(None)

def testuri(url):
    #  valide que l'uri donneé est bien comme il faut
    pattern = r'https:\/\/check-host.net\/check-report\/[a-z0-9]{12}+'
    if re.match(pattern,url):
        return True
    return False


def checkhost(url):
    # Effectuer la requête HTTP avec l'entête
    response = requests.get(url, headers=headers)

    # Vérifier que la requête a réussi
    if response.status_code == 200:
        # Analyser l'HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Utiliser une expression régulière pour extraire le FQDN
        # pattern = '<h1>.*<div class="inline-block"><span(?: id="[a-z_]+")? class="break-all bg-neutral-200 px-1"(?: id="[a-z_]+")?>(?:http[s]?:\/\/)?([a-z0-9_\-.]+?)(?::[0-9]+\/?)?<\/span><\/div><\/h1>'
        pattern = '<h1>.*<div class="inline-block"><span(?: id="[a-z_]+")? class="break-all bg-neutral-200 px-1"(?: id="[a-z_]+")?>(?:http[s]?:\/\/)?([a-z0-9_\-.]+?)(?::[0-9]+\/?)?(?:\/.*)?<\/span><\/div><\/h1>'
        match = re.search(pattern, str(soup))
        if match:
            fqdn = match.group(1)
            return(fqdn)
        else:
            return(None)
    else:
        print("Error statut :", response.status_code)
        return(None)


# Functions
def getparam(count):
    """Retrieve the parameters appended """
    if len(sys.argv) != count + 1:
        print('My command')
        print('To Use: %s my params' % sys.argv[0])
        sys.exit(1)
    else:
        return sys.argv[1]


# Main Code #####
def main():
    param = getparam(1)
    if testuri(param):
        fqdn = checkhost(param)
        if fqdn:
            ips = resolveall(fqdn)
            target = { "fqdn":fqdn, "ips":ips}
            print(target)
        else:
            print("Check Host URI not found")

if __name__ == '__main__':
    main()
