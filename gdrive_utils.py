# Copyright 2018 Ravi Sojitra. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
import shutil

from pathlib import Path
from subprocess import call


def install_pydrive():
    """ See https://colab.research.google.com/notebooks/io.ipynb. """
    call(['pip', 'install', '-U', '-q', 'PyDrive'])


def get_gdrive():
    """ Installs pydrive and returns an authenticated GoogleDrive object. """
    install_pydrive()

    from google.colab import auth  # Will throw error if not run from a Colab.
    from oauth2client.client import GoogleCredentials
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive

    # Authenticate and create the PyDrive client.
    auth.authenticate_user()
    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials.get_application_default()
    gdrive = GoogleDrive(gauth)

    return gdrive


def ls_gdrive(gdrive, gdrive_directory_id=None):
    """ Lists content in a Google Drive directory. """
    gnarly_string = "'{}' in parents and trashed=false"

    if gdrive_directory_id is None:
        gdrive_directory_id = 'root'

    listfile_arg = {'q': gnarly_string.format(gdrive_directory_id)}
    gdrive_files = gdrive.ListFile(listfile_arg)

    title_to_id_dict = dict()

    for gdrive_file in gdrive_files.GetList():
        key = gdrive_file['title']
        value = gdrive_file['id']

        title_to_id_dict[key] = value

    return title_to_id_dict


def get_gdrive_id(gdrive, gdrive_fpath, gdrive_parent_directory_id=None):
    """ Finds the ID of a file. """
    fpath_parts = Path(gdrive_fpath).parts

    if fpath_parts[0] == os.sep:
        fpath_parts = fpath_parts[1:]
        gdrive_parent_directory_id = 'root'

    elif gdrive_parent_directory_id is None:
        gdrive_parent_directory_id = 'root'

    current_ls_dict = ls_gdrive(gdrive, gdrive_parent_directory_id)

    if len(fpath_parts) == 1:
        return current_ls_dict[fpath_parts[0]]

    else:
        assert type(fpath_parts) == tuple
        assert len(fpath_parts) > 1

        for part in fpath_parts[:-1]:
            gdrive_parent_directory_id = current_ls_dict[part]
            current_ls_dict = ls_gdrive(gdrive, gdrive_parent_directory_id)

        last_part = fpath_parts[-1]

        return current_ls_dict[last_part]


def push_to_gdrive(gdrive, fpath_to_upload,
                   gdrive_absolute_save_directory=None,
                   gdrive_absolute_save_directory_id=None):
    """ Uploads content to Google Drive from Google Colaboratory. """
    if gdrive_absolute_save_directory is not None:
        assert gdrive_absolute_save_directory_id is None

        args = (gdrive, gdrive_absolute_save_directory)
        gdrive_absolute_save_directory_id = get_gdrive_id(*args)

    else:
        assert gdrive_absolute_save_directory_id is not None

    createfile_arg = {'parents': [{'id': gdrive_absolute_save_directory_id}]}
    gdrive_file = gdrive.CreateFile(createfile_arg)
    gdrive_file.SetContentFile(fpath_to_upload)
    gdrive_file['title'] = os.path.basename(fpath_to_upload)
    gdrive_file.Upload()

    # print(gdrive_file['id'])
    # print(gdrive_file['title'])
    # print(gdrive_file['parents'])

    return gdrive_file


def push_to_tdrive(gdrive, fpath_to_upload,
                   tdrive_chooser, tdrive_path_chooser):
    """ Uploads content to Google Team Drive from Google Colaboratory. """
    tdrive_string = '{}'

    if tdrive_path_chooser is None:
        tdrive_path_chooser = tdrive_chooser

    createfile_arg = {
      'parents': [{
            'kind': 'drive#fileLink',
            'teamDriveId': tdrive_string.format(tdrive_chooser),
            'id': tdrive_string.format(tdrive_path_chooser)
        }]
    }

    tdrive_file = gdrive.CreateFile(createfile_arg)
    tdrive_file.SetContentFile(fpath_to_upload)
    tdrive_file['title'] = os.path.basename(fpath_to_upload)
    tdrive_file.Upload(param={'supportsTeamDrives': True})

    return tdrive_file


def pull_from_gdrive(gdrive, absolute_gdrive_path=None,
                     colaboratory_save_directory=None,
                     absolute_gdrive_path_id=None):
    """ Downloads content from Google Colaboratory to Google Drive. """
    if absolute_gdrive_path is not None:
        assert absolute_gdrive_path_id is None
        absolute_gdrive_path_id = get_gdrive_id(gdrive, absolute_gdrive_path)

    assert absolute_gdrive_path_id is not None

    gdrive_file = gdrive.CreateFile({'id': absolute_gdrive_path_id})
    gdrive_file.GetContentFile(gdrive_file['title'])

    if colaboratory_save_directory is not None:
        shutil.move(gdrive_file['title'], colaboratory_save_directory)

    return gdrive_file
