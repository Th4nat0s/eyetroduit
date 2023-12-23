from flask import render_template, jsonify, request, Response
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, BaseView, has_access
from flask_appbuilder.api import expose
from flask_appbuilder.models.decorators import renders
from sqlalchemy.exc import IntegrityError
from flask_appbuilder.models.filters import BaseFilter
from flask_appbuilder.actions import action
from flask import redirect

from . import appbuilder, db
from .models import Groups, Comms, Tags, Medias, Tools, Victims, Configs, ApiKeys, Hashts
from .models import CheckhostVictims, ClaimedVictims
from .lib import adb, getandparse, util, checkhost

from flask_appbuilder import IndexView
import re
import os
import json
import tldextract
from datetime import datetime

def valid_time_format(string):
    format_attendu = "%Y-%m-%d %H:%M:%S"
    try:
        datetime.strptime(string, format_attendu)
        return True
    except ValueError:
        return False


# DDOSIA affichage des dernieres cibles
class VictimsView(ModelView):
    datamodel = SQLAInterface(Victims)
    list_columns = ['timestamp', 'host', 'country', 'Filename']
    base_order = ('timestamp', 'desc()')
    label_columns = {'timestamp': 'Timestamp UTC'}

    # Route qui file la last conf, need apikey
    # accessible par tout le monde

    # curl -X POST -d "api_key=votre_api_key" https://..../victimsview/ddosia_last_conf
    @expose('/ddosia_last_conf', methods=['POST'])
    def last_conf(self):
        key = request.form.get('api_key')
        if not key:
            return jsonify({'error': 'Not Found'}), 404  # je dis pas apikey invalid sinon un pentest me fera chier.
        # check Api KEy
        db.session.query(Victims.filename).order_by(Victims.timestamp.desc()).first()
        auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()

        if auth_valid:
            # determine last config file
            filename = db.session.query(Victims.filename).order_by(Victims.timestamp.desc()).first()
            file_path = db.app.config.get('DDOSIA')
            file_path = os.path.join(file_path, filename[0])
            if os.path.isfile(file_path):
                # Chargez le contenu du fichier JSON
                with open(file_path, 'r') as json_file:
                    json_data = json.load(json_file)
                json_str = json.dumps(json_data, indent=4)
                response = Response(json_str, content_type='application/json; charset=utf-8')
                response.status_code = 200  # Code de statut HTTP OK
            return response
        return jsonify({'error': 'Not Found'}), 404


    @expose('/conf_download/<filename>')
    @has_access  # toute personne authentifiée
    def conf_download(self, filename):
        est_valide = lambda filename: all(c in "0123456789abcdefghijklmnopqrstuvwxyz_. " for c in filename)
        file_path = db.app.config.get('DDOSIA')
        file_path = os.path.join(file_path, filename)

        if os.path.isfile(file_path) and est_valide:
            # Chargez le contenu du fichier JSON
            with open(file_path, 'r') as json_file:
                json_data = json.load(json_file)

            # Renvoyez une réponse JSON basée sur le contenu du fichier
            # j'utilise pas jsonify mais json.dumps() 
            # avec l'argument indent pour formater la réponse JSON
            json_str = json.dumps(json_data, indent=4)

            # Créez une réponse Flask avec la chaîne JSON formatée
            response = Response(json_str, content_type='application/json; charset=utf-8')
            response.status_code = 200  # Code de statut HTTP OK

            return response
            # return jsonify(json_data, indent=4)
        else:
            # Gérez le cas où le fichier n'existe pas
            return jsonify({'error': 'Not Found'}), 404


class ConfigsView(ModelView):
    datamodel = SQLAInterface(Configs)
    list_columns = ['timestamp', 'md5', 'download']
    base_order = ('timestamp', 'desc()')
class ApiKeysView(ModelView):
    datamodel = SQLAInterface(ApiKeys)
    list_columns = ['key','active']
class ToolsView(ModelView):
    datamodel = SQLAInterface(Tools)
    list_columns = ['toolname','groups']



