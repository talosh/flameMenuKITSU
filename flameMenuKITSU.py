'''
flameMenuKITSU
Flame 2023 and higher
written by Andrii Toloshnyy
andriy.toloshnyy@gmail.com
'''

import os
import sys
import time
import threading
import atexit
import inspect
import re
from pprint import pprint
from pprint import pformat

__version__ = 'v0.0.1 dev 002'

menu_group_name = 'KITSU'
app_name = 'flameMenuKITSU'
DEBUG = True


default_templates = {
# Resolved fields are:
# {Sequence},{sg_asset_type},{Asset},{Shot},{Step},{Step_code},{name},{version},{version_four},{frame},{ext}
# {name} and {version} (or {version_four}) are taken from the clip name or from Batch name and number of Batch itertations as a fallback.
# EXAMPLE: There are 9 batch iterations in batch group.
# Any of the clips named as "mycomp", "SHOT_001_mycomp", "SHOT_001_mycomp_009", "SHOT_001_mycomp_v009"
# Would give us "mycomp" as a {name} and 009 as {version}
# Version number padding are default to 3 at the moment, ### style padding is not yet implemented
# Publishing into asset will just replace {Shot} fied with asset name
'Shot': {
    'flame_render': {
        'default': 'sequences/{Sequence}/{Shot}/{Step}/publish/{Shot}_{name}_v{version}/{Shot}_{name}_v{version}.{frame}.{ext}',
        'PublishedFileType': 'Flame Render'
        },
    'flame_batch': {
        'default': 'sequences/{Sequence}/{Shot}/{Step}/publish/flame_batch/{Shot}_{name}_v{version}.batch',
        'PublishedFileType': 'Flame Batch File'                  
        },
    'version_name': {
        'default': '{Shot}_{name}_v{version}',
    },
    'fields': ['{Sequence}', '{Shot}', '{Step}', '{Step_code}', '{name}', '{version}', '{version_four}', '{frame}', '{ext}']
},
'Asset':{
    'flame_render': {
        'default': 'assets/{sg_asset_type}/{Asset}/{Step}/publish/{Asset}_{name}_v{version}/{Asset}_{name}_v{version}.{frame}.{ext}',
        'PublishedFileType': 'Flame Render'
        },
    'flame_batch': {
        'default': 'assets/{sg_asset_type}/{Asset}/{Step}/publish/flame_batch/{Asset}_{name}_v{version}.batch',
        'PublishedFileType': 'Flame Batch File'                  
        },
    'version_name': {
        'default': '{Asset}_{name}_v{version}',
    },
    'fields': ['{Sequence}', '{sg_asset_type}', '{Asset}', '{Step}', '{Step_code}', '{name}', '{version}', '{version_four}', '{frame}', '{ext}']
}}

default_flame_export_presets = {
    # {0: flame.PresetVisibility.Project, 1: flame.PresetVisibility.Shared, 2: flame.PresetVisibility.Autodesk, 3: flame.PresetVisibility.Shotgun}
    # {0: flame.PresetType.Image_Sequence, 1: flame.PresetType.Audio, 2: flame.PresetType.Movie, 3: flame.PresetType.Sequence_Publish}
    'Publish': {'PresetVisibility': 2, 'PresetType': 0, 'PresetFile': 'OpenEXR/OpenEXR (16-bit fp PIZ).xml'},
    'Preview': {'PresetVisibility': 3, 'PresetType': 2, 'PresetFile': 'Generate Preview.xml'},
    'Thumbnail': {'PresetVisibility': 3, 'PresetType': 0, 'PresetFile': 'Generate Thumbnail.xml'}
}


class flameAppFramework(object):
    # flameAppFramework class takes care of preferences

    class prefs_dict(dict):
        # subclass of a dict() in order to directly link it 
        # to main framework prefs dictionaries
        # when accessed directly it will operate on a dictionary under a 'name'
        # key in master dictionary.
        # master = {}
        # p = prefs(master, 'app_name')
        # p['key'] = 'value'
        # master - {'app_name': {'key', 'value'}}
            
        def __init__(self, master, name, **kwargs):
            self.name = name
            self.master = master
            if not self.master.get(self.name):
                self.master[self.name] = {}
            self.master[self.name].__init__()

        def __getitem__(self, k):
            return self.master[self.name].__getitem__(k)
        
        def __setitem__(self, k, v):
            return self.master[self.name].__setitem__(k, v)

        def __delitem__(self, k):
            return self.master[self.name].__delitem__(k)
        
        def get(self, k, default=None):
            return self.master[self.name].get(k, default)
        
        def setdefault(self, k, default=None):
            return self.master[self.name].setdefault(k, default)

        def pop(self, k, v=object()):
            if v is object():
                return self.master[self.name].pop(k)
            return self.master[self.name].pop(k, v)
        
        def update(self, mapping=(), **kwargs):
            self.master[self.name].update(mapping, **kwargs)
        
        def __contains__(self, k):
            return self.master[self.name].__contains__(k)

        def copy(self): # don't delegate w/ super - dict.copy() -> dict :(
            return type(self)(self)
        
        def keys(self):
            return self.master[self.name].keys()

        @classmethod
        def fromkeys(cls, keys, v=None):
            return self.master[self.name].fromkeys(keys, v)
        
        def __repr__(self):
            return '{0}({1})'.format(type(self).__name__, self.master[self.name].__repr__())

        def master_keys(self):
            return self.master.keys()

    def __init__(self):
        self.name = self.__class__.__name__
        self.bundle_name = 'flameMenuKITSU'
        # self.prefs scope is limited to flame project and user
        self.prefs = {}
        self.prefs_user = {}
        self.prefs_global = {}
        self.debug = DEBUG
        
        self.flame_project_name = 'UnknownFlameProject'
        self.flame_user_name = 'UnknownFlameUser'

        try:
            import flame
            self.flame = flame
            self.flame_project_name = self.flame.project.current_project.name
            self.flame_user_name = flame.users.current_user.name
        except:
            self.flame = None
        
        import socket
        self.hostname = socket.gethostname()
        
        if sys.platform == 'darwin':
            self.prefs_folder = os.path.join(
                os.path.expanduser('~'),
                 'Library',
                 'Caches',
                 self.bundle_name)
        elif sys.platform.startswith('linux'):
            self.prefs_folder = os.path.join(
                os.path.expanduser('~'),
                '.config',
                self.bundle_name)

        self.prefs_folder = os.path.join(
            self.prefs_folder,
            self.hostname,
        )

        self.log('[%s] waking up' % self.__class__.__name__)
        self.load_prefs()

        # menu auto-refresh defaults

        if not self.prefs_global.get('menu_auto_refresh'):
            self.prefs_global['menu_auto_refresh'] = {
                'media_panel': True,
                'batch': True,
                'main_menu': True
            }

        self.apps = []

    def log(self, message):
        print ('[%s] %s' % (self.bundle_name, message))

    def log_debug(self, message):
        if self.debug:
            print ('[DEBUG %s] %s' % (self.bundle_name, message))

    def load_prefs(self):
        import pickle
        
        prefix = self.prefs_folder + os.path.sep + self.bundle_name
        prefs_file_path = prefix + '.' + self.flame_user_name + '.' + self.flame_project_name + '.prefs'
        prefs_user_file_path = prefix + '.' + self.flame_user_name  + '.prefs'
        prefs_global_file_path = prefix + '.prefs'

        try:
            prefs_file = open(prefs_file_path, 'rb')
            self.prefs = pickle.load(prefs_file)
            prefs_file.close()
            self.log_debug('preferences loaded from %s' % prefs_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_file_path)
            self.log_debug(e)

        try:
            prefs_file = open(prefs_user_file_path, 'rb')
            self.prefs_user = pickle.load(prefs_file)
            prefs_file.close()
            self.log_debug('preferences loaded from %s' % prefs_user_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs_user))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_user_file_path)
            self.log_debug(e)

        try:
            prefs_file = open(prefs_global_file_path, 'rb')
            self.prefs_global = pickle.load(prefs_file)
            prefs_file.close()
            self.log_debug('preferences loaded from %s' % prefs_global_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs_global))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_global_file_path)
            self.log_debug(e)

        return True

    def save_prefs(self):
        import pickle

        if not os.path.isdir(self.prefs_folder):
            try:
                os.makedirs(self.prefs_folder)
            except:
                self.log('unable to create folder %s' % self.prefs_folder)
                return False

        prefix = self.prefs_folder + os.path.sep + self.bundle_name
        prefs_file_path = prefix + '.' + self.flame_user_name + '.' + self.flame_project_name + '.prefs'
        prefs_user_file_path = prefix + '.' + self.flame_user_name  + '.prefs'
        prefs_global_file_path = prefix + '.prefs'

        try:
            prefs_file = open(prefs_file_path, 'wb')
            pickle.dump(self.prefs, prefs_file)
            prefs_file.close()
            self.log_debug('preferences saved to %s' % prefs_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs))
        except Exception as e:
            self.log('unable to save preferences to %s' % prefs_file_path)
            self.log_debug(e)

        try:
            prefs_file = open(prefs_user_file_path, 'wb')
            pickle.dump(self.prefs_user, prefs_file)
            prefs_file.close()
            self.log_debug('preferences saved to %s' % prefs_user_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs_user))
        except:
            self.log('unable to save preferences to %s' % prefs_user_file_path)
            self.log_debug(e)

        try:
            prefs_file = open(prefs_global_file_path, 'wb')
            pickle.dump(self.prefs_global, prefs_file)
            prefs_file.close()
            self.log_debug('preferences saved to %s' % prefs_global_file_path)
            self.log_debug('preferences contents:\n' + pformat(self.prefs_global))
        except:
            self.log('unable to save preferences to %s' % prefs_global_file_path)
            self.log_debug(e)
            
        return True


