# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""ggrc.login

Provides basic login and session management using Flask-Login with various
backends
"""

import json
import re
from functools import wraps
from werkzeug.exceptions import Forbidden

import flask_login
from flask import g
from flask import request
from flask import redirect
from ggrc.extensions import get_extension_module_for
from ggrc.rbac import SystemWideRoles


def get_login_module():
  return get_extension_module_for('LOGIN_MANAGER', False)


def user_loader(user_id):
  from ggrc.utils.user_generator import find_user_by_id
  return find_user_by_id(user_id)


def init_app(app):
  """Initialize Flask_Login LoginManager with our app"""
  login_module = get_login_module()
  if not login_module:
    return

  login_manager = flask_login.LoginManager()
  login_manager.init_app(app)
  # login_manager.session_protection = 'strong'

  # pylint: disable=unused-variable
  @app.login_manager.unauthorized_handler
  def unauthorized():
    """Called when the user tries to access an endpoint guarded with
       login_required but they are not authorized.

       Endpoints like /dashboard, /program/1, etc. redirect the user to the
       /login page.

       Endpoints like /api /query, /import, etc. resolve with 401 UNAUTHORIZED
       and a simple json error object.
    """
    if (re.match(r'^(\/api|\/query|\/search)', request.path) or
       request.headers.get('X-Requested-By') == 'GGRC'):
      return json.dumps({'error': 'unauthorized'}), 401
    return redirect(flask_login.login_url('/login', request.url))

  app.route('/login')(login_module.login)
  app.route('/logout')(login_module.logout)

  app.login_manager.user_loader(user_loader)
  if hasattr(login_module, 'before_request'):
    app.before_request(login_module.before_request)
  if hasattr(login_module, 'request_loader'):
    app.login_manager.request_loader(login_module.request_loader)
  # app.context_processor(login_module.session_context)


def get_current_user():
  if hasattr(g, '_current_user'):
    return getattr(g, '_current_user')
  if get_login_module():
    return flask_login.current_user
  else:
    return None


def get_current_user_id():
  user = get_current_user()
  if user is not None and not user.is_anonymous():
    return user.id
  else:
    return None


def login_required(func):
  if get_login_module():
    return flask_login.login_required(func)
  else:
    return func


def admin_required(func):
  """Adming required decorator

    Raises Forbidden if the current user is not an admin"""
  @wraps(func)
  def admin_check(*args, **kwargs):
    """Helper function that performs the admin check"""
    user = get_current_user()
    role = getattr(user, 'system_wide_role', None)
    if role not in SystemWideRoles.admins:
      raise Forbidden()
    return func(*args, **kwargs)
  return admin_check


def is_creator():
  """Check if the current user has global role Creator."""
  current_user = get_current_user()
  return (hasattr(current_user, 'system_wide_role') and
          current_user.system_wide_role == SystemWideRoles.CREATOR)


def is_external_app_user():
  """Checks if the current user is an external application.

  Account for external application is defined in settings. External application
  requests require special processing and validations.
  """
  user = get_current_user()
  if not user or user.is_anonymous():
    return False

  from ggrc.utils.user_generator import is_external_app_user_email
  return is_external_app_user_email(user.email)
