from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi

from . import appbuilder, db
from .models import Groups, Comms, Tags, Medias, Tools

class ToolsView(ModelView):
    datamodel = SQLAInterface(Tools)
class MediasView(ModelView):
    datamodel = SQLAInterface(Medias)
class CommsView(ModelView):
    datamodel = SQLAInterface(Comms)
    list_columns = ['comm_group','link', 'media']
class TagsView(ModelView):
    datamodel = SQLAInterface(Tags)
    list_columns = ['tname','groups']
class GroupsView(ModelView):
    label_columns = {'name': 'Groups Name', 'comm': 'Links'}
    list_columns = ['name','tags', 'comm']
    # list_columns = ['name', 'tags.tname']  # Utilisez 'tags.tname' pour afficher le nom du tag du groupe

    datamodel = SQLAInterface(Groups)


#class ProductTypeView(ModelView):
#    datamodel = SQLAInterface(group)
#    related_views = [ProductView]

appbuilder.add_view( ToolsView, "Tools Management", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( TagsView, "Tags Management", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( MediasView, "Comm Source", icon="fa-folder-open-o", category="Config"    )
appbuilder.add_view( GroupsView, "Groups Management", icon="fa-folder-open-o", category="Groups"    )
appbuilder.add_view( CommsView, "Comm. Chanels", icon="fa-folder-open-o", category="Groups"    )




@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
