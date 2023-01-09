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

menu_group_name = 'Menu(KITSU)'
app_name = 'flameMenuKITSU'
DEBUG = False

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
        self.framework.log('[' + self.name + '] ' + message)

    def log_debug(self, message):
        self.framework.log_debug('[' + self.name + '] ' + message)

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

        if not self.prefs_global.get('user signed out', False):
            self.log_debug('requesting for user')
            try:
                self.get_user()
            except Exception as e:
                self.log_debug(pformat(e))

        self.gazu_client = None
        
        '''
        if not 'tank_name_overrides' in self.prefs.keys():
            # tank_name_overrides are {'project_id': 'overrided_tank_name'}
            self.prefs['tank_name_overrides'] = {}
        
        self.sg_user = None
        self.sg_human_user = None
        self.sg_user_name = None
        self.sg = None
        if not self.prefs_global.get('user signed out', False):
            self.log_debug('requesting for Shotgun user')
            try:
                self.get_user()
            except Exception as e:
                self.log_debug(pformat(e))
        
        self.flame_project = None
        self.sg_linked_project = None
        self.sg_linked_project_id = None

        self.async_cache = {}

        self.async_cache_hash = hash(pformat(self.async_cache))

        self.flame_workspace_state = self.prefs.get('wks_state')
        if not self.flame_workspace_state:
            self.flame_workspace_state = {}

        self.check_sg_linked_project()
        self.update_sg_storage_root()

        # UID for all tasks in async cache

        self.current_tasks_uid = None
        self.current_versions_uid = None

        # loop threads init. first arg in args is loop cycle time in seconds

        self.loops = []
        self.threads = True
        self.loops.append(threading.Thread(target=self.cache_long_loop, args=(45, )))
        self.loops.append(threading.Thread(target=self.cache_short_loop, args=(4, )))
        # self.loops.append(threading.Thread(target=self.flame_scan_loop))
        
        for loop in self.loops:
            loop.daemon = True
            loop.start()

        self.tk_engine = None
        self.bootstrap_toolkit()

        # register tasks query for async cache loop
        self.register_common_queries()

        from PySide2 import QtWidgets
        self.mbox = QtWidgets.QMessageBox()
'''

    def log(self, message):
        self.framework.log('[' + self.name + '] ' + message)

    def log_debug(self, message):
        self.framework.log_debug('[' + self.name + '] ' + message)

    def get_user(self, *args, **kwargs):
        import base64
        # get saved credentials
        self.kitsu_host = self.prefs_user.get('kitsu_host', 'http://localhost/api/')
        self.kitsu_user = self.prefs_user.get('kitsu_user', 'username')
        encoded_kitsu_pass = self.prefs_user.get('kitsu_pass', '')
        if self.kitsu_pass:
            self.kitsu_pass = base64.b64decode(encoded_kitsu_pass).decode("utf-8")
        pprint (self.kitsu_pass)

        def login():
            host = self.kitsu_host
            if not host.endswith('/api/'):
                if self.kitsu_host.endswith('/'):
                    host = host + 'api/'
                else:
                    host = host + '/api/'
            elif host.endswith('/api'):
                host = host + ('/')

            try:
                self.gazu_client = self.gazu.client.create_client(host)
                self.gazu.log_in(self.kitsu_user, self.kitsu_pass, client = self.gazu_client)
                return True
            except Exception as e:
                pprint (e)
            return False

        login_status = False
        while not login_status:
            credentials = self.login_dialog()
            if not credentials:
                break
            else:
                self.kitsu_host = credentials.get('host')
                self.kitsu_user = credentials.get('user')
                self.kitsu_pass = credentials.get('password', '')
                login_status = login()

        pprint (self.gazu.client.get_current_user(client = self.gazu_client))

        self.prefs_user['kitsu_host'] = self.kitsu_host
        self.prefs_user['kitsu_user'] = self.kitsu_user
        self.prefs_user['kitsu_pass'] = base64.b64encode(self.kitsu_pass.encode("utf-8"))
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
        txt_KitsuHost.setFocusPolicy(QtCore.Qt.ClickFocus)
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
        txt_KitsuUser.setFocusPolicy(QtCore.Qt.ClickFocus)
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
        txt_KitsuPass.setFocusPolicy(QtCore.Qt.ClickFocus)
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
        select_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        select_btn.setMinimumSize(100, 28)
        select_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        select_btn.clicked.connect(window.accept)

        cancel_btn = QtWidgets.QPushButton('Cancel', window)
        cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
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
        pass
        # apps.append(flameMenuProjectconnect(app_framework, kitsuConnector))
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