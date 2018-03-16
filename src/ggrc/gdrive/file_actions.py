# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""File action utitlities for GDrive module"""

from StringIO import StringIO
from logging import getLogger
from os import path

from apiclient import discovery
from apiclient import http
from apiclient.errors import HttpError
from flask import json
from oauth2client.client import HttpAccessTokenRefreshError

from werkzeug.exceptions import (
    BadRequest, NotFound, InternalServerError, Unauthorized
)

from ggrc.converters.import_helper import read_csv_file
from ggrc.gdrive import get_http_auth
from ggrc.gdrive import handle_token_error

API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

ALLOWED_FILENAME_CHARS = "_ ()-'"

# pylint: disable=invalid-name
logger = getLogger(__name__)


def hande_http_error(ex):
  """Helper for http error handling"""
  message = json.loads(ex.content).get("error").get("message")
  if ex.resp.status == 404:
    raise NotFound(message)
  if ex.resp.status == 401:
    raise Unauthorized(message)
  if ex.resp.status == 400:
    logger.warning(message)
    raise BadRequest("The file is not in a recognized format. " +
                     "Please import a Google sheet or a file in .csv format.")
  raise InternalServerError(message)


def create_gdrive_file(csv_string, filename):
  """Post text/csv data to a gdrive file"""
  http_auth = get_http_auth()
  try:
    drive_service = discovery.build(API_SERVICE_NAME, API_VERSION,
                                    http=http_auth)
    # make export to sheets
    file_metadata = {
        'name': filename,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    media = http.MediaInMemoryUpload(csv_string,
                                     mimetype='text/csv',
                                     resumable=True)
    result = drive_service.files().create(body=file_metadata,
                                          media_body=media,
                                          fields='id, name, parents').execute()
    return result
  except HttpAccessTokenRefreshError:
    handle_token_error()
  except HttpError as ex:
    hande_http_error(ex)


def get_gdrive_file(file_data):
  """Get text/csv data from gdrive file"""
  csv_data, _, _ = get_gdrive_file_data(file_data)
  return csv_data


def get_gdrive_file_data(file_data):
  """Get text/csv data from gdrive file"""
  http_auth = get_http_auth()
  try:
    drive_service = discovery.build(API_SERVICE_NAME, API_VERSION,
                                    http=http_auth)
    # check file type
    file_meta = drive_service.files().get(fileId=file_data['id']).execute()
    if file_meta.get('mimeType') == 'text/csv':
      file_data = drive_service.files().get_media(
          fileId=file_data['id']).execute()
    else:
      file_data = drive_service.files().export_media(
          fileId=file_data['id'], mimeType='text/csv').execute()
    csv_data = read_csv_file(StringIO(file_data))
  except AttributeError:
    # when file_data has no splitlines() method
    raise BadRequest('Wrong file format.')
  except HttpAccessTokenRefreshError:
    handle_token_error('Try to reload /import page')
  except HttpError as ex:
    hande_http_error(ex)
  except Exception as ex:
    logger.error(ex.message)
    raise InternalServerError('Import failed due to internal server error.')
  return csv_data, file_data, file_meta.get('name')


def copy_file_request(drive_service, file_id, body):
  """Send copy request to gdrive"""
  response = drive_service.files().copy(
      fileId=file_id,
      body=body,
      fields='webViewLink,name'
  ).execute()
  return response


def rename_file_request(drive_service, file_id, body):
  """Send rename request to gdrive"""
  return drive_service.files().update(
      fileId=file_id,
      body=body,
      fields='webViewLink,name'
  ).execute()


def process_gdrive_file(folder_id, file_id, postfix, separator,
                        is_uploaded=False):
  """Process gdrive file to new folder with renaming"""
  http_auth = get_http_auth()
  try:
    drive_service = discovery.build(
        API_SERVICE_NAME, API_VERSION, http=http_auth)
    file_meta = drive_service.files().get(fileId=file_id).execute()
    new_file_name = generate_file_name(file_meta['name'], postfix, separator)
    if is_uploaded:
      #  if file was uploaded from a local folder, FE put it into
      #  a gdrive folder, we just need to rename file.
      response = rename_file_request(drive_service, file_id,
                                     body={'name': new_file_name})
    else:
      body = _build_request_body(folder_id, new_file_name)
      response = copy_file_request(drive_service, file_id, body)
    return response
  except HttpAccessTokenRefreshError:
    handle_token_error()
  except HttpError as ex:
    hande_http_error(ex)
  except Exception as ex:
    logger.error(ex.message)
    raise InternalServerError('Processing of the file failed due to'
                              ' internal server error.')
  return response


def _build_request_body(folder_id, new_file_name):
  """Helper for generate request body"""
  body = {'name': new_file_name}
  if folder_id:
    body['parents'] = [folder_id]
  return body


def generate_file_name(original_name, postfix, separator):
  """Helper for sanitize filename"""
  original_name, extension = path.splitext(original_name)
  # remove an old postfix
  original_name = original_name.split(separator)[0]
  new_name = ''.join([original_name, postfix]).strip('_')
  # sanitize file name
  new_name = ''.join([char if char.isalnum() or char in ALLOWED_FILENAME_CHARS
                      else '-' for char in new_name]
                     )
  return new_name + extension
