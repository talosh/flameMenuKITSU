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
import traceback
from pprint import pprint, pformat

settings = {
    'menu_group_name': 'Kitsu',
    'debug': False,
    'app_name': 'flameMenuKITSU',
    'version': 'v0.0.6',
}

packages_folder = os.path.join(
    os.path.dirname(inspect.getfile(lambda: None)),
    'packages',
    '.site-packages'
)

if packages_folder not in sys.path:
    sys.path.append(packages_folder)
try:
    import gazu
except Exception as e:
    print (f'[{settings.get("app_name")}]: Unable to import Gazu: {e}')
if packages_folder in sys.path:
    sys.path.remove(packages_folder)

# __version__ = 'v0.0.6 dev 001'
# menu_group_name = 'KITSU'
# app_name = 'flameMenuKITSU'
# DEBUG = False

default_storage_root = '/media/dirtylooks_vfx'

shot_code_field = '30_dl_vfx_id'

default_templates = {
    'Shot': {
        'flame_render': {
            'default': '{Project}/scenes/{Sequence}/{Shot}/{TaskType}/publish/{Shot}_{name}_v{version}/{Shot}_{name}_v{version}.{frame}.{ext}',
            'PublishedFileType': 'Flame Render'
            },
        'flame_batch': {
            'default': '{Project}/scenes/{Sequence}/{Shot}/{TaskType}/publish/flame_batch/{Shot}_{name}_v{version}.batch',
            'PublishedFileType': 'Flame Batch File'                  
            },
        'version_name': {
            'default': '{Shot}_{name}_v{version}',
        },
        'fields': ['{Project}','{Sequence}', '{Shot}', '{TaskType}', '{name}', '{version}', '{version_four}', '{frame}', '{ext}']
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
        'fields': ['{Project}', '{Sequence}', '{AssetType}', '{Asset}', '{TaskType}', '{name}', '{version}', '{version_four}', '{frame}', '{ext}']
    }
}

default_templates_zou = {
    "working": {
        "mountpoint": "/media",
        "root": "dirtylooks_vfx",
        "folder_path": {
            "shot": "<Project>/scenes/<Sequence>/<Shot>/<TaskType>",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>",
            "sequence": "<Project>/sequences/<Sequence>/<TaskType>",
            "scene": "<Project>/scenes/<Sequence>/<Scene>/<TaskType>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Project>_<Shot>_<TaskType>",
            "asset": "<Project>_<AssetType>_<Asset>_<TaskType>",
            "sequence": "<Project>_<Sequence>_<TaskType>",
            "scene": "<Project>_<Sequence>_<Scene>_<TaskType>",
            "style": "lowercase"
        }
    },
    "output": {
        "mountpoint": "/media",
        "root": "dirtylooks_vfx",
        "folder_path": {
            "shot": "<Project>/shots/<Sequence>/<Shot>/<OutputType>",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<OutputType>",
            "sequence": "<Project>/sequences/<Sequence>/<OutputType>",
            "scene": "<Project>/scenes/<Sequence>/<Scene>/<OutputType>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Project>_<Sequence>_<Shot>_<OutputType>_<OutputFile>",
            "asset": "<Project>_<AssetType>_<Asset>_<OutputType>_<OutputFile>",
            "sequence": "<Project>_<Sequence>_<OuputType>_<OutputFile>",
            "scene": "<Project>_<Sequence>_<Scene>_<OutputType>_<OutputFile>",
            "style": "lowercase"
        }
    },
    "preview": {
        "mountpoint": "/media",
        "root": "dirtylooks_vfx",
        "folder_path": {
            "shot": "<Project>/shots/<Sequence>/<Shot>/<TaskType>",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>",
            "sequence": "<Project>/sequences/<Sequence>/<TaskType>",
            "scene": "<Project>/scene/<Scene>/<TaskType>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Project>_<Sequence>_<Shot>_<TaskType>",
            "asset": "<Project>_<AssetType>_<Asset>_<TaskType>",
            "sequence": "<Project>_<Sequence>_<TaskType>",
            "scene": "<Project>_<Scene>_<TaskType>",
            "style": "lowercase"
        }
    }
}

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
            return list(self.master[self.name].keys())

        @classmethod
        def fromkeys(cls, keys, v=None):
            return self.master[self.name].fromkeys(keys, v)
        
        def __repr__(self):
            return '{0}({1})'.format(type(self).__name__, self.master[self.name].__repr__())

        def master_keys(self):
            return list(self.master.keys())

    def __init__(self, *args, **kwargs):
        self.name = self.__class__.__name__
        self.app_name = kwargs.get('app_name', 'flameApp')
        self.bundle_name = self.sanitize_name(self.app_name)
        self.version = settings['version']
        # self.prefs scope is limited to flame project and user
        self.prefs = {}
        self.prefs_user = {}
        self.prefs_global = {}
        self.debug = settings['debug']
        
        try:
            import flame
            self.flame = flame
            self.flame_project_name = self.flame.project.current_project.name
            self.flame_user_name = flame.users.current_user.name
        except:
            self.flame = None
            self.flame_project_name = 'UnknownFlameProject'
            self.flame_user_name = 'UnknownFlameUser'
        
        import socket
        self.hostname = socket.gethostname()
        
        if sys.platform == 'darwin':
            self.prefs_folder = os.path.join(
                os.path.expanduser('~'),
                 'Library',
                 'Preferences',
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

        '''
        # site-packages check and payload unpack if nessesary
        self.site_packages_folder = os.path.join(
            '/var/tmp',
            self.bundle_name,
            'site-packages'
        )

        if not self.check_bundle_id():
            self.unpack_bundle(os.path.dirname(self.site_packages_folder))
        '''

    def log(self, message):
        try:
            print ('[%s] %s' % (self.bundle_name, str(message)))
        except:
            pass

    def log_debug(self, message):
        if self.debug:
            try:
                print ('[DEBUG %s] %s' % (self.bundle_name, str(message)))
            except:
                pass

    def load_prefs(self):
        import json

        prefix = self.prefs_folder + os.path.sep + self.bundle_name
        prefs_file_path = prefix + '.' + self.flame_user_name + '.' + self.flame_project_name + '.prefs.json'
        prefs_user_file_path = prefix + '.' + self.flame_user_name  + '.prefs.json'
        prefs_global_file_path = prefix + '.prefs.json'

        def tuple_decoder(obj):
            if "__tuple__" in obj:
                return tuple(obj["data"])
            return obj

        try:
            with open(prefs_file_path, 'r') as prefs_file:
                self.prefs = json.load(prefs_file, object_hook=tuple_decoder)
            self.log_debug('preferences loaded from %s' % prefs_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs, indent=4))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_file_path)
            self.log_debug(e)

        try:
            with open(prefs_user_file_path, 'r') as prefs_file:
                self.prefs_user = json.load(prefs_file, object_hook=tuple_decoder)
            self.log_debug('preferences loaded from %s' % prefs_user_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs_user, indent=4))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_user_file_path)
            self.log_debug(e)

        try:
            with open(prefs_global_file_path, 'r') as prefs_file:
                self.prefs_global = json.load(prefs_file, object_hook=tuple_decoder)
            self.log_debug('preferences loaded from %s' % prefs_global_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs_global, indent=4))
        except Exception as e:
            self.log('unable to load preferences from %s' % prefs_global_file_path)
            self.log_debug(e)

        return True
    
    def save_prefs(self):
        import json

        class TupleKeyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, dict):
                    return {json.dumps(k): v for k, v in obj.items()}  # Convert tuples to JSON strings
                return super().default(obj)

        class TupleEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, tuple):
                    return {"__tuple__": True, "data": list(obj)}  # Store as object with a key
                return super().default(obj)

        if not os.path.isdir(self.prefs_folder):
            try:
                os.makedirs(self.prefs_folder)
            except:
                self.log('unable to create folder %s' % self.prefs_folder)
                return False

        prefix = self.prefs_folder + os.path.sep + self.bundle_name
        prefs_file_path = prefix + '.' + self.flame_user_name + '.' + self.flame_project_name + '.prefs.json'
        prefs_user_file_path = prefix + '.' + self.flame_user_name  + '.prefs.json'
        prefs_global_file_path = prefix + '.prefs.json'

        try:
            with open(prefs_file_path, 'w') as prefs_file:
                json.dump(self.prefs, prefs_file, cls=TupleKeyEncoder, indent=4)
            self.log_debug('preferences saved to %s' % prefs_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs, indent=4))
        except Exception as e:
            self.log('unable to save preferences to %s' % prefs_file_path)
            self.log(e)
            pprint (self.prefs)

        try:
            with open(prefs_user_file_path, 'w') as prefs_file:
                json.dump(self.prefs_user, prefs_file, cls=TupleKeyEncoder, indent=4)
            self.log_debug('preferences saved to %s' % prefs_user_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs_user, indent=4))
        except Exception as e:
            self.log('unable to save preferences to %s' % prefs_user_file_path)
            self.log(e)
            pprint (self.prefs)

        try:
            with open(prefs_global_file_path, 'w') as prefs_file:
                json.dump(self.prefs_global, prefs_file, cls=TupleKeyEncoder, indent=4)
            self.log_debug('preferences saved to %s' % prefs_global_file_path)
            self.log_debug('preferences contents:\n' + json.dumps(self.prefs_global, indent=4))
        except Exception as e:
            self.log('unable to save preferences to %s' % prefs_global_file_path)
            self.log(e)
            pprint (self.prefs)

        return True

    def check_bundle_id(self):
        bundle_id_file_path = os.path.join(
            os.path.dirname(self.site_packages_folder),
            'bundle_id'
            )
        bundle_id = self.version

        if (os.path.isdir(self.site_packages_folder) and os.path.isfile(bundle_id_file_path)):
            self.log('checking existing bundle id %s' % bundle_id_file_path)
            try:
                with open(bundle_id_file_path, 'r') as bundle_id_file:
                    if bundle_id_file.read() == bundle_id:
                        self.log('site packages folder exists with id matching current version')
                        bundle_id_file.close()
                        return True
                    else:
                        self.log('existing env bundle id does not match current one')
                        return False
            except Exception as e:
                self.log(pformat(e))
                return False
        elif not os.path.isdir(self.site_packages_folder):
            self.log('site packages folder does not exist: %s' % self.site_packages_folder)
            return False
        elif not os.path.isfile(bundle_id_file_path):
            self.log('site packages bundle id file does not exist: %s' % bundle_id_file_path)
            return False

    def unpack_bundle(self, bundle_path):
        start = time.time()
        script_file_name, ext = os.path.splitext(os.path.abspath(__file__))
        script_file_name += '.py'
        self.log('script file: %s' % script_file_name)
        script = None
        payload = None

        try:
            with open(script_file_name, 'r+') as scriptfile:
                script = scriptfile.read()
                start_position = script.rfind('# bundle payload starts here')
                
                if script[start_position -1: start_position] != '\n':
                    scriptfile.close()
                    return False

                start_position += 33
                payload = script[start_position:-4]
                # scriptfile.truncate(start_position - 34)
                scriptfile.close()
        except Exception as e:
            self.log_exception(e)
            return False
        
        del script
        if not payload:
            return False

        bundle_backup_folder = ''
        if os.path.isdir(bundle_path):
            bundle_backup_folder = os.path.abspath(bundle_path + '.previous')
            if os.path.isdir(bundle_backup_folder):
                try:
                    cmd = 'rm -rf "' + os.path.abspath(bundle_backup_folder) + '"'
                    self.log('removing previous backup folder')
                    self.log('Executing command: %s' % cmd)
                    os.system(cmd)
                except Exception as e:
                    self.log_exception(e)
                    return False
            try:
                cmd = 'mv "' + os.path.abspath(bundle_path) + '" "' + bundle_backup_folder + '"'
                self.log('backing up existing bundle folder')
                self.log('Executing command: %s' % cmd)
                os.system(cmd)
            except Exception as e:
                self.log_exception(e)
                return False

        try:
            self.log('creating new bundle folder: %s' % bundle_path)
            os.makedirs(bundle_path)
        except Exception as e:
            self.log_exception(e)
            return False

        payload_dest = os.path.join(
            bundle_path, 
            self.sanitize_name(self.bundle_name + '.' + __version__ + '.bundle.tar')
            )
        
        try:
            import base64
            self.log('unpacking payload: %s' % payload_dest)
            with open(payload_dest, 'wb') as payload_file:
                payload_file.write(base64.b64decode(payload))
                payload_file.close()
            cmd = 'tar xf "' + payload_dest + '" -C "' + bundle_path + '/"'
            self.log('Executing command: %s' % cmd)
            status = os.system(cmd)
            self.log('exit status %s' % os.WEXITSTATUS(status))

            # self.log('cleaning up %s' % payload_dest, logfile)
            # os.remove(payload_dest)
        
        except Exception as e:
            self.log_exception(e)
            return False

        delta = time.time() - start
        self.log('bundle extracted to %s' % bundle_path)
        self.log('extracting bundle took %s sec' % '{:.1f}'.format(delta))

        del payload
        try:
            os.remove(payload_dest)
        except Exception as e:
            self.log_exception(e)

        try:
            with open(os.path.join(bundle_path, 'bundle_id'), 'w+') as bundle_id_file:
                bundle_id_file.write(self.version)
        except Exception as e:
            self.log_exception(e)
            return False
        
        return True

    def log_exception(self, e):
        self.log(pformat(e))
        self.log_debug(pformat(traceback.format_exc()))

    def sanitize_name(self, name_to_sanitize):
        if name_to_sanitize is None:
            return None
        
        stripped_name = name_to_sanitize.strip()
        exp = re.compile(u'[^\w\.-]', re.UNICODE)

        result = exp.sub('_', stripped_name)
        return re.sub('_\_+', '_', result)


