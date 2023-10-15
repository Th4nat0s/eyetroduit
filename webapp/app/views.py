from flask import render_template, jsonify, request, Response
# from flask import Flask, jsonify, render_template, request, send_file
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, BaseView
from flask_appbuilder.api import expose
from flask_appbuilder.models.decorators import renders

from . import appbuilder, db
from .models import Groups, Comms, Tags, Medias, Tools, Victims, Configs, ApiKeys
from .lib import adb, getandparse

from flask_appbuilder import IndexView
import os
import json

class VictimsView(ModelView):
    datamodel = SQLAInterface(Victims)
    list_columns = ['timestamp', 'host', 'country', 'Filename']
    base_order = ('timestamp', 'desc()')

    @expose('/conf_download/<filename>')
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

class ApiKeysView(ModelView):
    datamodel = SQLAInterface(ApiKeys)

class ToolsView(ModelView):
    datamodel = SQLAInterface(Tools)
class MediasView(ModelView):
    datamodel = SQLAInterface(Medias)
class TagsView(ModelView):
    datamodel = SQLAInterface(Tags)
    list_columns = ['tname','groups']

class CommsView(ModelView):
    datamodel = SQLAInterface(Comms)
    list_columns = ['comm_group','last_seen','link', 'media', 'eyetelex']
class GroupsView(ModelView):
    label_columns = {'name': 'Groups Name', 'comm': 'Links'}
    list_columns = ['name','tags', 'comm']
    datamodel = SQLAInterface(Groups)

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
appbuilder.add_view( MediasView, "Comm Source", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( GroupsView, "Groups Management", icon="fa-folder-open-o", category="Groups"    )
appbuilder.add_view( CommsView, "Communication Sources", icon="fa-folder-open-o", category="Groups"    )
appbuilder.add_view( VictimsView, "Victims", icon="fa-folder-open-o", category="DDoSia"    )
appbuilder.add_view( ConfigsView, "Configs", icon="fa-folder-open-o", category="DDoSia"    )

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
