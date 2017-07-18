# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Manage "static" assets

The actual list of stylesheets and javascripts to compile is in
`assets/assets.yaml`.

When developing, you can use `webassets` to automatically recompile changed
assets by starting the `webassets` command-line utility:

..
  cd src/ggrc
  webassets -m ggrc.assets watch

Currently, SASS is used to build CSS assets, and it has its own
monitor utility, which can be invoked thusly:

..
  cd /
  webpack --watch --watch-poll
"""

from . import settings

# Initialize webassets to handle the asset pipeline
import imp
import os
import webassets
import webassets.updater
import yaml

from webassets.filter.jst import JSTemplateFilter

environment = webassets.Environment()
manifest = os.path.join(settings.BASE_DIR, 'ggrc', 'assets', 'assets.manifest')
environment.manifest = 'file:' + manifest
environment.versions = 'hash:32'

# `asset-debug` mode doesn't merge bundles into a single file
environment.debug = settings.DEBUG_ASSETS

# `settings-debug` mode doesn't finger-print files (no cache-busting)
if settings.DEBUG:
  environment.url_expire = False

environment.updater = webassets.updater.TimestampUpdater()

# Read asset listing from YAML file

assets_yamls = [os.path.join(settings.MODULE_DIR, 'assets', 'assets.yaml')]

module_load_paths = [settings.MODULE_DIR, ]
for extension in settings.EXTENSIONS:
  file, pathname, description = imp.find_module(extension)
  module_load_paths.append(pathname)
  p = os.path.join(pathname, 'assets', 'assets.yaml')
  if os.path.exists(p):
    assets_yamls.append(p)
asset_paths = {}
for assets_yaml_path in assets_yamls:
  with open(assets_yaml_path) as f:
    for k, v in yaml.load(f.read()).items():
      asset_paths.setdefault(k, []).extend(v or [])

if not settings.AUTOBUILD_ASSETS:
  environment.auto_build = False

environment.url = '/static'
environment.directory = os.path.join(settings.MODULE_DIR, 'static')

environment.load_path = [settings.THIRD_PARTY_DIR, settings.BOWER_DIR]

_per_module_load_suffixes = [
    'assets/javascripts',
    'assets/mustache',
    'assets/vendor/javascripts',
    'assets/vendor/bootstrap-sass/vendor/assets/javascripts',
    'assets/vendor/remoteipart/vendor/assets/javascripts',
    'assets/stylesheets',
    'assets/vendor/stylesheets',
    'assets/js_specs'
]

for module_load_base in module_load_paths:
  module_load_paths = [os.path.join(module_load_base, load_suffix)
                       for load_suffix in _per_module_load_suffixes]
  environment.load_path.extend(module_load_paths)


def path_without_assets_base(path):
  steps = path.split(os.path.sep)
  if len(steps) > 3 and steps[1] == 'assets' and steps[2] == 'mustache':
    return os.path.join(*steps[3:])
  return path


class MustacheFilter(JSTemplateFilter):
  """
  Populate GGRC.Templates from list of mustache templates
    * mostly copies webassets.filter.jst.JST
  """

  name = 'mustache'
  options = {
      'namespace': 'GGRC.Templates'
  }

  def process_templates(self, out, hunks, **kwargs):
    namespace = self.namespace or 'GGRC.Templates'

    out.write("{namespace} = {namespace} || {{}};\n".format(
        '{}', namespace=namespace))

    for name, hunk in self.iter_templates_with_base(hunks):
      name = path_without_assets_base(name)
      contents = hunk.data().replace('\n', '\\n').replace("'", r"\'")
      out.write("{namespace}['{name}']".format(
          namespace=namespace, name=name))
      out.write("= '{template}';\n".format(template=contents))

version_suffix = '-%(version)s'
if settings.DEBUG:
  version_suffix = ''

environment.register("dashboard-js", webassets.Bundle(
    *asset_paths['dashboard-js-files'],
    # filters='jsmin',
    output='dashboard' + version_suffix + '.js'))

environment.register("app-init-js", webassets.Bundle(
    *asset_paths['app-init-files'],
    # filters='jsmin',
    output='app-init' + version_suffix + '.js'))

environment.register("dashboard-js-templates", webassets.Bundle(
    *asset_paths['dashboard-js-template-files'],
    filters=MustacheFilter,
    output='dashboard-templates' + version_suffix + '.js',
    # Always keep `debug` False here, since raw mustache is not valid JS
    debug=False))

environment.register("dashboard-css", webassets.Bundle(
    *asset_paths['dashboard-css-files'],
    output='dashboard' + version_suffix + '.css'))

if settings.ENABLE_JASMINE:
  environment.register("dashboard-js-specs", webassets.Bundle(
      *asset_paths['dashboard-js-spec-files'],
      output='dashboard' + version_suffix + '-specs.js'))

  environment.register("dashboard-js-spec-helpers", webassets.Bundle(
      *asset_paths['dashboard-js-spec-helpers'],
      output='dashboard' + version_suffix + '-spec-helpers.js'))