class flameMenuApp(object):
    def __init__(self, framework):
        self.name = self.__class__.__name__
        self.framework = framework
        self.connector = None
        self.menu_group_name = settings['menu_group_name']
        self.debug = settings['debug']
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

        try:
            from PySide2 import QtWidgets
            self.mbox = QtWidgets.QMessageBox()
        except ImportError:
            from PySide6 import QtWidgets
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
            preset_file = preset.get('PresetFile', 'OpenEXR/OpenEXR (16-bit fp PIZ).xml')
            if preset_file.startswith(os.path.sep):
                preset_file = preset_file[1:]

            for visibility in range(4):
                export_preset_folder = flame.PyExporter.get_presets_dir(flame.PyExporter.PresetVisibility.values.get(visibility),
                                flame.PyExporter.PresetType.values.get(0))
                preset_path = os.path.join(export_preset_folder, preset_file)
                if os.path.isfile(preset_path):
                    break

            '''
            path_prefix = self.flame.PyExporter.get_presets_dir(
                self.flame.PyExporter.PresetVisibility.values.get(preset.get('PresetVisibility', 1)),
                self.flame.PyExporter.PresetType.values.get(preset.get('PresetType', 0))
            )

            print (f'path prefix: {path_prefix}')

            preset_file = preset.get('PresetFile', 'OpenEXR/OpenEXR (16-bit fp PIZ).xml')
            if preset_file.startswith(os.path.sep):
                preset_file = preset_file[1:]
            preset_path = os.path.join(path_prefix, preset_file)
            '''

        # print (f'preset_path: {preset_path}')

        self.log_debug('parsing Flame export preset: %s' % preset_path)
        
        preset_xml_doc = None
        try:
            preset_xml_doc = minidom.parse(preset_path)
        except Exception as e:
            message = f'{settings["app_name"]}: Unable to parse xml export preset file:\n{e}'
            self.mbox.setText(message)
            self.mbox.exec_()
            return {}

        preset_fields['path'] = preset_path

        preset_type = preset_xml_doc.getElementsByTagName('type')
        if len(preset_type) > 0:
            preset_fields['type'] = preset_type[0].firstChild.data

        video = preset_xml_doc.getElementsByTagName('video')
        if len(video) < 1:
            message = 'flameMenuKITSU: XML parser error:\nUnable to find xml video tag in:\n%s' % preset_path
            self.mbox.setText(message)
            self.mbox.exec_()
            return {}
        
        filetype = video[0].getElementsByTagName('fileType')
        if len(filetype) < 1:
            message = 'flameMenuKITSU: XML parser error:\nUnable to find video::fileType tag in:\n%s' % preset_path
            self.mbox.setText(message)
            self.mbox.exec_()
            return {}

        preset_fields['fileType'] = filetype[0].firstChild.data
        if preset_fields.get('fileType', '') not in flame_extension_map:
            message = 'flameMenuKITSU:\nUnable to find extension corresponding to fileType:\n%s' % preset_fields.get('fileType', '')
            self.mbox.setText(message)
            self.mbox.exec_()
            return {}
        
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
        self.app_name = settings['app_name']
        self.framework = framework
        self.connector = self
        self.log('waking up')

        self.prefs = self.framework.prefs_dict(self.framework.prefs, self.name)
        self.prefs_user = self.framework.prefs_dict(self.framework.prefs_user, self.name)
        self.prefs_global = self.framework.prefs_dict(self.framework.prefs_global, self.name)

        self.gazu = gazu

        '''
        site_packages_folder = self.framework.site_packages_folder
        if not os.path.isdir(site_packages_folder):
            self.log('unable to find site packages folder at %s' % site_packages_folder)
            self.gazu = None
        else:
            sys.path.insert(0, site_packages_folder)
            import gazu
            self.gazu = gazu
            sys.path.pop(0)
        '''

        self.gazu_client = None

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

        if not self.prefs.get('storage_root'):
            self.prefs['storage_root'] = default_storage_root
            self.framework.save_prefs()

        self.flame_project = None
        self.linked_project = None
        self.linked_project_id = None

        self.init_pipeline_data()
        self.shot_code_field = shot_code_field

        self.check_linked_project()

        self.loops = []
        self.threads = True
        self.loops.append(threading.Thread(target=self.cache_short_loop, args=(8, )))
        self.loops.append(threading.Thread(target=self.cache_long_loop, args=(8, )))
        self.loops.append(threading.Thread(target=self.cache_utility_loop, args=(1, )))

        for loop in self.loops:
            loop.daemon = True
            loop.start()

        try:
            from PySide2 import QtWidgets
            self.mbox = QtWidgets.QMessageBox()
        except ImportError:
            from PySide6 import QtWidgets
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

        def login(msg=True):
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
                if msg:
                    self.mbox.setText(pformat(e))
                    self.mbox.exec_()
            return False

        login_status = login(msg=False)
        while not login_status:
            credentials = self.login_dialog()
            if not credentials:
                self.prefs_global['user signed out'] = True
                self.kitsu_pass = ''
                break
            else:
                self.kitsu_host = credentials.get('host')
                self.kitsu_user = credentials.get('user')
                self.kitsu_pass = credentials.get('password', '')
                login_status = login()

        # self.log_debug(pformat(self.user))
        self.log_debug(self.user_name)

        self.prefs_user['kitsu_host'] = self.kitsu_host
        self.prefs_user['kitsu_user'] = self.kitsu_user
        self.prefs_user['kitsu_pass'] = base64.b64encode(self.kitsu_pass.encode("utf-8")).decode("utf-8")
        self.framework.save_prefs()

    def get_gazu_version(self):
        if not self.gazu:
            return None
        return self.gazu.__version__

    def get_api_version(self):
        if not self.gazu:
            return None
        if not self.gazu_client:
            return None
        try:
            return self.gazu.client.get_api_version(client = self.gazu_client)
        except:
            return None

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
        try:
            from PySide2 import QtWidgets, QtCore
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui

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

        if QtCore.__version_info__[0] < 6:
            screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        else:
            mainWindow = QtGui.QGuiApplication.primaryScreen()
            screen_res = mainWindow.screenGeometry()
        
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

        lbl_User = QtWidgets.QLabel('User: ', window)
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
        select_btn.setDefault(True)

        cancel_btn = QtWidgets.QPushButton('Cancel', window)
        cancel_btn.setFocusPolicy(QtCore.Qt.StrongFocus)
        cancel_btn.setMinimumSize(100, 28)
        cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        cancel_btn.clicked.connect(window.reject)
        cancel_btn.setDefault(False)

        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(cancel_btn)
        hbox4.addWidget(select_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(20, 20, 20, 20)
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
                self.linked_project_id = project.get('id')
            else:
                self.log_debug('no project id found for project name: %s' % flame.project.current_project.shotgun_project_name)
        return True

    def init_pipeline_data(self):
        self.pipeline_data = {}
        self.pipeline_data['current_project'] = {}
        self.pipeline_data['project_tasks_for_person'] = []
        self.pipeline_data['all_episodes_for_project'] = []
        self.pipeline_data['all_sequences_for_project'] = []
        self.pipeline_data['all_shots_for_project'] = []
        self.pipeline_data['all_assets_for_project'] = []
        self.pipeline_data['entitiy_keys'] = set()
        self.pipeline_data['tasks_by_entity_id'] = {}
        self.pipeline_data['preview_by_task_id'] = {}
        self.pipeline_data['all_task_types_for_project'] = []
        self.pipeline_data['all_task_statuses_for_project'] = []
        self.pipeline_data['entity_by_id'] = {}

    def cache_short_loop(self, timeout):
        avg_delta = timeout / 2
        recent_deltas = [avg_delta]*9
        while self.threads:
            start = time.time()                
            
            if (not self.user) and (not self.linked_project_id):
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
                self.log_debug('short loop: no id')
                self.gazu.log_out(client = shortloop_gazu_client)
                time.sleep(1)
                continue
            
            active_projects = self.pipeline_data.get('active_projects')
            if not active_projects:
                self.log_debug('no active_projects')
                self.gazu.log_out(client = shortloop_gazu_client)
                time.sleep(1)
                continue

            projects_by_id = {x.get('id'):x for x in self.pipeline_data['active_projects']}
            current_project = projects_by_id.get(self.linked_project_id)
            
            self.collect_pipeline_data(current_project=current_project, current_client=shortloop_gazu_client)

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

    def cache_long_loop(self, timeout):
        avg_delta = timeout / 2
        recent_deltas = [avg_delta]*9
        while self.threads:
            start = time.time()

            if (not self.user) and (not self.linked_project_id):
                time.sleep(1)
                continue

            longloop_gazu_client = None
            try:
                host = self.kitsu_host
                if not host.endswith('/api/'):
                    if self.kitsu_host.endswith('/'):
                        host = host + 'api/'
                    else:
                        host = host + '/api/'
                elif host.endswith('/api'):
                    host = host + ('/')
                longloop_gazu_client = self.gazu.client.create_client(host)
                self.gazu.log_in(self.kitsu_user, self.kitsu_pass, client=longloop_gazu_client)

                # main job body
                for entity_key in self.pipeline_data.get('entitiy_keys'):
                    self.collect_entity_linked_info(entity_key, current_client = longloop_gazu_client)
                
            except Exception as e:
                self.log_debug('error updating cache in cache_long_loop: %s' % e)

            self.gazu.log_out(client = longloop_gazu_client)
            
            # self.preformat_common_queries()

            self.log_debug('cache_long_loop took %s sec' % str(time.time() - start))
            delta = time.time() - start
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

    def cache_utility_loop(self, timeout):
        while self.threads:
            start = time.time()                
            
            if (not self.user) and (not self.linked_project_id):
                time.sleep(1)
                continue

            # pprint (self.pipeline_data['current_project'])

            self.loop_timeout(timeout, start)

    def collect_pipeline_data(self, current_project = None, current_client = None):
        if not self.linked_project_id:
            return
        if not current_project:
            current_project = {'id': self.linked_project_id}
        if not current_client:
            current_client = self.gazu_client

        # query requests defined as functions

        def get_current_project():
            try:
                current_project = self.gazu.project.get_project(self.linked_project_id, client=current_client)
                self.pipeline_data['current_project'] = dict(current_project)
                self.pipeline_data['entity_by_id'][current_project.get('id')] = dict(current_project)
            except Exception as e:
                self.log(pformat(e))

        def project_tasks_for_person():
            try:
                all_tasks_for_person = self.gazu.task.all_tasks_for_person(self.user, client=current_client)
                all_tasks_for_person.extend(self.gazu.task.all_done_tasks_for_person(self.user, client=current_client))
                project_tasks_for_person = []
                for x in all_tasks_for_person:
                    if x.get('project_id') == self.linked_project_id:
                        project_tasks_for_person.append(x)
                self.pipeline_data['project_tasks_for_person'] = list(project_tasks_for_person)
                for task in project_tasks_for_person:
                    self.pipeline_data['entitiy_keys'].add((task.get('entity_type_name'), task.get('entity_id')))
            except Exception as e:
                self.log(pformat(e))

        def all_episodes_for_project():
            try:
                all_episodes_for_project = self.gazu.shot.all_episodes_for_project(current_project, client=current_client)
                if not isinstance(all_episodes_for_project, list):
                    all_episodes_for_project = []
                                 
                episodes = []
                for episode in all_episodes_for_project:
                    episode_assets = self.gazu.asset.all_assets_for_episode(episode, client=current_client)
                    if not isinstance(episode_assets, list):
                        episode_assets = []
                    episode_assets_by_id = {x.get('id'):x for x in episode_assets}
                    episode['assets'] = episode_assets
                    episode['assets_by_id'] = episode_assets_by_id
                    
                    episode_shots = self.gazu.shot.all_shots_for_episode(episode, client=current_client)
                    if not isinstance(episode_shots, list):
                        episode_shots = []
                    episode_shots_by_id = {x.get('id'):x for x in episode_shots}
                    episode['shots'] = episode_shots
                    episode['shots_by_id'] = episode_shots_by_id

                    episodes.append(episode)

                self.pipeline_data['all_episodes_for_project'] = list(episodes)
                for entity in all_episodes_for_project:
                    self.pipeline_data['entitiy_keys'].add((entity.get('type'), entity.get('id')))
                    self.pipeline_data['entity_by_id'][entity.get('id')] = entity
            except Exception as e:
                self.log(pformat(e))

        def all_assets_for_project():
            try:
                assets_with_modified_code = []
                all_assets_for_project = self.gazu.asset.all_assets_for_project(current_project, client=current_client)
                
                for asset in all_assets_for_project:
                    asset['code'] = asset['name']
                    if self.shot_code_field:
                        data = asset.get('data')
                        if data:
                            code = data.get(shot_code_field)
                            if code:
                                asset['code'] = code
                    assets_with_modified_code.append(asset)

                episodes = self.connector.pipeline_data.get('all_episodes_for_project')
                episodes_by_id = {x.get('id'):x for x in episodes}
                episode_id_by_entity_id = {}
                for episode in episodes:
                    episode_id = episode.get('id')
                    if not episode_id:
                        continue
                    episode_assets_by_id = episode.get('assets_by_id')
                    if not episode_assets_by_id:
                        episode_assets_by_id = {}
                    for asset_id in episode_assets_by_id.keys():
                        episode_id_by_entity_id[asset_id] = episode_id
                    episode_shots_by_id = episode.get('shots_by_id')
                    if not episode_shots_by_id:
                        episode_shots_by_id = {}
                    for shot_id in episode_shots_by_id.keys():
                        episode_id_by_entity_id[shot_id] = episode_id
                for asset in assets_with_modified_code:
                    asset_episode_id = episode_id_by_entity_id.get(asset.get('id'))
                    asset_episode_name = None
                    if asset_episode_id:
                        asset_episode = episodes_by_id.get(asset_episode_id)
                        if asset_episode:
                            asset_episode_name = asset_episode.get('name')
                    asset['episode_id'] = asset_episode_id
                    asset['episode_name'] = asset_episode_name

                
                self.pipeline_data['all_assets_for_project'] = list(assets_with_modified_code)
                for entity in assets_with_modified_code:
                    self.pipeline_data['entitiy_keys'].add((entity.get('type'), entity.get('id')))
                    self.pipeline_data['entity_by_id'][entity.get('id')] = entity
            except Exception as e:
                self.log(pformat(e))

        def all_shots_for_project():
            try:
                shots_with_modified_code = []
                all_shots_for_project = self.gazu.shot.all_shots_for_project(current_project, client=current_client)
                for shot in all_shots_for_project:
                    shot['code'] = shot['name']
                    if self.shot_code_field:
                        data = shot.get('data')
                        if data:
                            code = data.get(shot_code_field)
                            if code:
                                shot['code'] = code
                    shots_with_modified_code.append(shot)
            
                episodes = self.connector.pipeline_data.get('all_episodes_for_project')
                episodes_by_id = {x.get('id'):x for x in episodes}
                episode_id_by_entity_id = {}
                for episode in episodes:
                    episode_id = episode.get('id')
                    if not episode_id:
                        continue
                    episode_assets_by_id = episode.get('assets_by_id')
                    if not episode_assets_by_id:
                        episode_assets_by_id = {}
                    for asset_id in episode_assets_by_id.keys():
                        episode_id_by_entity_id[asset_id] = episode_id
                    episode_shots_by_id = episode.get('shots_by_id')
                    if not episode_shots_by_id:
                        episode_shots_by_id = {}
                    for shot_id in episode_shots_by_id.keys():
                        episode_id_by_entity_id[shot_id] = episode_id

                for shot in shots_with_modified_code:
                    shot_episode_id = episode_id_by_entity_id.get(shot.get('id'))
                    shot_episode_name = None
                    if shot_episode_id:
                        shot_episode = episodes_by_id.get(shot_episode_id)
                        if shot_episode:
                            shot_episode_name = shot_episode.get('name')
                    shot['episode_id'] = shot_episode_id
                    shot['episode_name'] = shot_episode_name

                self.pipeline_data['all_shots_for_project'] = list(shots_with_modified_code)
                for entity in shots_with_modified_code:
                    self.pipeline_data['entitiy_keys'].add((entity.get('type'), entity.get('id')))
                    self.pipeline_data['entity_by_id'][entity.get('id')] = entity
            except Exception as e:
                self.log(pformat(e))

        def all_sequences_for_project():
            try:
                all_sequences_for_project = self.gazu.shot.all_sequences_for_project(current_project, client=current_client)
                self.pipeline_data['all_sequences_for_project'] = list(all_sequences_for_project)
                for entity in all_sequences_for_project:
                    self.pipeline_data['entitiy_keys'].add((entity.get('type'), entity.get('id')))
                    self.pipeline_data['entity_by_id'][entity.get('id')] = entity
            except Exception as e:
                self.log(pformat(e))

        def all_task_types_for_project():
            try:
                all_task_types_for_project = self.connector.gazu.task.all_task_types_for_project(current_project, client=current_client)
                self.pipeline_data['all_task_types_for_project'] = list(all_task_types_for_project)
            except Exception as e:
                self.log(pformat(e))

        def all_task_statuses_for_project():
            try:
                all_task_types_for_project = self.connector.gazu.task.all_task_statuses_for_project(current_project, client=current_client)
                self.pipeline_data['all_task_statuses_for_project'] = list(all_task_types_for_project)
            except Exception as e:
                self.log(pformat(e))

        requests = []
        requests.append(threading.Thread(target=get_current_project, args=()))
        requests.append(threading.Thread(target=project_tasks_for_person, args=()))
        requests.append(threading.Thread(target=all_episodes_for_project, args=()))
        requests.append(threading.Thread(target=all_assets_for_project, args=()))
        requests.append(threading.Thread(target=all_shots_for_project, args=()))
        requests.append(threading.Thread(target=all_sequences_for_project, args=()))
        requests.append(threading.Thread(target=all_task_types_for_project, args=()))
        requests.append(threading.Thread(target=all_task_statuses_for_project, args=()))

        for request in requests:
            request.daemon = True
            request.start()

        for request in requests:
            request.join()

        # this block is to add episode id and name to shot or asset
        episodes = self.connector.pipeline_data.get('all_episodes_for_project')
        episodes_by_id = {x.get('id'):x for x in episodes}
        episode_id_by_entity_id = {}
        for episode in episodes:
            episode_id = episode.get('id')
            if not episode_id:
                continue
            episode_assets_by_id = episode.get('assets_by_id')
            if not episode_assets_by_id:
                episode_assets_by_id = {}
            for asset_id in episode_assets_by_id.keys():
                episode_id_by_entity_id[asset_id] = episode_id
            episode_shots_by_id = episode.get('shots_by_id')
            if not episode_shots_by_id:
                episode_shots_by_id = {}
            for shot_id in episode_shots_by_id.keys():
                episode_id_by_entity_id[shot_id] = episode_id
        for asset in self.connector.pipeline_data.get('all_assets_for_project'):
            asset_episode_id = episode_id_by_entity_id.get(asset.get('id'))
            asset_episode_name = None
            if asset_episode_id:
                asset_episode = episodes_by_id.get(asset_episode_id)
                if asset_episode:
                    asset_episode_name = asset_episode.get('name')
            asset['episode_id'] = asset_episode_id
            asset['episode_name'] = asset_episode_name
        for shot in self.connector.pipeline_data.get('all_shots_for_project'):
            shot_episode_id = episode_id_by_entity_id.get(shot.get('id'))
            shot_episode_name = None
            if shot_episode_id:
                shot_episode = episodes_by_id.get(shot_episode_id)
                if shot_episode:
                    shot_episode_name = shot_episode.get('name')
            shot['episode_id'] = shot_episode_id
            shot['episode_name'] = shot_episode_name

    def collect_entity_linked_info(self, entity_key, current_client = None):
        if not current_client:
            current_client = self.gazu_client

        entity_type, entity_id = entity_key

        if entity_type == 'Shot':
            shot_tasks = self.gazu.task.all_tasks_for_shot({'id': entity_id}, client = current_client)
            self.pipeline_data['tasks_by_entity_id'][entity_id] = shot_tasks
            for task in shot_tasks:
                task_preview_files = self.gazu.files.get_all_preview_files_for_task(
                    {'id': task.get('id')},
                    client = current_client)
                self.pipeline_data['preview_by_task_id'][task.get('id')] = task_preview_files

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

    def resolve_storage_root(self):
        storage_root = self.prefs.get('storage_root')
        return storage_root


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

        self.connector.linked_project = self.flame.project.current_project.shotgun_project_name.get_value()

        menu = {'actions': []}

        if not self.connector.user:
            menu['name'] = self.menu_group_name

            menu_item = {}
            menu_item['name'] = 'Sign in to Kitsu'
            menu_item['waitCursor'] = False
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
        self.connector.init_pipeline_data()
        self.rescan()

    def link_project(self, project):
        self.connector.init_pipeline_data()
        project_name = project.get('name')
        if project_name:
            self.flame.project.current_project.shotgun_project_name = project_name
            self.connector.linked_project = project_name
            if 'id' in project.keys():
                self.connector.linked_project_id = project.get('id')
        self.rescan()
        
    def refresh(self, *args, **kwargs):        
        # self.connector.cache_retrive_result(self.active_projects_uid, True)
        self.connector.collect_pipeline_data()
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
        try:
            self._preferences_window(*args, **kwargs)
        except Exception as e:
            print (e)
            print(pformat(traceback.format_exc()))

    def _preferences_window(self, *args, **kwargs):

        # The first attemt to draft preferences window in one function
        # became a bit monstrous
        # Probably need to put it in subclass instead

        try:
            from PySide2 import QtWidgets, QtCore, QtGui
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui

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
            pipeline_config_info.setText('None')

            # if self.connector.get_pipeline_configurations():
            #    pipeline_config_info.setText('Found')
            #else:
            #    pipeline_config_info.setText('None')

        def change_storage_root_dialog():
            path = QtWidgets.QFileDialog().getExistingDirectory(
                        None,
                        'Select Project Location',
                        self.connector.prefs.get('storage_root'),
                        QtWidgets.QFileDialog.DontUseNativeDialog | QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
            if os.path.isdir(path):
                self.connector.prefs['storage_root'] = path
                storage_root_paths.setText(str(path))

            '''
            dialog = QtWidgets.QFileDialog()
            dialog.setWindowTitle('Select Project Location')
            # dialog.setNameFilter('XML files (*.xml)')
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
            '''

            # update_pipeline_config_info()
            # update_project_path_info()

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
            preset_path = export_preset_fields.get('path', '')
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

        window = QtWidgets.QDialog()
        window.setFixedSize(1028, 328)
        window.setWindowTitle(self.framework.bundle_name + ' Preferences')
        window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setStyleSheet('background-color: #2e2e2e')

        if QtCore.__version_info__[0] < 6:
            screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        else:
            mainWindow = QtGui.QGuiApplication.primaryScreen()
            screen_res = mainWindow.screenGeometry()

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
        vbox_apps.addLayout(hbox_General)
        vbox_apps.setAlignment(hbox_General, QtCore.Qt.AlignLeft)

        # Modules: flameMenuPublisher button

        hbox_Publish = QtWidgets.QHBoxLayout()
        hbox_Publish.setAlignment(QtCore.Qt.AlignLeft)
        btn_Publish = QtWidgets.QPushButton('Menu Publish', window)
        btn_Publish.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Publish.setMinimumSize(128, 28)
        btn_Publish.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Publish.pressed.connect(pressPublish)
        hbox_Publish.addWidget(btn_Publish)
        vbox_apps.addLayout(hbox_Publish)
        vbox_apps.setAlignment(hbox_Publish, QtCore.Qt.AlignLeft)

        # Modules: flameSuperclips button

        hbox_Superclips = QtWidgets.QHBoxLayout()
        hbox_Superclips.setAlignment(QtCore.Qt.AlignLeft)
        btn_Superclips = QtWidgets.QPushButton('Superclips', window)
        btn_Superclips.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Superclips.setMinimumSize(128, 28)
        btn_Superclips.setStyleSheet('QPushButton {color: #989898; background-color: #373737; border-top: 1px inset #555555; border-bottom: 1px inset black}')
        btn_Superclips.pressed.connect(pressSuperclips)
        hbox_Superclips.addWidget(btn_Superclips)
        vbox_apps.addLayout(hbox_Superclips)
        vbox_apps.setAlignment(hbox_Superclips, QtCore.Qt.AlignLeft)

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
            self.framework.prefs['flameBatchBlessing']['flame_batch_root'] = '/var/tmp/flameMenuKITSU/flame_batch_setups'
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
        '''
        shot_task_templates = self.connector.sg.find('TaskTemplate', [['entity_type', 'is', 'Shot']], ['code'])
        shot_task_templates = [{}]
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
        '''

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
        '''
        # asset_task_templates = self.connector.sg.find('TaskTemplate', [['entity_type', 'is', 'Asset']], ['code'])
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
        '''

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
        storage_root_btn.setText('MountPoint')
        
        storage_root_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        storage_root_btn.setMinimumSize(199, 28)
        storage_root_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        storage_root_btn.clicked.connect(change_storage_root_dialog)
        hbox_storage.addWidget(storage_root_btn)
        hbox_storage.setAlignment(storage_root_btn, QtCore.Qt.AlignLeft)

        # storage_name = QtWidgets.QLabel('Pipeline configuration:', window)
        # hbox_storage.addWidget(storage_name, alignment = QtCore.Qt.AlignLeft)

        # pipeline_config_info = QtWidgets.QLabel(window)
        # boldFont = QtGui.QFont()
        # boldFont.setBold(True)
        # pipeline_config_info.setFont(boldFont)

        # update_pipeline_config_info()        
        # hbox_storage.addWidget(pipeline_config_info, alignment = QtCore.Qt.AlignRight)
        vbox_storage_root.addLayout(hbox_storage)


        # Publish: StorageRoot: Paths info label
        storage_root_paths = QtWidgets.QLabel(window)
        storage_root_paths.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        storage_root_paths.setStyleSheet('QFrame {color: #9a9a9a; background-color: #2a2a2a; border: 1px solid #696969 }')
        storage_root_paths.setText(str(self.connector.prefs.get('storage_root')))

        # update_project_path_info()

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
        hbox_export_preset.addWidget(btn_changePreset)
        hbox_export_preset.setAlignment(btn_changePreset, QtCore.Qt.AlignLeft)

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
        try:
            txt_shot_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_render').get('value', '')
        except Exception as e:
            txt_shot_value = pformat(e)
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
        try:
            txt_shotBatch_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('flame_batch').get('value', '')
        except Exception as e:
            txt_shotBatch_value = pformat(e)
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
        try:
            txt_shotVersion_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Shot', {}).get('version_name').get('value', '')
        except Exception as e:
            txt_shotVersion_value = pformat(e)
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
        try:
            txt_asset_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_render').get('value', '')
        except Exception as e:
            txt_asset_value = pformat(e)
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
        try:
            txt_assetBatch_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('flame_batch').get('value', '')
        except Exception as e:
            txt_assetBatch_value = pformat(e)
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
        try:
            txt_assetVersion_value = self.framework.prefs.get('flameMenuPublisher', {}).get('templates', {}).get('Asset', {}).get('version_name').get('value', '')
        except Exception as e:
            txt_assetVersion_value = pformat(e)
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
            try:
                self.framework.prefs['flameMenuPublisher']['templates']['Shot']['flame_render']['value'] = txt_shot.text()
                self.framework.prefs['flameMenuPublisher']['templates']['Shot']['flame_batch']['value'] = txt_shotBatch.text()
                self.framework.prefs['flameMenuPublisher']['templates']['Shot']['version_name']['value'] = txt_shotVersion.text()
                self.framework.save_prefs()
            except Exception as e:
                self.log(pformat(e))
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
        self.connector.collect_pipeline_data()

        if self.flame:
            self.flame.execute_shortcut('Rescan Python Hooks')
            self.log_debug('Rescan Python Hooks')


class flameBatchBlessing(flameMenuApp):
    def __init__(self, framework):
        flameMenuApp.__init__(self, framework)
        
        # app defaults
        if not self.prefs.master.get(self.name):
            self.prefs['flame_batch_root'] = '/var/tmp/flameMenuKITSU/flame_batch_setups'
            self.prefs['enabled'] = True
            self.prefs['use_project'] = True

        self.root_folder = self.batch_setup_root_folder()

    def batch_setup_root_folder(self):
        try:
            import flame
        except:
            return False
        
        flame_batch_name = 'unklnown_batch'
        current_project_name = 'unknown_project'
    
        if flame.batch.name:
            flame_batch_name = flame.batch.name.get_value()
        if 'project' in dir(flame):
            current_project_name = flame.project.current_project.name

        if self.prefs.get('use_project'):
            flame_batch_path = os.path.join(
                                        self.prefs.get('flame_batch_root'),
                                        current_project_name,
                                        flame_batch_name)
        else:
            flame_batch_path = os.path.join(
                                        self.prefs.get('flame_batch_root'),
                                        flame_batch_name)
        
        if not os.path.isdir(flame_batch_path):
            try:
                os.makedirs(flame_batch_path)
                self.log_debug('creating %s' % flame_batch_path)
            except:
                print ('PYTHON\t: %s can not create %s' % (self.framework.bundle_name, flame_batch_path))
                return False
        return flame_batch_path

    def collect_clip_uids(self, render_dest):        
        # collects clip uids from locations specified in render_dest dictionary
        # returns:    dictionary of lists of clip uid's at the locations specified
        #            in render_dest dictionary.
        #            clip_uids = {
        #                        'Batch Reels': {
        #                            'BatchReel Name': [uid1, uid2]
        #                            }
        #                        'Batch Shelf Reels': {
        #                            'Shelf Reel Name 1': [uid3, uid4]
        #                            'Shelf Reel Name 2': [uid5, uid6, uid7]
        #                            }
        #                        'Libraries': {
        #                            'Library Name 3': [uid8, uid9]
        #                        }
        #                        'Reel Groups': {
        #                            'Reel Group Name 1': {
        #                                'Reel 1': []
        #                                'Reel 2: []
        #                            }
        #                            'Reel Group Name 2': {
        #                                'Reel 1': []
        #                                'Reel 2: []
        #                            }
        #
        #                        }
        #            }

        import flame

        collected_uids = dict()
        for dest in render_dest.keys():
            if dest == 'Batch Reels':
                render_dest_names = list(render_dest.get(dest))
                if not render_dest_names:
                    continue
                
                batch_reels = dict()
                for reel in flame.batch.reels:
                    current_uids = list()
                    if reel.name in render_dest_names:
                        for clip in reel.clips:
                            current_uids.append(clip.uid)
                        batch_reels[reel.name] = current_uids
                collected_uids['Batch Reels'] = batch_reels

                batch_shelf_reels = dict()
                for reel in flame.batch.shelf_reels:
                    current_uids = list()
                    if reel.name in render_dest_names:
                        for clip in reel.clips:
                            current_uids.append(clip.uid)
                        batch_shelf_reels[reel.name] = current_uids
                collected_uids['Batch Shelf Reels'] = batch_shelf_reels

            elif dest == 'Libraries':
                render_dest_names = list(render_dest.get(dest))
                if not render_dest_names:
                    continue

                libraries = dict()
                current_workspace_libraries = flame.project.current_project.current_workspace.libraries           
                for library in current_workspace_libraries:
                    current_uids = list()
                    if library.name in render_dest_names:
                        for clip in library.clips:
                            current_uids.append(clip.uid)
                        libraries[library.name] = current_uids
                collected_uids['Libraries'] = libraries
                            
            elif dest == 'Reel Groups':
                render_dest_names = list(render_dest.get(dest))
                if not render_dest_names:
                    continue
                reel_groups = dict()
                current_desktop_reel_groups = flame.project.current_project.current_workspace.desktop.reel_groups
                for reel_group in current_desktop_reel_groups:
                    reels = dict()
                    if reel_group.name in render_dest_names:
                        for reel in reel_group.reels:
                            current_uids = list()
                            for clip in reel.clips:
                                current_uids.append(clip.uid)
                            reels[reel.name] = current_uids
                    reel_groups[reel_group.name] = reels
                collected_uids['Reel Groups'] = reel_groups
            
        return collected_uids

    def bless_clip(self, clip, **kwargs):
        batch_setup_name = kwargs.get('batch_setup_name')
        batch_setup_file = kwargs.get('batch_setup_file')
        blessing_string = str({'batch_file': batch_setup_file})
        for version in clip.versions:
            for track in version.tracks:
                for segment in track.segments:
                    new_comment = segment.comment + blessing_string
                    segment.comment = new_comment
                    self.log_debug('blessing %s with %s' % (clip.name, blessing_string))
        return True

    def bless_batch_renders(self, userData):
        import flame
        
        # finds clips that was not in the render destionations before
        # and blesses them by adding batch_setup_name to the comments

        batch_setup_name = userData.get('batch_setup_name')
        batch_setup_file = userData.get('batch_setup_file')
        render_dest_uids = userData.get('render_dest_uids')

        for dest in render_dest_uids.keys():
            previous_uids = None
            if dest == 'Batch Reels':
                batch_reels_dest = render_dest_uids.get(dest)
                for batch_reel_name in batch_reels_dest.keys():
                    previous_uids = batch_reels_dest.get(batch_reel_name)
                    for reel in flame.batch.reels:
                        if reel.name == batch_reel_name:
                            for clip in reel.clips:
                                if clip.uid not in previous_uids:
                                    self.bless_clip(clip, 
                                        batch_setup_name = batch_setup_name, 
                                        batch_setup_file = batch_setup_file)

            elif dest == 'Batch Shelf Reels':
                batch_shelf_reels_dest = render_dest_uids.get(dest)
                for batch_shelf_reel_name in batch_shelf_reels_dest.keys():
                    previous_uids = batch_shelf_reels_dest.get(batch_shelf_reel_name)
                    for reel in flame.batch.shelf_reels:
                        if reel.name == batch_shelf_reel_name:
                            for clip in reel.clips:
                                if clip.uid not in previous_uids:
                                    self.bless_clip(clip, 
                                        batch_setup_name = batch_setup_name,
                                        batch_setup_file = batch_setup_file)

            elif dest == 'Libraries':
                libraries_dest = render_dest_uids.get(dest)
                current_workspace_libraries = flame.project.current_project.current_workspace.libraries
                for library_name in libraries_dest.keys():
                    previous_uids = libraries_dest.get(library_name)
                    for library in current_workspace_libraries:
                        if library.name == library_name:
                            for clip in library.clips:
                                if clip.uid not in previous_uids:
                                    try:
                                        self.bless_clip(clip, 
                                            batch_setup_name = batch_setup_name,
                                            batch_setup_file = batch_setup_file)
                                    except:
                                        print ('PYTHON\t: %s unable to bless %s' % (self.framework.bundle_name, clip.name))
                                        print ('PYTHON\t: %s libraries are protected from editing' % self.framework.bundle_name)
                                        continue

            elif dest == 'Reel Groups':
                reel_grous_dest = render_dest_uids.get(dest)
                current_desktop_reel_groups = flame.project.current_project.current_workspace.desktop.reel_groups
                for reel_group_name in reel_grous_dest.keys():
                    for desktop_reel_group in current_desktop_reel_groups:
                        if desktop_reel_group.name == reel_group_name:
                            reels = reel_grous_dest[reel_group_name]
                            for reel_name in reels.keys():
                                previous_uids = reels.get(reel_name)
                                for reel in desktop_reel_group.reels:
                                    if reel.name == reel_name:
                                        for clip in reel.clips:
                                            if clip.uid not in previous_uids:
                                                self.bless_clip(clip, 
                                                    batch_setup_name = batch_setup_name,
                                                    batch_setup_file = batch_setup_file)

    def create_batch_uid(self):
        # generates UUID for the batch setup
        import uuid
        from datetime import datetime
        
        uid = ((str(uuid.uuid1()).replace('-', '')).upper())
        timestamp = (datetime.now()).strftime('%Y%b%d_%H%M').upper()
        return timestamp + '_' + uid[:3]


class flameMenuNewBatch(flameMenuApp):
    def __init__(self, framework, connector):
        # app constructor
        flameMenuApp.__init__(self, framework)
        self.connector = connector
        self.log('initializing')

        # app configuration settings
        self.steps_to_ignore = [
            'step_one',
            'step_two'
        ]
        self.types_to_include = [
            'Image Sequence',
            'Flame Render'
        ]

        if not self.prefs.master.get(self.name):
            self.prefs['show_all'] = True
            self.prefs['current_page'] = 0
            self.prefs['menu_max_items_per_page'] = 128

            self.prefs['last_sequence_used'] = {}

    def __getattr__(self, name):
        def method(*args, **kwargs):

            if str(name).startswith('pg_fwd'):
                self.page_fwd(menu_name = name.replace('pg_fwd ', ''))
            if str(name).startswith('pg_bkw'):
                self.page_bkw(menu_name = name.replace('pg_bkw ', ''))

            entity = self.dynamic_menu_data.get(name)
            if entity:
                self.create_new_batch(entity)
        return method

    def build_menu(self):
        '''
        # ---------------------------------
        # menu build time debug code

        number_of_menu_itmes = 256
        menu = {'name': self.name, 'actions': []}
        for i in xrange(1, number_of_menu_itmes+1):
            menu['actions'].append({
                'name': 'Test selection ' + str(i),
                # 'isVisible': self.scope_reel,
                'execute': getattr(self, 'menu_item_' + str(i))
            })
        return menu

        # ---------------------------------
        # menu build time debug code
        '''

        if not self.connector.user:
            return []
        if not self.connector.linked_project_id:
            return []
        if not self.flame:
            return []

        total_menu_itmes = 0

        batch_groups = []
        for batch_group in self.flame.project.current_project.current_workspace.desktop.batch_groups:
            batch_groups.append(batch_group.name.get_value())

        menu = {'actions': [], 'hierarchy': []}
        menu['name'] = self.menu_group_name + ' Create new batch:'
        menu_item_order = 0

        menu_item = {}
        menu_item['name'] = '~ Rescan'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['execute'] = self.rescan
        menu['actions'].append(menu_item)

        menu_item = {}
        if self.prefs['show_all']:            
            menu_item['name'] = '~ Show Assigned Only'
        else:
            menu_item['name'] = '~ Show All Avaliable'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['separator'] = 'below'
        menu_item['execute'] = self.flip_assigned
        menu['actions'].append(menu_item)

        # found entities menu

        user_only = not self.prefs['show_all']
        filter_out = ['Project', 'Sequence']
        found_entities = self.get_entities(user_only, filter_out)
        found_assets = found_entities.get('Asset')
        if not found_assets:
            found_assets = []
        found_shots = found_entities.get('Shot')
        if not found_shots:
            found_shots = []
        entities_with_no_episode = {'Shot': [], 'Asset': []}
        found_entity_episodes = {}
        for asset in found_assets:           
            entity_episode_name = asset.get('episode_name')
            if entity_episode_name:
                if entity_episode_name not in found_entity_episodes.keys():
                    found_entity_episodes[entity_episode_name] = {}
                if not isinstance(found_entity_episodes[entity_episode_name].get('Asset'), list):
                    found_entity_episodes[entity_episode_name]['Asset'] = []
                found_entity_episodes[entity_episode_name]['Asset'].append(asset)
            else:
                entities_with_no_episode['Asset'].append(asset)        
        for shot in found_shots:           
            entity_episode_name = shot.get('episode_name')
            if entity_episode_name:
                if entity_episode_name not in found_entity_episodes.keys():
                    found_entity_episodes[entity_episode_name] = {}
                if not isinstance(found_entity_episodes[entity_episode_name].get('Shot'), list):
                    found_entity_episodes[entity_episode_name]['Shot'] = []
                found_entity_episodes[entity_episode_name]['Shot'].append(shot)
            else:
                entities_with_no_episode['Shot'].append(shot)
        # found_entities = entities_with_no_episode

        def build_menu_body(menu, found_entities, menu_item_order = 1):            
            menu_main_body = []

            if not found_entities:
                menu_item = {}
                menu_item['name'] = '- [ Assets ] [+]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu_item['separator'] = 'above'
                menu_item['execute'] = self.create_asset_dialog
                menu_item['waitCursor'] = False
                menu_main_body.append(menu_item)

                menu_item = {}
                menu_item['name'] = '- [ Shots ] [+]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu_item['execute'] = self.create_shot_dialog
                menu_item['waitCursor'] = False
                menu_main_body.append(menu_item)
            
            if len(found_entities.keys()) == 1:
                if 'Shot' in found_entities.keys():
                    menu_item = {}
                    menu_item['name'] = '- [ Assets ] [+]'
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu_item['separator'] = 'above'
                    menu_item['execute'] = self.create_asset_dialog
                    menu_item['waitCursor'] = False
                    menu_main_body.append(menu_item)

            menu_ctrls_len = len(menu)
            menu_lenght = menu_ctrls_len
            menu_lenght += len(found_entities.keys())
            for entity_type in found_entities.keys():
                menu_lenght += len(found_entities.get(entity_type))
            max_menu_lenght = self.prefs.get('menu_max_items_per_page')

            for index, entity_type in enumerate(sorted(found_entities.keys())):
                menu_item = {}
                menu_item['name'] = '- [ ' + entity_type + 's ] [+]'
                if entity_type == 'Asset':
                    menu_item['execute'] = self.create_asset_dialog
                elif entity_type == 'Shot':
                    menu_item['execute'] = self.create_shot_dialog
                else:
                    menu_item['execute'] = self.rescan
                menu_item['waitCursor'] = False
                menu_main_body.append(menu_item)
                    
                entities_by_name = {}
                for entity in found_entities[entity_type]:
                    entities_by_name[entity.get('code')] = entity
                for entity_name in sorted(entities_by_name.keys()):
                    entity = entities_by_name.get(entity_name)
                    menu_item = {}
                    if entity.get('code') in batch_groups:
                        menu_item['name'] = '  * ' + entity.get('code')
                    else:
                        menu_item['name'] = '     ' + entity.get('code')

                    self.dynamic_menu_data[str(id(entity))] = entity
                    menu_item['execute'] = getattr(self, str(id(entity)))
                    menu_main_body.append(menu_item)

            if len(found_entities.keys()) == 1:
                if 'Asset' in found_entities.keys():
                    menu_item = {}
                    menu_item['name'] = '- [ Shots ] [+]'
                    menu_item['execute'] = self.create_shot_dialog
                    menu_item['waitCursor'] = False
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu_main_body.append(menu_item)

            if menu_lenght < max_menu_lenght:
            # controls and entites fits within menu size
            # we do not need additional page switch controls
                for menu_item in menu_main_body:
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)

            else:
                # round up number of pages and get current page
                num_of_pages = ((menu_lenght) + max_menu_lenght - 1) // max_menu_lenght
                curr_page = self.prefs.get('current_page_' + menu.get('name'), 0)
                if curr_page > num_of_pages:
                    curr_page = num_of_pages
                
                # decorate top with move backward control
                # if we're not on the first page
                if curr_page > 0:
                    menu_item = {}
                    menu_item['name'] = '<<[ prev page ' + str(curr_page) + ' of ' + str(num_of_pages) + ' ]'
                    menu_item['execute'] = getattr(self, 'pg_bkw ' + str(menu.get('name')))
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)

                # calculate the start and end position of a window
                # and append items to the list
                menu_used_space = menu_ctrls_len + 2 # two more controls for page flip
                window_size = max_menu_lenght - menu_used_space
                start_index = window_size*curr_page + min(1*curr_page, 1)
                end_index = window_size*curr_page+window_size + ((curr_page+1) // num_of_pages)

                for menu_item in menu_main_body[start_index:end_index]:
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)
                
                # decorate bottom with move forward control
                # if we're not on the last page            
                if curr_page < (num_of_pages - 1):
                    menu_item = {}
                    menu_item['name'] = '[ next page ' + str(curr_page+2) + ' of ' + str(num_of_pages) + ' ]>>'
                    menu_item['execute'] = getattr(self, 'pg_fwd ' + str(menu.get('name')))
                    # menu_item['execute'] = self.page_fwd
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)
            
            return menu

        build_menu_body (menu, entities_with_no_episode, menu_item_order=menu_item_order)
        menu_item_order = len(menu['actions'])
        total_menu_itmes = menu_item_order

        # for action in menu['actions']:
        #    action['isVisible'] = self.scope_desktop
        
        menu_combined = [menu]

        for episode_name in sorted(found_entity_episodes.keys()):
            menu_episode = {}
            menu_episode['name'] = episode_name
            menu_episode['order'] = menu_item_order
            menu_item_order += 1
            menu_episode['actions'] = []
            menu_episode['hierarchy'] = [menu['name']]
            build_menu_body(menu_episode, found_entity_episodes.get(episode_name))
            total_menu_itmes += len(menu_episode['actions'])
            menu_combined.append(menu_episode)

        if total_menu_itmes > self.prefs.get('menu_max_items_per_page'):
            return self.build_menu_classic()

        return menu_combined

    def build_menu_classic(self):
        '''
        # ---------------------------------
        # menu build time debug code

        number_of_menu_itmes = 256
        menu = {'name': self.name, 'actions': []}
        for i in xrange(1, number_of_menu_itmes+1):
            menu['actions'].append({
                'name': 'Test selection ' + str(i),
                # 'isVisible': self.scope_reel,
                'execute': getattr(self, 'menu_item_' + str(i))
            })
        return menu

        # ---------------------------------
        # menu build time debug code
        '''

        if not self.connector.user:
            return []
        if not self.connector.linked_project_id:
            return []
        if not self.flame:
            return []

        batch_groups = []
        for batch_group in self.flame.project.current_project.current_workspace.desktop.batch_groups:
            batch_groups.append(batch_group.name.get_value())

        menu = {'actions': []}
        menu['name'] = self.menu_group_name + ' Create new batch:'
        menu_item_order = 0

        menu_item = {}
        menu_item['name'] = '~ Rescan'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['execute'] = self.rescan
        menu['actions'].append(menu_item)

        menu_item = {}
        if self.prefs['show_all']:            
            menu_item['name'] = '~ Show Assigned Only'
        else:
            menu_item['name'] = '~ Show All Avaliable'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['separator'] = 'below'
        menu_item['execute'] = self.flip_assigned
        menu['actions'].append(menu_item)

        # found entities menu

        user_only = not self.prefs['show_all']
        filter_out = ['Project', 'Sequence']
        found_entities = self.get_entities(user_only, filter_out)
        menu_main_body = []

        if not found_entities:
            menu_item = {}
            menu_item['name'] = '- [ Assets ] [+]'
            menu_item['order'] = menu_item_order
            menu_item_order += 1
            menu_item['separator'] = 'above'
            menu_item['execute'] = self.create_asset_dialog
            menu_item['waitCursor'] = False
            menu_main_body.append(menu_item)

            menu_item = {}
            menu_item['name'] = '- [ Shots ] [+]'
            menu_item['order'] = menu_item_order
            menu_item_order += 1
            menu_item['execute'] = self.create_shot_dialog
            menu_item['waitCursor'] = False
            menu_main_body.append(menu_item)
        
        if len(found_entities.keys()) == 1:
            if 'Shot' in found_entities.keys():
                menu_item = {}
                menu_item['name'] = '- [ Assets ] [+]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu_item['separator'] = 'above'
                menu_item['execute'] = self.create_asset_dialog
                menu_item['waitCursor'] = False
                menu_main_body.append(menu_item)

        menu_ctrls_len = len(menu)
        menu_lenght = menu_ctrls_len
        menu_lenght += len(found_entities.keys())
        for entity_type in found_entities.keys():
            menu_lenght += len(found_entities.get(entity_type))
        max_menu_lenght = self.prefs.get('menu_max_items_per_page')

        for index, entity_type in enumerate(sorted(found_entities.keys())):
            menu_item = {}
            menu_item['name'] = '- [ ' + entity_type + 's ] [+]'
            if entity_type == 'Asset':
                menu_item['execute'] = self.create_asset_dialog
            elif entity_type == 'Shot':
                menu_item['execute'] = self.create_shot_dialog
            else:
                menu_item['execute'] = self.rescan
            menu_item['waitCursor'] = False
            menu_main_body.append(menu_item)
                
            entities_by_name = {}
            for entity in found_entities[entity_type]:
                entities_by_name[entity.get('episode_name', '') + ' ' + entity.get('code')] = entity
            for entity_name in sorted(entities_by_name.keys()):
                entity = entities_by_name.get(entity_name)
                menu_item = {}
                episode_name = entity.get('episode_name', '') 

                if entity.get('code') in batch_groups:
                    menu_item['name'] = '  * ' + episode_name + ': ' + entity.get('code')
                else:
                    menu_item['name'] = '     ' + episode_name + ': ' + entity.get('code')

                self.dynamic_menu_data[str(id(entity))] = entity
                menu_item['execute'] = getattr(self, str(id(entity)))
                menu_main_body.append(menu_item)

        if len(found_entities.keys()) == 1:
            if 'Asset' in found_entities.keys():
                menu_item = {}
                menu_item['name'] = '- [ Shots ] [+]'
                menu_item['execute'] = self.create_shot_dialog
                menu_item['waitCursor'] = False
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu_main_body.append(menu_item)

        if menu_lenght < max_menu_lenght:
        # controls and entites fits within menu size
        # we do not need additional page switch controls
            for menu_item in menu_main_body:
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

        else:
            # round up number of pages and get current page
            num_of_pages = ((menu_lenght) + max_menu_lenght - 1) // max_menu_lenght
            curr_page = self.prefs.get('current_page')
            
            # decorate top with move backward control
            # if we're not on the first page
            if curr_page > 0:
                menu_item = {}
                menu_item['name'] = '<<[ prev page ' + str(curr_page) + ' of ' + str(num_of_pages) + ' ]'
                menu_item['execute'] = self.page_bkw
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

            # calculate the start and end position of a window
            # and append items to the list
            menu_used_space = menu_ctrls_len + 2 # two more controls for page flip
            window_size = max_menu_lenght - menu_used_space
            start_index = window_size*curr_page + min(1*curr_page, 1)
            end_index = window_size*curr_page+window_size + ((curr_page+1) // num_of_pages)

            for menu_item in menu_main_body[start_index:end_index]:
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
            
            # decorate bottom with move forward control
            # if we're not on the last page            
            if curr_page < (num_of_pages - 1):
                menu_item = {}
                menu_item['name'] = '[ next page ' + str(curr_page+2) + ' of ' + str(num_of_pages) + ' ]>>'
                menu_item['execute'] = self.page_fwd
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

        # for action in menu['actions']:
        #    action['isVisible'] = self.scope_desktop

        return [menu]


    def get_entities(self, user_only = True, filter_out=[]):
        if user_only:
            cached_tasks = self.connector.pipeline_data.get('project_tasks_for_person')
            if not isinstance(cached_tasks, list):
                # try to collect pipeline data in foreground
                self.connector.collect_pipeline_data()
                cached_tasks = self.connector.pipeline_data.get('project_tasks_for_person')
                if not isinstance(cached_tasks, list):
                    # give up
                    return {}
            if not cached_tasks:
                return {}
            else:
                cached_tasks_by_entity_id = {x.get('entity_id'):x for x in cached_tasks}
                entities = {'Shot': [], 'Asset': []}
                shots = self.connector.pipeline_data.get('all_shots_for_project')
                if not shots:
                    shots = []
                for shot in shots:
                    shot_id = shot.get('id')
                    if not shot_id:
                        continue

                    if shot.get('id') in cached_tasks_by_entity_id.keys():
                        entities['Shot'].append(shot)
                assets = self.connector.pipeline_data.get('all_assets_for_project')
                if not assets:
                    assets = []
                for asset in assets:
                    if asset.get('id') in cached_tasks_by_entity_id.keys():
                        entities['Asset'].append(asset)
                return entities
            
        else:
            shots = self.connector.pipeline_data.get('all_shots_for_project')
            if not isinstance(shots, list):
                self.connector.collect_pipeline_data()
                shots = self.connector.pipeline_data.get('all_shots_for_project')
                if not shots:
                    shots = []
            assets = self.connector.pipeline_data.get('all_assets_for_project')
            if not isinstance(assets, list):
                self.connector.collect_pipeline_data()
                assets = self.connector.pipeline_data.get('all_assets_for_project')
                if not assets:
                    assets = []
            return {'Shot': shots, 'Asset': assets}

    def create_new_batch(self, entity):
        # check if flame batch with entity name already in desktop
        batch_groups = []
        for batch_group in self.flame.project.current_project.current_workspace.desktop.batch_groups:
            batch_groups.append(batch_group.name.get_value())

        code = entity.get('code')
        if not code:
            code = 'New Batch'

        if code in batch_groups:
            return False

        
        '''
        publishes = sg.find (
            'PublishedFile',
            [['entity', 'is', {'id': entity.get('id'), 'type': entity.get('type')}]],
            [
                'path_cache',
                'path_cache_storage',
                'name',
                'version_number',
                'published_file_type',
                'version.Version.code',
                'task.Task.step.Step.code',
                'task.Task.step.Step.short_name'
            ]
        )

        publishes_to_import = []
        publishes_by_step = {}
        for publish in publishes:
            step_short_name = publish.get('task.Task.step.Step.short_name')
            if step_short_name in self.steps_to_ignore:
                continue
            if step_short_name not in publishes_by_step.keys():
                publishes_by_step[step_short_name] = []
            published_file_type = publish.get('published_file_type')
            if published_file_type:
                published_file_type_name = published_file_type.get('name')
            if published_file_type_name in self.types_to_include:
                publishes_by_step[step_short_name].append(publish)
        

        for step in publishes_by_step.keys():
            step_group = publishes_by_step.get(step)
            names_group = dict()
            
            for publish in step_group:
                name = publish.get('name')
                if name not in names_group.keys():
                    names_group[name] = []
                names_group[name].append(publish)
            
            for name in names_group.keys():
                version_numbers = []
                for publish in names_group[name]:
                    version_number = publish.get('version_number')
                    version_numbers.append(version_number)
                max_version = max(version_numbers)
                for publish in names_group[name]:
                    version_number = publish.get('version_number')
                    if version_number == max_version:
                        publishes_to_import.append(publish)
        '''
        flame_paths_to_import = []
        '''
        for publish in publishes_to_import:
            path_cache = publish.get('path_cache')
            if not path_cache:
                continue            
            storage_root = self.connector.resolve_storage_root(publish.get('path_cache_storage'))
            if not storage_root:
                continue
            path = os.path.join(storage_root, path_cache)
            flame_path = self.build_flame_friendly_path(path)
            flame_paths_to_import.append(flame_path)
        
        sg_head_in = entity.get('sg_head_in')
        if not sg_head_in:
            sg_head_in = 1001
        
        sg_tail_out = entity.get('sg_tail_out')
        if not sg_tail_out:
            sg_tail_out = 1100

        sg_vfx_req = entity.get('sg_vfx_requirements')
        if not sg_vfx_req:
            sg_vfx_req = 'no requirements specified'
        '''

        dur = entity.get('nb_frames')
        if not dur:
            dur = 100
        
        self.flame.batch.create_batch_group (
            code, start_frame = 1, duration = dur
        )
        
        for flame_path in flame_paths_to_import:
            self.flame.batch.import_clip(flame_path, 'Schematic Reel 1')

        render_node = self.flame.batch.create_node('Render')
        render_node.name.set_value('<batch name>_comp_v<iteration###>')

        self.flame.batch.organize()

    def create_asset_dialog(self, *args, **kwargs):
        try:
            from PySide2 import QtWidgets, QtCore
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui

        self.asset_name = ''
        flameMenuNewBatch_prefs = self.framework.prefs.get('flameMenuNewBatch', {})
        self.asset_task_template =  flameMenuNewBatch_prefs.get('asset_task_template', {})

        window = QtWidgets.QDialog()
        window.setMinimumSize(280, 180)
        window.setWindowTitle('Create Asset in ShotGrid')
        window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setStyleSheet('background-color: #313131')

        if QtCore.__version_info__[0] < 6:
            screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        else:
            mainWindow = QtGui.QGuiApplication.primaryScreen()
            screen_res = mainWindow.screenGeometry()

        window.move((screen_res.width()/2)-150, (screen_res.height() / 2)-180)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        # Asset Task Template label

        lbl_TaskTemplate = QtWidgets.QLabel('Task Template', window)
        lbl_TaskTemplate.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_TaskTemplate.setMinimumHeight(28)
        lbl_TaskTemplate.setMaximumHeight(28)
        lbl_TaskTemplate.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_TaskTemplate)

        # Shot Task Template Menu

        btn_AssetTaskTemplate = QtWidgets.QPushButton(window)
        flameMenuNewBatch_prefs = self.framework.prefs.get('flameMenuNewBatch', {})
        asset_task_template = flameMenuNewBatch_prefs.get('asset_task_template', {})
        code = asset_task_template.get('code', 'No code')
        btn_AssetTaskTemplate.setText(code)
        asset_task_templates = self.connector.sg.find('TaskTemplate', [['entity_type', 'is', 'Asset']], ['code'])
        asset_task_templates_by_id = {x.get('id'):x for x in asset_task_templates}
        asset_task_templates_by_code_id = {x.get('code') + '_' + str(x.get('id')):x for x in asset_task_templates}
        def selectAssetTaskTemplate(template_id):
            template = shot_task_templates_by_id.get(template_id, {})
            code = template.get('code', 'no_code')
            btn_AssetTaskTemplate.setText(code)
            self.asset_task_template = template
        btn_AssetTaskTemplate.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_AssetTaskTemplate.setMinimumSize(258, 28)
        btn_AssetTaskTemplate.move(40, 102)
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
        vbox.addWidget(btn_AssetTaskTemplate)

        # Shot Name Label

        lbl_AssettName = QtWidgets.QLabel('New Asset Name', window)
        lbl_AssettName.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_AssettName.setMinimumHeight(28)
        lbl_AssettName.setMaximumHeight(28)
        lbl_AssettName.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_AssettName)

        # Shot Name Text Field
        def txt_AssetName_textChanged():
            self.asset_name = txt_AssetName.text()
        txt_AssetName = QtWidgets.QLineEdit('', window)
        txt_AssetName.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_AssetName.setMinimumSize(280, 28)
        txt_AssetName.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        txt_AssetName.textChanged.connect(txt_AssetName_textChanged)
        vbox.addWidget(txt_AssetName)

        # Spacer Label

        lbl_Spacer = QtWidgets.QLabel('', window)
        lbl_Spacer.setStyleSheet('QFrame {color: #989898; background-color: #313131}')
        lbl_Spacer.setMinimumHeight(4)
        lbl_Spacer.setMaximumHeight(4)
        lbl_Spacer.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_Spacer)

        # Create and Cancel Buttons
        hbox_Create = QtWidgets.QHBoxLayout()

        select_btn = QtWidgets.QPushButton('Create', window)
        select_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        select_btn.setMinimumSize(128, 28)
        select_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        select_btn.clicked.connect(window.accept)

        cancel_btn = QtWidgets.QPushButton('Cancel', window)
        cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        cancel_btn.setMinimumSize(128, 28)
        cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        cancel_btn.clicked.connect(window.reject)

        hbox_Create.addWidget(cancel_btn)
        hbox_Create.addWidget(select_btn)

        vbox.addLayout(hbox_Create)

        window.setLayout(vbox)
        if window.exec_():
            if self.asset_name == '':
                return {}
            else:
                data = {'project': {'type': 'Project','id': self.connector.sg_linked_project_id},
                'code': self.asset_name,
                'task_template': self.asset_task_template}
                self.log_debug('creating new asset...')
                new_asset = self.connector.sg.create('Asset', data)
                self.log_debug('new asset:\n%s' % pformat(new_asset))
                self.log_debug('updating async cache for cuttent_tasks')
                self.connnector.collect_pipeline_data()
                # self.connector.cache_retrive_result('current_tasks', True)
                self.log_debug('creating new batch')
                self.create_new_batch(new_asset)

                for app in self.framework.apps:
                    app.rescan()

                return new_asset
        else:
            return {}

    def create_shot_dialog(self, *args, **kwargs):
        try:
            from PySide2 import QtWidgets, QtCore
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui

        self.sequence_name = ''
        self.sequence_id = -1
        flameMenuNewBatch_prefs = self.framework.prefs.get('flameMenuNewBatch', {})
        self.shot_task_template =  flameMenuNewBatch_prefs.get('shot_task_template', {})
        self.shot_name = ''

        def newSequenceDialog():
            window_NewSequnece = QtWidgets.QDialog()
            window_NewSequnece.setMinimumSize(280, 100)
            window_NewSequnece.setWindowTitle('Create New Sequence in ShotGrid')
            window_NewSequnece.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
            window_NewSequnece.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            window_NewSequnece.setStyleSheet('background-color: #313131')

            if QtCore.__version_info__[0] < 6:
                screen_res = QtWidgets.QDesktopWidget().screenGeometry()
            else:
                mainWindow = QtGui.QGuiApplication.primaryScreen()
                screen_res = mainWindow.screenGeometry()

            window_NewSequnece.move((screen_res.width()/2)-150, (screen_res.height() / 2)-280)

            vbox_NewSequnece = QtWidgets.QVBoxLayout()
            vbox_NewSequnece.setAlignment(QtCore.Qt.AlignTop)

            # Shot Name Label

            lbl_SequenceName = QtWidgets.QLabel('New Sequence Name', window_NewSequnece)
            lbl_SequenceName.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
            lbl_SequenceName.setMinimumHeight(28)
            lbl_SequenceName.setMaximumHeight(28)
            lbl_SequenceName.setAlignment(QtCore.Qt.AlignCenter)
            vbox_NewSequnece.addWidget(lbl_SequenceName)

            # Sequence Name Text Field
            def txt_NewSequenceName_textChanged():
                self.sequence_name = txt_NewSequenceName.text()
            txt_NewSequenceName = QtWidgets.QLineEdit('', window_NewSequnece)
            txt_NewSequenceName.setFocusPolicy(QtCore.Qt.ClickFocus)
            txt_NewSequenceName.setMinimumSize(280, 28)
            txt_NewSequenceName.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
            txt_NewSequenceName.textChanged.connect(txt_NewSequenceName_textChanged)
            vbox_NewSequnece.addWidget(txt_NewSequenceName)

            # Create and Cancel Buttons
            hbox_NewSequneceCreate = QtWidgets.QHBoxLayout()

            btn_NewSequenceCreate = QtWidgets.QPushButton('Create', window_NewSequnece)
            btn_NewSequenceCreate.setFocusPolicy(QtCore.Qt.NoFocus)
            btn_NewSequenceCreate.setMinimumSize(128, 28)
            btn_NewSequenceCreate.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
            btn_NewSequenceCreate.clicked.connect(window_NewSequnece.accept)

            btn_NewSequenceCancel = QtWidgets.QPushButton('Cancel', window_NewSequnece)
            btn_NewSequenceCancel.setFocusPolicy(QtCore.Qt.NoFocus)
            btn_NewSequenceCancel.setMinimumSize(128, 28)
            btn_NewSequenceCancel.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}')
            btn_NewSequenceCancel.clicked.connect(window_NewSequnece.reject)

            hbox_NewSequneceCreate.addWidget(btn_NewSequenceCancel)
            hbox_NewSequneceCreate.addWidget(btn_NewSequenceCreate)

            vbox_NewSequnece.addLayout(hbox_NewSequneceCreate)

            window_NewSequnece.setLayout(vbox_NewSequnece)

            if window_NewSequnece.exec_():
                if self.sequence_name == '':
                    return {}
                else:
                    data = {'project': {'type': 'Project','id': self.connector.sg_linked_project_id},
                    'code': self.sequence_name}
                    return self.connector.sg.create('Sequence', data)
            else:
                return {}

        window = QtWidgets.QDialog()
        window.setMinimumSize(280, 180)
        window.setWindowTitle('Create Shot in ShotGrid')
        window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setStyleSheet('background-color: #313131')

        if QtCore.__version_info__[0] < 6:
            screen_res = QtWidgets.QDesktopWidget().screenGeometry()
        else:
            mainWindow = QtGui.QGuiApplication.primaryScreen()
            screen_res = mainWindow.screenGeometry()

        window.move((screen_res.width()/2)-150, (screen_res.height() / 2)-180)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setAlignment(QtCore.Qt.AlignTop)

        # Sequence label

        lbl_Sequence = QtWidgets.QLabel('Sequence', window)
        lbl_Sequence.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_Sequence.setMinimumHeight(28)
        lbl_Sequence.setMaximumHeight(28)
        lbl_Sequence.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_Sequence)

        # Sequence Selector and New Sequence Button Hbox

        # hbox_Sequence = QtWidgets.QHBoxLayout()
        # hbox_Sequence.setAlignment(QtCore.Qt.AlignLeft)

        # Sequence Selector Button

        btn_Sequence = QtWidgets.QPushButton(window)
        self.sequences = self.connector.sg.find('Sequence', 
            [['project', 'is', {'type': 'Project', 'id': self.connector.sg_linked_project_id}]], 
            ['code'])
        if self.prefs.get('last_sequence_used'):
            sequence = self.prefs.get('last_sequence_used', {})
            code = sequence.get('code', 'No Name')
            self.sequence_id = sequence.get('id', -1)
        else:
            code = 'DefaultSequence'
        btn_Sequence.setText(code)
        self.sequences_by_id = {x.get('id'):x for x in self.sequences}
        self.sequences_by_code_id = {x.get('code') + '_' + str(x.get('id')):x for x in self.sequences}
        def selectSequence(sequence_id):
            
            if sequence_id == 0:
                new_sequence = newSequenceDialog()
                if new_sequence:
                    btn_Sequence_menu.clear()
                    self.sequences = self.connector.sg.find('Sequence', 
                    [['project', 'is', {'type': 'Project', 'id': self.connector.sg_linked_project_id}]], 
                    ['code'])
                    self.sequences_by_id = {x.get('id'):x for x in self.sequences}
                    self.sequences_by_code_id = {x.get('code') + '_' + str(x.get('id')):x for x in self.sequences}
                    action = btn_Sequence_menu.addAction('DefaultSequence')
                    x = lambda chk=False, sequence_id=-1: selectSequence(sequence_id)
                    action.triggered[()].connect(x)
                    for code_id in sorted(self.sequences_by_code_id.keys()):
                        sequence = self.sequences_by_code_id.get(code_id, {})
                        code = sequence.get('code', 'No code')
                        sequence_id = sequence.get('id')
                        action = btn_Sequence_menu.addAction(code)
                        xx = lambda chk=False, sequence_id=sequence_id: selectSequence(sequence_id)
                        action.triggered[()].connect(xx)
                    action = btn_Sequence_menu.addAction('Create New Sequence...')
                    xxx = lambda chk=False, sequence_id=0: selectSequence(sequence_id)
                    action.triggered[()].connect(xxx)
                    btn_Sequence.setMenu(btn_Sequence_menu)
                    self.sequence_id = new_sequence.get('id')
                    btn_Sequence.setText(new_sequence.get('code'))

            elif sequence_id == -1:
                self.sequence_id = -1
                btn_Sequence.setText('DefaultSequence')
                return
            else:
                sequence = self.sequences_by_id.get(sequence_id, {})
                code = sequence.get('code', 'no_code')
                btn_Sequence.setText(code)
                self.sequence_id = sequence_id
                self.prefs['last_sequence_used'] = sequence

        btn_Sequence.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_Sequence.setMinimumSize(280, 28)
        btn_Sequence.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #29323d; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                    'QPushButton:pressed {font:italic; color: #d9d9d9}'
                                    'QPushButton::menu-indicator {image: none;}')
        btn_Sequence_menu = QtWidgets.QMenu()
        action = btn_Sequence_menu.addAction('DefaultSequence')
        x = lambda chk=False, sequence_id=-1: selectSequence(sequence_id)
        action.triggered[()].connect(x)
        for code_id in sorted(self.sequences_by_code_id.keys()):
            sequence = self.sequences_by_code_id.get(code_id, {})
            code = sequence.get('code', 'No code')
            sequence_id = sequence.get('id')
            action = btn_Sequence_menu.addAction(code)
            xx = lambda chk=False, sequence_id=sequence_id: selectSequence(sequence_id)
            action.triggered[()].connect(xx)
        action = btn_Sequence_menu.addAction('Create New Sequence...')
        xxx = lambda chk=False, sequence_id=0: selectSequence(sequence_id)
        action.triggered[()].connect(xxx)
        btn_Sequence.setMenu(btn_Sequence_menu)
        vbox.addWidget(btn_Sequence)

        # Shot Task Template label

        lbl_TaskTemplate = QtWidgets.QLabel('Task Template', window)
        lbl_TaskTemplate.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_TaskTemplate.setMinimumHeight(28)
        lbl_TaskTemplate.setMaximumHeight(28)
        lbl_TaskTemplate.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_TaskTemplate)

        # Shot Task Template Menu

        btn_ShotTaskTemplate = QtWidgets.QPushButton(window)
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
            self.shot_task_template = template
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
        vbox.addWidget(btn_ShotTaskTemplate)

        # Shot Name Label

        lbl_ShotName = QtWidgets.QLabel('New Shot Name', window)
        lbl_ShotName.setStyleSheet('QFrame {color: #989898; background-color: #373737}')
        lbl_ShotName.setMinimumHeight(28)
        lbl_ShotName.setMaximumHeight(28)
        lbl_ShotName.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_ShotName)

        # shot name and buttons hbox
        # hbox_shotname = QtWidgets.QHBoxLayout()

        # Shot Name Text Field
        def txt_ShotName_textChanged():
            self.shot_name = txt_ShotName.text()
        txt_ShotName = QtWidgets.QLineEdit('', window)
        txt_ShotName.setFocusPolicy(QtCore.Qt.ClickFocus)
        txt_ShotName.setMinimumSize(280, 28)
        txt_ShotName.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; border-top: 1px inset #black; border-bottom: 1px inset #545454}')
        txt_ShotName.textChanged.connect(txt_ShotName_textChanged)

        # From Folder Button
        # btn_FromFolder = QtWidgets.QPushButton('From Folder', window)
        # btn_FromFolder.setFocusPolicy(QtCore.Qt.NoFocus)
        # btn_FromFolder.setMinimumSize(78, 28)
        # btn_FromFolder.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
        #                        'QPushButton:pressed {font:italic; color: #d9d9d9}')

        # hbox_shotname.addWidget(txt_ShotName)
        # hbox_shotname.addWidget(btn_FromFolder)
        # vbox.addLayout(hbox_shotname)
        vbox.addWidget(txt_ShotName)

        # Spacer Label

        lbl_Spacer = QtWidgets.QLabel('', window)
        lbl_Spacer.setStyleSheet('QFrame {color: #989898; background-color: #313131}')
        lbl_Spacer.setMinimumHeight(4)
        lbl_Spacer.setMaximumHeight(4)
        lbl_Spacer.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(lbl_Spacer)

        # Create and Cancel Buttons
        hbox_Create = QtWidgets.QHBoxLayout()

        select_btn = QtWidgets.QPushButton('Create', window)
        select_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        select_btn.setMinimumSize(128, 28)
        select_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        select_btn.clicked.connect(window.accept)

        cancel_btn = QtWidgets.QPushButton('Cancel', window)
        cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        cancel_btn.setMinimumSize(128, 28)
        cancel_btn.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black}'
                                'QPushButton:pressed {font:italic; color: #d9d9d9}')
        cancel_btn.clicked.connect(window.reject)

        hbox_Create.addWidget(cancel_btn)
        hbox_Create.addWidget(select_btn)

        vbox.addLayout(hbox_Create)

        window.setLayout(vbox)
        if window.exec_():
            if self.shot_name == '':
                return {}
            else:
                if self.sequence_id == -1:
                    shot_sequence = self.connector.sg.find_one('Sequence',
                        [['project', 'is', {'type': 'Project', 'id': self.connector.sg_linked_project_id}], 
                        ['code', 'is', 'DefaultSequence']]
                        )
                    if not shot_sequence:
                        sequence_data = {'project': {'type': 'Project','id': self.connector.sg_linked_project_id},
                        'code': 'DefaultSequence'}
                        shot_sequence = self.connector.sg.create('Sequence', sequence_data)
                else:
                    shot_sequence = self.connector.sg.find_one('Sequence', [['id', 'is', self.sequence_id]])

                data = {'project': {'type': 'Project','id': self.connector.sg_linked_project_id},
                'code': self.shot_name,
                'sg_sequence': shot_sequence,
                'task_template': self.shot_task_template}
                self.log_debug('creating new shot...')
                new_shot = self.connector.sg.create('Shot', data)
                self.log_debug('new shot:\n%s' % pformat(new_shot))
                self.log_debug('updating async cache for current tasks')
                self.connector.collect_pipeline_data()
                # self.connector.cache_retrive_result('current_tasks', True)
                self.log_debug('creating new batch')
                self.create_new_batch(new_shot)

                # for app in self.framework.apps:
                #    app.rescan()

                return new_shot
        else:
            return {}

        '''
        data = {'project': {'type': 'Project','id': 4},
        'code': '100_010',
        'description': 'dark shot with wicked cool ninjas',
        'task_template': template }
        result = sg.create('Shot', data)
        '''

    def build_flame_friendly_path(self, path):
        import re
        import glob
        import fnmatch

        file_names = os.listdir(os.path.dirname(path))
        if not file_names:
            return None
        frame_pattern = re.compile(r"^(.+?)([0-9#]+|[%]0\dd)$")
        root, ext = os.path.splitext(os.path.basename(path))
        match = re.search(frame_pattern, root)
        if not match:
            return None
        pattern = os.path.join("%s%s" % (re.sub(match.group(2), "*", root), ext))
        files = []
        for file_name in file_names:
            if fnmatch.fnmatch(file_name, pattern):
                files.append(os.path.join(os.path.dirname(path), file_name))
        if not files:
            return None
        file_roots = [os.path.splitext(f)[0] for f in files]
        frame_padding = len(re.search(frame_pattern, file_roots[0]).group(2))
        offset = len(match.group(1))

        # consitency check
        frames = []
        for f in file_roots:
            try:
                frame = int(os.path.basename(f)[offset:offset+frame_padding])
            except:
                continue
            frames.append(frame)
        if not frames:
            return None
        min_frame = min(frames)
        max_frame = max(frames)
        if ((max_frame + 1) - min_frame) != len(frames):
            # report what exactly are missing
            current_frame = min_frame
            for frame in frames:
                if not current_frame in frames:
                    # report logic to be placed here
                    pass
                current_frame += 1
            return None
        
        format_str = "[%%0%sd-%%0%sd]" % (
                frame_padding,
                frame_padding
            )
        
        frame_spec = format_str % (min_frame, max_frame)
        file_name = "%s%s%s" % (match.group(1), frame_spec, ext)

        return os.path.join(
                    os.path.dirname (path),
                    file_name
                    )

    def scope_desktop(self, selection):
        for item in selection:
            if isinstance(item, (self.flame.PyDesktop)):
                return True
        return False

    def flip_assigned(self, *args, **kwargs):
        self.prefs['show_all'] = not self.prefs['show_all']
        self.framework.save_prefs()
        # self.rescan()

    def page_fwd(self, *args, **kwargs):
        if kwargs.get('menu_name'):
            if not self.prefs.get('current_page_' + kwargs.get('menu_name')):
                self.prefs['current_page_' + kwargs.get('menu_name')] = 1
            else:
                self.prefs['current_page_' + kwargs.get('menu_name')] += 1
        else:
            self.prefs['current_page'] += 1
        self.framework.save_prefs()

    def page_bkw(self, *args, **kwargs):
        if kwargs.get('menu_name'):
            if not self.prefs.get('current_page_' + kwargs.get('menu_name')):
                self.prefs['current_page_' + kwargs.get('menu_name')] = 0
            else:
                self.prefs['current_page_' + kwargs.get('menu_name')] = max(self.prefs['current_page_' + kwargs.get('menu_name')] -1, 0)
        else:
            self.prefs['current_page'] = max(self.prefs['current_page'] - 1, 0)
        self.framework.save_prefs()

    def rescan(self, *args, **kwargs):
        if not self.flame:
            try:
                import flame
                self.flame = flame
            except:
                self.flame = None

        # self.connector.cache_retrive_result('current_tasks', True)
        self.connector.collect_pipeline_data()

        if self.flame:
            self.flame.execute_shortcut('Rescan Python Hooks')
            self.log_debug('Rescan Python Hooks')