class flameMenuApp(object):
    def __init__(self, framework):
        self.name = self.__class__.__name__
        self.framework = framework
        self.connector = None
        self.menu_group_name = menu_group_name
        self.debug = DEBUG
        self.dynamic_menu_data = {}

        # flame module is only avaliable when a 
        # flame project is loaded and initialized
        self.flame = None
        try:
            import flame
            self.flame = flame
        except:
            self.flame = None
        
        self.prefs = self.framework.prefs_dict(self.framework.prefs, self.name)
        self.prefs_user = self.framework.prefs_dict(self.framework.prefs_user, self.name)
        self.prefs_global = self.framework.prefs_dict(self.framework.prefs_global, self.name)

        from PySide2 import QtWidgets
        self.mbox = QtWidgets.QMessageBox()

    @property
    def flame_extension_map(self):
        return {
            'Alias': 'als',
            'Cineon': 'cin',
            'Dpx': 'dpx',
            'Jpeg': 'jpg',
            'Maya': 'iff',
            'OpenEXR': 'exr',
            'Pict': 'pict',
            'Pixar': 'picio',
            'Sgi': 'sgi',
            'SoftImage': 'pic',
            'Targa': 'tga',
            'Tiff': 'tif',
            'Wavefront': 'rla',
            'QuickTime': 'mov',
            'MXF': 'mxf',
            'SonyMXF': 'mxf'
        }
        
    def __getattr__(self, name):
        def method(*args, **kwargs):
            print ('calling %s' % name)
        return method

    def log(self, message):
        self.framework.log('[' + self.name + '] ' + str(message))

    def log_debug(self, message):
        self.framework.log_debug('[' + self.name + '] ' + str(message))

    def rescan(self, *args, **kwargs):
        if not self.flame:
            try:
                import flame
                self.flame = flame
            except:
                self.flame = None

        if self.flame:
            self.flame.execute_shortcut('Rescan Python Hooks')
            self.log_debug('Rescan Python Hooks')

    def get_export_preset_fields(self, preset):
        
        self.log_debug('Flame export preset parser')

        # parses Flame Export preset and returns a dict of a parsed values
        # of False on error.
        # Example:
        # {'type': 'image',
        #  'fileType': 'OpenEXR',
        #  'fileExt': 'exr',
        #  'framePadding': 8
        #  'startFrame': 1001
        #  'useTimecode': 0
        # }
        
        from xml.dom import minidom

        preset_fields = {}

        # Flame type to file extension map

        flame_extension_map = {
            'Alias': 'als',
            'Cineon': 'cin',
            'Dpx': 'dpx',
            'Jpeg': 'jpg',
            'Maya': 'iff',
            'OpenEXR': 'exr',
            'Pict': 'pict',
            'Pixar': 'picio',
            'Sgi': 'sgi',
            'SoftImage': 'pic',
            'Targa': 'tga',
            'Tiff': 'tif',
            'Wavefront': 'rla',
            'QuickTime': 'mov',
            'MXF': 'mxf',
            'SonyMXF': 'mxf'
        }

        preset_path = ''

        if os.path.isfile(preset.get('PresetFile', '')):
            preset_path = preset.get('PresetFile')
        else:
            path_prefix = self.flame.PyExporter.get_presets_dir(
                self.flame.PyExporter.PresetVisibility.values.get(preset.get('PresetVisibility', 2)),
                self.flame.PyExporter.PresetType.values.get(preset.get('PresetType', 0))
            )
            preset_file = preset.get('PresetFile')
            if preset_file.startswith(os.path.sep):
                preset_file = preset_file[1:]
            preset_path = os.path.join(path_prefix, preset_file)

        self.log_debug('parsing Flame export preset: %s' % preset_path)
        
        preset_xml_doc = None
        try:
            preset_xml_doc = minidom.parse(preset_path)
        except Exception as e:
            message = 'flameMenuSG: Unable parse xml export preset file:\n%s' % e
            self.mbox.setText(message)
            self.mbox.exec_()
            return False

        preset_fields['path'] = preset_path

        preset_type = preset_xml_doc.getElementsByTagName('type')
        if len(preset_type) > 0:
            preset_fields['type'] = preset_type[0].firstChild.data

        video = preset_xml_doc.getElementsByTagName('video')
        if len(video) < 1:
            message = 'flameMenuSG: XML parser error:\nUnable to find xml video tag in:\n%s' % preset_path
            self.mbox.setText(message)
            self.mbox.exec_()
            return False
        
        filetype = video[0].getElementsByTagName('fileType')
        if len(filetype) < 1:
            message = 'flameMenuSG: XML parser error:\nUnable to find video::fileType tag in:\n%s' % preset_path
            self.mbox.setText(message)
            self.mbox.exec_()
            return False

        preset_fields['fileType'] = filetype[0].firstChild.data
        if preset_fields.get('fileType', '') not in flame_extension_map:
            message = 'flameMenuSG:\nUnable to find extension corresponding to fileType:\n%s' % preset_fields.get('fileType', '')
            self.mbox.setText(message)
            self.mbox.exec_()
            return False
        
        preset_fields['fileExt'] = flame_extension_map.get(preset_fields.get('fileType'))

        name = preset_xml_doc.getElementsByTagName('name')
        if len(name) > 0:
            framePadding = name[0].getElementsByTagName('framePadding')
            startFrame = name[0].getElementsByTagName('startFrame')
            useTimecode = name[0].getElementsByTagName('useTimecode')
            if len(framePadding) > 0:
                preset_fields['framePadding'] = int(framePadding[0].firstChild.data)
            if len(startFrame) > 0:
                preset_fields['startFrame'] = int(startFrame[0].firstChild.data)
            if len(useTimecode) > 0:
                preset_fields['useTimecode'] = useTimecode[0].firstChild.data

        return preset_fields


