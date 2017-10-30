=====================
Deployment and Update
=====================

TODO (Please add any questions or clarification requests here):

1. Add a summary of deployment-specific values (e.g., filename of
   deployment settings file, filename of ``ggrc/settings/*`` file)
   and/or use some convention to denote these as variable in this
   document

2. Add a CHANGELOG’ or version/upgrade matrix in steps 2 and 3 (and 5,
   for settings modules) to make it clear when the step must be repeated
   or more closely examined (or which values/APIs have changed)

3. Add note about how to verify backup in Cloud Storage

4. Update ``deploy_appengine`` to (optionally) handle migrations --
   environment variables and database settings are too opaque and
   error-prone. Could also have it check and warn about valid settings
   in settings files, maybe? At least several “verify this value” steps
   for database and App Engine instance name.

5. Add steps to set up a new Cloud SQL instance.


0. Complete initial development environment setup
=================================================

This step should only need to be done once per deployment machine.
Intall the requirements and clone the repo following instructions
in the main `README <https://github.com/google/ggrc-core/blob/dev/README.md>`_.

1. Create/Update deployment settings
====================================

By convention, these files will be located in
``extras/deploy/<something>``, where ``<something>`` is the name of
the deployment instance. These files are not part of the repository,
as they are deployment-specific and contain private data (API keys,
for instance).

Create or update the deployment settings
(e.g. ``extras/deploy/test-instance``). If this is an upgrade, this
file will likely be complete, except for a recent change to the set or
expected values of settings.

To create deployment settings for a new project, please do (assuming
you are in the project root directory):

..  code-block:: bash

    PROJECT="test-instance"
    mkdir -pv "./extras/deploy/$PROJECT"
    cp "./extras/deploy/override-template.sh" "./extras/deploy/$PROJECT/override.sh"
    cp "./extras/deploy/settings-template.sh" "./extras/deploy/$PROJECT/settings.sh"

Settings from ``settings.sh``
-----------------------------

+-----------------------------+---------------------------------------------------------------------------+
| Setting                     | Description                                                               |
+=============================+===========================================================================+
| APPENGINE_INSTANCE          | The “Application Identifier” you see at `Cloud console`_                  |
+-----------------------------+---------------------------------------------------------------------------+
| SETTINGS_MODULE             | List of Python modules importable from ``src`` or ``src/ggrc/settings``   |
|                             | that provide different parameters for the app                             |
+-----------------------------+---------------------------------------------------------------------------+
| DATABASE_URI                | The connection string for the database. Should be constructed using       |
|                             | DB_NAME, DB_INSTANCE_CONNECTION_NAME.                                     |
+-----------------------------+---------------------------------------------------------------------------+
| DB_NAME                     | The name of the application's database                                    |
+-----------------------------+---------------------------------------------------------------------------+
| DB_INSTANCE_CONNECTION_NAME | Connection string for your database instance                              |
+-----------------------------+---------------------------------------------------------------------------+
| GAPI_KEY                    | The “Browser Key” from Step 2                                             |
+-----------------------------+---------------------------------------------------------------------------+
| GAPI_CLIENT_ID              | The “OAuth Client ID” from Step 2                                         |
+-----------------------------+---------------------------------------------------------------------------+
| GAPI_CLIENT_SECRET          | The “OAuth Client Secret” from Step 2                                     |
+-----------------------------+---------------------------------------------------------------------------+
| GAPI_ADMIN_GROUP            | The group which is used in messages like "Contact your admin at           |
|                             | ``<group_email>``"                                                        |
+-----------------------------+---------------------------------------------------------------------------+
| APPENGINE_EMAIL             | The email address to use as the “From” address in outgoing email          |
|                             | notifications                                                             |
+-----------------------------+---------------------------------------------------------------------------+
| INSTANCE_CLASS              | The instance class that should be used on appengine                       |
+-----------------------------+---------------------------------------------------------------------------+
| MAX_INSTANCES               | The maximum number of instances to be used on appengine                   |
+-----------------------------+---------------------------------------------------------------------------+
| SECRET_KEY                  | Random string that is used as a seed for Flask session ids                |
+-----------------------------+---------------------------------------------------------------------------+
| GOOGLE_ANALYTICS_ID         | Project ID for Google Analytics                                           |
+-----------------------------+---------------------------------------------------------------------------+
| GOOGLE_ANALYTICS_DOMAIN     | Project domain for Google Analytics                                       |
+-----------------------------+---------------------------------------------------------------------------+
| BOOTSTRAP_ADMIN_USERS       | Space-separated emails of users granted superuser access (usually the     |
|                             | people who deploy and manage the project)                                 |
+-----------------------------+---------------------------------------------------------------------------+
| MIGRATOR                    | **UNUSED** Name and email of the user that is used as current user during |
|                             | migrations                                                                |
+-----------------------------+---------------------------------------------------------------------------+
| RISK_ASSESSMENT_URL         | Link to Risk Assessment application                                       |
+-----------------------------+---------------------------------------------------------------------------+
| CUSTOM_URL_ROOT             | Equal to the URL where the app is supposed to be deployed too; used to    |
|                             | generate links to internal objects in email notifications                 |
+-----------------------------+---------------------------------------------------------------------------+
| ABOUT_URL                   | Link to the About document                                                |
+-----------------------------+---------------------------------------------------------------------------+
| ABOUT_TEXT                  | Text that is shown on the login page                                      |
+-----------------------------+---------------------------------------------------------------------------+
| EXTERNAL_HELP_URL           | Link to user documentation on an external service                         |
+-----------------------------+---------------------------------------------------------------------------+
| EXTERNAL_IMPORT_HELP_URL    | Link to import-specific user documentation on an external service         |
+-----------------------------+---------------------------------------------------------------------------+
| GGRC_Q_INTEGRATION_URL      | Link to GGRCQ instance synced with this instance                          |
+-----------------------------+---------------------------------------------------------------------------+
| DASHBOARD_INTEGRATION       | Link to Dashboards that use data from this instance                       |
+-----------------------------+---------------------------------------------------------------------------+
| ALLOWED_QUERYAPI_APP_IDS    | List of Appengine application ids that are allowed to access this         |
|                             | instance's APIs                                                           |
+-----------------------------+---------------------------------------------------------------------------+
| AUTHORIZED_DOMAIN           | Users from this domain automatically get Creator role                     |
+-----------------------------+---------------------------------------------------------------------------+
| SCALING                     | ``app.yaml:*scaling`` section                                             |
+-----------------------------+---------------------------------------------------------------------------+
| STATIC_SERVING              | Section of ``app.yaml:handlers`` to serve static files as static (doesn't |
|                             | work properly on some instances and not enabled by default)               |
+-----------------------------+---------------------------------------------------------------------------+


Settings from ``override.sh``
-----------------------------

+-------------------+-------------------------------------------------------------------------------------+
| Setting           | Description                                                                         |
+===================+=====================================================================================+
| GGRC_DATABASE_URI | The connection string for the database (using connection by IP, as it is used by    |
|                   | the migrations runner that is launched from your host during deployment). Should be |
|                   | constructed using DB_USER, DB_PASSWORN, DB_IP                                       |
+-------------------+-------------------------------------------------------------------------------------+
| DB_USER           | Username of the migrator in the DB                                                  |
+-------------------+-------------------------------------------------------------------------------------+
| DB_PASSWORD       | Password of the migrator in the DB                                                  |
+-------------------+-------------------------------------------------------------------------------------+
| DB_IP             | IP address of the SQL instance                                                      |
+-------------------+-------------------------------------------------------------------------------------+


There may also be a customized ``src/ggrc/settings/<something>.py``
file, for example, ``ggrc/settings/app_engine_test_instance.py`` (This
file should also not be included in the repository, though examples
can be found at :src:`ggrc/settings`). This file can contain
additional configuration variables, including:

+---------------------------+---------------------------------------------------------------------------------+
| Setting                   | Description                                                                     |
+===========================+=================================================================================+
| COMPANY                   | This is the company name shown in the “Copyright” footer at                     |
|                           | the bottom of each page                                                         |
+---------------------------+---------------------------------------------------------------------------------+
| COMPANY_LOGO              | If specified, this is an image to be displayed in the top-left corner           |
|                           | of each page.                                                                   |
+---------------------------+---------------------------------------------------------------------------------+
| COMPANY_LOGO_TEXT         | If COMPANY_LOGO is not set, this (text) value is used instead of an image in    |
|                           | the top-left corner of each page.                                               |
+---------------------------+---------------------------------------------------------------------------------+
| SQLALCHEMY_RECORD_QUERIES | This setting causes queries to be reported in the App Engine logs. Possible     |
|                           | options are: 'count' - only the number of queries is logged, 'slow' - only slow |
|                           | queries are logged, 'all' - all queries are logged.  This is useful for         |
|                           | debugging purposes.                                                             |
+---------------------------+---------------------------------------------------------------------------------+
| CALENDAR_MECHANISM        | If True, Workflow includes Google Calendar integration                          |
+---------------------------+---------------------------------------------------------------------------------+

Please note: settings files must use ASCII quotation marks, not the
stylized marks used in rich text documents. E.g., they should be
straight, like " or ', not “” or ‘’.

2. Configure Google APIs
========================

Note: This step only needs to be done once, but required APIs might
change, so during upgrades, verify rather than add the APIs and keys.

1.  Go to the `Cloud Console`_ and select the Project being updated.

2.  Click “APIs & services” in the left-hand column. Find each of the
    following APIs and enable it:

    * Drive API
    * Google Picker API

    Your screen should now look like the following:

    .. figure:: /_static/res/deployment1.png
       :alt: Enable APIs

3.  Select “Credentials” in the left-hand column, and click “Create
    credentials” → “OAuth client ID”.

    * Select “Web Application”
    * Add “https://<your-project>.appspot.com” to the box labeled
      “Authorized JavaScript origins”
    * Add “https://<your-project>.appspot.com/authorize” to the box
      labeled “Authorized redirect URI”

      Your screen should look like the following:

      .. figure:: /_static/res/deployment2.png
         :alt: Create Client ID

    * Click “Create Client ID”. You'll see a popup with new Client ID
      and Client Secret that should be stored into your
      ``settings.sh`` ``GAPI_CLIENT_ID`` and ``GAPI_CLIENT_SECRET``
      respectively.

      **Please note!**

      The “Client Secret” should never be revealed to untrusted
      parties. If other parties have the “Client secret” value, they
      may be able to impersonate the GGRC application.

4. Click “Create credentials” → “API key”. You'll see a popup with a
   new API key that you should store into ``settings.sh``
   ``GAPI_KEY``.

Now we’re done setting up the Google APIs and ready for the deployment.


3. Backup the database via Google Cloud Console
===============================================

In the left-hand column of the `Cloud Console`_, select “Cloud SQL”
and select the database instance to be used.

In the top line, click the “Export...” button, select a Cloud Storage
path, and click “OK”. The Cloud Storage Path should look something like::

    gs://****-backups/****-yyyymmdd.sql

4. Complete the deployment
==========================

Go back to your local environment and do the following:

..  code-block:: bash

    ./bin/deploy test-instance

``test-instance`` is the name of the directory that contains your
settings.

The script creates a container, installs all the dependencies inside,
runs the migrations and deploys the application.

To deploy a specific version, run:

.. code-block:: bash

   ./bin/deploy test-instance 0.10.35-Raspberry  # a tag or a branch name

.. _Cloud Console: https://console.cloud.google.com/
