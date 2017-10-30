Overview
========

This document is a reference for anyone interested in understanding how
GGRC is constructed. The goal for this document is to explain how
everything works in moderate detail with references to source code which
can be used to understand in exact detail how GGRC works.

Server Side
-----------

Overview
~~~~~~~~

The interface to the back-end is a REST API. This API is also referred
to as a “resource layer”.

Requests come into the REST API. These requests pass through various
filters which handle basic concerns such as
authentication/authorization/session management (ggrc.login, RBAC),
parsing request and formatting responses and others (e.g. query
generation).

Besides saving/creating/deleting/updating models the server-side REST API
also includes business logic and validation. The server-side is
stateless. Complex business logic is also duplicated within the client-side
portions of the application to make operations like validating inputs more
responsive.

Composing the server-side
~~~~~~~~~~~~~~~~~~~~~~~~~

All of the server-side functionality and behaviors are pulled together
in :src:`ggrc/app.py`. This is where all
infrastructure is initialized and loaded.

Resource Layer
~~~~~~~~~~~~~~

Overview
^^^^^^^^

The resource layer provides a uniform, external interface to the data
model. There isn’t much more to it than that.

The code that builds out the API (what endpoints exist and what HTTP
verbs are allowed on each) is in :src:`ggrc/services`.

See :ref:`api-docs` for more details.


General REST parameters
^^^^^^^^^^^^^^^^^^^^^^^

Every REST API request can take the following parameters:

-  ``__stubs_only`` - return only the ``id``, ``type``, ``href`` and
   ``context_id`` (A context is a Role-Based Access Control context;
   every program, audit or workflow has one) fields for each matched
   object
-  ``__fields`` - specify field names to return

Every REST request (except for search) must pass an
``'Accept':'application/json'`` header (in order to prevent XSS
attacks), or a 406 error will be returned.

**Example** - return the fields ``id``, ``title`` and ``description``
for two programs:

::

    GET /api/programs?id__in=2935,2806&__fields=id,title,description


REST Response Result Paging
^^^^^^^^^^^^^^^^^^^^^^^^^^^

20 records per request are returned by default. This is configurable up
to a max of 100 results per page.  See ``apply_paging`` in
:src:`ggrc/services/common.py`. Request
parameters:

*   ``__page_only`` - only returns paging information, but not resource
    information
*   page - defaults to 0 if ``__page_only`` was specified, and 1
    otherwise TBD

**Example** - return the first 20 programs:

::

    GET /api/programs?id__in=1,2,...&__page=1

Search
^^^^^^

⚠️ The /search API is being deprecated in favor of :ref:`advanced-query-api`

The server-side logic that handles search is in :src:`ggrc/services/search.py`.

Parameters:

-  ``q`` - the query; mandatory, but can be the empty string
-  ``contact_id`` - assume that id as the initiating user. Not a great
   name for it -- it's the user to whom items should be related. For
   MyWork, this will be the current user, but on another user X's
   profile page, it's user X.
-  ``__permission_type`` - default "read" TBD
-  ``__permission_model`` - ? TBD
-  ``group_by_type`` - ? TBD
-  ``counts_only`` - return only the counts of the items found. Used to
   show the counts in the LHN tree.
-  ``types`` - restrict search to the specified types, e.g.
   types=Program,Audit
-  ``extra_params`` - unsure. When retrieving counts for workflow states
   (active, inactive, draft), this parameter is
   "Workflow_All=Workflow,Workflow_Active=Workflow,Workflow_Draft=Workflow,Workflow_Inactive=Workflow".
   This may be a special case to handle the extra counts in the LHN
   Workflows section. TBD.
-  ``extra_columns`` - same as above, this parameter is:
   "Workflow:status=Active;Workflow_Active:status=Active;Workflow_Inactive:status=Inactive;Workflow_Draft:status=Draft"
   TBD

Routing
^^^^^^^

Routes to types of resources (audits, programs, etc.), as well as the
base routes for the REST API (``/api/`` and ``/search/``) are determined
with the help of a small amount of metadata specified in :src:`ggrc/services/__init__.py`.

Routes are specified in other places within the Python code via the
@app.route annotation.

Presentation Layer
~~~~~~~~~~~~~~~~~~

Templates
^^^^^^^^^

Templates are HAML files which define the structural HTML which is
basically the scaffolding around which the functionality and features of
GGRC are built. Templates don’t define JavaScript logic, client-side
models, or “how to render an Audit”. Those types of view logic are
defined in ``.js`` and ``.mustache`` files.

Views
^^^^^

Enough HTML to bootstrap JavaScript. Views are defined in
``src/<module>/views``. They are Python methods
which are mapped to routes (relative URLs).

These views serve two functions:

1. They provide a way to augment the underlying resource paradigm with
   addition of non-RESTful application logic (Ex. ``/admin/reindex``).