class flameKitsuConnector(object):
    def __init__(self, framework):
        self.name = self.__class__.__name__
        self.app_name = app_name
        self.framework = framework
        self.connector = self
        self.log('waking up')

        self.prefs = self.framework.prefs_dict(self.framework.prefs, self.name)
        self.prefs_user = self.framework.prefs_dict(self.framework.prefs_user, self.name)
        self.prefs_global = self.framework.prefs_dict(self.framework.prefs_global, self.name)

        site_packages_folder = os.path.join(
            os.path.dirname(__file__),
            '.site-packages'
        )
        
        if not os.path.isdir(site_packages_folder):
            self.log('unable to find site packages folder at %s' % site_packages_folder)
            self.gazu = None
        else:
            sys.path.insert(0, site_packages_folder)
            import gazu
            self.gazu = gazu
            sys.path.pop(0)

        # defautl values are set here
        if not 'user signed out' in self.prefs_global.keys():
            self.prefs_global['user signed out'] = False
        

        self.user = None
        self.user_name = None

        if not self.prefs_global.get('user signed out', False):
            self.log_debug('requesting for user')
            try:
                self.get_user()
            except Exception as e:
                self.log_debug(pformat(e))

        self.flame_project = None
        self.linked_project = None
        self.linked_project_id = None
        self.pipeline_data = {}

        self.check_linked_project()

        self.loops = []
        self.threads = True
        self.loops.append(threading.Thread(target=self.cache_short_loop, args=(4, )))

        for loop in self.loops:
            loop.daemon = True
            loop.start()

        from PySide2 import QtWidgets
        self.mbox = QtWidgets.QMessageBox()

    def log(self, message):
        self.framework.log('[' + self.name + '] ' + str(message))

    def log_debug(self, message):
        self.framework.log_debug('[' + self.name + '] ' + str(message))

    def get_user(self, *args, **kwargs):
        # get saved credentials
        import base64
        self.gazu_client = None
        self.kitsu_host = self.prefs_user.get('kitsu_host', 'http://localhost/api/')
        self.kitsu_user = self.prefs_user.get('kitsu_user', 'user@host')
        self.kitsu_pass = ''
        encoded_kitsu_pass = self.prefs_user.get('kitsu_pass', '')
        if encoded_kitsu_pass:
            self.kitsu_pass = base64.b64decode(encoded_kitsu_pass).decode("utf-8")

        def login():
            try:
                host = self.kitsu_host                
                if not host.endswith('/api/'):
                    if self.kitsu_host.endswith('/'):
                        host = host + 'api/'
                    else:
                        host = host + '/api/'
                elif host.endswith('/api'):
                    host = host + ('/')

                self.gazu_client = self.gazu.client.create_client(host)
                self.gazu.log_in(self.kitsu_user, self.kitsu_pass, client = self.gazu_client)
                self.user = self.gazu.client.get_current_user(client = self.gazu_client)
                self.user_name = self.user.get('full_name')
                return True
            except Exception as e:
                pprint (e)
            return False

        while not login():
            credentials = self.login_dialog()
            print ('coming from login dialog')
            pprint (credentials)

            if not credentials:
                self.prefs_global['user signed out'] = True
                self.kitsu_pass = ''
                break
            else:
                self.kitsu_host = credentials.get('host')
                self.kitsu_user = credentials.get('user')
                self.kitsu_pass = credentials.get('password', '')

        # self.log_debug(pformat(self.user))
        self.log_debug(self.user_name)

        self.prefs_user['kitsu_host'] = self.kitsu_host
        self.prefs_user['kitsu_user'] = self.kitsu_user
        self.prefs_user['kitsu_pass'] = base64.b64encode(self.kitsu_pass.encode("utf-8"))
        self.framework.save_prefs()

    def clear_user(self, *args, **kwargs):
        try:
            self.gazu.log_out(client = self.gazu_client)
        except Exception as e:
            self.log(pformat(e))

        self.gazu_client = None
        self.user = None
        self.user_name = None
        self.prefs_user['kitsu_pass'] = ''
        self.framework.save_prefs()

    def login_dialog(self):
        from PySide2 import QtWidgets, QtCore

        self.kitsu_host_text = self.kitsu_host
        self.kitsu_user_text = self.kitsu_user
        self.kitsu_pass_text = self.kitsu_pass

        def txt_KitsuHost_textChanged():
            self.kitsu_host_text = txt_KitsuHost.text()
            # storage_root_paths.setText(calculate_project_path())

        def txt_KitsuUser_textChanged():
            self.kitsu_user_text = txt_KitsuUser.text()

        def txt_KitsuPass_textChanged():
            self.kitsu_pass_text = txt_KitsuPass.text()


        window = QtWidgets.QDialog()
        window.setFixedSize(450, 180)
        window.setWindowTitle(self.app_name + ' - Login')
        window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setStyleSheet('background-color: #313131')

        screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        window.move((screen_res.width()/2)-150, (screen_res.height() / 2)-180)

        vbox1 = QtWidgets.QVBoxLayout()

        hbox1 = QtWidgets.QHBoxLayout()

        lbl_Host = QtWidgets.QLabel('Server: ', window)
        lbl_Host.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_Host.setFixedSize(108, 28)
        lbl_Host.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        txt_KitsuHost = QtWidgets.QLineEdit(self.kitsu_host, window)
        txt_KitsuHost.setFocusPolicy(QtCore.Qt.StrongFocus)
        txt_KitsuHost.setMinimumSize(280, 28)
        txt_KitsuHost.move(128,0)
        txt_KitsuHost.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        txt_KitsuHost.textChanged.connect(txt_KitsuHost_textChanged)
        # txt_tankName.setVisible(False)

        hbox1.addWidget(lbl_Host)
        hbox1.addWidget(txt_KitsuHost)

        hbox2 = QtWidgets.QHBoxLayout()

        lbl_User = QtWidgets.QLabel('Email: ', window)
        lbl_User.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_User.setFixedSize(108, 28)
        lbl_User.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        txt_KitsuUser = QtWidgets.QLineEdit(self.kitsu_user, window)
        txt_KitsuUser.setFocusPolicy(QtCore.Qt.StrongFocus)
        txt_KitsuUser.setMinimumSize(280, 28)
        txt_KitsuUser.move(128,0)
        txt_KitsuUser.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        txt_KitsuUser.textChanged.connect(txt_KitsuUser_textChanged)

        hbox2.addWidget(lbl_User)
        hbox2.addWidget(txt_KitsuUser)

        hbox3 = QtWidgets.QHBoxLayout()

        lbl_Pass = QtWidgets.QLabel('Password: ', window)
        lbl_Pass.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_Pass.setFixedSize(108, 28)
        lbl_Pass.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        txt_KitsuPass = QtWidgets.QLineEdit(self.kitsu_pass, window)
        txt_KitsuPass.setFocusPolicy(QtCore.Qt.StrongFocus)
        txt_KitsuPass.setMinimumSize(280, 28)
        txt_KitsuPass.move(128,0)
        txt_KitsuPass.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        txt_KitsuPass.setEchoMode(QtWidgets.QLineEdit.Password)
        txt_KitsuPass.textChanged.connect(txt_KitsuPass_textChanged)

        hbox3.addWidget(lbl_Pass)
        hbox3.addWidget(txt_KitsuPass)

        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox2)
        vbox1.addLayout(hbox3)

        hbox_spacer = QtWidgets.QHBoxLayout()
        lbl_spacer = QtWidgets.QLabel('', window)
        lbl_spacer.setMinimumHeight(8)
        hbox_spacer.addWidget(lbl_spacer)
        vbox1.addLayout(hbox_spacer)

        select_btn = QtWidgets.QPushButton('Login', window)
        select_btn.setFocusPolicy(QtCore.Qt.StrongFocus)
        select_btn.setMinimumSize(100, 28)
        select_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        select_btn.clicked.connect(window.accept)
        select_btn.setAutoDefault(True)

        cancel_btn = QtWidgets.QPushButton('Cancel', window)
        cancel_btn.setFocusPolicy(QtCore.Qt.StrongFocus)
        cancel_btn.setMinimumSize(100, 28)
        cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        cancel_btn.clicked.connect(window.reject)

        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(cancel_btn)
        hbox4.addWidget(select_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setMargin(20)
        vbox.addLayout(vbox1)
        vbox.addLayout(hbox4)

        window.setLayout(vbox)

        window.setTabOrder(txt_KitsuHost, txt_KitsuUser)
        window.setTabOrder(txt_KitsuUser, txt_KitsuPass)
        window.setTabOrder(txt_KitsuPass, cancel_btn)
        window.setTabOrder(cancel_btn, select_btn)
        window.setTabOrder(select_btn, txt_KitsuHost)

        txt_KitsuUser.setFocus()
        txt_KitsuHost.setFocus()
        
        if window.exec_():
            # login
            result = {
                'host': self.kitsu_host_text,
                'user': self.kitsu_user_text,
                'password': self.kitsu_pass_text
            }
        else:
            # cancel
            result = {}

        return result

    def check_linked_project(self, *args, **kwargs):
        try:
            import flame
        except:
            self.log_debug('no flame module avaliable to import')
            return False
        try:
            if self.flame_project != flame.project.current_project.name:
                self.log_debug('updating flame project name: %s' % flame.project.current_project.name)
                self.flame_project = flame.project.current_project.name
        except:
            return False

        try:
            if self.linked_project != flame.project.current_project.shotgun_project_name:
                self.log_debug('updating linked project: %s' % flame.project.current_project.shotgun_project_name)
                self.linked_project = flame.project.current_project.shotgun_project_name.get_value()
        except:
            return False

        if self.user:
            self.log_debug('updating project id')
            project = self.gazu.project.get_project_by_name(self.linked_project, client = self.gazu_client)
            if project:
                pprint (project)
                self.linked_project_id = project.get('id')
            else:
                self.log_debug('no project id found for project name: %s' % flame.project.current_project.shotgun_project_name)
        return True

    def cache_short_loop(self, timeout):
        print ('short loop entry point')
        avg_delta = timeout / 2
        recent_deltas = [avg_delta]*9
        while self.threads:
            start = time.time()                
            
            if (not self.user) and (not self.linked_project_id):
                print ('short loop: no user and id')
                time.sleep(1)
                continue

            shortloop_gazu_client = None
            try:
                host = self.kitsu_host
                if not host.endswith('/api/'):
                    if self.kitsu_host.endswith('/'):
                        host = host + 'api/'
                    else:
                        host = host + '/api/'
                elif host.endswith('/api'):
                    host = host + ('/')
                shortloop_gazu_client = self.gazu.client.create_client(host)
                self.gazu.log_in(self.kitsu_user, self.kitsu_pass, client=shortloop_gazu_client)
                # self.cache_update(shortloop_gazu_client)
            except Exception as e:
                self.log_debug('error soft updating cache in cache_short_loop: %s' % e)

            if self.user and shortloop_gazu_client:
                try:
                    self.pipeline_data['active_projects'] = self.gazu.project.all_open_projects(client=shortloop_gazu_client)
                    if not self.pipeline_data['active_projects']:
                        self.pipeline_data['active_projects'] = [{}]
                except Exception as e:
                    self.log(pformat(e))

            if not self.linked_project_id:
                print ('short loop: no id')
                self.gazu.log_out(client = shortloop_gazu_client)
                time.sleep(1)
                continue
            
            active_projects = self.pipeline_data.get('active_projects')
            if not active_projects:
                print ('no active_projects')
                self.gazu.log_out(client = shortloop_gazu_client)
                time.sleep(1)
                continue

            projects_by_id = {x.get('id'):x for x in self.pipeline_data['active_projects']}
            current_project = projects_by_id.get(self.linked_project_id)

            try:
                self.pipeline_data['all_tasks_for_project'] = self.gazu.task.all_tasks_for_project(current_project, client=shortloop_gazu_client)
            except Exception as e:
                self.log(pformat(e))

            self.gazu.log_out(client = shortloop_gazu_client)

            # self.preformat_common_queries()

            delta = time.time() - start
            self.log_debug('cache_short_loop took %s sec' % str(delta))

            last_delta = recent_deltas[len(recent_deltas) - 1]
            recent_deltas.pop(0)
            
            if abs(delta - last_delta) > last_delta*3:
                delta = last_delta*3

            recent_deltas.append(delta)
            avg_delta = sum(recent_deltas)/float(len(recent_deltas))
            if avg_delta > timeout/2:
                self.loop_timeout(avg_delta*2, start)
            else:
                self.loop_timeout(timeout, start)

            # pprint (self.pipeline_data)

    def terminate_loops(self):
        self.threads = False
        
        for loop in self.loops:
            loop.join()

    def loop_timeout(self, timeout, start):
        time_passed = int(time.time() - start)
        if timeout <= time_passed:
            return
        else:
            for n in range(int(timeout - time_passed) * 10):
                if not self.threads:
                    self.log_debug('leaving loop thread: %s' % inspect.currentframe().f_back.f_code.co_name)
                    break
                time.sleep(0.1)

    def scan_active_projects(self):
        if self.user:
            try:
                self.pipeline_data['active_projects'] = self.gazu.project.all_open_projects(client=self.gazu_client)
                if not self.pipeline_data['active_projects']:
                    self.pipeline_data['active_projects'] = [{}]
            except Exception as e:
                self.log(pformat(e))


class flameMenuProjectconnect(flameMenuApp):

    # flameMenuProjectconnect app takes care of the preferences dialog as well
    
    def __init__(self, framework, connector):
        flameMenuApp.__init__(self, framework)
        self.connector = connector
        self.log('initializing')

        '''
        # register async cache query
        self.active_projects_uid = self.connector.cache_register({
                    'entity': 'Project',
                    'filters': [['archived', 'is', False], ['is_template', 'is', False]],
                    'fields': ['name', 'tank_name']
                    }, perform_query = True)
        '''

        if self.connector.linked_project and (not self.connector.linked_project_id):
            self.log_debug("project '%s' can not be found" % self.connector.linked_project)
            self.log_debug("unlinking project: '%s'" % self.connector.linked_project)
            self.unlink_project()
        
    def __getattr__(self, name):
        def method(*args, **kwargs):
            project = self.dynamic_menu_data.get(name)
            if project:
                self.link_project(project)
        return method
    
    def build_menu(self):
        if not self.flame:
            return []

        flame_project_name = self.flame.project.current_project.name
        self.connector.linked_project = self.flame.project.current_project.shotgun_project_name.get_value()

        menu = {'actions': []}

        if not self.connector.user:
            menu['name'] = self.menu_group_name

            menu_item = {}
            menu_item['name'] = 'Sign in to Kitsu'
            menu_item['execute'] = self.sign_in
            menu['actions'].append(menu_item)

        elif self.connector.linked_project:
            menu['name'] = self.menu_group_name

            menu_item = {}
            menu_item['order'] = 1
            menu_item['name'] = 'Unlink from `' + self.connector.linked_project + '`'
            menu_item['execute'] = self.unlink_project
            menu['actions'].append(menu_item)
            
            menu_item = {}
            menu_item['order'] = 2
            menu_item['name'] = 'Sign Out: ' + str(self.connector.user_name)
            menu_item['execute'] = self.sign_out
            menu['actions'].append(menu_item)
            
            menu_item = {}
            menu_item['order'] = 3
            menu_item['name'] = 'Preferences'
            menu_item['execute'] = self.preferences_window
            menu_item['waitCursor'] = False
            menu['actions'].append(menu_item)

        else:
            # menu['name'] = self.menu_group_name + ': Link `' + flame_project_name + '` to Shotgun'
            menu['name'] = self.menu_group_name + ': Link to Project'

            menu_item = {}
            menu_item['order'] = 1
            menu_item['name'] = '~ Rescan Projects'
            menu_item['execute'] = self.rescan
            menu['actions'].append(menu_item)

            menu_item = {}
            menu_item['order'] = 2
            menu_item['name'] = '---'
            menu_item['execute'] = self.rescan
            menu['actions'].append(menu_item)

            projects = self.get_projects()
            projects_by_name = {}
            for project in projects:
                projects_by_name[project.get('name')] = project

            index = 0
            for index, project_name in enumerate(sorted(projects_by_name.keys(), key=str.casefold)):
                project = projects_by_name.get(project_name)
                self.dynamic_menu_data[str(id(project))] = project

                menu_item = {}
                menu_item['order'] = index + 2
                menu_item['name'] = project_name
                menu_item['execute'] = getattr(self, str(id(project)))
                menu['actions'].append(menu_item)
            
            menu_item = {}
            menu_item['order'] = index + 3
            menu_item['name'] = '--'
            menu_item['execute'] = self.rescan
            menu['actions'].append(menu_item)

            menu_item = {}
            menu_item['order'] = index + 4
            menu_item['name'] = 'Sign Out: ' + str(self.connector.user_name)
            menu_item['execute'] = self.sign_out
            menu['actions'].append(menu_item)

            menu_item = {}
            menu_item['order'] = index + 5
            menu_item['name'] = 'Preferences'
            menu_item['execute'] = self.preferences_window
            menu_item['waitCursor'] = False
            menu['actions'].append(menu_item)

        return menu

    def get_projects(self, *args, **kwargs):
        projects = self.connector.pipeline_data.get('active_projects')

        if not projects:
            try:
                projects = self.connector.gazu.project.all_open_projects(client = self.connector.gazu_client)
            except Exception as e:
                self.log(pformat(e))
        
        if not isinstance(projects, list):
            projects = [{}]
        return projects

    def unlink_project(self, *args, **kwargs):
        self.flame.project.current_project.shotgun_project_name = ''
        self.connector.linked_project = None
        self.connector.linked_project_id = None
        self.rescan()

    def link_project(self, project):
        project_name = project.get('name')
        if project_name:
            self.flame.project.current_project.shotgun_project_name = project_name
            self.connector.linked_project = project_name
            if 'id' in project.keys():
                self.connector.linked_project_id = project.get('id')
        self.rescan()
        
    def refresh(self, *args, **kwargs):        
        # self.connector.cache_retrive_result(self.active_projects_uid, True)
        self.rescan()

    def sign_in(self, *args, **kwargs):
        # self.connector.destroy_toolkit_engine()
        self.connector.prefs_global['user signed out'] = False
        self.connector.get_user()
        self.framework.save_prefs()
        self.rescan()
        # self.connector.register_common_queries()
        # self.connector.bootstrap_toolkit()

    def sign_out(self, *args, **kwargs):
        # self.connector.destroy_toolkit_engine()
        # self.connector.unregister_common_queries()
        self.connector.prefs_global['user signed out'] = True
        self.connector.clear_user()
        self.framework.save_prefs()
        self.rescan()

    def preferences_window(self, *args, **kwargs):

        # The first attemt to draft preferences window in one function
        # became a bit monstrous
        # Probably need to put it in subclass instead

        from PySide2 import QtWidgets, QtCore, QtGui
        
        # storage root section
        # self.connector.update_sg_storage_root()

        def compose_project_path_messge(tank_name):
            self.connector.update_sg_storage_root()

            if not self.connector.sg_storage_root:
                # no storage selected
                return 'Linux path: no storage selected\nMac path: no storage selected\nWindows path: no storage selected'
            
            linux_path = str(self.connector.sg_storage_root.get('linux_path', ''))
            mac_path = str(self.connector.sg_storage_root.get('mac_path', ''))
            win_path = str(self.connector.sg_storage_root.get('windows_path', ''))
            msg = 'Linux path: '
            if linux_path != 'None':
                if self.txt_tankName_text:
                    msg += os.path.join(linux_path, tank_name)
            else:
                msg += 'None'
            msg += '\nMac path: '
            if mac_path != 'None':
                if self.txt_tankName_text:
                    msg += os.path.join(mac_path, tank_name)
            else:
                msg += 'None'
            msg += '\nWindows path: '
            if win_path != 'None':
                if self.txt_tankName_text:
                    msg += os.path.join(mac_path, tank_name)
            else:
                msg += 'None'

            return msg

        def update_project_path_info():
            tank_name = self.connector.get_tank_name()
            storage_root_paths.setText(compose_project_path_messge(tank_name))

        def update_pipeline_config_info():
            if self.connector.get_pipeline_configurations():
                pipeline_config_info.setText('Found')
            else:
                pipeline_config_info.setText('None')

        def change_storage_root_dialog():
            self.connector.project_path_dialog()

            update_pipeline_config_info()
            update_project_path_info()

        def set_presetTypeImage():
            btn_presetType.setText('File Sequence')
            self.presetType = 0
        
        def set_presetTypeMovie():
            btn_presetType.setText('Movie')
            self.presetType = 2

        def set_presetLocationProject():
            btn_PresetLocation.setText('Project')
            self.PresetVisibility = 0
            
        def set_presetLocationShared():
            btn_PresetLocation.setText('Shared')
            self.PresetVisibility = 1

        def set_presetLocationADSK():
            btn_PresetLocation.setText('Autodesk')
            self.PresetVisibility = 2

        def set_presetLocationCustom():
            btn_PresetLocation.setText('Custom')
            self.PresetVisibility = -1            

        def format_preset_details(export_preset_fields):
            preset_path = export_preset_fields.get('path')
            preset_details = ''
            preset_details += 'Name: ' + os.path.basename(preset_path) + '\n'
            preset_details += 'File Type: ' + export_preset_fields.get('fileType') + ', '
            preset_details += 'Extension: ' + export_preset_fields.get('fileExt') + '\n'
            preset_details += 'Frame Padding: ' + str(export_preset_fields.get('framePadding')) +', '
            if (export_preset_fields.get('useTimecode') == '1') or (export_preset_fields.get('useTimecode') == 'True'):
                preset_details += 'Use Timecode'
            else:
                preset_details += 'Start Frame: ' + str(export_preset_fields.get('startFrame'))
            return preset_details

        def changeExportPreset():
            dialog = QtWidgets.QFileDialog()
            dialog.setWindowTitle('Select Format Preset')
            dialog.setNameFilter('XML files (*.xml)')
            if self.PresetVisibility == -1:
                dialog.setDirectory(os.path.expanduser('~'))
            else:
                preset_folder = self.flame.PyExporter.get_presets_dir(self.flame.PyExporter.PresetVisibility.values.get(self.PresetVisibility),
                                        self.flame.PyExporter.PresetType.values.get(self.presetType))
                dialog.setDirectory(preset_folder)
            dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                file_full_path = str(dialog.selectedFiles()[0])
                file_full_path = file_full_path[len(preset_folder)+1:] if file_full_path.startswith(preset_folder) else file_full_path
                preset = {'PresetVisibility': self.PresetVisibility, 'PresetType': self.presetType, 'PresetFile': file_full_path}
                export_preset_fields = self.get_export_preset_fields(preset)
                if export_preset_fields:
                    self.framework.prefs['flameMenuPublisher']['flame_export_presets']['Publish'] = preset
                    lbl_presetDetails.setText(format_preset_details(export_preset_fields))
                else:
                    pass
        
        # Prefs window functions

        def pressGeneral():
            btn_General.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
            btn_Publish.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Superclips.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            
            paneGeneral.setVisible(False)
            panePublish.setVisible(False)
            paneTemplatesSelector.setVisible(False)
            paneSuperclips.setVisible(False)

            paneGeneral.setVisible(True)

        def pressPublish():
            btn_General.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Publish.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
            btn_Superclips.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')

            paneGeneral.setVisible(False)
            panePublish.setVisible(False)
            paneTemplatesSelector.setVisible(False)
            paneSuperclips.setVisible(False)

            paneTemplatesSelector.setVisible(True)
            panePublish.setVisible(True)

        def pressSuperclips():
            btn_General.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Publish.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Superclips.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')

            paneGeneral.setVisible(False)
            panePublish.setVisible(False)
            paneTemplatesSelector.setVisible(False)
            paneSuperclips.setVisible(False)

            paneSuperclips.setVisible(True)

        window = None
        window = QtWidgets.QDialog()
        window.setFixedSize(1028, 328)
        window.setWindowTitle(self.framework.bundle_name + ' Preferences')
        window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setStyleSheet('background-color: #2e2e2e')

        screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        window.move((screen_res.width()/2)-400, (screen_res.height() / 2)-180)

        # Prefs Pane widgets
        
        paneTabs = QtWidgets.QWidget(window)
        paneGeneral = QtWidgets.QWidget(window)
        panePublish = QtWidgets.QWidget(window)
        paneSuperclips = QtWidgets.QWidget(window)

        # Main window HBox

        hbox_main = QtWidgets.QHBoxLayout()
        hbox_main.setAlignment(QtCore.Qt.AlignLeft)

        # Modules: apps selector preferences block
        # Modules: apps are hardcoded at the moment

        # Modules: Button functions

        vbox_apps = QtWidgets.QVBoxLayout()
        vbox_apps.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        # Modules: Label

        lbl_modules = QtWidgets.QLabel('Modules', window)
        lbl_modules.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_modules.setMinimumSize(128, 28)
        lbl_modules.setAlignment(QtCore.Qt.AlignCenter)
        lbl_modules.setVisible(False)
        # vbox_apps.addWidget(lbl_modules)

        # Modules: Selection buttons

        # Modules: General preferences button

        hbox_General = QtWidgets.QHBoxLayout()
        hbox_General.setAlignment(QtCore.Qt.AlignLeft)
        btn_General = QtWidgets.QPushButton('General', window)
        btn_General.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_General.setMinimumSize(128, 28)
        btn_General.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_General.pressed.connect(pressGeneral)
        hbox_General.addWidget(btn_General)
        vbox_apps.addLayout(hbox_General, alignment = QtCore.Qt.AlignLeft)

        # Modules: flameMenuPublisher button

        hbox_Publish = QtWidgets.QHBoxLayout()
        hbox_Publish.setAlignment(QtCore.Qt.AlignLeft)
        btn_Publish = QtWidgets.QPushButton('Menu Publish', window)
        btn_Publish.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Publish.setMinimumSize(128, 28)
        btn_Publish.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Publish.pressed.connect(pressPublish)
        hbox_Publish.addWidget(btn_Publish)
        vbox_apps.addLayout(hbox_Publish, alignment = QtCore.Qt.AlignLeft)

        # Modules: flameSuperclips button

        hbox_Superclips = QtWidgets.QHBoxLayout()
        hbox_Superclips.setAlignment(QtCore.Qt.AlignLeft)
        btn_Superclips = QtWidgets.QPushButton('Superclips', window)
        btn_Superclips.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Superclips.setMinimumSize(128, 28)
        btn_Superclips.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Superclips.pressed.connect(pressSuperclips)
        hbox_Superclips.addWidget(btn_Superclips)
        vbox_apps.addLayout(hbox_Superclips, alignment = QtCore.Qt.AlignLeft)

        # Modules: End of Modules section
        hbox_main.addLayout(vbox_apps)

        # Vertical separation line
        
        vertical_sep_01 = QtWidgets.QLabel('', window)
        vertical_sep_01.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Plain)
        vertical_sep_01.setStyleSheet('QFrame {color: #444444}')
        hbox_main.addWidget(vertical_sep_01)
        paneTabs.setLayout(hbox_main)
        paneTabs.move(10, 10)

        # General

        paneGeneral.setFixedSize(840, 264)
        paneGeneral.move(172, 20)
        paneGeneral.setVisible(False)

        # General::BatchLink label

        lbl_batchLink = QtWidgets.QLabel('Batch Link Autosave Path', paneGeneral)
        lbl_batchLink.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_batchLink.setMinimumSize(840, 28)
        lbl_batchLink.setAlignment(QtCore.Qt.AlignCenter)

        def update_batchLinkPathLabel():
            batch_link_path = self.framework.prefs.get('flameBatchBlessing', {}).get('flame_batch_root')
            flame_project_name = self.flame.project.current_project.name
            if self.framework.prefs['flameBatchBlessing'].get('use_project', True):
                lbl_batchLinkPath.setText(os.path.join(batch_link_path, flame_project_name))
            else:
                lbl_batchLinkPath.setText(batch_link_path)

        # General::BatchLink Enable button
        
        def enableBatchLink():
            if self.framework.prefs['flameBatchBlessing'].get('enabled', True):
                btn_batchLink.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
                self.framework.prefs['flameBatchBlessing']['enabled'] = False
            else:
                btn_batchLink.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
                self.framework.prefs['flameBatchBlessing']['enabled'] = True

        btn_batchLink = QtWidgets.QPushButton('Batch Link', paneGeneral)
        btn_batchLink.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_batchLink.setMinimumSize(88, 28)
        btn_batchLink.move(0, 34)
        if self.framework.prefs['flameBatchBlessing'].get('enabled', True):
            btn_batchLink.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
        else:
            btn_batchLink.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_batchLink.pressed.connect(enableBatchLink)

        # General::BatchLink default path button

        def batchLinkDefault():
            self.framework.prefs['flameBatchBlessing']['flame_batch_root'] = '/var/tmp/flameMenuSG/flame_batch_setups'
            update_batchLinkPathLabel()
            self.framework.save_prefs()
        btn_batchLinkDefault = QtWidgets.QPushButton('Default', paneGeneral)
        btn_batchLinkDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_batchLinkDefault.setMinimumSize(88, 28)
        btn_batchLinkDefault.move(94, 34)
        btn_batchLinkDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_batchLinkDefault.clicked.connect(batchLinkDefault)

        # General::BatchLink path field

        lbl_batchLinkPath = QtWidgets.QLabel(paneGeneral)
        lbl_batchLinkPath.setFocusPolicy(QtCore.Qt.NoFocus)
        lbl_batchLinkPath.setMinimumSize(464, 28)
        lbl_batchLinkPath.move(188,34)
        lbl_batchLinkPath.setStyleSheet('QFrame {color: #9a9a9a; background-color: #222222}')
        lbl_batchLinkPath.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        update_batchLinkPathLabel()

        # General::BatchLink Add Flame project name button
        
        def batchLinkUseProject():            
            if self.framework.prefs['flameBatchBlessing'].get('use_project', True):
                btn_batchLinkUseProject.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
                self.framework.prefs['flameBatchBlessing']['use_project'] = False
            else:
                btn_batchLinkUseProject.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
                self.framework.prefs['flameBatchBlessing']['use_project'] = True
            update_batchLinkPathLabel()
            self.framework.save_prefs()
        
        btn_batchLinkUseProject = QtWidgets.QPushButton('Use Project', paneGeneral)
        btn_batchLinkUseProject.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_batchLinkUseProject.setMinimumSize(88, 28)
        btn_batchLinkUseProject.move(658, 34)
        if self.framework.prefs['flameBatchBlessing'].get('use_project', True):
            btn_batchLinkUseProject.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset black; border-bottom: 1px inset #555555}')
        else:
            btn_batchLinkUseProject.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_batchLinkUseProject.pressed.connect(batchLinkUseProject)


        # General::BatchLink Browse button
        def batchLinkBrowse():
            batch_link_path = self.framework.prefs.get('flameBatchBlessing', {}).get('flame_batch_root')
            dialog = QtWidgets.QFileDialog()
            dialog.setWindowTitle('Select Batch Autosave Folder')
            dialog.setDirectory(batch_link_path)
            new_path = dialog.getExistingDirectory(directory=batch_link_path,
                                                    options=dialog.ShowDirsOnly)
            if new_path:
                self.framework.prefs['flameBatchBlessing']['flame_batch_root'] = new_path
                update_batchLinkPathLabel()
                self.framework.save_prefs()

        btn_batchLinkBrowse = QtWidgets.QPushButton('Browse', paneGeneral)
        btn_batchLinkBrowse.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_batchLinkBrowse.setMinimumSize(88, 28)
        btn_batchLinkBrowse.move(752, 34)
        btn_batchLinkBrowse.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_batchLinkBrowse.clicked.connect(batchLinkBrowse)

        # General::Loader PublishedFileTypes label

        '''

        lbl_PublishedFileTypes = QtWidgets.QLabel('Loader Published File Types', paneGeneral)
        lbl_PublishedFileTypes.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_PublishedFileTypes.setMinimumSize(536, 28)
        lbl_PublishedFileTypes.move(304, 68)
        lbl_PublishedFileTypes.setAlignment(QtCore.Qt.AlignCenter)

        # General::Loader PublishedFileTypes Button 1

        btn_PublishedFileType1 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType1.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType1.setText('Not Implemented')
        btn_PublishedFileType1.setMinimumSize(128, 28)
        btn_PublishedFileType1.move(304, 102)
        btn_PublishedFileType1.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType1_menu = QtWidgets.QMenu()
        btn_PublishedFileType1_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType1_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType1.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 2

        btn_PublishedFileType2 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType2.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType2.setText('Not Implemented')
        btn_PublishedFileType2.setMinimumSize(128, 28)
        btn_PublishedFileType2.move(440, 102)
        btn_PublishedFileType2.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType2_menu = QtWidgets.QMenu()
        btn_PublishedFileType2_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType2_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType2.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 3

        btn_PublishedFileType3 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType3.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType3.setText('Not Implemented')
        btn_PublishedFileType3.setMinimumSize(128, 28)
        btn_PublishedFileType3.move(576, 102)
        btn_PublishedFileType3.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType3_menu = QtWidgets.QMenu()
        btn_PublishedFileType3_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType3_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType3.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 4

        btn_PublishedFileType4 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType4.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType4.setText('Not Implemented')
        btn_PublishedFileType4.setMinimumSize(128, 28)
        btn_PublishedFileType4.move(712, 102)
        btn_PublishedFileType4.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType4_menu = QtWidgets.QMenu()
        btn_PublishedFileType4_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType4_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType4.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 5

        btn_PublishedFileType5 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType5.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType5.setText('Flame Batch File')
        btn_PublishedFileType5.setMinimumSize(128, 28)
        btn_PublishedFileType5.move(304, 136)
        btn_PublishedFileType5.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType5_menu = QtWidgets.QMenu()
        btn_PublishedFileType5_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType5_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType5.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 6

        btn_PublishedFileType6 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType6.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType6.setText('Flame Batch File')
        btn_PublishedFileType6.setMinimumSize(128, 28)
        btn_PublishedFileType6.move(440, 136)
        btn_PublishedFileType6.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType6_menu = QtWidgets.QMenu()
        btn_PublishedFileType6_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType6_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType6.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 7

        btn_PublishedFileType7 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType7.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType7.setText('Flame Batch File')
        btn_PublishedFileType7.setMinimumSize(128, 28)
        btn_PublishedFileType7.move(576, 136)
        btn_PublishedFileType7.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType7_menu = QtWidgets.QMenu()
        btn_PublishedFileType7_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType7_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType7.setMenu(btn_PublishedFileType1_menu)

        # General::Loader PublishedFileTypes Button 8

        btn_PublishedFileType8 = QtWidgets.QPushButton(paneGeneral)
        btn_PublishedFileType8.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PublishedFileType8.setText('Flame Batch File')
        btn_PublishedFileType8.setMinimumSize(128, 28)
        btn_PublishedFileType8.move(712, 136)
        btn_PublishedFileType8.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_PublishedFileType8_menu = QtWidgets.QMenu()
        btn_PublishedFileType8_menu.addAction('File Sequence', set_presetTypeImage)
        btn_PublishedFileType8_menu.addAction('Movie', set_presetTypeMovie)
        btn_PublishedFileType8.setMenu(btn_PublishedFileType1_menu)

        ''' # end of loader PublishedFileType settings

        # General::Create Default Task Template Label

        lbl_DefTaskTemplate = QtWidgets.QLabel('Default Task Template', paneGeneral)
        lbl_DefTaskTemplate.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_DefTaskTemplate.setMinimumSize(298, 28)
        lbl_DefTaskTemplate.move(0, 68)
        lbl_DefTaskTemplate.setAlignment(QtCore.Qt.AlignCenter)

        # General::Create Shot Task Template Label

        lbl_ShotTaskTemplate = QtWidgets.QLabel('Shot', paneGeneral)
        lbl_ShotTaskTemplate.setStyleSheet('QFrame {color: #989898;}')
        lbl_ShotTaskTemplate.setMinimumSize(36, 28)
        lbl_ShotTaskTemplate.move(0, 102)

        # General::Loader Shot Task Template Menu
        btn_ShotTaskTemplate = QtWidgets.QPushButton(paneGeneral)
        flameMenuNewBatch_prefs = self.framework.prefs.get('flameMenuNewBatch', {})
        shot_task_template = flameMenuNewBatch_prefs.get('shot_task_template', {})
        code = shot_task_template.get('code', 'No code')
        btn_ShotTaskTemplate.setText(code)
        shot_task_templates = self.connector.sg.find('TaskTemplate', [['entity_type', 'is', 'Shot']], ['code'])
        shot_task_templates_by_id = {x.get('id'):x for x in shot_task_templates}
        shot_task_templates_by_code_id = {x.get('code') + '_' + str(x.get('id')):x for x in shot_task_templates}
        def selectShotTaskTemplate(template_id):
            template = shot_task_templates_by_id.get(template_id, {})
            code = template.get('code', 'no_code')
            btn_ShotTaskTemplate.setText(code)
            self.framework.prefs['flameMenuNewBatch']['shot_task_template'] = template
        btn_ShotTaskTemplate.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_ShotTaskTemplate.setMinimumSize(258, 28)
        btn_ShotTaskTemplate.move(40, 102)
        btn_ShotTaskTemplate.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_ShotTaskTemplate_menu = QtWidgets.QMenu()
        for code_id in sorted(shot_task_templates_by_code_id.keys()):
            template = shot_task_templates_by_code_id.get(code_id, {})
            code = template.get('code', 'no_code')
            template_id = template.get('id')
            action = btn_ShotTaskTemplate_menu.addAction(code)
            x = lambda chk=False, template_id=template_id: selectShotTaskTemplate(template_id)
            action.triggered[()].connect(x)
        btn_ShotTaskTemplate.setMenu(btn_ShotTaskTemplate_menu)

        # General::Create Asset Task Template Label

        lbl_AssetTaskTemplate = QtWidgets.QLabel('Asset', paneGeneral)
        lbl_AssetTaskTemplate.setStyleSheet('QFrame {color: #989898;}')
        lbl_AssetTaskTemplate.setMinimumSize(36, 28)
        lbl_AssetTaskTemplate.move(0, 136)

        # General::Loader Asset Task Template Menu
        btn_AssetTaskTemplate = QtWidgets.QPushButton(paneGeneral)
        flameMenuNewBatch_prefs = self.framework.prefs.get('flameMenuNewBatch', {})
        shot_task_template = flameMenuNewBatch_prefs.get('asset_task_template', {})
        code = shot_task_template.get('code', 'No code')
        btn_AssetTaskTemplate.setText(code)
        asset_task_templates = self.connector.sg.find('TaskTemplate', [['entity_type', 'is', 'Asset']], ['code'])
        asset_task_templates_by_id = {x.get('id'):x for x in asset_task_templates}
        asset_task_templates_by_code_id = {x.get('code') + '_' + str(x.get('id')):x for x in asset_task_templates}
        def selectAssetTaskTemplate(template_id):
            template = shot_task_templates_by_id.get(template_id, {})
            code = template.get('code', 'no_code')
            btn_AssetTaskTemplate.setText(code)
            self.framework.prefs['flameMenuNewBatch']['asset_task_template'] = template
        btn_AssetTaskTemplate.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_AssetTaskTemplate.setMinimumSize(258, 28)
        btn_AssetTaskTemplate.move(40, 136)
        btn_AssetTaskTemplate.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_AssetTaskTemplate_menu = QtWidgets.QMenu()
        for code_id in sorted(asset_task_templates_by_code_id.keys()):
            template = asset_task_templates_by_code_id.get(code_id, {})
            code = template.get('code', 'no_code')
            template_id = template.get('id')
            action = btn_AssetTaskTemplate_menu.addAction(code)
            x = lambda chk=False, template_id=template_id: selectAssetTaskTemplate(template_id)
            action.triggered[()].connect(x)
        btn_AssetTaskTemplate.setMenu(btn_AssetTaskTemplate_menu)

        # General::AutoRefresh button Label

        lbl_AutoRefresh = QtWidgets.QLabel('Refresh Menu Automatically', paneGeneral)
        lbl_AutoRefresh.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_AutoRefresh.setMinimumSize(298, 28)
        lbl_AutoRefresh.move(0, 170)
        lbl_AutoRefresh.setAlignment(QtCore.Qt.AlignCenter)

        lbl_AutoRefreshMsg = QtWidgets.QLabel('Use to debug right-click menu performance', paneGeneral)
        lbl_AutoRefreshMsg.setStyleSheet('QFrame {color: #989898;}')
        lbl_AutoRefreshMsg.setMinimumSize(36, 28)
        lbl_AutoRefreshMsg.move(0, 204)

        # General::AutoRefresh Main refresh button

        def update_AutoRefreshMain():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            main_menu = menu_auto_refresh.get('main_menu', False)
            if main_menu:
                btn_AutoRefreshMain.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            else:
                btn_AutoRefreshMain.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        def clicked_AutoRefreshMain():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            menu_auto_refresh['main_menu'] = not menu_auto_refresh.get('main_menu', False)
            self.framework.prefs_global['menu_auto_refresh'] = menu_auto_refresh
            update_AutoRefreshMain()
        btn_AutoRefreshMain = QtWidgets.QPushButton('Main Menu', paneGeneral)
        btn_AutoRefreshMain.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_AutoRefreshMain.setMinimumSize(94, 28)
        btn_AutoRefreshMain.move(0, 238)
        btn_AutoRefreshMain.clicked.connect(clicked_AutoRefreshMain)
        update_AutoRefreshMain()

        # General::AutoRefresh Batch refresh button

        def update_AutoRefreshBatch():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            batch = menu_auto_refresh.get('batch', False)
            if batch:
                btn_AutoRefreshBatch.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            else:
                btn_AutoRefreshBatch.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        def clicked_AutoRefreshBatch():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            menu_auto_refresh['batch'] = not menu_auto_refresh.get('batch', False)
            self.framework.prefs_global['menu_auto_refresh'] = menu_auto_refresh
            update_AutoRefreshBatch()
        btn_AutoRefreshBatch = QtWidgets.QPushButton('Batch Menu', paneGeneral)
        btn_AutoRefreshBatch.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_AutoRefreshBatch.setMinimumSize(94, 28)
        btn_AutoRefreshBatch.move(100, 238)
        btn_AutoRefreshBatch.clicked.connect(clicked_AutoRefreshBatch)
        update_AutoRefreshBatch()

        # General::AutoRefresh Media Panel refresh button

        def update_AutoRefreshMediaPanel():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            media_panel = menu_auto_refresh.get('media_panel', False)
            if media_panel:
                btn_AutoRefreshMediaPanel.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            else:
                btn_AutoRefreshMediaPanel.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        def clicked_AutoRefreshMediaPanel():
            menu_auto_refresh = self.framework.prefs_global.get('menu_auto_refresh', {})
            menu_auto_refresh['media_panel'] = not menu_auto_refresh.get('media_panel', False)
            self.framework.prefs_global['menu_auto_refresh'] = menu_auto_refresh
            update_AutoRefreshMediaPanel()
        btn_AutoRefreshMediaPanel = QtWidgets.QPushButton('Media Panel', paneGeneral)
        btn_AutoRefreshMediaPanel.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_AutoRefreshMediaPanel.setMinimumSize(94, 28)
        btn_AutoRefreshMediaPanel.move(200, 238)
        btn_AutoRefreshMediaPanel.clicked.connect(clicked_AutoRefreshMediaPanel)
        update_AutoRefreshMediaPanel()


        #lbl_General = QtWidgets.QLabel('General', paneGeneral)
        #lbl_General.setStyleSheet('QFrame {color: #989898}')
        #lbl_General.setAlignment(QtCore.Qt.AlignCenter)
        #lbl_General.setFixedSize(840, 264)
        #lbl_General.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)

        # Publish section:
        # Publish: main VBox
        vbox_publish = QtWidgets.QVBoxLayout()
        vbox_publish.setAlignment(QtCore.Qt.AlignTop)

        # Publish: hbox for storage root and export presets
        hbox_storage_root = QtWidgets.QHBoxLayout()
        hbox_storage_root.setAlignment(QtCore.Qt.AlignLeft)

        # Publish: StorageRoot section

        vbox_storage_root = QtWidgets.QVBoxLayout()
        vbox_storage_root.setAlignment(QtCore.Qt.AlignTop)
        
        # Publish: StorageRoot: label

        lbl_storage_root = QtWidgets.QLabel('Project Location', window)
        lbl_storage_root.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_storage_root.setMinimumSize(200, 28)
        lbl_storage_root.setAlignment(QtCore.Qt.AlignCenter)

        vbox_storage_root.addWidget(lbl_storage_root)

        # Publish: StorageRoot: button and storage root name block

        hbox_storage = QtWidgets.QHBoxLayout()
        storage_root_btn = QtWidgets.QPushButton(window)
        storage_root_btn.setText('Set Project Location')
        
        storage_root_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        storage_root_btn.setMinimumSize(199, 28)
        storage_root_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        storage_root_btn.clicked.connect(change_storage_root_dialog)
        hbox_storage.addWidget(storage_root_btn, alignment = QtCore.Qt.AlignLeft)

        storage_name = QtWidgets.QLabel('Pipeline configuration:', window)
        hbox_storage.addWidget(storage_name, alignment = QtCore.Qt.AlignLeft)

        pipeline_config_info = QtWidgets.QLabel(window)
        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        pipeline_config_info.setFont(boldFont)

        update_pipeline_config_info()        
        hbox_storage.addWidget(pipeline_config_info, alignment = QtCore.Qt.AlignRight)
        vbox_storage_root.addLayout(hbox_storage)


        # Publish: StorageRoot: Paths info label
        storage_root_paths = QtWidgets.QLabel(window)
        storage_root_paths.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        storage_root_paths.setStyleSheet('QFrame {color: #9a9a9a; background-color: #2a2a2a; border: 1px solid #696969 }')

        update_project_path_info()

        vbox_storage_root.addWidget(storage_root_paths)
        hbox_storage_root.addLayout(vbox_storage_root)

        # Publish: StorageRoot: end of section

        # Publish: ExportPresets section

        vbox_export_preset = QtWidgets.QVBoxLayout()
        vbox_export_preset.setAlignment(QtCore.Qt.AlignTop)

        # Publish: ExportPresets: label

        lbl_export_preset = QtWidgets.QLabel('Publish Format Preset', window)
        lbl_export_preset.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_export_preset.setMinimumSize(440, 28)
        lbl_export_preset.setAlignment(QtCore.Qt.AlignCenter)
        vbox_export_preset.addWidget(lbl_export_preset)

        # Publish: ExportPresets: Change, Default buttons and preset name HBox

        hbox_export_preset = QtWidgets.QHBoxLayout()
        hbox_export_preset.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        # Publish: ExportPresets: Preset type selector

        btn_presetType = QtWidgets.QPushButton(window)

        self.publish_preset = self.framework.prefs.get('flameMenuPublisher', {}).get('flame_export_presets', {}).get('Publish', {})
        export_preset_fields = self.get_export_preset_fields(self.publish_preset)

        if export_preset_fields.get('type', 'image') == 'movie':
            self.presetType = 2
        else:
            self.presetType = 0

        if self.presetType == 2:
            btn_presetType.setText('Movie')
        else:
            btn_presetType.setText('File Sequence')
        
        btn_presetType.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_presetType.setMinimumSize(108, 28)
        btn_presetType.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_presetType_menu = QtWidgets.QMenu()
        btn_presetType_menu.addAction('File Sequence', set_presetTypeImage)
        btn_presetType_menu.addAction('Movie', set_presetTypeMovie)
        btn_presetType.setMenu(btn_presetType_menu)
        hbox_export_preset.addWidget(btn_presetType)

        # Publish: ExportPresets: Preset location selector

        self.exportPresetDirProject = self.flame.PyExporter.get_presets_dir(self.flame.PyExporter.PresetVisibility.values.get(0),
                                        self.flame.PyExporter.PresetType.values.get(self.presetType))
        self.exportPresetDirShared = self.flame.PyExporter.get_presets_dir(self.flame.PyExporter.PresetVisibility.values.get(1),
                                        self.flame.PyExporter.PresetType.values.get(self.presetType))
        self.exportPresetDirADSK = self.flame.PyExporter.get_presets_dir(self.flame.PyExporter.PresetVisibility.values.get(2),
                                        self.flame.PyExporter.PresetType.values.get(self.presetType))

        btn_PresetLocation = QtWidgets.QPushButton(window)

        if export_preset_fields.get('path').startswith(self.exportPresetDirProject):
            self.PresetVisibility = 0
            btn_PresetLocation.setText('Project')
        elif export_preset_fields.get('path').startswith(self.exportPresetDirShared):
            self.PresetVisibility = 1
            btn_PresetLocation.setText('Shared')
        elif export_preset_fields.get('path').startswith(self.exportPresetDirADSK):
            self.PresetVisibility = 2
            btn_PresetLocation.setText('Autodesk')
        else:
            self.PresetVisibility = -1
            btn_PresetLocation.setText('Custom')

        btn_PresetLocation.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PresetLocation.setMinimumSize(108, 28)
        btn_PresetLocation.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')

        btn_PresetLocation_menu = QtWidgets.QMenu()
        btn_PresetLocation_menu.addAction('Project', set_presetLocationProject)
        btn_PresetLocation_menu.addAction('Shared', set_presetLocationShared)
        btn_PresetLocation_menu.addAction('Autodesk', set_presetLocationADSK)
        btn_PresetLocation_menu.addAction('Custom', set_presetLocationCustom)

        btn_PresetLocation.setMenu(btn_PresetLocation_menu)
        hbox_export_preset.addWidget(btn_PresetLocation)

        # Publish: ExportPresets: Export preset selector
        # this saved for feauture ADSK style menu
        '''
        btn_PresetSelector = QtWidgets.QPushButton('Publish', window)
        btn_PresetSelector.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_PresetSelector.setMinimumSize(88, 28)
        btn_PresetSelector.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_another_menu = QtWidgets.QMenu()
        btn_another_menu.addAction('Another action')
        btn_another_menu.setTitle('Submenu')
        btn_defaultPreset_menu = QtWidgets.QMenu()
        btn_defaultPreset_menu.addAction('Publish')
        btn_defaultPreset_menu.addAction('Preview')
        btn_defaultPreset_menu.addAction('Thumbnail')
        btn_defaultPreset_menu.addMenu(btn_another_menu)
        btn_PresetSelector.setMenu(btn_defaultPreset_menu)
        hbox_export_preset.addWidget(btn_PresetSelector)
        '''

        # Publish: ExportPresets: Change button
        
        btn_changePreset = QtWidgets.QPushButton('Load', window)
        btn_changePreset.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_changePreset.setMinimumSize(88, 28)
        btn_changePreset.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_changePreset.clicked.connect(changeExportPreset)
        hbox_export_preset.addWidget(btn_changePreset, alignment = QtCore.Qt.AlignLeft)
        
        # Publish: ExportPresets: End of Change, Default buttons and preset name HBox
        vbox_export_preset.addLayout(hbox_export_preset)

        # Publish: ExportPresets: Exoprt preset details
        preset_details = format_preset_details(export_preset_fields)
        lbl_presetDetails = QtWidgets.QLabel(preset_details, window)
        lbl_presetDetails.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        lbl_presetDetails.setStyleSheet('QFrame {color: #9a9a9a; background-color: #2a2a2a; border: 1px solid #696969 }')

        vbox_export_preset.addWidget(lbl_presetDetails)

        # Publish: ExportPresets: End of Export Preset section
        hbox_storage_root.addLayout(vbox_export_preset)

        # Publish: End of upper storage root and export preset section
        vbox_publish.addLayout(hbox_storage_root)


        ### PUBLISH::TEMPLATES ###
        # Publish::Tempates actions

        def action_showShot():
            # btn_Entity.setText('Shot')
            btn_Shot.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Asset.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            lbl_templates.setText('Publishing Templates: Shot')
            # lbl_shotTemplate.setText('Shot Publish')
            # lbl_batchTemplate.setText('Shot Batch')
            # lbl_versionTemplate.setText('Shot Version')
            paneAssetTemplates.setVisible(False)
            paneShotTemplates.setVisible(True)

        def action_showAsset():
            # btn_Entity.setText('Asset')
            btn_Shot.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            btn_Asset.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            lbl_templates.setText('Publishing Templates: Asset')
            # lbl_shotTemplate.setText('Asset Publish')
            # lbl_batchTemplate.setText('Asset Batch')
            # lbl_versionTemplate.setText('Asset Version')
            paneShotTemplates.setVisible(False)
            paneAssetTemplates.setVisible(True)

        # Publish::Tempates: Shot / Asset selector

        paneTemplatesSelector = QtWidgets.QWidget(window)
        paneTemplatesSelector.setFixedSize(158, 142)
        paneTemplatesSelector.move(0, 143)

        lbl_Entity = QtWidgets.QLabel('Entity', paneTemplatesSelector)
        lbl_Entity.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_Entity.setFixedSize(128, 28)
        lbl_Entity.move(20, 0)
        lbl_Entity.setAlignment(QtCore.Qt.AlignCenter)

        btn_Shot = QtWidgets.QPushButton('Shot', paneTemplatesSelector)
        btn_Shot.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Shot.setFixedSize(128, 28)
        btn_Shot.move(20, 34)
        btn_Shot.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Shot.pressed.connect(action_showShot)

        btn_Asset = QtWidgets.QPushButton('Asset', paneTemplatesSelector)
        btn_Asset.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Asset.setFixedSize(128, 28)
        btn_Asset.move(20, 68)
        btn_Asset.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Asset.pressed.connect(action_showAsset)

        # Publish::Tempates pane widget

        paneTemplates = QtWidgets.QWidget(panePublish)
        paneTemplates.setFixedSize(840, 142)

        # Publish::Tempates: label

        lbl_templates = QtWidgets.QLabel('Publishing Templates: Shot', paneTemplates)
        lbl_templates.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_templates.setFixedSize(840, 28)
        lbl_templates.setAlignment(QtCore.Qt.AlignCenter)

        # Publish::Tempates: Publish Template label
        lbl_shotTemplate = QtWidgets.QLabel('Publish', paneTemplates)
        lbl_shotTemplate.setFixedSize(88, 28)
        lbl_shotTemplate.move(0, 34)

        # Publish::Tempates: Batch Template label
        lbl_batchTemplate = QtWidgets.QLabel('Batch', paneTemplates)
        lbl_batchTemplate.setFixedSize(88, 28)
        lbl_batchTemplate.move(0, 68)

        # Publish::Tempates: Version Template label
        lbl_versionTemplate = QtWidgets.QLabel('Version', paneTemplates)
        lbl_versionTemplate.setFixedSize(88, 28)
        lbl_versionTemplate.move(0, 102)

        # Publish::Templates::ShotPane: Show and hide
        # depending on an Entity toggle
        
        paneShotTemplates = QtWidgets.QWidget(paneTemplates)
        paneShotTemplates.setFixedSize(776, 142)
        paneShotTemplates.move(64, 34)
        
        # Publish::Templates::ShotPane: Publish default button
        def setShotDefault():
            txt_shot.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_render').get('default', ''))
        btn_shotDefault = QtWidgets.QPushButton('Default', paneShotTemplates)
        btn_shotDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotDefault.setFixedSize(88, 28)
        btn_shotDefault.move(0, 0)
        btn_shotDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotDefault.clicked.connect(setShotDefault)

        # Publish::Templates::ShotPane: Publish template text field
        txt_shot_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_render').get('value', '')
        txt_shot = QtWidgets.QLineEdit(txt_shot_value, paneShotTemplates)
        txt_shot.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_shot.setFixedSize(588, 28)
        txt_shot.move (94, 0)
        txt_shot.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::ShotPane: Publish template fields button
        def addShotField(field):
            txt_shot.insert(field)
        shot_template_fields = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('fields', [])
        btn_shotFields = QtWidgets.QPushButton('Add Field', paneShotTemplates)
        btn_shotFields.setFixedSize(88, 28)
        btn_shotFields.move(688, 0)
        btn_shotFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotFields_menu = QtWidgets.QMenu()
        for field in shot_template_fields:
            action = btn_shotFields_menu.addAction(field)
            x = lambda chk=False, field=field: addShotField(field)
            action.triggered[()].connect(x)
        btn_shotFields.setMenu(btn_shotFields_menu)

        # Publish::Templates::ShotPane: Batch template default button
        def setShotBatchDefault():
            txt_shotBatch.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_batch').get('default', ''))
        btn_shotBatchDefault = QtWidgets.QPushButton('Default', paneShotTemplates)
        btn_shotBatchDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotBatchDefault.setFixedSize(88, 28)
        btn_shotBatchDefault.move(0, 34)
        btn_shotBatchDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotBatchDefault.clicked.connect(setShotBatchDefault)

        # Publish::Templates::ShotPane: Batch template text field

        txt_shotBatch_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_batch').get('value', '')
        txt_shotBatch = QtWidgets.QLineEdit(txt_shotBatch_value, paneShotTemplates)
        txt_shotBatch.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_shotBatch.setMinimumSize(588, 28)
        txt_shotBatch.move(94, 34)
        txt_shotBatch.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::ShotPane: Batch template fields button
        def addShotBatchField(field):
            txt_shotBatch.insert(field)
        btn_shotBatchFields = QtWidgets.QPushButton('Add Field', paneShotTemplates)
        btn_shotBatchFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotBatchFields.setMinimumSize(88, 28)
        btn_shotBatchFields.move(688, 34)
        btn_shotBatchFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotBatchFields_menu = QtWidgets.QMenu()
        for field in shot_template_fields:
            action = btn_shotBatchFields_menu.addAction(field)
            x = lambda chk=False, field=field: addShotBatchField(field)
            action.triggered[()].connect(x)
        btn_shotBatchFields.setMenu(btn_shotBatchFields_menu)

        # Publish::Templates::ShotPane: Version template default button
        def setShotVersionDefault():
            txt_shotVersion.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('version_name').get('default', ''))
        btn_shotVersionDefault = QtWidgets.QPushButton('Default', paneShotTemplates)
        btn_shotVersionDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotVersionDefault.setMinimumSize(88, 28)
        btn_shotVersionDefault.move(0, 68)
        btn_shotVersionDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotVersionDefault.clicked.connect(setShotVersionDefault)

        # Publish::Templates::ShotPane: Vesrion template text field

        txt_shotVersion_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('version_name').get('value', '')
        txt_shotVersion = QtWidgets.QLineEdit(txt_shotVersion_value, paneShotTemplates)
        txt_shotVersion.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_shotVersion.setMinimumSize(256, 28)
        txt_shotVersion.move(94, 68)
        txt_shotVersion.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::ShotPane: Version template fields button
        def addShotVersionField(field):
            txt_shotVersion.insert(field)
        btn_shotVersionFields = QtWidgets.QPushButton('Add Field', paneShotTemplates)
        btn_shotVersionFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotVersionFields.setMinimumSize(88, 28)
        btn_shotVersionFields.move(356, 68)
        btn_shotVersionFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_shotVersionFields_menu = QtWidgets.QMenu()
        for field in shot_template_fields:
            action = btn_shotVersionFields_menu.addAction(field)
            x = lambda chk=False, field=field: addShotVersionField(field)
            action.triggered[()].connect(x)
        btn_shotVersionFields.setMenu(btn_shotVersionFields_menu)

        # Publish::Templates::ShotPane: Version zero button
        '''
        def update_shotVersionZero():
            publish_prefs = self.framework.prefs.get('flameMenuPublisher', {})
            version_zero = publish_prefs.get('version_zero', False)
            if version_zero:
                btn_shotVersionZero.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            else:sequences/{SeqnuPublisher']['version_zero'] = not version_zero
            update_shotVersionZero()
            update_assetVersionZero()

        btn_shotVersionZero = QtWidgets.QPushButton('Start From Zero', paneShotTemplates)
        btn_shotVersionZero.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_shotVersionZero.setMinimumSize(108, 28)
        btn_shotVersionZero.move(450, 102)
        btn_shotVersionZero.clicked.connect(clicked_shotVersionZero)
        update_shotVersionZero()
        '''

        '''
        # Publish::Templates::ShotPane: Poster Frame Label

        lbl_shotPosterFrame = QtWidgets.QLabel('Thumbnail Frame', paneShotTemplates)
        lbl_shotPosterFrame.setFixedSize(108, 28)
        lbl_shotPosterFrame.move(568, 102)
        lbl_shotPosterFrame.setStyleSheet('QLabel {color: #989898}')

        # Publish::Templates::ShotPane: Poster Frame text field

        txt_shotPosterFrame = QtWidgets.QLineEdit('1', paneShotTemplates)
        txt_shotPosterFrame.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_shotPosterFrame.setFixedSize(40, 28)
        txt_shotPosterFrame.move(682, 102)
        txt_shotPosterFrame.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        '''

        # Publish::Templates::ShotPane: END OF SECTION
        # Publish::Templates::AssetPane: Show and hide
        # depending on an Entity toggle

        paneAssetTemplates = QtWidgets.QWidget(paneTemplates)
        paneAssetTemplates.setFixedSize(776, 142)
        paneAssetTemplates.move(64, 34)

        # Publish::Templates::AssetPane: Publish default button
        def setAssetDefault():
            txt_asset.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_render').get('default', ''))
        btn_assetDefault = QtWidgets.QPushButton('Default', paneAssetTemplates)
        btn_assetDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetDefault.setFixedSize(88, 28)
        btn_assetDefault.move(0, 0)
        btn_assetDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetDefault.clicked.connect(setAssetDefault)

        # Publish::Templates::AssetPane: Publish template text field
        txt_asset_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_render').get('value', '')
        txt_asset = QtWidgets.QLineEdit(txt_asset_value, paneAssetTemplates)
        txt_asset.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_asset.setFixedSize(588, 28)
        txt_asset.move (94, 0)
        txt_asset.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::AssetPane: Publish template fields button
        asset_template_fields = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('fields', [])

        def addAssetField(field):
            txt_asset.insert(field)
        btn_assetFields = QtWidgets.QPushButton('Add Field', paneAssetTemplates)
        btn_assetFields.setFixedSize(88, 28)
        btn_assetFields.move(688, 0)
        btn_assetFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetFields_menu = QtWidgets.QMenu()
        for field in asset_template_fields:
            action = btn_assetFields_menu.addAction(field)
            x = lambda chk=False, field=field: addAssetField(field)
            action.triggered[()].connect(x)
        btn_assetFields.setMenu(btn_assetFields_menu)

        # Publish::Templates::AssetPane: Batch template default button
        def setAssetBatchDefault():
            txt_assetBatch.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_batch').get('default', ''))
        btn_assetBatchDefault = QtWidgets.QPushButton('Default', paneAssetTemplates)
        btn_assetBatchDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetBatchDefault.setFixedSize(88, 28)
        btn_assetBatchDefault.move(0, 34)
        btn_assetBatchDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetBatchDefault.clicked.connect(setAssetBatchDefault)

        # Publish::Templates::AssetPane: Batch template text field
        txt_assetBatch_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_batch').get('value', '')
        txt_assetBatch = QtWidgets.QLineEdit(txt_assetBatch_value, paneAssetTemplates)
        txt_assetBatch.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_assetBatch.setMinimumSize(588, 28)
        txt_assetBatch.move(94, 34)
        txt_assetBatch.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::AssetPane: Batch template fields button
        def addAssetBatchField(field):
            txt_assetBatch.insert(field)
        btn_assetBatchFields = QtWidgets.QPushButton('Add Field', paneAssetTemplates)
        btn_assetBatchFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetBatchFields.setMinimumSize(88, 28)
        btn_assetBatchFields.move(688, 34)
        btn_assetBatchFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetBatchFields_menu = QtWidgets.QMenu()
        for field in asset_template_fields:
            action = btn_assetBatchFields_menu.addAction(field)
            x = lambda chk=False, field=field: addAssetBatchField(field)
            action.triggered[()].connect(x)
        btn_assetBatchFields.setMenu(btn_assetBatchFields_menu)

        # Publish::Templates::AssetPane: Version template default button
        def setAssetVersionDefault():
            txt_assetVersion.setText(self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('version_name').get('default', ''))
        btn_assetVersionDefault = QtWidgets.QPushButton('Default', paneAssetTemplates)
        btn_assetVersionDefault.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetVersionDefault.setMinimumSize(88, 28)
        btn_assetVersionDefault.move(0, 68)
        btn_assetVersionDefault.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetVersionDefault.clicked.connect(setAssetVersionDefault)

        # Publish::Templates::AssetPane: Vesrion template text field
        txt_assetVersion_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('version_name').get('value', '')
        txt_assetVersion = QtWidgets.QLineEdit(txt_assetVersion_value, paneAssetTemplates)
        txt_assetVersion.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_assetVersion.setMinimumSize(256, 28)
        txt_assetVersion.move(94, 68)
        txt_assetVersion.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')

        # Publish::Templates::AssetPane: Version template fields button
        def addAssetVersionField(field):
            txt_assetVersion.insert(field)
        btn_assetVersionFields = QtWidgets.QPushButton('Add Field', paneAssetTemplates)
        btn_assetVersionFields.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetVersionFields.setMinimumSize(88, 28)
        btn_assetVersionFields.move(356, 68)
        btn_assetVersionFields.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
        btn_assetVersionFields_menu = QtWidgets.QMenu()
        for field in asset_template_fields:
            action = btn_assetVersionFields_menu.addAction(field)
            x = lambda chk=False, field=field: addAssetVersionField(field)
            action.triggered[()].connect(x)
        btn_assetVersionFields.setMenu(btn_assetVersionFields_menu)

        # Publish::Templates::AssetPane: Version zero button
        '''
        def update_assetVersionZero():
            publish_prefs = self.framework.prefs.get('flameMenuPublisher', {})
            version_zero = publish_prefs.get('version_zero', False)
            if version_zero:
                btn_assetVersionZero.setStyleSheet('QPushButton {font:italic; background-color: #4f4f4f; color: #d9d9d9; border-top: 1px inset #555555; border-bottom: 1px inset black}')
            else:
                btn_assetVersionZero.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')

        def clicked_assetVersionZero():
            publish_prefs = self.framework.prefs.get('flameMenuPublisher', {})
            version_zero = publish_prefs.get('version_zero', False)
            self.framework.prefs['flameMenuPublisher']['version_zero'] = not version_zero
            update_shotVersionZero()
            update_assetVersionZero()

        btn_assetVersionZero = QtWidgets.QPushButton('Start From Zero', paneAssetTemplates)
        btn_assetVersionZero.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_assetVersionZero.setMinimumSize(108, 28)
        btn_assetVersionZero.move(450, 102)
        btn_assetVersionZero.clicked.connect(clicked_shotVersionZero)
        update_assetVersionZero()
        '''

        # Publish::Templates::AssetPane: END OF SECTION


        vbox_publish.addWidget(paneTemplates)
        panePublish.setLayout(vbox_publish)
        panePublish.setFixedSize(860, 280)
        panePublish.move(160, 10)
        panePublish.setVisible(False)


        # Superclips

        paneSuperclips.setFixedSize(840, 264)
        paneSuperclips.move(172, 20)
        paneSuperclips.setVisible(False)
        lbl_paneSuperclips = QtWidgets.QLabel('Superclis', paneSuperclips)
        lbl_paneSuperclips.setStyleSheet('QFrame {color: #989898}')
        lbl_paneSuperclips.setFixedSize(840, 264)
        lbl_paneSuperclips.setAlignment(QtCore.Qt.AlignCenter)
        lbl_paneSuperclips.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)

        # Close button

        def close_prefs_dialog():
            self.framework.prefs['flameMenuPublisher']['templates']['Shot']['flame_render']['value'] = txt_shot.text()
            self.framework.prefs['flameMenuPublisher']['templates']['Shot']['flame_batch']['value'] = txt_shotBatch.text()
            self.framework.prefs['flameMenuPublisher']['templates']['Shot']['version_name']['value'] = txt_shotVersion.text()
            self.framework.save_prefs()
            window.accept()

        close_btn = QtWidgets.QPushButton('Close', window)
        close_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        close_btn.setFixedSize(88, 28)
        close_btn.move(924, 292)
        close_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        close_btn.clicked.connect(close_prefs_dialog)

        # Set default tab and start window
        action_showShot()
        pressPublish()
        window.exec_()

    def rescan(self, *args, **kwargs):
        if not self.flame:
            try:
                import flame
                self.flame = flame
            except:
                self.flame = None

        # self.connector.cache_retrive_result(self.active_projects_uid, True)

        if self.flame:
            self.flame.execute_shortcut('Rescan Python Hooks')
            self.log_debug('Rescan Python Hooks')


