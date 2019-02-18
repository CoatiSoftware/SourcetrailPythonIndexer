# -*- mode: python -*-

import glob
import jedi
import parso


block_cipher = None


def get_file_list(root_path, package_path, extensions):
    files = []
    for directory_info in os.walk(os.path.join(root_path, package_path)):
        directory_path = directory_info[0]
        rel_path = os.path.relpath(directory_path, root_path)
        for extension in extensions:
            for file in glob.glob(os.path.join(directory_path, extension)):
                files.append((file, rel_path))
    return files


def get_binaries():
    binaries = []
    site_packages_path = os.path.dirname(os.path.dirname(os.path.abspath(jedi.__file__)))
    print(site_packages_path)
    binaries.extend(get_file_list(site_packages_path, 'jedi', ['*.py']))
    binaries.extend(get_file_list(site_packages_path, 'parso', ['*.py', '*.txt']))
    return binaries


a = Analysis(['run.py'],
             pathex=['C:\\sourcetrail\\language_packages\\SourcetrailPythonIndexer\\SourcetrailPythonIndexer'],
             binaries=[],
             datas=get_binaries(),
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='SourcetrailPythonIndexer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='SourcetrailPythonIndexer')