2. They provide entry points into the application from which templates
   can be rendered, which bootstraps the JavaScript which constructs the
   majority of the actual UI.

Encoding and Formatting
^^^^^^^^^^^^^^^^^^^^^^^

Responses returned from the server-side are generated by rendering
Python objects into an encoding and format that is understood by the
client-side. The standard format is JSON.

The Python code that marshals/unmarshals models to/from JSON is in :src:`ggrc/builder`.

Import
^^^^^^

Data Import is a special case in which requests (as opposed to
responses) have to be parsed in order to build models which can then be
saved to the underlying database. This is basically just the exact
reverse of formatting python objects as JSON, with the caveat that the
import format is CSV instead of JSON.

Export
^^^^^^

Export is similar to default response formatting in the sense that
Python models are rendered in a standard format (usually JSON). But in
the case of export, the format is CSV.

Request Interpretation and Response Construction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The code that interprets requests (to figure out what action to take on
the server-side) and constructs responses (applying rendering logic to
models) lives in :src:`ggrc/services`. :src:`ggrc/services/common.py`
is particularly important. It implements ModelView & Resource (which extends ModelView).


Infrastructure and Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Persistence
^^^^^^^^^^^

CloudSQL MySQL 2nd Gen 5.6 is the underlying database used when running on App Engine.

MySQL 5.6 is used when running locally (for development).


Caching
^^^^^^^

Memcache is used.

A manifest of the types of objects that should be cached exists in
:src:`ggrc/cache/cache.py`. Types not listed in this file will not be cached
by Memcache.

All of the logic related to cache management is in :src:`ggrc/cache`.


Authentication
^^^^^^^^^^^^^^

The Python code that handles authentication is in :src:`ggrc/login`.
There are currently two handlers, one to enable integration with
Google Accounts and another to enable a developer to log in as a specific
user by modifying a config file or request header.


Data Import
^^^^^^^^^^^

Several types of data can be imported into GGRC by uploading CSV files.
The data in those files needs to be converted into python models and
validated before being persisted. The code that handles all of this is
in :src:`ggrc/converters`. All of the base
classes which define common handling logic, as well as code specific to
one or more types of model is in that folder.


Extensions
^^^^^^^^^^

Core code which enables the extension mechanism is in :src:`ggrc/extensions.py`.

Core code which bootstraps the core GGRC extensions (such as Workflow
and GDrive integration) is in :src:`ggrc/ext/__init__.py`.


Notifications
^^^^^^^^^^^^^

Code relevant to sending notifications (e.g. email) is in :src:`ggrc/notifications`.


Cron
^^^^

Cron jobs are available through App Engine's scheduled tasks mechanism.
This facility is configured via :src:`cron.yaml`.


Ad-Hoc Scheduled Tasks in Task Queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generating assessments, Rebuilding full-text index, updating revisions


Runtime Configurations
~~~~~~~~~~~~~~~~~~~~~~

GGRC runs in different environments in two dimensions. The first
dimension is App Engine vs. local. The second dimension is
development/testing/production.

Which settings are loaded is determined by the environment variable
``GGRC_SETTINGS_MODULE``. This variable is expected to contain a set of
strings separated by spaces. It should be pretty clear as to how these
strings correlate to Python files/modules after looking at the value of
that variable.


Appengine Runtime vs. Local Runtime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GGRC uses MySQL when running locally. There are other configurations
like logging level and authorization which can be configured.

GGRC always uses Google Accounts for authentication when running in App
Engine. This is handled by :src:`ggrc/login/appengine.py`. When
running locally, however, different authentication logic is substituted
via :src:`ggrc/login/noop.py`. Within
this file a developer can hard-code authentication email address and
name. There is also logic to allow a developer to pass their email
address (allowing them to log in as a specific user) in through a
request header (``X-ggrc-user``) which can be manipulated with one of a
few Chrome browser plugins. This makes it efficient for a developer to
switch among user accounts to test functionality.

Please take a minute to look at :src:`ggrc/settings/app_engine.py` and
:src:`ggrc/settings/default.py` for more information on settings that
can be configured for running in either App Engine or local environments.


Development/Testing/Production Runtime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This dimension of runtime configuration allows setting of database
credentials, query and application logging and other configurations.

Settings typical for a development environment are in
:src:`ggrc/settings/development.py`.

Settings typical for a testing environment are in
:src:`ggrc/settings/testing.py`.


Testing
-------

GGRC testing consists of 4 components:


Manual tests
~~~~~~~~~~~~

Several day's worth of tests defined in spreadsheets and executed by the
QA team.  These are the primary source of regression stories
and bug-finding.


Automated Browser Tests
~~~~~~~~~~~~~~~~~~~~~~~

Implemented using WebDriver for Python and executed either locally or on
the CI server.


Python Unit/Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are currently defined in :src:`ggrc/tests`.