# Affichage des type de media (twitter , telegram etc )
# Panneau de configuration 
class MediasView(ModelView):
    datamodel = SQLAInterface(Medias)
    list_columns = ['mname','comm']
    label_columns = {'mname': 'Media', 'comm': 'Links'}

    # curl -X POST -d "api_key=votre_api_key" https://..../mediasview/api_get_telegram_job
    @expose('/api_get_telegram_job', methods=['POST'])
    def api_get_telegram_job(self):
        '''
            Get all the groups à Sucer, en telegram
        '''

        # validate key
        key = request.form.get('api_key')
        if not key:
            return jsonify({'job': []}), 401
        auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            # get telegram ID
            media = db.session.query(Medias).filter(Medias.mname == "Telegram").first()
            links = db.session.query(Comms.link).filter(Comms.eyetelex == True, Comms.media==media).all()
            # convertis en array
            olinks = []

            # Split sur le last / pour faire plaisir à dave
            for link in links:
                nom = util.lnk2tel(link[0]) # Get short name
                olinks.append(nom)
            return jsonify({'job': olinks}), 200  # je dis pas apikey invalid sinon un pentest me fera chier.
        return jsonify({'job': []}), 401


    '''
    curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "uri": "Xurl", "datetime": "2023-10-11 16:07:34"}' \
    http://127.0.0.1:5000/mediasview/api_time_media

    Format de temps YYYY-MM-DD HH:MM.SS
    '''
    @expose('/api_time_media', methods=['POST'])
    def api_time_media(self):
        '''
        Route API pour ajouter un nouveau lien dans la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()

        # check minima
        if 'api_key' in data and 'uri' in data and 'datetime' in data:
            key = data['api_key']
        # check Api KEy
        auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            uri = data['uri']
            date = data['datetime']

            urlo = db.session.query(Comms).filter(Comms.link==uri).first() # Find the url
            if not urlo:
                return jsonify({'error': 'media not found'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.

            # Check le format de time "2023-10-11 16:07:34"
            if not valid_time_format(date):
                return jsonify({'error': 'datetime invalid'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.

            # Arrivé ici c'est bon, update du last message
            urlo.last_seen = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            # bon maintenant on choppe le group relatif a cet url
            if urlo.comm_group:
                urlo.comm_group.last_seen =  datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            db.session.commit()
            return jsonify({'success': 'Timestamp added'}), 200
        return jsonify({'error': 'Invalid API token'}), 401


    # curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "uri": "urlX", "type": "Telegram"}' http://127.0.0.1:5000/mediasview/api_add_media
    @expose('/api_add_media', methods=['POST'])
    def add_media(self):
        '''
        Route API pour ajouter un nouveau lien dans la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()

        # check minima
        if 'api_key' in data and 'uri' in data and 'type' in data:
            key = data['api_key']
        # check Api KEy
        auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            uri = data['uri']
            media_type = data['type']
            media = db.session.query(Medias).filter(Medias.mname == media_type).first()
            if not media:
                return jsonify({'error': 'Not added, Uknow type'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.
            new_tag = db.session.query(Tags).filter(Tags.tname == "New").first() # Recupere pour tagger les "New"
            new_comm = Comms(link=uri, eyetelex=False, media=media, tags=[new_tag] )  # Create new record
            db.session.add(new_comm)
            try:
                # save l'objet
                db.session.commit()
            except IntegrityError as e:
                # Si pas content, c'est déja existant , on rollbck
                db.session.rollback()
                return jsonify({'error': 'Not added, Already present'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.
            return jsonify({'sucess': 'source added'}), 200  # je dis pas apikey invalid sinon un pentest me fera chier.
        else:
            return jsonify({'error': 'Not added, invalid api key'}), 401  # je dis pas apikey invalid sinon un pentest me fera chier.

class HashtsView(ModelView):
    datamodel = SQLAInterface(Hashts)
    list_columns = ['name','count','last_seen','repr_links']
    label_columns = {'name': 'HashTag', 'last_seen': 'Last Seen (UTC)', 'repr_links': 'Links'}
    base_order = ('last_seen', 'asc()')
    list_title = "List HashTags"
    show_title = "View HashTag"
    edit_title = "Edit HastTag"
    add_title = "Add HashTag"

    list_template = 'list_hasht.html'



    # curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "hashtag": "#free-mandela", "count": 5, "channels": ["Telegram","Truc"]}' http://127.0.0.1:5000/hashtsview/api_upd_hashtag
    @expose('/api_upd_hashtag', methods=['POST'])
    def add_media(self):
        '''
        Route API pour updater un Hashtag
            api_key = la clef
            hashtag = le hashtag
            count = combien de fois il a été vu
            channel = les channels ou il a été vu

            # perte de combien de fois par channel il a été vu... a traiter un jour.
            # la on compte juste la popularité d'un tag, pas ou il est populaire encore.

            name =  Column(String(150), unique = True, nullable=False)
            count = Column(Integer, default = 0)
            first_seen = Column(DateTime, default=func.now())
            last_seen = Column(DateTime, default=func.now())
            comms = relationship("Comms", secondary='hasht_comm_association', back_populates="hashts")

        '''
        # Récupérez le JSON
        data = request.get_json()

        # check minima
        if 'api_key' in data and 'hashtag' in data and 'channels' in data and 'count' in data:
            key = data['api_key']
        # check Api KEy
        auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid and type(data['count']==int):
            # récupère les channel qu'on cherche.
            # todo check if channel est une list
            dbchannels = []
            for uri in data['channels']:
                uri = f"https://t.me/{uri}"
                urlo = db.session.query(Comms).filter(Comms.link==uri).first() # Find the url
                if urlo:
                    dbchannels.append(urlo)
                else:
                    # arrivé là c'est une URL que je ne connais pas qu'on me reporte... créons là.
                    pass

            # Add dans la db, le hashtag
            new_hashtag = Hashts(name=data['hashtag'], count=data['count'], comms=dbchannels )  # Create new record
            db.session.add(new_hashtag)
            try:
                # save l'objet
                db.session.commit()
            except IntegrityError as e:
                # Si pas content, c'est déja existant , on rollbck, et on update l'object exitstant
                db.session.rollback()
                exist_hashtag = db.session.query(Hashts).filter(Hashts.name == data['hashtag']).first()
                exist_hashtag.count += data['count']
                exist_hashtag.last_seen =  datetime.now().replace(microsecond=0)  # Grande question, doit t'on passer l date dans le jison
                exist_hashtag.comms += dbchannels  # Le pipe sort unqi est fait magiquement
                db.session.commit()
            return jsonify({'success': 'hashtag updated'}), 200 
        else:
            return jsonify({'error': 'Not changes, invalid api key'}), 401


class TagsView(ModelView):
    datamodel = SQLAInterface(Tags)
    list_columns = ['tname','groups']
    label_columns = {'tname': 'Tags', 'group': 'Groups name'}
    base_order = ('tname', 'asc()')
    label = 'Hash Tags seen in Channels (Daily Updated)'

# Affichage des URL (telegram etc... )
# Listing des URL Collectées et suivies
class CommsView(ModelView):
    datamodel = SQLAInterface(Comms)
    list_columns = ['comm_group','alltags', 'last_seen','nice_link', 'media', 'nice_eyetelex']
    label_columns = {'comm_group': 'Groups Name', 'nice_link': 'Links', 'alltags': 'Tags', 'nice_eyetelex': 'Fetch'}
    base_order = ('comm_group.name', 'asc()')
    list_template = 'list_comm.html'

    list_title = "List Links"
    show_title = "View Link"
    edit_title = "Edit Link"
    add_title = "Add Link"

    # action to allow pick and delete in the list
    @action("muldelete", "&nbsp;Delete", "Delete selection ?", "fa-trash-alt", single=True)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())


class GroupsView(ModelView):
    label_columns = {'name': 'Groups Name', 'nice_comms': 'Links', 'nice_tags': 'Tags'}
    list_columns = ['name','nice_tags', 'nice_comms']
    base_order = ('name', 'asc()')
    datamodel = SQLAInterface(Groups)


class CheckhostVictimsView(ModelView):
    label_columns = {'chekhost': 'Ddos check ID', 'checkhostvictim_comm': 'Links'}
    list_columns = ['timestamp','checkhost', 'host','checkhostvictim_comm' ]
    base_order = ('checkhost', 'asc()')
    datamodel = SQLAInterface(CheckhostVictims)


    '''
    $ curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "count": 1 }' http://127.0.0.1:5000/checkhostvictimsview/api_process_checkhost_victim

    Api simple, qui traine "N" report de checkhost victim et scrap checkhostvictim pour la resolution
    Doit etre crontabé quelque part.. pour faire faier le taff a la db
    '''
    @expose('/api_process_checkhost_victim', methods=['POST'])
    def api_process_checkhost_victim(self):
        '''
        Route API pour processer les victimes de DDOS la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()
        auth_valid = None

        # check minima
        if 'api_key' in data and 'count' in data:
            key = data['api_key']
            # check Api KEy
            auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            count = data['count']
            count = int(count)  # surement mieux a faire pour s'assurer d'un INT
            if count > 50: # Hard limit
                count = 50
            # Arrivé ici on sais combien on va en traiter.
            candidates = db.session.query(CheckhostVictims).filter(CheckhostVictims.status == 0).limit(count)
            if candidates: # parce que ptet y a rien a faire....
                for candidate in candidates:
                    try:
                        host = checkhost.checkhost2fqdn(candidate.checkhost)
                        candidate.domain = tldextract.extract(host).domain + "." + tldextract.extract(host).suffix # Get domain info
                        ips = checkhost.resolveall(host)
                        candidate.host = host
                        if ips: # resoud lat long de la première IP qu'on vois.
                            first_ip = ips[0]
                            print (first_ip)
                            geoinfo = getandparse.ip2geo(first_ip)
                            candidate.country = geoinfo.country.name
                            candidate.lat = geoinfo.location.latitude
                            candidate.lon =  geoinfo.location.longitude
                        candidate.ip = ', '.join(ips)
                        candidate.status = 2  # Code 2 all good
                    except:
                        # Resolution ratée, mais testé on passe en code 1
                        candidate.status = 1
                    db.session.commit()

            return jsonify({'success': 'DDOS report updated'}), 200
        else:
            return jsonify({'error': 'No changes, invalid api key'}), 401



    '''
    $ curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "channel": "Indian_Cyber_Force_Official" ,"checkhost": "https://check-host.net/check-report/idcheckhosturl", "datetime": "2023-10-11 16:07:34"}'     http://127.0.0.1:5000/checkhostvictimsview/api_checkhost_victim

    Format de temps YYYY-MM-DD HH:MM.SS
    Format des noms de channel telegram "court"
    '''
    @expose('/api_checkhost_victim', methods=['POST'])
    def api_checkhost_victim(self):
        '''
        Route API pour ajouter un nouveau lien DDOS dans la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()
        auth_valid = None

        # check minima
        if 'api_key' in data and 'channel' in data and 'datetime' in data and 'checkhost' in data:
            key = data['api_key']
            # check Api KEy
            auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            checkhost = data['checkhost']
            uri = data['channel']
            date = data['datetime']


            # Retrouvons le channel de comm dont on parle
            uri = f"https://t.me/{uri}"
            urlo = db.session.query(Comms).filter(Comms.link==uri).first() # Find the url
            if not urlo:
                return jsonify({'error': 'media not found'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.

            # Check le format de time "2023-10-11 16:07:34"
            if not valid_time_format(date):
                return jsonify({'error': 'datetime invalid'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.

            # Il y a 3 type de check-host possible
            '''
            "https://check-host.cc/report?u=417d7d7a-7baf-4e3f-8dfe-c6f56402a8f2"
            "https://check-host.cc/report?u=6ac73fd7-9be9-4766-a8e3-52a6b1e73da7"

            "https://check-host.net/check-report/12ccafb1ke1d"
            "https://check-host.net/check-report/12546cc8k366"

            "https://check-host.net/check-http?host=https://edupedia.co.il/&csrf_token=2cee683281373a371d43e65f5ca33ecfd14cccd1"
            "https://check-host.net/check-http?host=https://police.gov.in/&csrf_token=be5001c1c945a1cb7e488ea94cc9db38ba5bcaef"

            si c'est check-report on le mange direct.
            Si c'est check-http on récupère quele parameter host on gicle le reste.
            Si c'est .cc/report on recuper le "u".
            '''
            # check du format de "checkhost"
            val_pattern = re.compile(r"((https?:\/\/)?check-host.(net|cc)\/(check-report\/[a-z0-9]{12}+|check-http\?(host|csrf_token)=[\w\d:\.\/%]*&(host|csrf_token)=[\w\d:\.\/%]*|report\?u=[\da-f\-]*))")
            # pattern = re.compile(r'^https:\/\/check-host\.net\/check-report\/.*$')
            if not val_pattern.match(checkhost):
                # check du format de "checkhost"
                return jsonify({'error': 'Invalid CheckHost url'}), 400


            # Arrivé ici, est-ce que ce record est déja enregistré
            # Same time, Same chan, Same Checkhost

            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            existing = db.session.query(CheckhostVictims).filter(CheckhostVictims.checkhost == checkhost, CheckhostVictims.timestamp == date, CheckhostVictims.checkhostvictim_comm==urlo).first()
            print (existing)
            if existing:
                return jsonify({'error': 'This event is already reported'}), 400

            # Arrivé ici c'est bon, ajout du DDOS record
            new_ddos = CheckhostVictims(timestamp=date, checkhost=checkhost, checkhostvictim_comm=urlo)  # Create new record
            db.session.add(new_ddos)
            try:
                # save l'objet
                db.session.commit()
            except IntegrityError as e:
                # Si pas content, c'est déja existant , on rollbck, et on update l'object exitstant
                db.session.rollback()
                return jsonify({'success': 'Error registering DDOS'}), 200
            return jsonify({'success': 'DDOS report updated'}), 200 
        else:
            return jsonify({'error': 'No changes, invalid api key'}), 401


# View des rapports de site de reward
class ClaimedVictimsView(ModelView):
    label_columns = {'reference': 'Claim Location', 'adversary': 'Adversary'}
    list_columns = ['timestamp','reference', 'host','adversary']
    base_order = ('timestamp', 'asc()')
    datamodel = SQLAInterface(ClaimedVictims)

    '''

    $ curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "adversary": "Tomodashi" ,"target": "https://perdu.com" , "reference": "https://mirror-h.org/zone/5563973/" , "datetime": "2023-10-11 16:07:34", "source": 6}' http://127.0.0.1:5000/claimedvictimsview/api_claimed_victim

    Format de temps YYYY-MM-DD HH:MM.SS
 
    Source is the ID of eyetroduit/mediasview (should be created first)
    # 5 : Ownzyou
    # 6 : mirror-h

    '''
    @expose('/api_claimed_victim', methods=['POST'])
    def api_claimed_victim(self):
        '''
        Route API pour ajouter une nouvelle victime dans la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()
        auth_valid = None

        # check minima
        if 'api_key' in data and 'adversary' in data and 'datetime' in data and 'reference' in data and 'target' in data and 'source' in data:
            key = data['api_key']
            # check Api KEy
            auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            # Check le format de time "2023-10-11 16:07:34"
            if not valid_time_format(data['datetime']):
                return jsonify({'error': 'datetime invalid'}), 400  # je dis pas apikey invalid sinon un pentest me fera chier.

            # Arrivé ici, est-ce que ce record est déja enregistré
            # Same time, Same chan
            date = datetime.strptime(data['datetime'], "%Y-%m-%d %H:%M:%S")
            existing = db.session.query(ClaimedVictims).filter(ClaimedVictims.fullurl == data['target'], ClaimedVictims.timestamp == date).first()
            if existing:
                return jsonify({'error': 'This event is already reported'}), 400

            # Récupération de la source
            source = db.session.query(Medias).filter(Medias.id == data['source']).first()
            if not source:
                return jsonify({'error': 'This source not found'}), 400


            # Arrivé ici c'est bon, ajout du Claim record
            new_victim = ClaimedVictims(timestamp=date, media=source, fullurl=data['target'], adversary=data['adversary'], reference=data['reference'] )  # Create new record
            db.session.add(new_victim)
            try:
                # save l'objet
                db.session.commit()
            except IntegrityError as e:
                # Si pas content, c'est déja existant , on rollbck, et on update l'object exitstant
                db.session.rollback()
                return jsonify({'success': 'Error registering Victim'}), 200
            return jsonify({'success': 'Victim report updated'}), 200
        else:
            return jsonify({'error': 'No changes, invalid api key'}), 401


    '''
    $ curl -X POST -H "Content-Type: application/json" -d '{"api_key": "zoubida", "count": 1 }' http://127.0.0.1:5000/claimedvictimsview/api_process_claimed_victim

    Api simple, qui traine "N" report de checkhost victim et scrap checkhostvictim pour la resolution
    Doit etre crontabé quelque part.. pour faire faier le taff a la db
    '''
    @expose('/api_process_claimed_victim', methods=['POST'])
    def api_process_claimed_victim(self):
        '''
        Route API pour processer les victimes de DDOS la db automagiquement.
        '''
        # Récupérez le JSON
        data = request.get_json()
        auth_valid = None

        # check minima
        if 'api_key' in data and 'count' in data:
            key = data['api_key']
            # check Api KEy
            auth_valid = db.session.query(ApiKeys).filter(ApiKeys.key == key, ApiKeys.active == True).first()
        if auth_valid:
            count = data['count']
            count = int(count)  # surement mieux a faire pour s'assurer d'un INT
            if count > 50: # Hard limit
                count = 50
            # Arrivé ici on sais combien on va en traiter.
            candidates = db.session.query(ClaimedVictims).filter(ClaimedVictims.status == 0).limit(count)
            print (candidates)
            if candidates: # parce que ptet y a rien a faire....
                for candidate in candidates:
                    try:
                        candidate.domain = tldextract.extract(candidate.fullurl).domain + "." + tldextract.extract(candidate.fullurl).suffix # Get domain info
                        prefix = tldextract.extract(candidate.fullurl).subdomain
                        if prefix:
                            host = tldextract.extract(candidate.fullurl).subdomain +"."+ candidate.domain
                        else:
                            host = candidate.domain
                        ips = checkhost.resolveall(host)
                        print( host )
                        print (ips)
                        candidate.host = host
                        if ips: # resoud lat long de la première IP qu'on vois.
                            first_ip = ips[0]
                            print (first_ip)
                            geoinfo = getandparse.ip2geo(first_ip)
                            candidate.country = geoinfo.country.name
                            candidate.lat = geoinfo.location.latitude
                            candidate.lon =  geoinfo.location.longitude
                        candidate.ip = ', '.join(ips)
                        candidate.status = 2  # Code 2 all good
                    except:
                        # Resolution ratée, mais testé on passe en code 1
                        candidate.status = 1
                    db.session.commit()

            return jsonify({'success': 'DDOS report updated'}), 200
        else:
            return jsonify({'error': 'No changes, invalid api key'}), 401




class api(BaseView):
    @expose('/push', methods=['POST'])
    def push(self):
        try:
            data = request.get_json()  # Récupère le JSON de la requête
            # bon si y a un random dedans ok seens legit je le suce
            if data.get("randoms") and data.get("metadata"):
                if adb.valid_key_push(data.get("metadata").get("api_key")):
                    time_json = data.get("metadata").get("timestamp")
                    del data["metadata"] # purge metadata from json
                    if adb.notindb(data, time_json):
                        parsed_data = getandparse.parse_report(data, time_json) # Parse victims for db insert
                        del data["metadata"] # purge metadata from json (mis pare parse _repot #todo)
                        adb.save(parsed_data, time_json) # Save victims in db.
                        getandparse.file_save(data, time_json) # Save the config in the repo
                        adb.savemd5(data, time_json)
                        return jsonify({"message": "JSON Stored", "data": True}), 200
                    return jsonify({"message": "JSON already Stored", "data": False}), 200
                return jsonify({"message": "Invalid Api Key", "data": False}), 200
        except Exception as e:
            print(str(e))
            return jsonify({"error": str(e)}), 400



appbuilder.add_view( ApiKeysView, "Api Key Management", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( ToolsView, "Tools Management", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( TagsView, "Tags Management", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( MediasView, "Comm. Source", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( GroupsView, "Groups Management", icon="fa-folder-open-o", category="Groups"    )
appbuilder.add_view( CommsView, "Comm. Links", icon="fa-folder-open-o", category="Groups" )
appbuilder.add_view( HashtsView, "HashTags", icon="fa-folder-open-o", category="Groups"    )
appbuilder.add_view( VictimsView, "DDosia Victims", icon="fa-folder-open-o", category="DDoS"    )
appbuilder.add_view( ConfigsView, "DDosia Configs", icon="fa-folder-open-o", category="DDoS"    )
appbuilder.add_view( CheckhostVictimsView, "Telegram reports", icon="fa-folder-open-o", category="DDoS"    )
appbuilder.add_view( ClaimedVictimsView, "Hacking Claim", icon="fa-folder-open-o", category="Web Monitoring"    )


# Active les liens d'export sans faire de menu
appbuilder.add_view_no_menu(api())



@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