# --- FLAME STARTUP SEQUENCE ---
# Flame startup sequence is a bit complicated
# If the app installed in /opt/Autodesk/<user>/python
# project hooks are not called at startup. 
# One of the ways to work around it is to check 
# if we are able to import flame module straght away. 
# If it is the case - flame project is already loaded 
# and we can start out constructor. Otherwise we need 
# to wait for app_initialized hook to be called - that would 
# mean the project is finally loaded. 
# project_changed_dict hook seem to be a good place to wrap things up

# main objects:
# app_framework takes care of preferences and general stuff
# kitsuConnector is a gateway to KITSU database
# apps is a list of apps to load inside the main program

app_framework = None
kitsuConnector = None
apps = []

# Exception handler
'''
def exeption_handler(exctype, value, tb):
    from PySide2 import QtWidgets
    import traceback
    msg = 'flameMenuSG: Python exception %s in %s' % (value, exctype)
    mbox = QtWidgets.QMessageBox()
    mbox.setText(msg)
    mbox.setDetailedText(pformat(traceback.format_exception(exctype, value, tb)))
    mbox.setStyleSheet('QLabel{min-width: 800px;}')
    mbox.exec_()
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exeption_handler
'''

# register clean up logic to be called at Flame exit
def cleanup(apps, app_framework, kitsuConnector):
    if kitsuConnector: kitsuConnector.terminate_loops()
    
    if apps:
        if DEBUG:
            print ('[DEBUG %s] unloading apps:\n%s' % ('flameMenuSG', pformat(apps)))
        while len(apps):
            app = apps.pop()
            if DEBUG:
                print ('[DEBUG %s] unloading: %s' % ('flameMenuSG', app.name))
            del app        
        del apps

    if kitsuConnector: del kitsuConnector

    if app_framework:
        print ('PYTHON\t: %s cleaning up' % app_framework.bundle_name)
        app_framework.save_prefs()
        del app_framework