class flameMenuPublisher(flameMenuApp):
    def __init__(self, framework, connector):
        flameMenuApp.__init__(self, framework)
        self.connector = connector

        # app defaults
        if not self.prefs.master.get(self.name):
            self.prefs['show_all'] = True
            self.prefs['current_page'] = 0
            self.prefs['menu_max_items_per_page'] = 32
            self.prefs['templates'] = default_templates
            # init values from default
            for entity_type in self.prefs['templates'].keys():
                for template in self.prefs['templates'][entity_type].keys():
                    if isinstance(self.prefs['templates'][entity_type][template], dict):
                        if 'default' in self.prefs['templates'][entity_type][template].keys():
                            self.prefs['templates'][entity_type][template]['value'] = self.prefs['templates'][entity_type][template]['default']
         
            self.prefs['flame_export_presets'] = default_flame_export_presets
            self.prefs['poster_frame'] = 1
            self.prefs['version_zero'] = False

        if not self.prefs_global.master.get(self.name):
            self.prefs_global['temp_files_list'] = []

        self.selected_clips = []
        self.create_export_presets()
        self.progress = self.publish_progress_dialog()
        
    def __getattr__(self, name):
        def method(*args, **kwargs):
            entity = self.dynamic_menu_data.get(name)
            if entity:
                if entity.get('caller') == 'build_addremove_menu':
                    self.update_loader_list(entity)
                elif entity.get('caller') == 'flip_assigned_for_entity':
                    self.flip_assigned_for_entity(entity)
                elif entity.get('caller') == 'fold_step_entity':
                    self.fold_step_entity(entity)
                elif entity.get('caller') == 'fold_task_entity':
                    self.fold_task_entity(entity)
                elif entity.get('caller') == 'publish':
                    self.publish(entity, args[0])
            self.rescan()
            self.progress.hide()
        return method

    def create_uid(self):
        import uuid
        uid = ((str(uuid.uuid1()).replace('-', '')).upper())
        return uid[:4]

    def scope_clip(self, selection):
        selected_clips = []
        visibility = False
        for item in selection:
            if isinstance(item, (self.flame.PyClip)):
                selected_clips.append(item)
                visibility = True
        return visibility

    def build_menu(self):
        if not self.connector.user:
            return None
        if not self.connector.linked_project_id:
            return None

        batch_name = self.flame.batch.name.get_value()
        entities_by_id = {}
        all_shots = self.connector.pipeline_data.get('all_shots_for_project')
        all_assets = self.connector.pipeline_data.get('all_assets_for_project')

        for shot in all_shots:
            entities_by_id[shot.get('id')] = shot
        for asset in all_assets:
            entities_by_id[asset.get('id')] = asset
        
        add_menu_list = []

        if (('additional menu ' + batch_name) in self.prefs.keys()) and self.prefs.get('additional menu ' + batch_name):
            add_menu_list = self.prefs.get('additional menu ' + batch_name)

            for index, stored_entity in enumerate(add_menu_list):
                stored_entity_type = stored_entity.get('type', 'Shot')
                stored_entity_id = stored_entity.get('id', 0)
                if not stored_entity_id in entities_by_id.keys():
                    add_menu_list.pop(index)
            
            if not add_menu_list:
                entity = {}
                for current_entity in entities_by_id.values():
                    if current_entity.get('code') == batch_name:
                            entity = current_entity
                            break
                if entity:
                    self.update_loader_list(entity)
                add_menu_list = self.prefs.get('additional menu ' + batch_name)
        else:
            self.prefs['additional menu ' + batch_name] = []

            entity = {}
            for current_entity in entities_by_id.values():
                if current_entity.get('code') == batch_name:
                        entity = current_entity
            if entity:
                self.update_loader_list(entity)
            add_menu_list = self.prefs.get('additional menu ' + batch_name)

        menus = []

        # add_remove_menu = self.build_addremove_menu()
        # for action in add_remove_menu['actions']:
        #    action['isVisible'] = self.scope_clip
        # menus.append(add_remove_menu)
        
        for entity in add_menu_list:
            publish_menu = self.build_publish_menu(entity)
            if publish_menu:
                # for action in publish_menu['actions']:
                #     action['isVisible'] = self.scope_clip
                menus.append(publish_menu)

        return menus

    def build_addremove_menu(self):
        if not self.connector.user:
            return None
        if not self.connector.linked_project:
            return None

        flame_project_name = self.flame.project.current_project.name
        batch_name = self.flame.batch.name.get_value()
        entities_to_mark = []
        add_menu_list = self.prefs.get('additional menu ' + batch_name)
        for item in add_menu_list:
            entities_to_mark.append(item.get('id'))

        menu = {'actions': []}
        menu['name'] = self.menu_group_name + ' Add/Remove'
        menu_item_order = 0

        menu_item = {}
        menu_item['name'] = '~ Rescan'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['execute'] = self.rescan
        menu['actions'].append(menu_item)

        menu_item = {}
        if self.prefs['show_all']:            
            menu_item['name'] = '~ Show Assigned Only'
        else:
            menu_item['name'] = '~ Show All'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['execute'] = self.flip_assigned
        menu['actions'].append(menu_item)

        user_only = not self.prefs['show_all']
        filter_out = ['Project', 'Sequence']
        found_entities = self.get_entities(user_only, filter_out)
        menu_main_body = []

        if len(found_entities) == 0:
            menu_item = {}
            if self.prefs['show_all']:
                menu_item['name'] = ' '*4 + 'No tasks found'
            else:
                menu_item['name'] = ' '*4 + 'No assigned tasks found'
            menu_item['order'] = menu_item_order
            menu_item_order += 1
            menu_item['execute'] = self.rescan
            menu_item['isEnabled'] = False
            menu['actions'].append(menu_item)

        menu_ctrls_len = len(menu)
        menu_lenght = menu_ctrls_len
        menu_lenght += len(found_entities.keys())
        for entity_type in found_entities.keys():
            menu_lenght += len(found_entities.get(entity_type))
        max_menu_lenght = self.prefs.get('menu_max_items_per_page')

        for index, entity_type in enumerate(sorted(found_entities.keys())):
            menu_item = {}
            menu_item['name'] = '- [ ' + entity_type + 's ]'
            menu_item['execute'] = self.rescan
            menu_main_body.append(menu_item)

            entities_by_name = {}
            for entity in found_entities[entity_type]:
                entities_by_name[entity.get('code')] = entity
            for entity_name in sorted(entities_by_name.keys()):
                entity = entities_by_name.get(entity_name)
                menu_item = {}
                if entity.get('id') in entities_to_mark:
                    menu_item['name'] = '  * ' + entity.get('code')
                else:
                    menu_item['name'] = '     ' + entity.get('code')

                entity['caller'] = inspect.currentframe().f_code.co_name
                self.dynamic_menu_data[str(id(entity))] = entity
                menu_item['execute'] = getattr(self, str(id(entity)))
                menu_main_body.append(menu_item)

        if menu_lenght < max_menu_lenght:
        # controls and entites fits within menu size
        # we do not need additional page switch controls
            for menu_item in menu_main_body:
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

        else:
            # round up number of pages and get current page
            num_of_pages = ((menu_lenght) + max_menu_lenght - 1) // max_menu_lenght
            curr_page = self.prefs.get('current_page')
            
            # decorate top with move backward control
            # if we're not on the first page
            if curr_page > 0:
                menu_item = {}
                menu_item['name'] = '<<[ prev page ' + str(curr_page) + ' of ' + str(num_of_pages) + ' ]'
                menu_item['execute'] = self.page_bkw
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

            # calculate the start and end position of a window
            # and append items to the list
            menu_used_space = menu_ctrls_len + 2 # two more controls for page flip
            window_size = max_menu_lenght - menu_used_space
            start_index = window_size*curr_page + min(1*curr_page, 1)
            end_index = window_size*curr_page+window_size + ((curr_page+1) // num_of_pages)

            for menu_item in menu_main_body[start_index:end_index]:
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
            
            # decorate bottom with move forward control
            # if we're not on the last page            
            if curr_page < (num_of_pages - 1):
                menu_item = {}
                menu_item['name'] = '[ next page ' + str(curr_page+2) + ' of ' + str(num_of_pages) + ' ]>>'
                menu_item['execute'] = self.page_fwd
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

        return menu

    def build_publish_menu(self, entity):
        
        # pprint (self.connector.pipeline_data.get('entity_by_id').get(entity.get('parent_id')))

        if not entity.get('code'):
            entity['code'] = entity.get('name', 'no_name')
        
        entity_type = entity.get('type')
        entity_id = entity.get('id')
        entity_key = (entity_type, entity_id)
        if entity_key not in self.prefs.keys():
            self.prefs[entity_key] = {}
            self.prefs[entity_key]['show_all'] = True

        tasks_by_entity_id = self.connector.pipeline_data.get('tasks_by_entity_id')

        if not tasks_by_entity_id:
            tasks_by_entity_id = {}

        if not entity_id in tasks_by_entity_id.keys():
            # try to collect data
            self.connector.collect_entity_linked_info(entity_key)
            if not entity_id in tasks_by_entity_id.keys():
                # something went wrong
                tasks = []
            else:
                tasks = tasks_by_entity_id.get(entity_id)
        else:
            tasks = tasks_by_entity_id.get(entity_id)

        preview_by_task_id = self.connector.pipeline_data.get('preview_by_task_id')
        if not preview_by_task_id:
            preview_by_task_id = {}

        if not self.connector.user:
            human_user = {'id': 0}
        else:
            human_user = self.connector.user

        menu = {}
        menu['name'] = self.menu_group_name + ' Publish ' + entity.get('code') + ':'
        menu['actions'] = []
        menu_item_order = 0


        menu_item = {}
        menu_item['name'] = '~ Rescan'
        menu_item['order'] = menu_item_order
        menu_item_order += 1
        menu_item['execute'] = self.rescan
        menu['actions'].append(menu_item)

        menu_item = {}        
        show_all_entity = dict(entity)
        show_all_entity['caller'] = 'flip_assigned_for_entity'

        if self.prefs[entity_key]['show_all']:            
            menu_item['name'] = '~ Show Assigned Only'
        else:
            menu_item['name'] = '~ Show All Tasks'

        menu_item['order'] = menu_item_order
        menu_item_order += 1
        self.dynamic_menu_data[str(id(show_all_entity))] = show_all_entity
        menu_item['execute'] = getattr(self, str(id(show_all_entity)))
        menu['actions'].append(menu_item)

        tasks_by_step = {}
        for task in tasks:
            task_assignees = task.get('assignees')
            if not self.prefs[entity_key]['show_all']:
                if human_user.get('id') not in task_assignees:
                    continue
            
            step_name = task.get('task_type_name')
            if not step_name:
                step_name = ''
            step_id = task.get('task_type_id')

            if step_name not in tasks_by_step.keys():
                tasks_by_step[step_name] = []
            tasks_by_step[step_name].append(task)
        
        if len(tasks_by_step.values()) == 0:
            menu_item = {}
            if self.prefs[entity_key]['show_all']:
                menu_item['name'] = ' '*4 + 'No tasks found'
            else:
                menu_item['name'] = ' '*4 + 'No assigned tasks found'

            menu_item['order'] = menu_item_order
            menu_item_order += 1
            menu_item['execute'] = self.rescan
            menu_item['isEnabled'] = False
            menu['actions'].append(menu_item)

        current_steps = self.connector.pipeline_data.get('all_task_types_for_project')
        entity_steps = [x for x in current_steps if x.get('for_entity') == entity_type]
        entity_steps_by_code = {step.get('name'):step for step in entity_steps}
        current_step_names = tasks_by_step.keys()
        current_step_order = []
        for step in current_step_names:
            current_step_order.append(entity_steps_by_code.get(step, dict()).get('priority', 999))

        for step_name in (x for _, x in sorted(zip(current_step_order, current_step_names))):
            step_key = ('Step', step_name)

            if step_key not in self.prefs[entity_key].keys():
                self.prefs[entity_key][step_key] = {'isFolded': False}

            fold_step_entity = dict(entity)
            fold_step_entity['caller'] = 'fold_step_entity'
            fold_step_entity['key'] = step_key
            self.dynamic_menu_data[str(id(fold_step_entity))] = fold_step_entity

            menu_item = {}
            menu_item['execute'] = getattr(self, str(id(fold_step_entity)))

            if self.prefs[entity_key][step_key].get('isFolded') and len(tasks_by_step[step_name]) != 1:
                menu_item['name'] = '+ [ ' + step_name + ' ]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
                continue
            elif self.prefs[entity_key][step_key].get('isFolded') and tasks_by_step[step_name][0].get('content') != step_name:
                menu_item['name'] = '+ [ ' + step_name + ' ]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
                continue

            if len(tasks_by_step[step_name]) != 1:
                menu_item['name'] = '- [ ' + step_name + ' ]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
            elif tasks_by_step[step_name][0].get('content') != step_name:
                menu_item['name'] = '- [ ' + step_name + ' ]'
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)

            for task in tasks_by_step[step_name]:
                task_key = ('Task', task.get('id'))
                if task_key not in self.prefs[entity_key].keys():
                    self.prefs[entity_key][task_key] = {'isFolded': False}
                
                fold_task_entity = dict(entity)
                fold_task_entity['caller'] = 'fold_task_entity'
                fold_task_entity['key'] = task_key
                self.dynamic_menu_data[str(id(fold_task_entity))] = fold_task_entity
                
                task_name = task.get('task_type_name')
                menu_item = {}

                if (task_name == step_name) and (len(tasks_by_step[step_name]) == 1):
                    pass
                    # if self.prefs[entity_key][task_key].get('isFolded'):
                    #    menu_item['name'] = '+ [ ' + task_name + ' ]'
                    # else:
                    #    menu_item['name'] = '- [ ' + task_name + ' ]'
                else:
                    if self.prefs[entity_key][task_key].get('isFolded'):
                        menu_item['name'] = ' '*4 + '+ [ ' + task_name + ' ]'
                    else:
                        menu_item['name'] = ' '*4 + '- [ ' + task_name + ' ]'
                    menu_item['execute'] = getattr(self, str(id(fold_task_entity)))
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)

                if self.prefs[entity_key][task_key].get('isFolded'): continue

                task_id = task.get('id')
                task_versions = preview_by_task_id.get(task_id)

                version_names = []
                version_names_set = set()

                for version in task_versions:
                    version_names_set.add('* ' + version.get('original_name'))

                for name in sorted(version_names_set):
                    version_names.append('* ' + name)

                for version_name in version_names:
                    menu_item = {}
                    menu_item['name'] = ' '*8 + version_name
                    menu_item['execute'] = self.rescan
                    menu_item['isEnabled'] = False
                    menu_item['order'] = menu_item_order
                    menu_item_order += 1
                    menu['actions'].append(menu_item)
                
                menu_item = {}
                menu_item['name'] = ' '*12 + 'publish to task "' + task_name + '"'
                publish_entity = {}
                publish_entity['caller'] = 'publish'
                publish_entity['task'] = task
                publish_entity['entity'] = entity
                publish_entity['parent'] = self.connector.pipeline_data['entity_by_id'].get(entity.get('parent_id'))
                self.dynamic_menu_data[str(id(publish_entity))] = publish_entity
                menu_item['execute'] = getattr(self, str(id(publish_entity)))
                menu_item['waitCursor'] = False
                menu_item['order'] = menu_item_order
                menu_item_order += 1
                menu['actions'].append(menu_item)
                
        return menu

    def publish(self, entity, selection):
        
        # Main publishing function

        # temporary move built-in integration out of the way
        # we may not need by passing the empty set of hooks
        # self.connector.destroy_toolkit_engine()
        
        # First,let's check if the project folder is there
        # and if not - try to create one
        # connector takes care of storage root check and selection
        # we're going to get empty path if connector was not able to resolve it

        project_path = self.connector.resolve_storage_root()

        if not project_path:
        #    message = 'Publishing stopped: Unable to resolve project path.'
        #    self.mbox.setText(message)
        #    self.mbox.exec_()
            return False

        # check if the project path is there and try to create if not

        if not os.path.isdir(project_path):
            try:
                os.makedirs(project_path)
            except Exception as e:
                message = 'Publishing stopped: Unable to create project folder %s, reason: %s' % (project_path, e)
                self.mbox.setText(message)
                self.mbox.exec_()
                return False

        # get necessary fields from currently selected export preset

        export_preset_fields = self.get_export_preset_fields(self.prefs['flame_export_presets'].get('Publish'))
        if not export_preset_fields:
            return False

        # try to publish each of selected clips
        
        versions_published = set()
        versions_failed = set()
        pb_published = dict()
        pb_failed = dict()

        for clip in selection:
            pb_info, is_cancelled = self.publish_clip(clip, entity, project_path, export_preset_fields)

            if not pb_info:
                continue
        
            if pb_info.get('status', False):
                version_name = pb_info.get('version_name')
                versions_published.add(version_name)
                data = pb_published.get(version_name, [])
                data.append(pb_info)
                pb_published[version_name] = data
            else:
                version_name = pb_info.get('version_name')
                versions_failed.add(version_name)
                data = pb_failed.get(version_name, [])
                data.append(pb_info)
                pb_failed[version_name] = data
            if is_cancelled:
                break

        # report user of the status
        
        if is_cancelled and (len(versions_published) == 0):
            return False
        elif (len(versions_published) == 0) and (len(versions_failed) > 0):
            msg = 'Failed to publish into %s versions' % len(versions_failed)
        elif (len(versions_published) > 0) and (len(versions_failed) == 0):
            msg = 'Published %s version(s)' % len(versions_published)
        else:
            msg = 'Published %s version(s), %s version(s) failed' % (len(versions_published), len(versions_failed))

        # We may not need it by passing empty set of hooks
        # self.connector.bootstrap_toolkit()

        mbox = self.mbox
        mbox.setText('flameMenuKITSU: ' + msg)

        detailed_msg = ''

        if len(versions_published) > 0:
            detailed_msg += 'Published:\n'
            for version_name in sorted(pb_published.keys()):
                pb_info_list = pb_published.get(version_name)
                for pb_info in pb_info_list:
                    detailed_msg += ' '*4 + pb_info.get('version_name') + ':\n'
                    if pb_info.get('flame_render', {}).get('flame_path'):
                        path = pb_info.get('flame_render', {}).get('flame_path')
                    else:
                        path = pb_info.get('flame_render', {}).get('path_cache')
                    detailed_msg += ' '*8 + os.path.basename(path) + '\n'
                    path_cache = pb_info.get('flame_batch', {}).get('path_cache')
                    detailed_msg += ' '*8 + os.path.basename(path_cache) + '\n'
        if len(versions_failed) > 0:
            detailed_msg += 'Failed to publish: \n'
            for version_name in sorted(pb_failed.keys()):
                pb_info_list = pb_failed.get(version_name)
                for pb_info in pb_info_list:
                    detailed_msg += ' '*4 + pb_info.get('flame_clip_name') + ':\n'
        mbox.setDetailedText(detailed_msg)
        mbox.setStyleSheet('QLabel{min-width: 500px;}')
        mbox.exec_()

        return True

    def publish_clip(self, clip, entity, project_path, preset_fields):

        # Publishes the clip and returns published files info and status
        
        # Each flame clip publish will create primary publish, and batch file.
        # there could be potentially secondary published defined in the future.
        # the function will return the dictionary with information on that publishes
        # to be presented to user, as well as is_cancelled flag.
        # If there's an error and current publish should be stopped that gives
        # user the possibility to stop other selected clips from being published
        # returns: (dict)pb_info , (bool)is_cancelled

        # dictionary that holds information about publish
        # publish_clip will return the list of info dicts
        # along with the status. It is purely to be able
        # to inform user of the status after we processed multpile clips

        try:
            from PySide2 import QtWidgets
        except ImportError:
            from PySide6 import QtWidgets

        pb_info = {
            'flame_clip_name': clip.name.get_value(),        # name of the clip selected in flame
            'version_name': '',     # name of a version in shotgun
            'flame_render': {       # 'flame_render' related data
                'path_cache': '',
                'pb_file_name': ''
            },
            'flame_batch': {        # 'flame_batch' related data
                'path_cache': '',
                'pb_file_name': ''
            },
            'status': False         # status of the flame clip publish
        }

        # Process info we've got from entity

        self.log_debug('Starting publish_clip for %s with entity:' % pb_info.get('flame_clip_name'))
        self.log_debug('\n%s' % pformat(entity))

        task = entity.get('task')
        task_entity = entity.get('entity')
        task_entity_type = task_entity.get('type')
        task_entity_name = task_entity.get('code')
        task_entity_id = task_entity.get('id')
        task_step = task.get('task_type_name')
        task_step_code = task.get('task_type_name')
        if not task_step_code:
            task_step_code = task_step.upper()
        sequence = entity.get('parent')
        if not sequence:
            sequence_name = 'NoSequence'
        else:
            sequence_name = sequence.get('name', 'NoSequence')
        sg_asset_type = task.get('entity.Asset.sg_asset_type','NoType')
        uid = self.create_uid()
        
        # linked .batch file path resolution
        # if the clip consists of several clips with different linked batch setups
        # fall back to the current batch setup (should probably publish all of them?)

        self.log_debug('looking for linked batch setup...')

        import ast

        linked_batch_path = None
        comments = set()
        for version in clip.versions:
            for track in version.tracks:
                for segment in track.segments:
                    comments.add(segment.comment.get_value())
        if len(comments) == 1:
            comment = comments.pop()
            start_index = comment.find("{'batch_file': ")
            end_index = comment.find("'}", start_index)
            if (start_index > 0) and (end_index > 0):
                try:
                    linked_batch_path_dict = ast.literal_eval(comment[start_index:end_index+2])
                    linked_batch_path = linked_batch_path_dict.get('batch_file')
                except:
                    pass

        self.log_debug('linked batch setup: %s' % linked_batch_path)

        # basic name/version detection from clip name

        self.log_debug('parsing clip name %s' % pb_info.get('flame_clip_name'))

        batch_group_name = self.flame.batch.name.get_value()

        clip_name = clip.name.get_value()
        version_number = -1
        version_padding = -1
        if clip_name.startswith(batch_group_name):
            clip_name = clip_name[len(batch_group_name):]
        if len(clip_name) == 0:
            clip_name = task_step_code.lower()

        if clip_name[-1].isdigit():
            match = re.split('(\d+)', clip_name)
            try:
                version_number = int(match[-2])
            except:
                pass

            version_padding = len(match[-2])
            clip_name = clip_name[: -version_padding]
        
        if clip_name.endswith('v'):
            clip_name = clip_name[:-1] 
        
        if any([clip_name.startswith('_'), clip_name.startswith(' '), clip_name.startswith('.')]):
            clip_name = clip_name[1:]
        if any([clip_name.endswith('_'), clip_name.endswith(' '), clip_name.endswith('.')]):
            clip_name = clip_name[:-1]

        self.log_debug('parsed clip_name: %s' % clip_name)

        if version_number == -1:
            self.log_debug('can not parse version, looking for batch iterations')
            version_number = len(self.flame.batch.batch_iterations) + 1
            # if (version_number == 0) and (not self.prefs.get('version_zero', False)):
            #    version_number = 1
            version_padding = 3
        
        self.log_debug('version number: %s' % version_number)
        self.log_debug('version_zero status: %s' % self.prefs.get('version_zero', False))

        # collect known template fields

        self.log_debug('preset fields: %s' % pformat(preset_fields))

        if preset_fields.get('type') == 'movie':
            sg_frame = ''
        else:
            sg_frame = '%' + '{:02d}'.format(preset_fields.get('framePadding')) + 'd'

        template_fields = {}
        template_fields['Project'] = self.connector.linked_project
        template_fields['Shot'] = task_entity_name
        template_fields['Asset'] = task_entity_name
        template_fields['sg_asset_type'] = sg_asset_type
        template_fields['name'] = clip_name
        template_fields['TaskType'] = task_step
        template_fields['Step_code'] = task_step_code
        template_fields['Sequence'] = sequence_name
        template_fields['version'] = '{:03d}'.format(version_number)
        template_fields['version_four'] = '{:04d}'.format(version_number)
        template_fields['ext'] = preset_fields.get('fileExt')
        template_fields['frame'] = sg_frame

        self.log_debug('template fields:')
        self.log_debug('\n%s' % pformat(template_fields))

        # compose version name from template
        
        version_name = self.prefs.get('templates', {}).get(task_entity_type, {}).get('version_name', {}).get('value', '')

        self.log_debug('version name template: %s' % version_name)

        version_name = version_name.format(**template_fields)
        update_version_preview = True
        update_version_thumbnail = True
        pb_info['version_name'] = version_name

        self.log_debug('resolved version name: %s' % version_name)

        # 'flame_render'
        # start with flame_render publish first.

        self.log_debug('starting flame_render publish...') 

        pb_file_name = task_entity_name + ', ' + clip_name

        # compose export path anf path_cache filed from template fields

        export_path = self.prefs.get('templates', {}).get(task_entity_type, {}).get('flame_render', {}).get('value', '')

        self.log_debug('flame_render export preset: %s' % export_path)

        export_path = export_path.format(**template_fields)
        path_cache = export_path.format(**template_fields)
        export_path = os.path.join(project_path, export_path)
        path_cache = os.path.join(os.path.basename(project_path), path_cache)

        if preset_fields.get('type') == 'movie':
            export_path = export_path.replace('..', '.')
            path_cache = path_cache.replace('..', '.')

        self.log_debug('resolved export path: %s' % export_path)
        self.log_debug('path_cache %s' % path_cache)

        # get PublishedFileType from Shotgun
        # if it is not there - create it
        flame_render_type = self.prefs.get('templates', {}).get(task_entity_type, {}).get('flame_render', {}).get('PublishedFileType', '')
        # self.log_debug('PublishedFile type: %s, querying ShotGrid' % flame_render_type)
        # published_file_type = self.connector.sg.find_one('PublishedFileType', filters=[["code", "is", flame_render_type]])
        # self.log_debug('PublishedFile type: found: %s' % pformat(published_file_type))        
        # if not published_file_type:
        #    self.log_debug('creating PublishedFile type %s' % flame_render_type)
        #    published_file_type = self.connector.sg.create("PublishedFileType", {"code": flame_render_type})
        #    self.log_debug('created: %s' % pformat(published_file_type))

        # fill the pb_info data for 'flame_render'
        pb_info['flame_render']['path_cache'] = path_cache
        pb_info['flame_render']['pb_file_name'] = pb_file_name

        # Export section

        original_clip_name = clip.name.get_value()

        # Try to export preview and thumbnail in background
                
        class BgExportHooks(object):
            def preExport(self, info, userData, *args, **kwargs):
                pass
            def postExport(self, info, userData, *args, **kwargs):
                pass
            def preExportSequence(self, info, userData, *args, **kwargs):
                pass
            def postExportSequence(self, info, userData, *args, **kwargs):
                pass
            def preExportAsset(self, info, userData, *args, **kwargs):
                pass
            def postExportAsset(self, info, userData, *args, **kwargs):
                del args, kwargs
                pass
            def exportOverwriteFile(self, path, *args, **kwargs):
                del path, args, kwargs
                return "overwrite"
        
        bg_exporter = self.flame.PyExporter()
        bg_exporter.foreground = False

        # Exporting previews in background 
        # doesn'r really work with concurrent exports in FG
        # Render queue just becomes cluttered with
        # unneeded and unfinished exports

        # Disabling preview bg export block at the moment
        # But leaving thumbnail export
        
        # self.log_debug('sending preview to background export')
        # preset_path = os.path.join(self.framework.prefs_folder, 'GeneratePreview.xml')
        # clip.name.set_value(version_name + '_preview_' + uid)
        export_dir = '/var/tmp'
        preview_path = os.path.join(export_dir, version_name + '_preview_' + uid + '.mov')
        # self.prefs_global['temp_files_list'].append(preview_path)

        '''
        self.log_debug('background exporting preview %s' % clip.name.get_value())
        self.log_debug('with preset: %s' % preset_path)
        self.log_debug('into folder: %s' % export_dir)

        try:
            bg_exporter.export(clip, preset_path, export_dir,  hooks=BgExportHooks())
        except Exception as e:
            self.log_debug('error exporting in background %s' % e)
            pass
        '''

        preset_path = os.path.join(self.framework.prefs_folder, 'GenerateThumbnail.xml')
        preset_path = self.create_export_preset(preset_path)

        clip.name.set_value(version_name + '_thumbnail_' + uid)
        export_dir = '/var/tmp'
        thumbnail_path = os.path.join(export_dir, version_name + '_thumbnail_' + uid + '.jpg')
        self.prefs_global['temp_files_list'].append(thumbnail_path)
        clip_in_mark = clip.in_mark.get_value()
        clip_out_mark = clip.out_mark.get_value()
        clip.in_mark = self.prefs.get('poster_frame', 1)
        clip.out_mark = self.prefs.get('poster_frame', 1) + 1
        bg_exporter.export_between_marks = True

        self.log_debug('background exporting thumbnail %s' % clip.name.get_value())
        self.log_debug('with preset: %s' % preset_path)
        self.log_debug('into folder: %s' % export_dir)
        self.log_debug('poster frame: %s' % self.prefs.get('poster_frame', 1))

        try:
            bg_exporter.export(clip, preset_path, export_dir,  hooks=BgExportHooks())
        except Exception as e:
            self.log_debug('error exporting in background %s' % e)
            pass

        clip.in_mark.set_value(clip_in_mark)
        clip.out_mark.set_value(clip_out_mark)
        clip.name.set_value(original_clip_name)

        # Export using main preset

        self.log_debug('starting export form flame')

        preset_path = preset_fields.get('path')

        self.log_debug('export preset: %s' % preset_path)

        class ExportHooks(object):
            def preExport(self, info, userData, *args, **kwargs):
                pass
            def postExport(self, info, userData, *args, **kwargs):
                pass
            def preExportSequence(self, info, userData, *args, **kwargs):
                pass
            def postExportSequence(self, info, userData, *args, **kwargs):
                pass
            def preExportAsset(self, info, userData, *args, **kwargs):
                pass
            def postExportAsset(self, info, userData, *args, **kwargs):
                del args, kwargs
                pass
            def exportOverwriteFile(self, path, *args, **kwargs):
                del path, args, kwargs
                return "overwrite"

        exporter = self.flame.PyExporter()
        exporter.foreground = True
        export_clip_name, ext = os.path.splitext(os.path.basename(export_path))
        export_clip_name = export_clip_name.replace(sg_frame, '')
        if export_clip_name.endswith('.'):
            export_clip_name = export_clip_name[:-1]
        clip.name.set_value(str(export_clip_name))
        export_dir = str(os.path.dirname(export_path))

        if not os.path.isdir(export_dir):
            self.log_debug('creating folders: %s' % export_dir)
            try:
                os.makedirs(export_dir)
            except:
                clip.name.set_value(original_clip_name)
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error publishing flame clip %s:\nunable to create destination folder.' % pb_info.get('flame_clip_name', ''))
                mbox.setDetailedText('Path: ' + export_dir)
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)

        self.log_debug('exporting clip %s' % clip.name.get_value())
        self.log_debug('with preset: %s' % preset_path)
        self.log_debug('into folder: %s' % export_dir)

        try:
            exporter.export(clip, preset_path, export_dir, hooks=ExportHooks())
            clip.name.set_value(original_clip_name)
        except Exception as e:
            clip.name.set_value(original_clip_name)
            mbox = QtWidgets.QMessageBox()
            mbox.setText('Error publishing flame clip %s:\n%s.' % (pb_info.get('flame_clip_name', ''), e))
            mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
            # mbox.setStyleSheet('QLabel{min-width: 400px;}')
            btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
            btn_Continue.setText('Continue')
            mbox.exec_()
            if mbox.clickedButton() == btn_Continue:
                return (pb_info, False)
            else:
                return (pb_info, True)

        if not (os.path.isfile(preview_path) and os.path.isfile(thumbnail_path)):
            self.log_debug('no background previews ready, exporting in fg')
            
            # Export preview to temp folder

            # preset_dir = self.flame.PyExporter.get_presets_dir(
            #   self.flame.PyExporter.PresetVisibility.Shotgun,
            #   self.flame.PyExporter.PresetType.Movie
            # )
            # preset_path = os.path.join(preset_dir, 'Generate Preview.xml')
            preset_path = os.path.join(self.framework.prefs_folder, 'GeneratePreview.xml')
            preset_path = self.create_export_preset(preset_path)
            # clip.name.set_value(version_name + '_preview_' + uid)
            export_dir = '/var/tmp'
            # preview_path = os.path.join(export_dir, version_name + '_preview_' + uid + '.mov')
            preview_path = os.path.join(export_dir, version_name + '.mov')
            try:
                os.remove(preview_path)
            except:
                pass

            self.log_debug('exporting preview %s' % clip.name.get_value())
            self.log_debug('with preset: %s' % preset_path)
            self.log_debug('into folder: %s' % export_dir)

            try:
                exporter.export(clip, preset_path, export_dir,  hooks=ExportHooks())
            except:
                pass
            
            '''
            # Set clip in and out marks and export thumbnail to temp folder

            # preset_dir = self.flame.PyExporter.get_presets_dir(
            #    self.flame.PyExporter.PresetVisibility.Shotgun,
            #    self.flame.PyExporter.PresetType.Image_Sequence
            # )
            # preset_path = os.path.join(preset_dir, 'Generate Thumbnail.xml')
            preset_path = os.path.join(self.framework.prefs_folder, 'GenerateThumbnail.xml')
            clip.name.set_value(version_name + '_thumbnail_' + uid)
            export_dir = '/var/tmp'
            thumbnail_path = os.path.join(export_dir, version_name + '_thumbnail_' + uid + '.jpg')
            clip_in_mark = clip.in_mark.get_value()
            clip_out_mark = clip.out_mark.get_value()
            clip.in_mark = self.prefs.get('poster_frame', 1)
            clip.out_mark = self.prefs.get('poster_frame', 1) + 1
            exporter.export_between_marks = True

            self.log_debug('exporting thumbnail %s' % clip.name.get_value())
            self.log_debug('with preset: %s' % preset_path)
            self.log_debug('into folder: %s' % export_dir)
            self.log_debug('poster frame: %s' % self.prefs.get('poster_frame', 1))

            try:
                exporter.export(clip, preset_path, export_dir,  hooks=ExportHooks())
            except:
                pass
            '''
            
            clip.in_mark.set_value(clip_in_mark)
            clip.out_mark.set_value(clip_out_mark)
            clip.name.set_value(original_clip_name)


        # Create version in Shotgun

        self.log_debug('creating new comment in Kitsu')
        self.progress.show()
        self.progress.set_progress(version_name, 'Creating comment...')

        task_status = {'id': task.get('task_status_id')}

        try:
            kitsu_comment = self.connector.gazu.task.add_comment(
                task,
                task_status,
                version_name,
                person = self.connector.user,
                client = self.connector.gazu_client
                )
            self.log_debug('created comment: \n%s' % pformat(comment))
        except Exception as e:
            self.progress.hide()
            mbox = QtWidgets.QMessageBox()
            mbox.setText('Error creating comment in Kitsu')
            mbox.setDetailedText(pformat(e))
            mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
            # mbox.setStyleSheet('QLabel{min-width: 400px;}')
            btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
            btn_Continue.setText('Continue')
            mbox.exec_()
            if mbox.clickedButton() == btn_Continue:
                return (pb_info, False)
            else:
                return (pb_info, True)        

        '''
        if os.path.isfile(thumbnail_path) and update_version_thumbnail:
            self.log_debug('uploading thumbnail %s' % thumbnail_path)
            self.progress.set_progress(version_name, 'Uploading thumbnail...')
            try:
                self.connector.sg.upload_thumbnail('Version', version.get('id'), thumbnail_path)
            except Exception as e:
                self.progress.hide()
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error uploading version thumbnail to ShotGrid')
                mbox.setDetailedText(pformat(e))
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)
        '''

        if os.path.isfile(preview_path) and update_version_preview:
            self.log_debug('uploading preview %s' % preview_path)
            self.progress.set_progress(version_name, 'Uploading preview...')
            time.sleep(0.1)
            self.progress.set_progress(version_name, 'Uploading preview...')
            try:
                kitsu_preview_response = self.connector.gazu.task.add_preview(
                    task,
                    kitsu_comment,
                    preview_path,
                    client = self.connector.gazu_client
                )
                self.log_debug('response for uploading preview %s' % pformat(kitsu_preview_response))
            except:
                try:
                    self.connector.gazu.task.add_preview(
                        task,
                        kitsu_comment,
                        preview_path,
                        client = self.connector.gazu_client
                    )
                except Exception as e:
                    self.progress.hide()
                    mbox = QtWidgets.QMessageBox()
                    mbox.setText('Error uploading preview to Kitsu')
                    mbox.setDetailedText(pformat(e))
                    mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                    # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                    btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                    btn_Continue.setText('Continue')
                    mbox.exec_()
                    if mbox.clickedButton() == btn_Continue:
                        return (pb_info, False)
                    else:
                        return (pb_info, True)

        # Create 'flame_render' PublishedFile
        '''
        self.log_debug('creating flame_render published file in ShotGrid')

        published_file_data = dict(
            project = {'type': 'Project', 'id': self.connector.sg_linked_project_id},
            version_number = version_number,
            task = {'type': 'Task', 'id': task.get('id')},
            version = version,
            entity = task_entity,
            published_file_type = published_file_type,
            path = {'relative_path': path_cache, 'local_storage': self.connector.sg_storage_root},
            path_cache = path_cache,
            code = os.path.basename(path_cache),
            name = pb_file_name
        )
        self.progress.set_progress(version_name, 'Registering main publish files...')
        try:
            published_file = self.connector.sg.create('PublishedFile', published_file_data)
        except Exception as e:
            self.progress.hide()
            mbox = QtWidgets.QMessageBox()
            mbox.setText('Error creating published file in ShotGrid')
            mbox.setDetailedText(pformat(e))
            mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
            # mbox.setStyleSheet('QLabel{min-width: 400px;}')
            btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
            btn_Continue.setText('Continue')
            mbox.exec_()
            if mbox.clickedButton() == btn_Continue:
                return (pb_info, False)
            else:
                return (pb_info, True)


        self.log_debug('created PublishedFile:\n%s' % pformat(published_file))
        self.log_debug('uploading thumbnail %s' % thumbnail_path)
        self.progress.set_progress(version_name, 'Uploading main publish files thumbnail...')
        try:
            self.connector.sg.upload_thumbnail('PublishedFile', published_file.get('id'), thumbnail_path)
        except:
            try:
                self.connector.sg.upload_thumbnail('PublishedFile', published_file.get('id'), thumbnail_path)
            except Exception as e:
                self.progress.hide()
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error uploading thumbnail to ShotGrid')
                mbox.setDetailedText(pformat(e))
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)        
        '''
        pb_info['status'] = True

        # check what we've actually exported and get start and end frames from there
        # this won't work for movie, so check the preset first
        # this should be moved in a separate function later

        self.log_debug('getting start and end frames from exported clip')
        
        flame_path = ''
        flame_render_path_cache = pb_info.get('flame_render', {}).get('path_cache', '')
        flame_render_export_dir = os.path.join(os.path.dirname(project_path), os.path.dirname(flame_render_path_cache))

        if preset_fields.get('type', 'image') == 'image':
            import fnmatch

            try:
                file_names = [f for f in os.listdir(flame_render_export_dir) if os.path.isfile(os.path.join(flame_render_export_dir, f))]
            except:
                file_names = []
                                    
            frame_pattern = re.compile(r"^(.+?)([0-9#]+|[%]0\dd)$")
            root, ext = os.path.splitext(os.path.basename(flame_render_path_cache))
            match = re.search(frame_pattern, root)
            if match:
                pattern = os.path.join("%s%s" % (re.sub(match.group(2), "*", root), ext))
                files = list()
                for file_name in file_names:
                    if fnmatch.fnmatch(file_name, pattern):
                        files.append(os.path.join(export_dir, file_name))
                
                if files:
                    file_roots = [os.path.splitext(f)[0] for f in files]
                    frame_padding = len(re.search(frame_pattern, file_roots[0]).group(2))
                    offset = len(match.group(1))
                    frames = list()
                    for f in file_roots:
                        try:
                            frame = int(os.path.basename(f)[offset:offset+frame_padding])
                        except:
                            continue
                        frames.append(frame)

                    if frames:
                        min_frame = min(frames)
                        self.log_debug('start frame: %s' % min_frame)
                        max_frame = max(frames)
                        self.log_debug('end_frame %s' % min_frame)
                        format_str = "[%%0%sd-%%0%sd]" % (frame_padding, frame_padding)
                        frame_spec = format_str % (min_frame, max_frame)
                        flame_file_name = "%s%s%s" % (match.group(1), frame_spec, ext)
                        flame_path = os.path.join(export_dir, flame_file_name)

                        # self.connector.sg.update('Version', version.get('id'), {'sg_first_frame': min_frame, 'sg_last_frame': max_frame})

            pb_info['flame_render']['flame_path'] = flame_path
        
        elif preset_fields.get('type', 'image') == 'movie':
            pass
            # placeholder for movie export

        # publish .batch file
        # compose batch export path and path_cache filed from template fields

        self.log_debug('starting .batch file publish')

        export_path = self.prefs.get('templates', {}).get(task_entity_type, {}).get('flame_batch', {}).get('value', '')
        export_path = export_path.format(**template_fields)
        path_cache = export_path.format(**template_fields)
        export_path = os.path.join(project_path, export_path)
        path_cache = os.path.join(os.path.basename(project_path), path_cache)

        self.log_debug('resolved export path: %s' % export_path)
        self.log_debug('path_cache %s' % path_cache)

        pb_info['flame_batch']['path_cache'] = path_cache
        pb_info['flame_batch']['pb_file_name'] = task_entity_name
        
        # copy flame .batch file linked to the clip or save current one if not resolved from comments

        export_dir = os.path.dirname(export_path)
        if not os.path.isdir(export_dir):
            self.log_debug('creating folders: %s' % export_dir)
            try:
                os.makedirs(export_dir)
            except:
                clip.name.set_value(original_clip_name)
                self.progress.hide()
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error publishing flame clip %s:\nunable to create destination .batch folder.' % pb_info.get('flame_clip_name', ''))
                mbox.setDetailedText('Path: ' + export_dir)
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)

        if linked_batch_path:
            self.progress.set_progress(version_name, 'Copying linked batch...')
            self.log_debug('copying linked .batch file')
            self.log_debug('from %s' % linked_batch_path)
            self.log_debug('to %s' % export_path)

            src, ext = os.path.splitext(linked_batch_path)
            dest, ext = os.path.splitext(export_path)
            if os.path.isfile(linked_batch_path) and  os.path.isdir(src):
                try:
                    from subprocess import call
                    call(['cp', '-a', src, dest])
                    call(['cp', '-a', linked_batch_path, export_path])
                except:
                    self.progress.hide()
                    mbox = QtWidgets.QMessageBox()
                    mbox.setText('Error publishing flame clip %s:\nunable to copy flame batch.' % pb_info.get('flame_clip_name', ''))
                    mbox.setDetailedText('Path: ' + export_path)
                    mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                    # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                    btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                    btn_Continue.setText('Continue')
                    mbox.exec_()
                    if mbox.clickedButton() == btn_Continue:
                        return (pb_info, False)
                    else:
                        return (pb_info, True)
            else:
                self.log_debug('no linked .batch file found on filesystem')
                self.log_debug('saving current batch to: %s' % export_path)
                self.flame.batch.save_setup(str(export_path))
        else:
            self.log_debug('no linked .batch file')
            self.log_debug('saving current batch to: %s' % export_path)
            self.progress.set_progress(version_name, 'Saving current batch...')
            self.flame.batch.save_setup(str(export_path))

        '''
        # get published file type for Flame Batch or create a published file type on the fly

        flame_batch_type = self.prefs.get('templates', {}).get(task_entity_type, {}).get('flame_batch', {}).get('PublishedFileType', '')
        self.log_debug('PublishedFile type: %s, querying ShotGrid' % flame_batch_type)
        published_file_type = self.connector.sg.find_one('PublishedFileType', filters=[["code", "is", flame_batch_type]])
        self.log_debug('PublishedFile type: found: %s' % pformat(published_file_type))
        if not published_file_type:
            self.log_debug('creating PublishedFile type %s' % flame_render_type)
            try:
                published_file_type = self.connector.sg.create("PublishedFileType", {"code": flame_batch_type})
            except Exception as e:
                self.progress.hide()
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error creating published file type in ShotGrid')
                mbox.setDetailedText(pformat(e))
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)

            self.log_debug('created: %s' % pformat(published_file_type))

        # update published file data and create PublishedFile for flame batch

        self.log_debug('creating flame_batch published file in ShotGrid')

        published_file_data['published_file_type'] = published_file_type
        published_file_data['path'] =  {'relative_path': path_cache, 'local_storage': self.connector.sg_storage_root}
        published_file_data['path_cache'] = path_cache
        published_file_data['code'] = os.path.basename(path_cache)
        published_file_data['name'] = task_entity_name

        self.progress.set_progress(version_name, 'Registering batch...')

        try:
            published_file = self.connector.sg.create('PublishedFile', published_file_data)
        except Exception as e:
            self.progress.hide()
            mbox = QtWidgets.QMessageBox()
            mbox.setText('Error creating published file in ShotGrid')
            mbox.setDetailedText(pformat(e))
            mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
            # mbox.setStyleSheet('QLabel{min-width: 400px;}')
            btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
            btn_Continue.setText('Continue')
            mbox.exec_()
            if mbox.clickedButton() == btn_Continue:
                return (pb_info, False)
            else:
                return (pb_info, True)
        
        self.log_debug('created PublishedFile:\n%s' % pformat(published_file))
        self.log_debug('uploading thumbnail %s' % thumbnail_path)
        
        self.progress.set_progress(version_name, 'Uploading batch thumbnail...')

        try:
            self.connector.sg.upload_thumbnail('PublishedFile', published_file.get('id'), thumbnail_path)
        except:
            try:
                self.connector.sg.upload_thumbnail('PublishedFile', published_file.get('id'), thumbnail_path)
            except Exception as e:
                self.progress.hide()
                mbox = QtWidgets.QMessageBox()
                mbox.setText('Error uploading thumbnail to ShotGrid')
                mbox.setDetailedText(pformat(e))
                mbox.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                # mbox.setStyleSheet('QLabel{min-width: 400px;}')
                btn_Continue = mbox.button(QtWidgets.QMessageBox.Ok)
                btn_Continue.setText('Continue')
                mbox.exec_()
                if mbox.clickedButton() == btn_Continue:
                    return (pb_info, False)
                else:
                    return (pb_info, True)
        '''
        # clean-up preview and thumbnail files

        self.log_debug('cleaning up preview and thumbnail files')
        self.progress.set_progress(version_name, 'Cleaning up...')

        try:
            # os.remove(thumbnail_path)
            os.remove(preview_path)
        except:
            self.log_debug('cleaning up failed')
        
        self.log_debug('returning info:\n%s' % pformat(pb_info))

        self.progress.hide()

        return (pb_info, False)

    def publish_progress_dialog(self):
        from sgtk.platform.qt import QtCore, QtGui
        
        class Ui_Progress(object):
            def setupUi(self, Progress):
                Progress.setObjectName("Progress")
                Progress.resize(211, 50)
                Progress.setStyleSheet("#Progress {background-color: #181818;} #frame {background-color: rgb(0, 0, 0, 20); border: 1px solid rgb(255, 255, 255, 20); border-radius: 5px;}\n")
                self.horizontalLayout_2 = QtGui.QHBoxLayout(Progress)
                self.horizontalLayout_2.setSpacing(0)
                self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
                self.horizontalLayout_2.setObjectName("horizontalLayout_2")
                self.frame = QtGui.QFrame(Progress)
                self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
                self.frame.setFrameShadow(QtGui.QFrame.Raised)
                self.frame.setObjectName("frame")

                self.horizontalLayout = QtGui.QHBoxLayout(self.frame)
                self.horizontalLayout.setSpacing(4)
                self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
                self.horizontalLayout.setObjectName("horizontalLayout")
                self.label = QtGui.QLabel(self.frame)
                self.label.setMinimumSize(QtCore.QSize(40, 40))
                self.label.setMaximumSize(QtCore.QSize(40, 40))
                self.label.setAlignment(QtCore.Qt.AlignCenter)
                self.label.setStyleSheet("color: #989898; border: 2px solid #4679A4; border-radius: 20px;") 
                self.label.setText('[K]')
                # self.label.setPixmap(QtGui.QPixmap(":/tk_flame_basic/shotgun_logo_blue.png"))
                self.label.setScaledContents(True)
                self.label.setObjectName("label")
                self.horizontalLayout.addWidget(self.label)
                self.verticalLayout = QtGui.QVBoxLayout()
                self.verticalLayout.setObjectName("verticalLayout")

                self.progress_header = QtGui.QLabel(self.frame)
                self.progress_header.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
                self.progress_header.setObjectName("progress_header")
                self.progress_header.setStyleSheet("#progress_header {font-size: 10px; qproperty-alignment: \'AlignBottom | AlignLeft\'; font-weight: bold; font-family: Open Sans; font-style: Regular; color: #878787;}")

                self.verticalLayout.addWidget(self.progress_header)
                self.progress_message = QtGui.QLabel(self.frame)
                self.progress_message.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
                self.progress_message.setObjectName("progress_message")
                self.progress_message.setStyleSheet("#progress_message {font-size: 10px; qproperty-alignment: \'AlignTop | AlignLeft\'; font-family: Open Sans; font-style: Regular; color: #58595A;}")
                self.verticalLayout.addWidget(self.progress_message)
                self.horizontalLayout.addLayout(self.verticalLayout)
                self.horizontalLayout_2.addWidget(self.frame)

                self.retranslateUi(Progress)
                QtCore.QMetaObject.connectSlotsByName(Progress)

            def retranslateUi(self, Progress):
                Progress.setWindowTitle(QtGui.QApplication.translate("Progress", "Form", None, QtGui.QApplication.UnicodeUTF8))
                self.progress_header.setText(QtGui.QApplication.translate("Progress", "ShotGrid Integration", None, QtGui.QApplication.UnicodeUTF8))
                self.progress_message.setText(QtGui.QApplication.translate("Progress", "Updating config....", None, QtGui.QApplication.UnicodeUTF8))

        class Progress(QtGui.QWidget):
            """
            Overlay widget that reports toolkit bootstrap progress to the user.
            """

            PROGRESS_HEIGHT = 48
            PROGRESS_WIDTH = 280
            PROGRESS_PADDING = 48

            def __init__(self):
                """
                Constructor
                """
                # first, call the base class and let it do its thing.
                QtGui.QWidget.__init__(self)

                # now load in the UI that was created in the UI designer
                self.ui = Ui_Progress()
                self.ui.setupUi(self)

                # make it frameless and have it stay on top
                self.setWindowFlags(
                    QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint
                )

                if QtCore.__version_info__[0] < 6:
                    # place it in the lower left corner of the primary screen
                    primary_screen = QtGui.QApplication.desktop().primaryScreen()
                    rect_screen = QtGui.QApplication.desktop().availableGeometry(primary_screen)
                else:
                    primary_screen = QtGui.QGuiApplication.primaryScreen()
                    rect_screen = primary_screen.availableGeometry()

                self.setGeometry(
                    ( rect_screen.left() + rect_screen.right() ) // 2 - self.PROGRESS_WIDTH // 2, 
                    ( rect_screen.bottom() - rect_screen.top() ) // 2 - self.PROGRESS_PADDING,
                    self.PROGRESS_WIDTH,
                    self.PROGRESS_HEIGHT
                )

            def set_progress(self, header, msg):
                self.ui.progress_header.setText(header)
                self.ui.progress_message.setText(msg)
                QtGui.QApplication.processEvents()

        return Progress()

    def update_loader_list(self, entity):
        batch_name = self.flame.batch.name.get_value()
        add_list = self.prefs.get('additional menu ' + batch_name)
        add_list_ids = []
        entity_id = entity.get('id')
        for existing_entity in add_list:
            add_list_ids.append(existing_entity.get('id'))
        if entity_id in add_list_ids:
            for index, existing_entity in enumerate(add_list):
                if existing_entity.get('id') == entity_id:
                    add_list.pop(index)
        else:
            add_list.append(entity)
        self.prefs['additional menu ' + batch_name] = add_list

    def get_entities(self, user_only = True, filter_out=[]):
        start = time.time()
   
        if user_only:
            cached_tasks = self.connector.pipeline_data.get('project_tasks_for_person')
            if not isinstance(cached_tasks, list):
                # try to collect pipeline data in foreground
                self.connector.collect_pipeline_data()
                cached_tasks = self.connector.pipeline_data('project_tasks_for_person')
                if not isinstance(cached_tasks, list):
                    # give up
                    return {}
            if not cached_tasks:
                return {}
            else:
                cached_tasks_by_entity_id = {x.get('entity_id'):x for x in cached_tasks}
                entities = {'Shot': [], 'Asset': []}
                shots = self.connector.pipeline_data.get('all_shots_for_project')
                if not shots:
                    shots = []
                for shot in shots:
                    if shot.get('id') in cached_tasks_by_entity_id.keys():
                        entities['Shot'].append(shot)
                assets = self.connector.pipeline_data.get('all_assets_for_project')
                if not assets:
                    assets = []
                for asset in assets:
                    if asset.get('id') in cached_tasks_by_entity_id.keys():
                        entities['Asset'].append(asset)
                return entities
        else:
            shots = self.connector.pipeline_data.get('all_shots_for_project')
            if not isinstance(shots, list):
                self.connector.collect_pipeline_data()
                shots = self.connector.pipeline_data.get('all_shots_for_project')
                if not shots:
                    shots = []
            assets = self.connector.pipeline_data.get('all_assets_for_project')
            if not isinstance(assets, list):
                self.connector.collect_pipeline_data()
                assets = self.connector.pipeline_data.get('all_assets_for_project')
                if not assets:
                    assets = []
            return {'Shot': shots, 'Asset': assets}

    def build_flame_friendly_path(self, path):
        import glob
        import fnmatch

        file_names = os.listdir(os.path.dirname(path))
        if not file_names:
            return None
        frame_pattern = re.compile(r"^(.+?)([0-9#]+|[%]0\dd)$")
        root, ext = os.path.splitext(os.path.basename(path))
        match = re.search(frame_pattern, root)
        if not match:
            return None
        pattern = os.path.join("%s%s" % (re.sub(match.group(2), "*", root), ext))
        files = []
        for file_name in file_names:
            if fnmatch.fnmatch(file_name, pattern):
                files.append(os.path.join(os.path.dirname(path), file_name))
        if not files:
            return None
        file_roots = [os.path.splitext(f)[0] for f in files]
        frame_padding = len(re.search(frame_pattern, file_roots[0]).group(2))
        offset = len(match.group(1))

        # consitency check
        frames = []
        for f in file_roots:
            try:
                frame = int(os.path.basename(f)[offset:offset+frame_padding])
            except:
                continue
            frames.append(frame)
        if not frames:
            return None
        min_frame = min(frames)
        max_frame = max(frames)
        if ((max_frame + 1) - min_frame) != len(frames):
            # report what exactly are missing
            current_frame = min_frame
            for frame in frames:
                if not current_frame in frames:
                    # report logic to be placed here
                    pass
                current_frame += 1
            return None
        
        format_str = "[%%0%sd-%%0%sd]" % (
                frame_padding,
                frame_padding
            )
        
        frame_spec = format_str % (min_frame, max_frame)
        file_name = "%s%s%s" % (match.group(1), frame_spec, ext)

        return os.path.join(
                    os.path.dirname (path),
                    file_name
                    )

    def flip_assigned(self, *args, **kwargs):
        self.prefs['show_all'] = not self.prefs['show_all']
        self.rescan()

    def flip_assigned_for_entity(self, entity):
        entity_type = entity.get('type')
        entity_id = entity.get('id')
        entity_key = (entity_type, entity_id)
        if entity_id:
            self.prefs[entity_key]['show_all'] = not self.prefs[entity_key]['show_all']

    def fold_step_entity(self, entity):
        entity_type = entity.get('type')
        entity_id = entity.get('id')
        entity_key = (entity_type, entity_id)
        step_key = entity.get('key')
        self.prefs[entity_key][step_key]['isFolded'] = not self.prefs[entity_key][step_key]['isFolded']

    def fold_task_entity(self, entity):
        entity_type = entity.get('type')
        entity_id = entity.get('id')
        entity_key = (entity_type, entity_id)
        task_key = entity.get('key')
        self.prefs[entity_key][task_key]['isFolded'] = not self.prefs[entity_key][task_key]['isFolded']

    def page_fwd(self, *args, **kwargs):
        self.prefs['current_page'] += 1

    def page_bkw(self, *args, **kwargs):
        self.prefs['current_page'] = max(self.prefs['current_page'] - 1, 0)

    def create_export_preset(self, export_preset_path):
        import flame

        def find_files_with_all_path_patterns(directory, patterns):
            import os
            import fnmatch

            matches = []
            for root, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    if all(fnmatch.fnmatch(full_path, pattern) for pattern in patterns):
                        matches.append(full_path)
            return matches

        def find_version_in_file(file_path):
            import os
            import re
            version_pattern = re.compile(r'<preset version="(\d+)">')
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        match = version_pattern.search(line)
                        if match:
                            return match.group(1)
                return None
            except (IOError, OSError) as e:
                print(f"Error reading file {file_path}: {e}")
                return None

        def update_version_in_file(src_path, dest_path, new_version):
            import os
            import xml.etree.ElementTree as ET

            try:
                # Parse the source XML file
                tree = ET.parse(src_path)
                root = tree.getroot()

                if 'version' in root.attrib:
                    root.set('version', str(new_version))

                # Write the updated XML to the destination file
                tree.write(dest_path, encoding='utf-8', xml_declaration=True)

                # print(f"Updated version in file saved to {dest_path}")
                return dest_path
            except ET.ParseError as e:
                print(f"Error parsing XML file {src_path}: {e}")
                return None
            except (IOError, OSError) as e:
                print(f"Error processing file: {e}")
                return None

        try:
            flame_presets_location = flame.PyExporter.get_presets_base_dir(
                        flame.PyExporter.PresetVisibility.Autodesk
                    )
            
            matching_files = find_files_with_all_path_patterns(flame_presets_location, ['*OpenEXR*.xml', '*file*', '*sequence*'])
            new_version = find_version_in_file(matching_files[0])

            # print (f'new version: {new_version}')

            dest_preset_path = os.path.join(
                    '/var/tmp',
                    os.path.basename(export_preset_path)
                )
            
            if os.path.isfile(dest_preset_path):
                # print (f'removing {dest_preset_path}')
                os.remove(dest_preset_path)

            preset_path = update_version_in_file(
                export_preset_path,
                dest_preset_path,
                new_version
            )

            if preset_path:
                return preset_path
            else:
                return export_preset_path

        except:
            return export_preset_path

    def create_export_presets(self):

        preview_preset = '''<?xml version="1.0"?>
        <preset version="11">
        <type>movie</type>
        <comment>Shotgun movie preview</comment>
        <movie>
            <fileType>QuickTime</fileType>
            <namePattern>&lt;name&gt;</namePattern>
            <yuvHeadroom>False</yuvHeadroom>
            <yuvColourSpace>PCS_UNKNOWN</yuvColourSpace>
        </movie>
        <video>
            <fileType>QuickTime</fileType>
            <codec>33622016</codec>
            <codecProfile>
                <rootPath>/opt/Autodesk/mediaconverter/</rootPath>
                <targetVersion>2020.2</targetVersion>
                <pathSuffix>/profiles/.33622016/Baseline_RIM_12Mbits.cdxprof</pathSuffix>
            </codecProfile>
            <namePattern>&lt;name&gt;</namePattern>
            <overwriteWithVersions>False</overwriteWithVersions>
            <lutState>
                <Setup>
                    <Base>
                        <Version>18</Version>
                        <Note></Note>
                        <Expanded>False</Expanded>
                        <ScrollBar>0</ScrollBar>
                        <Frames>79</Frames>
                        <Current_Time>1</Current_Time>
                        <Input_DataType>4</Input_DataType>
                        <ClampMode>0</ClampMode>
                        <AdapDegrad>False</AdapDegrad>
                        <ReadOnly>False</ReadOnly>
                        <NoMediaHandling>1</NoMediaHandling>
                        <UsedAsTransition>False</UsedAsTransition>
                        <FrameBounds W="3200" H="1800" X="0" Y="0" SX="26.666666666666664" SY="15"/>
                    </Base>
                    <State>
                        <LogLinTargetPixelFormat>143</LogLinTargetPixelFormat>
                        <LogLinPropRefWhite>True</LogLinPropRefWhite>
                        <LogLinPropRefBlack>True</LogLinPropRefBlack>
                        <LogLinPropHighlight>True</LogLinPropHighlight>
                        <LogLinPropShadow>True</LogLinPropShadow>
                        <LogLinPropSoftclip>True</LogLinPropSoftclip>
                        <LogLinPropDispGamma>True</LogLinPropDispGamma>
                        <LogLinPropFilmGamma>True</LogLinPropFilmGamma>
                        <LogLinPropExposure>True</LogLinPropExposure>
                        <LogLinPropDefog>True</LogLinPropDefog>
                        <LogLinPropKneeLow>True</LogLinPropKneeLow>
                        <LogLinPropKneeHigh>True</LogLinPropKneeHigh>
                        <LogLinAdjustPropLuts>True</LogLinAdjustPropLuts>
                        <LogLinPropLowRoll>True</LogLinPropLowRoll>
                        <LogLinPropLowCon>True</LogLinPropLowCon>
                        <LogLinPropContrast>True</LogLinPropContrast>
                        <LogLinPropHighCon>True</LogLinPropHighCon>
                        <LogLinPropHighRoll>True</LogLinPropHighRoll>
                        <LogLinHasBeenActivated>True</LogLinHasBeenActivated>
                        <LutsBuilder>
                            <LutsBuilder LutFileVersion="3">
                                <ConversionType>0</ConversionType>
                                <GammaType>1</GammaType>
                                <BasicMode>6</BasicMode>
                                <AdjustMode>False</AdjustMode>
                                <RedLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </RedLut>
                                <GreenLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </GreenLut>
                                <BlueLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </BlueLut>
                                <ColorTransformBuilder>
                                    <ColorTransformBuilder CTBVersion="1.400000">
                                        <CTBCustom>False</CTBCustom>
                                        <CTBInvert>False</CTBInvert>
                                        <CTBSolo>False</CTBSolo>
                                        <CTBSelected>-1</CTBSelected>
                                        <CTBIsColourSpaceConversion>False</CTBIsColourSpaceConversion>
                                        <CTBSrcColourSpace></CTBSrcColourSpace>
                                        <CTBDstColourSpace>Unknown</CTBDstColourSpace>
                                        <CTBTaggedColourSpace>From Source</CTBTaggedColourSpace>
                                        <CTBViewTransformEnabled>True</CTBViewTransformEnabled>
                                        <CTBVTSrcCS>From Source</CTBVTSrcCS>
                                        <CTBVTViewCS>From Rules</CTBVTViewCS>
                                        <CTBVTDispCS>sRGB display</CTBVTDispCS>
                                        <CTBItems/>
                                    </ColorTransformBuilder>
                                </ColorTransformBuilder>
                            </LutsBuilder>
                        </LutsBuilder>
                    </State>
                </Setup>
            </lutState>
            <resize>
                <resizeType>fit</resizeType>
                <resizeFilter>lanczos</resizeFilter>
                <width>2048</width>
                <height>1200
                </height>
                <bitsPerChannel>8</bitsPerChannel>
                <numChannels>3</numChannels>
                <floatingPoint>False</floatingPoint>
                <bigEndian>False</bigEndian>
                <pixelRatio>1</pixelRatio>
                <scanFormat>P</scanFormat>
            </resize>
        </video>
        <audio>
            <fileType>QuickTime</fileType>
            <codec>4027060226</codec>
            <codecProfile>
                <rootPath>/opt/Autodesk/mediaconverter/</rootPath>
                <targetVersion>2020.2</targetVersion>
                <pathSuffix>/profiles/.4027060226/160 kbps.cdxprof</pathSuffix>
            </codecProfile>
            <namePattern>&lt;name&gt;</namePattern>
            <mixdown>To2</mixdown>
            <sampleRate>-1</sampleRate>
            <bitDepth>-1</bitDepth>
        </audio>
        </preset>'''

        thumbnail_preset = '''<?xml version="1.0" encoding="UTF-8"?>
        <preset version="11">
        <type>image</type>
        <comment>Shotgun thumbnail</comment>
        <video>
            <fileType>Jpeg</fileType>
            <codec>923688</codec>
            <codecProfile></codecProfile>
            <namePattern>&lt;name&gt;.</namePattern>
            <compressionQuality>100</compressionQuality>
            <transferCharacteristic>2</transferCharacteristic>
            <publishLinked>0</publishLinked>
            <lutState>
                <Setup>
                    <Base>
                        <Version>18</Version>
                        <Note></Note>
                        <Expanded>False</Expanded>
                        <ScrollBar>0</ScrollBar>
                        <Frames>79</Frames>
                        <Current_Time>1</Current_Time>
                        <Input_DataType>4</Input_DataType>
                        <ClampMode>0</ClampMode>
                        <AdapDegrad>False</AdapDegrad>
                        <ReadOnly>False</ReadOnly>
                        <NoMediaHandling>1</NoMediaHandling>
                        <UsedAsTransition>False</UsedAsTransition>
                        <FrameBounds W="3200" H="1800" X="0" Y="0" SX="26.666666666666664" SY="15"/>
                    </Base>
                    <State>
                        <LogLinTargetPixelFormat>143</LogLinTargetPixelFormat>
                        <LogLinPropRefWhite>True</LogLinPropRefWhite>
                        <LogLinPropRefBlack>True</LogLinPropRefBlack>
                        <LogLinPropHighlight>True</LogLinPropHighlight>
                        <LogLinPropShadow>True</LogLinPropShadow>
                        <LogLinPropSoftclip>True</LogLinPropSoftclip>
                        <LogLinPropDispGamma>True</LogLinPropDispGamma>
                        <LogLinPropFilmGamma>True</LogLinPropFilmGamma>
                        <LogLinPropExposure>True</LogLinPropExposure>
                        <LogLinPropDefog>True</LogLinPropDefog>
                        <LogLinPropKneeLow>True</LogLinPropKneeLow>
                        <LogLinPropKneeHigh>True</LogLinPropKneeHigh>
                        <LogLinAdjustPropLuts>True</LogLinAdjustPropLuts>
                        <LogLinPropLowRoll>True</LogLinPropLowRoll>
                        <LogLinPropLowCon>True</LogLinPropLowCon>
                        <LogLinPropContrast>True</LogLinPropContrast>
                        <LogLinPropHighCon>True</LogLinPropHighCon>
                        <LogLinPropHighRoll>True</LogLinPropHighRoll>
                        <LogLinHasBeenActivated>True</LogLinHasBeenActivated>
                        <LutsBuilder>
                            <LutsBuilder LutFileVersion="3">
                                <ConversionType>0</ConversionType>
                                <GammaType>1</GammaType>
                                <BasicMode>6</BasicMode>
                                <AdjustMode>False</AdjustMode>
                                <RedLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </RedLut>
                                <GreenLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </GreenLut>
                                <BlueLut>
                                    <Cineon Version="1">
                                        <ConversionType>0</ConversionType>
                                        <ReferenceWhite>0.669599</ReferenceWhite>
                                        <ReferenceBlack>0.092864</ReferenceBlack>
                                        <Highlight>1</Highlight>
                                        <Shadow>0</Shadow>
                                        <Softclip>0</Softclip>
                                        <FilmGamma>0.600000</FilmGamma>
                                        <GammaCorrection>0.450000</GammaCorrection>
                                        <Defog>0</Defog>
                                        <KneeLow>0</KneeLow>
                                        <KneeHigh>0</KneeHigh>
                                        <Exposure>0</Exposure>
                                        <LowRoll>0</LowRoll>
                                        <LowCon>0</LowCon>
                                        <Contrast>0</Contrast>
                                        <HighCon>0</HighCon>
                                        <HighRoll>0</HighRoll>
                                        <Encoding>9</Encoding>
                                        <Invert>0</Invert>
                                    </Cineon>
                                </BlueLut>
                                <ColorTransformBuilder>
                                    <ColorTransformBuilder CTBVersion="1.400000">
                                        <CTBCustom>False</CTBCustom>
                                        <CTBInvert>False</CTBInvert>
                                        <CTBSolo>False</CTBSolo>
                                        <CTBSelected>-1</CTBSelected>
                                        <CTBIsColourSpaceConversion>False</CTBIsColourSpaceConversion>
                                        <CTBSrcColourSpace></CTBSrcColourSpace>
                                        <CTBDstColourSpace>Unknown</CTBDstColourSpace>
                                        <CTBTaggedColourSpace>From Source</CTBTaggedColourSpace>
                                        <CTBViewTransformEnabled>True</CTBViewTransformEnabled>
                                        <CTBVTSrcCS>From Source</CTBVTSrcCS>
                                        <CTBVTViewCS>From Rules</CTBVTViewCS>
                                        <CTBVTDispCS>sRGB display</CTBVTDispCS>
                                        <CTBItems/>
                                    </ColorTransformBuilder>
                                </ColorTransformBuilder>
                            </LutsBuilder>
                        </LutsBuilder>
                    </State>
                </Setup>
            </lutState>
            <resize>
            <resizeType>fit</resizeType>
            <resizeFilter>lanczos</resizeFilter>
            <width>720</width>
            <height>400</height>
            <bitsPerChannel>8</bitsPerChannel>
            <numChannels>3</numChannels>
            <floatingPoint>0</floatingPoint>
            <bigEndian>1</bigEndian>
            <pixelRatio>1.000000</pixelRatio>
            <scanFormat>P</scanFormat>
            </resize>
            </video>
        <name>
        <framePadding>0</framePadding>
        <startFrame>1</startFrame>
        <useTimecode>1</useTimecode>
        </name>
        </preset>'''

        preview_preset_file_path = os.path.join(self.framework.prefs_folder, 'GeneratePreview.xml')
        if not os.path.isdir(os.path.dirname(preview_preset_file_path)):
            try:
                os.makedirs(os.path.dirname(preview_preset_file_path))
            except Exception as e:
                self.log('unable to create folder %s' % os.path.dirname(preview_preset_file_path))
                self.log(e)

        if not os.path.isfile(preview_preset_file_path):
            try:
                with open(preview_preset_file_path, 'w') as preview_preset_file:
                    preview_preset_file.write(preview_preset)
                    preview_preset_file.close()
            except Exception as e:
                self.log('unable to save preview preset to %s' % preview_preset_file_path)
                self.log(e)                

        thumbnail_preset_file_path = os.path.join(self.framework.prefs_folder, 'GenerateThumbnail.xml')
        if not os.path.isfile(thumbnail_preset_file_path):
            try:
                with open(thumbnail_preset_file_path, 'w') as thumbnail_preset_file:
                    thumbnail_preset_file.write(thumbnail_preset)
                    thumbnail_preset_file.close()
            except Exception as e:
                self.log('unable to save thumbnail preset to %s' % preview_preset_file_path)
                self.log(e)

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
    msg = 'flameMenuKITSU: Python exception %s in %s' % (value, exctype)
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
        if settings.get('debug', False):
            print ('[DEBUG %s] unloading apps:\n%s' % ('flameMenuKITSU', pformat(apps)))
        while len(apps):
            app = apps.pop()
            if settings.get('debug', False):
                print ('[DEBUG %s] unloading: %s' % ('flameMenuKITSU', app.name))
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
        apps.append(flameBatchBlessing(app_framework))
        apps.append(flameMenuNewBatch(app_framework, kitsuConnector))
        # apps.append(flameMenuBatchLoader(app_framework, kitsuConnector))
        apps.append(flameMenuPublisher(app_framework, kitsuConnector))
    except Exception as e:
        import traceback
        pprint(e)
        traceback.print_tb(e.__traceback__)

    app_framework.apps = apps
    if settings.get('debug', False):
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
    app_framework = flameAppFramework(app_name = settings['app_name'])
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
        order = len(menu[0].get('actions')) + 1
        version_string = settings['version']
        gazu_version = flameMenuProjectconnectApp.connector.get_gazu_version()
        zou_version = flameMenuProjectconnectApp.connector.get_api_version()
        if gazu_version:
            version_string += ', gazu: v' + str(gazu_version)
        if zou_version:
            version_string += ', zou: v' + str(zou_version)
        menu[0]['actions'].append({'name': version_string, 'isEnabled': False, 'order': order})

    if app_framework:
        menu_auto_refresh = app_framework.prefs_global.get('menu_auto_refresh', {})
        if menu_auto_refresh.get('main_menu', True):
            try:
                import flame
                flame.schedule_idle_event(rescan_hooks)
            except:
                pass
    
    if settings.get('debug', False):
        print('main menu update took %s' % (time.time() - start))

    return menu

get_main_menu_custom_ui_actions.__dict__["waitCursor"] = False

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
    except Exception as e:
        pprint(e)

    for app in apps:
        if app.__class__.__name__ == 'flameMenuNewBatch':
            if scope_desktop(selection) or (not selection):
                app_menu = app.build_menu()
                if app_menu:
                    menu.extend(app_menu)

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
    
    if settings.get('debug', False):
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

    if settings.get('debug', False):
        print('batch menu update took %s' % (time.time() - start))

    return menu
