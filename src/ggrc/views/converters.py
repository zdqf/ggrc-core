# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Main view functions for import and export pages.

This module handles all view related function to import and export pages
including the import/export api endponts.
"""

from logging import getLogger
from StringIO import StringIO
from datetime import datetime

from apiclient.errors import HttpError
from google.appengine.ext import deferred

from flask import current_app
from flask import request
from flask import json
from flask import render_template
from flask import g
from werkzeug.exceptions import (
    BadRequest, InternalServerError, Unauthorized, Forbidden, NotFound
)

from ggrc import db
from ggrc.gdrive import file_actions as fa
from ggrc.app import app
from ggrc.converters.base import Converter
from ggrc.converters.import_helper import generate_csv_string, \
    count_objects, read_csv_file, get_export_filename
from ggrc.models import import_export, person
from ggrc.query.exceptions import BadQueryException
from ggrc.query.builder import QueryHelper
from ggrc.login import login_required, get_current_user
from ggrc.utils import benchmark


# pylint: disable=invalid-name
logger = getLogger(__name__)


def check_required_headers(required_headers):
  """Check required headers to the current request"""
  errors = []
  for header, valid_values in required_headers.items():
    if header not in request.headers:
      errors.append("Missing required header '{}'".format(header))
    elif request.headers[header] not in valid_values:
      errors.append("Invalid header value for '{}'".format(header))

  if errors:
    raise BadRequest("\n".join(errors))


def parse_export_request():
  """ Check if request contains all required fields """
  required_headers = {
      "X-Requested-By": ["GGRC"],
      "Content-Type": ["application/json"],
      "X-export-view": ["blocks", "grid"],
  }
  check_required_headers(required_headers)
  return request.json


def export_file(export_to, filename, csv_string=None):
  """Export file to csv file or gdrive file"""
  if export_to == "gdrive":
    gfile = fa.create_gdrive_file(csv_string, filename)
    headers = [('Content-Type', 'application/json'), ]
    return current_app.make_response((json.dumps(gfile), 200, headers))
  if export_to == "csv":
    headers = [
        ("Content-Type", "text/csv"),
        ("Content-Disposition",
         "attachment; filename='{}'".format(filename)),
    ]
    return current_app.make_response((csv_string, 200, headers))
  raise BadRequest("Bad params")


def handle_export_request():
  """Export request handler"""
  # pylint: disable=too-many-locals
  try:
    with benchmark("handle export request data"):
      data = parse_export_request()
      objects = data.get("objects")
      export_to = data.get("export_to")
      current_time = data.get("current_time")
    with benchmark("Generate CSV string"):
      csv_string, object_names = make_export(objects)
    with benchmark("Make response."):
      filename = "{}_{}.csv".format(object_names, current_time)
      return export_file(export_to, filename, csv_string)
  except BadQueryException as exception:
    raise BadRequest(exception.message)
  except Unauthorized as ex:
    raise Unauthorized("{} Try to reload /export page".format(ex.message))
  except HttpError as e:
    message = json.loads(e.content).get("error").get("message")
    if e.resp.code == 401:
      raise Unauthorized("{} Try to reload /export page".format(message))
    raise InternalServerError(message)
  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Export failed: %s", e.message)
    raise InternalServerError("Export failed due to internal server error.")


def make_export(objects):
  """Make export"""
  query_helper = QueryHelper(objects)
  ids_by_type = query_helper.get_ids()
  converter = Converter(ids_by_type=ids_by_type)
  csv_data = converter.to_array()
  object_names = "_".join(converter.get_object_names())
  return generate_csv_string(csv_data), object_names


def check_import_file():
  """Check if imported file format and type is valid"""
  if "file" not in request.files or not request.files["file"]:
    raise BadRequest("Missing csv file")
  csv_file = request.files["file"]
  if not csv_file.filename.lower().endswith(".csv"):
    raise BadRequest("Invalid file type.")
  return csv_file


def parse_import_request():
  """ Check if request contains all required fields """
  required_headers = {
      "X-Requested-By": ["GGRC"],
      "X-test-only": ["true", "false"],
  }
  check_required_headers(required_headers)
  try:
    file_data = request.json
    dry_run = request.headers["X-test-only"] == "true"
    return dry_run, file_data
  except:  # pylint: disable=bare-except
    raise BadRequest("Export failed due incorrect request data.")


def handle_import_request():
  """Import request handler"""
  dry_run, file_data = parse_import_request()
  csv_data = fa.get_gdrive_file(file_data)
  return make_response(make_import(csv_data, dry_run))


def make_response(data):
  """Make response"""
  response_json = json.dumps(data)
  headers = [("Content-Type", "application/json")]
  return current_app.make_response((response_json, 200, headers))


def make_import(csv_data, dry_run):
  """Make import"""
  try:
    converter = Converter(dry_run=dry_run, csv_data=csv_data)
    converter.import_csv()
    return converter.get_info()
  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Import failed: %s", e.message)
    raise BadRequest("Import failed due to server error: %s" % e.message)


def run_export(objects, ie_id, user_id):
  """Run export"""
  with app.app_context():
    try:
      user = person.Person.query.get(user_id)
      setattr(g, '_current_user', user)
      ie = import_export.get(ie_id, "Export")
      content, _ = make_export(objects)
      db.session.refresh(ie)
      if ie.status == "Stopped":
        return
      ie.status = "Finished"
      ie.content = content
      db.session.commit()
    except Exception as e:  # pylint: disable=broad-except
      logger.exception("Export failed: %s", e.message)
      try:
        ie.status = "Failed"
        ie.end_date = datetime.now()
        db.session.commit()
      except Exception:  # pylint: disable=broad-except
        pass


def run_import_phases(ie_id, user_id):  # noqa: ignore=C901
  """Execute import phases"""
  with app.app_context():
    try:
      user = person.Person.query.get(user_id)
      setattr(g, '_current_user', user)
      ie_job = import_export.get(ie_id, "Import")
      csv_data = read_csv_file(StringIO(ie_job.content))

      if ie_job.status == "Analysis":
        info = make_import(csv_data, True)
        db.session.refresh(ie_job)
        if ie_job.status == "Stopped":
          return
        ie_job.results = json.dumps(info)
        for block_info in info:
          if block_info["block_errors"] or block_info["row_errors"]:
            ie_job.status = "Analysis Failed"
            db.session.commit()
            return
        for block_info in info:
          if block_info["block_warnings"] or block_info["row_warnings"]:
            ie_job.status = "Blocked"
            db.session.commit()
            return
        ie_job.status = "In Progress"
        db.session.commit()

      if ie_job.status == "In Progress":
        info = make_import(csv_data, False)
        ie_job.results = json.dumps(info)
        for block_info in info:
          if block_info["block_errors"] or block_info["row_errors"]:
            ie_job.status = "Failed"
            db.session.commit()
            return
        ie_job.status = "Finished"
        db.session.commit()
    except Exception as e:  # pylint: disable=broad-except
      logger.exception("Import failed: %s", e.message)
      try:
        ie_job.status = \
            "Analysis Failed" if ie_job.status == "Analysis" else "Failed"
        ie_job.end_date = datetime.now()
        db.session.commit()
      except Exception:  # pylint: disable=broad-except
        pass


def init_converter_views():
  """Initialize views for import and export."""

  # pylint: disable=unused-variable
  # The view function trigger a false unused-variable.
  @app.route("/_service/export_csv", methods=["POST"])
  @login_required
  def handle_export_csv():
    """Calls export handler"""
    with benchmark("handle export request"):
      return handle_export_request()

  @app.route("/_service/import_csv", methods=["POST"])
  @login_required
  def handle_import_csv():
    """Calls import handler"""
    with benchmark("handle import request"):
      return handle_import_request()

  @app.route("/import")
  @login_required
  def import_view():
    """Get import view"""
    return render_template("import_export/import.haml")

  @app.route("/export")
  @login_required
  def export_view():
    """Get export view"""
    return render_template("import_export/export.haml")


def check_import_export_headers():
  """Check headers"""
  required_headers = {
      "X-Requested-By": ["GGRC"],
  }
  check_required_headers(required_headers)


def make_import_export_response(data):
  """Make response"""
  response_json = json.dumps(data)
  headers = [("Content-Type", "application/json")]
  return current_app.make_response((response_json, 200, headers))


def handle_start(ie_job, user_id):
  """Handle import start command"""
  if ie_job.status == "Not Started":
    ie_job.status = "Analysis"
  elif ie_job.status in ("Analysis", "Blocked"):
    ie_job.status = "In Progress"
  else:
    raise BadRequest("Wrong status")
  try:
    db.session.commit()
    deferred.defer(run_import_phases, ie_job.id, user_id)
    return make_import_export_response(ie_job.log_json())
  except Exception as e:
    logger.exception("Import failed: %s", e.message)
    raise BadRequest("Import failed")


def handle_import_put(**kwargs):
  """Handle import put"""
  command = kwargs.get("command2")
  ie_id = kwargs.get("id2")
  user = get_current_user()
  if user.system_wide_role == 'No Access':
    raise Forbidden()
  if not ie_id or not command or command not in ("start", "stop"):
    raise BadRequest("Import failed due incorrect request data")
  try:
    ie_job = import_export.get(ie_id, "Import")
  except (Forbidden, NotFound):
    raise
  except Exception as e:
    logger.exception("Import failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Import failed due incorrect request data")
  if command == 'start':
    return handle_start(ie_job, user.id)
  elif command == "stop":
    return handle_import_stop(**kwargs)
  raise BadRequest("Bad params")


def handle_import_get(**kwargs):
  """Handle import get"""
  return handle_get(kwargs.get("id2"), kwargs.get("command2"), "Import")


def handle_get(id2, command, job_type):
  """Handle simple get and collection get"""
  check_import_export_headers()
  if command:
    if command != "download":
      BadRequest("Unknown command")
    return handle_file_download(id2, job_type)
  try:
    if id2:
      res = import_export.get(id2, job_type).log_json()
    else:
      ids = request.args.get("id__in")
      res = import_export.get_jobs(job_type, ids.split(",") if ids else None)
  except (Forbidden, NotFound):
    raise
  except Exception as e:
    logger.exception("%s failed due incorrect request data: %s",
                     job_type, e.message)
    raise BadRequest("%s failed due incorrect request data" % job_type)

  return make_import_export_response(res)


def handle_import_post(**kwargs):
  """ Handle import post """
  check_import_export_headers()
  file_meta = request.json
  csv_data, csv_content, filename = fa.get_gdrive_file_data(file_meta)
  try:
    counts = count_objects(csv_data)
    ie = import_export.create_import_export_entry(
        content=csv_content,
        gdrive_metadata=file_meta,
        title=filename)
    return make_import_export_response({"objects": counts,
                                        "import_export": ie.log_json()})
  except Unauthorized:
    raise
  except Exception as e:
    logger.exception("Import failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Import failed due incorrect request data")


def handle_file_download(id2, job_type):
  """  Download file  """
  try:
    export_to = request.args.get("export_to")
    ie = import_export.get(id2, job_type)
    return export_file(export_to, ie.title, ie.content.encode("utf-8"))
  except (Forbidden, NotFound, Unauthorized):
    raise
  except Exception as e:
    logger.exception("Download failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Download failed due incorrect request data")


def handle_export_put(**kwargs):
  """Handle export put"""
  command = kwargs.get("command2")
  ie_id = kwargs.get("id2")
  if not ie_id or not command or command != "stop":
    raise BadRequest("Export failed due incorrect request data")
  return handle_export_stop(**kwargs)


def handle_export_get(**kwargs):
  """Handle export get"""
  return handle_get(kwargs.get("id2"), kwargs.get("command2"), "Export")


def handle_export_post(**kwargs):
  """Handle export post"""
  check_import_export_headers()
  objects = request.json.get("objects")
  current_time = request.json.get("current_time")
  user = get_current_user()
  if user.system_wide_role == 'No Access':
    raise Forbidden()
  if not objects or not current_time:
    raise BadRequest("Export failed due incorrect request data")
  try:
    filename = get_export_filename(objects, current_time)
    ie = import_export.create_import_export_entry(
        job_type="Export",
        status="In Progress",
        title=filename)
    deferred.defer(run_export, objects, ie.id, user.id)
    return make_import_export_response(ie.log_json())
  except Exception as e:
    logger.exception("Export failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Export failed due incorrect request data")


def handle_import_delete(**kwargs):
  """Delete import entry"""
  return handle_delete(kwargs.get("id2"), "Import")


def handle_export_delete(**kwargs):
  """Delete export entry"""
  return handle_delete(kwargs.get("id2"), "Export")


def handle_delete(id2, job_type):
  """ Delete import_export entry """
  check_import_export_headers()
  try:
    ie = import_export.get(id2, job_type)
    db.session.delete(ie)
    db.session.commit()
    return make_import_export_response("OK")
  except (Forbidden, NotFound):
    raise
  except Exception as e:
    logger.exception("%s failed due incorrect request data: %s",
                     job_type, e.message)
    raise BadRequest("%s failed due incorrect request data" % job_type)


def handle_import_stop(**kwargs):
  """Handle import stop"""
  try:
    ie_job = import_export.get(kwargs.get("id2"), "Import")
    if ie_job.status in ("Analysis", "Blocked"):
      ie_job.status = "Stopped"
      db.session.commit()
      return make_import_export_response(ie_job.log_json())
  except Forbidden:
    raise
  except Exception as e:
    logger.exception("Import stop failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Import stop failed due incorrect request data")
  raise BadRequest("Wrong status")


def handle_export_stop(**kwargs):
  """Handle export stop"""
  try:
    ie_job = import_export.get(kwargs.get("id2"), "Export")
    if ie_job.status == "In Progress":
      ie_job.status = "Stopped"
      db.session.commit()
      return make_import_export_response(ie_job.log_json())
  except Forbidden:
    raise
  except Exception as e:
    logger.exception("Export stop failed due incorrect request data: %s",
                     e.message)
    raise BadRequest("Export stop failed due incorrect request data")
  raise BadRequest("Wrong status")