atexit.register(cleanup, apps, app_framework, kitsuConnector)

def load_apps(apps, app_framework, kitsuConnector):
    try:
        apps.append(flameMenuProjectconnect(app_framework, kitsuConnector))
        # apps.append(flameBatchBlessing(app_framework))
        # apps.append(flameMenuNewBatch(app_framework, kitsuConnector))
        # apps.append(flameMenuBatchLoader(app_framework, kitsuConnector))
        # apps.append(flameMenuPublisher(app_framework, kitsuConnector))
    except:
        pass

    app_framework.apps = apps
    if DEBUG:
        print ('[DEBUG %s] loaded:\n%s' % (app_framework.bundle_name, pformat(apps)))

def rescan_hooks():
    try:
        import flame
        flame.execute_shortcut('Rescan Python Hooks')
    except:
        pass

def project_changed_dict(info):
    global app_framework
    global kitsuConnector
    global apps
    cleanup(apps, app_framework, kitsuConnector)

def app_initialized(project_name):
    global app_framework
    global kitsuConnector
    global apps
    app_framework = flameAppFramework()
    print ('PYTHON\t: %s initializing' % app_framework.bundle_name)
    kitsuConnector = flameKitsuConnector(app_framework)
    load_apps(apps, app_framework, kitsuConnector)

