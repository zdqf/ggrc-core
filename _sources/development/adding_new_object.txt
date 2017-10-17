Adding a new Object
===================

Backend
-------

Create ``new_object.py`` in ``src/<module>/models/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

..  code-block:: python

    class NewObject(mixins..., db.Model):
      __tablename__ = 'new_objects'

      new_object_attr = deferred(db.Column(db.String), 'NewObject')

      # REST properties
      _publish_attrs = [
          'new_object_attr',
      ]

Add the NewObject to the ``all_models`` list in ``all_models.py``, or
register it using the ``register_model`` method if your adding it inside
a module.

Generate a migration file
~~~~~~~~~~~~~~~~~~~~~~~~~

..  code-block:: bash

    python src/ggrc/migrate.py <module> revision --autogenerate -m "Add NewObject"

Consider the generated migration file a template that you need to
manually update.

**Important:** Make sure both ``db_migrate`` and ``db_downgrade`` are
working correctly, both in a clean database and in a database with
existing data

Add new Object to appropriate services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. ``ggrc/cache/cache.py`` configure memcache
2. ``ggrc/services/__init__.py`` or use ``init_extra_services()`` to
   init REST APIs for NewObject
3. ``ggrc/views/__init__.py`` or use ``init_extra_views()`` to init
   object view page

Add permissions for NewObject
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the NewObject to appropriate roles in
``ggrc_basic_permissions/roles``

Frontend
--------

Create a CMS.Models.Cacheable object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

..  code-block:: javascript

    can.Model.Cacheable("CMS.Models.NewObject", {
      root_object : "new_object",
      root_collection : "new_objects",
      findOne : "GET /api/new_objects/{id}",
      update : "PUT /api/new_objects/{id}",
      destroy : "DELETE /api/new_objects/{id}",
      create : "POST /api/new_objects",
      mixins : ["ownable", "contactable"],
      is_custom_attributable: true,
      attributes : {
        context : "CMS.Models.Context.stub",
        modified_by : "CMS.Models.Person.stub",
        custom_attribute_values : "CMS.Models.CustomAttributeValue.stubs",
        start_date: "date",
        end_date: "date"
      },
      init : function() {
        this._super && this._super.apply(this, arguments);
        this.validateNonBlank("title");
      }
    }, {

    });

1. Add ``new_object`` to ``object_type_decision_tree`` in
   assets/javascripts/ggrc-base.js or extended it in your module (see
   below).
2. Add ``new_object`` to ``business_object.js``

   ``baseWidgetsByType`` is where you define the attributes shown in
   widgets ``extra_descriptor_options`` is where you define special
   parameters for some of the widgets ie. their content controller,
   icon, widget name etc. ``extra_content_controller_options`` is where
   you define parameters for the ``content_controller`` ie can view
   children, mapping, model, footer view etc.

3. Add ``new_object`` to ``mappings-ggrc.js``

   Add the object to the list of mappings:
   ``GGRC.Mappings("ggrc_core", {base:{}, NewObject: {...}}``.

Extending
~~~~~~~~~

Create a ModuleExtension object:

..  code-block:: javascript

    var ModuleExtension = {
      name: "module",
      object_type_decision_tree: function() {
        return {
          NewModel: CMS.Models.NewModel
        }
      },
      init_widgets: function() {

      },
      init_admin_widgets: function() {

      },
    }
    GGRC.extensions.push(ModuleExtension);

    // Add mappings:

    var mappings = {
      // your mappings
    }
    new GGRC.Mappings("ggrc_new_module", mappings);

Add NewObject to the LHN
~~~~~~~~~~~~~~~~~~~~~~~~

In :src:`ggrc/assets/mustache/dashboard/lhn.mustache` add the line:

..  code-block:: javascript

    {{{renderLive '/static/mustache/dashboard/lhn_search.mustache' type="NewObject" li_class="class"}}}

If you are inside a module, you have to create a hook:

..  code-block:: javascript

    {{{render_hooks 'LHN.Sections_new_object'}}}

And then init the hook inside your module:

..  code-block:: javascript

    GGRC.register_hook("LHN.Sections_new_object", GGRC.mustache_path + "/dashboard/lhn_new_object");

Create mustache files
---------------------

``new_object/modal_content.mustache`` is the only mandatory mustache
file that needs to be created. Creating all the other mustache files is
optional. If the mustache file is not found in ``new_object`` it will be
taken from ``base_objects``.
