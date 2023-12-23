#!/usr/bin/env python3
# coding=utf-8
import sys

from urllib.parse import urlparse, parse_qs
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

    uri2 = ["https://check-host.cc/report?u=417d7d7a-7baf-4e3f-8dfe-c6f56402a8f2",
            "https://check-host.cc/report?u=6ac73fd7-9be9-4766-a8e3-52a6b1e73da7",
            "https://check-host.net/check-report/12ccafb1ke1d",
            "https://check-host.net/check-report/12546cc8k366",
            "https://check-host.net/check-http?host=https://edupedia.co.il/&csrf_token=2cee683281373a371d43e65f5ca33ecfd14cccd1",
            "https://check-host.net/check-http?csrf_token=be5001c1c945a1cb7e488ea94cc9db38ba5bcaef&host=https://police.gov.in"]

    '''
            si c'est check-report on le mange direct.
            Si c'est check-http on récupère quele parameter host on gicle le reste.
            Si c'est .cc/report on recuper le "u".
    '''


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
    # pattern = r'https:\/\/check-host.net\/check-report\/[a-z0-9]{12}+'
    pattern = r"((https?:\/\/)?check-host.(net|cc)\/(check-report\/[a-z0-9]{12}+|check-http\?(host|csrf_token)=[\w\d:\.\/%]*&(host|csrf_token)=[\w\d:\.\/%]*|report\?u=[\da-f\-]*))"
    if re.match(pattern,url):
        return True
    return False


def checkhost_type1(url):
    # Traite ca 'https://check-host.net/check-report/12d104abkc75'
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

def checkhost_type2(url):
    # https://check-host.cc/rest/V2/report?reportuuid=3fb64ba4-a46b-4a38-b5b5-9fefdb0ef2ff for detail
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if 'u' in query_params:
        u_value = query_params['u'][0]
        response = requests.get(f'https://check-host.cc/report?u={u_value}', headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            link_element = [a['href'] for a in soup.find_all('a', href=True)]
            link_element = link_element[1]
            # Extraire l'URL du lien (href)
            if link_element:
                parsed_url = urlparse(link_element)
                fqdn = f"{parsed_url.netloc}"
                return(fqdn)
    return (None)


def checkhost_type3(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'host' in query_params:
        host =  query_params['host'][0]
        # Défois on a un host defois une url
        if host.startswith('http'):
            parsed_url = urlparse(host)
            fqdn = f"{parsed_url.netloc}"
            return(fqdn)
        return(host)
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


'''
# checkhost2uri
# Step 1 detect quel type c'est
# Step 2 resolve URI
# Step 3 resolve IP for URI
# Return { fqdn }

    type 1 https://check-host.net/check-report/12ccafb1ke1d",
    type 2 https://check-host.cc/report?u=417d7d7a-7baf-4e3f-8dfe-c6f56402a8f2",
    type 3 https://check-host.net/check-http?host=https://edupedia.co.il/&csrf_token=2cee683281373a371d43e65f5ca33ecfd14cccd1",

    type 1, scrap site for data (html)
    type 2, scrap site ( json )
    type 3, parse "host" in query host=".*"& -> url decode

'''
def checkhost2fqdn(link):
    # Determine the Domain checkhost type
    # Then call the right parser.
    ch_type = checkhost_type1
    type1 = re.match(r'https?://check-host\.net/check-report', link)
    if not type1:
        ch_type = checkhost_type2
        type2 = re.match(r'https?://check-host\.cc/', link)
        if not type2:
            ch_type = checkhost_type3
            type3 = re.match(r'https?://check-host\.net/check-http', link)
            if not type3:
                raise ('Error Unknown CheckHost URL')
    # print(ch_type)
    return(ch_type(link))


# Main Code #####
def main():
    param = getparam(1)
    if testuri(param):
        fqdn = checkhost2fqdn(param)
        if fqdn:
            ips = resolveall(fqdn)
            target = { "fqdn":fqdn, "ips":ips}
            print(target)
        else:
            print("Check Host URI not found")

if __name__ == '__main__':
    main()