app_initialized.__dict__["waitCursor"] = False

try:
    import flame
    app_initialized(flame.project.current_project.name)
except:
    pass

# --- FLAME OPERATIONAL HOOKS ---
def project_saved(project_name, save_time, is_auto_save):
    global app_framework

    if app_framework:
        app_framework.save_prefs()
            
def get_main_menu_custom_ui_actions():
    start = time.time()
    menu = []
    flameMenuProjectconnectApp = None
    
    pprint (apps)

    for app in apps:
        if app.__class__.__name__ == 'flameMenuProjectconnect':
            flameMenuProjectconnectApp = app
    if flameMenuProjectconnectApp:
        menu.append(flameMenuProjectconnectApp.build_menu())
    if menu:
        menu[0]['actions'].append({'name': __version__, 'isEnabled': False})

    if app_framework:
        menu_auto_refresh = app_framework.prefs_global.get('menu_auto_refresh', {})
        if menu_auto_refresh.get('main_menu', True):
            try:
                import flame
                flame.schedule_idle_event(rescan_hooks)
            except:
                pass
    
    if DEBUG:
        print('main menu update took %s' % (time.time() - start))

    return menu

def get_media_panel_custom_ui_actions():
    
    def scope_desktop(selection):
        import flame
        for item in selection:
            if isinstance(item, (flame.PyDesktop)):
                return True
        return False

    def scope_clip(selection):
        import flame
        for item in selection:
            if isinstance(item, (flame.PyClip)):
                return True
        return False

    start = time.time()
    menu = []

    selection = []
    try:
        import flame
        selection = flame.media_panel.selected_entries
    except:
        pass

    for app in apps:
        if app.__class__.__name__ == 'flameMenuNewBatch':
            if scope_desktop(selection) or (not selection):
                app_menu = app.build_menu()
                if app_menu:
                    menu.append(app_menu)

        if app.__class__.__name__ == 'flameMenuPublisher':
            if scope_clip(selection):
                app_menu = app.build_menu()
                if app_menu:
                    menu.extend(app_menu)

    if app_framework:
        menu_auto_refresh = app_framework.prefs_global.get('menu_auto_refresh', {})
        if menu_auto_refresh.get('media_panel', True):
            try:
                import flame
                flame.schedule_idle_event(rescan_hooks)
            except:
                pass
    
    if DEBUG:
        print('media panel menu update took %s' % (time.time() - start))
    
    return menu

def get_batch_custom_ui_actions():
    start = time.time()
    menu = []
    flameMenuBatchLoaderApp = None
    for app in apps:
        if app.__class__.__name__ == 'flameMenuBatchLoader':
            flameMenuBatchLoaderApp = app
    if flameMenuBatchLoaderApp:
        app_menu = flameMenuBatchLoaderApp.build_menu()
        if app_menu:
            for menuitem in app_menu:
                menu.append(menuitem)

    if app_framework:
        menu_auto_refresh = app_framework.prefs_global.get('menu_auto_refresh', {})
        if menu_auto_refresh.get('batch', True):
            try:
                import flame
                flame.schedule_idle_event(rescan_hooks)
            except:
                pass

    if DEBUG:
        print('batch menu update took %s' % (time.time() - start))

    return menu