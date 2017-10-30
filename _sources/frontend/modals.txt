Modals
======

``modal-form.js``:
------------------

-  Where the basic low level code for modals exists
-  ModalForm subclasses Form, and it's cloned from Bootstrap for
   historical reasons. Some of the code may not be used any more.
-  Can generate flash messages that aren't obscured by the backdrop

``modal-ajax.js``:
------------------

-  Spawns modals; named that way for historical reasons (Rails)
-  A big click handler - looking at the ``data-toggle`` attribute to
   figure out which modal to open: ``data-toggle=modal-ajax``
-  ``GGRC.register_global_hook`` instantiates modals based on links that
   have that attribute
-  The biggest one is form - all the edit object modals
-  We apply modals controller in this file as well
-  We are handling modal:success on modal-ajax.js. It's used to navigate
   to a new URL here.
-  Dirty checks - legacy code, can possibly be removed. ``data-dirty``
   stuff in .mustache marks elements that need reload, but there are
   only a few left any more
-  Adding a new type of modal - create a new handler
-  `modal show <https://github.com/reciprocity/ggrc-core/blob/1e370e487c4377d7e1162dd881954cc26cffe5a9/src/ggrc/assets/javascripts/bootstrap/modal-ajax.js#L355-L423>`_:
   handles stacking, positioning and prevents double submit and escape
-  `line
   451 <https://github.com/reciprocity/ggrc-core/blob/1e370e487c4377d7e1162dd881954cc26cffe5a9/src/ggrc/assets/javascripts/bootstrap/modal-ajax.js#L451>`_
   extends the Bootstrap model
-  ``GGRC.register_global_hook`` can be used to add a special modal for
   a module
-  if you click Delete, a new modal is displayed, `lines
   119-151 <https://github.com/reciprocity/ggrc-core/blob/1e370e487c4377d7e1162dd881954cc26cffe5a9/src/ggrc/assets/javascripts/bootstrap/modal-ajax.js#L119-L151>`_

Each modal can have its own controller that handles actions performed by
the modals

``modals_controller.js``:
-------------------------

-  shows the spinner
-  establishes two-way data binding with the form fields; you want to
   find the state where things stop changing
-  ``data-also-set`` - TBD
-  'dfd' = abbreviation for deferred; we need the promise
-  ``wysiwyg_html`` extension - we need it to fire triggers when the
   textarea is updates because we can't read the iframe, it's not in the
   same domain

-  init()
-  fetch_all fetches the data and template
-  fetch_data a bit complex because we could be TBD
-  ``_transient`` property - added to the object instance while the object
   is open, but removed from the modal once the modal closes
-  run form_preload on the modal (if it exists)
-  apply object params - uses the data-object-params from the link that
   gets set on the modal. Example: when you create a request for an
   audit, a hidden field is the audit id. That's how you communicate any
   information, by adding it to the link that spawns the modal.
-  apply_object_params after all the deferreds - you can pass in
   arbitrary information into data-param
-  data-object-params gets added to the modal controller as the options
   object as well
-  calls serialize_form
-  triggers preload

-  serialize_form():
-  gets every element and then calls set_value_for_element()

-  autocomplete
-  extended jQuery UI plugin applied to every input that has data-lookup
   defined on it
-  ``autocomplete_select`` is the callback called when the autocomplete
   value is selected

-  set_value():
-  keeping TBD
-  "it's getting a bit unwieldy, the setvalue function is 100 lines"

Naming conventions in the forms:
--------------------------------

-  name of the input maps to the value of the instance. Most commonly
   ``<input name='url', value='{{url}}' />``
-  if name is name='contact.email' value="{{contact.email}}" - special
   cases for null in data-lookup onkeyup so that it clears the field

'Deferred' modal elements
-------------------------

``mark_for_deletion``/``mark_for_addition`` in ``cacheable.js``
adds/removes items into ``_pending_joins``. These pending joins are then
handled in ``resolve_deferred_bindings``. Removes are easy - it just
destroys the mapping. The "add" case is a bit more complex than the
"remove" case, as we must check we aren't re-mapping something which is
already mapped.

``ggrc_modal_connector`` Component used for mapping audits inside
modals. Double layer of indirection in this case because context is not
yet available when we are creating a new audit. When autocomplete
selects a person the app is using ``this.scope.changes`` to handle the
double deferred. Otherwise we just ``mark_for_addition`` (adding
responses). ``data-object-source`` used for picker additions.
``.ui-autocomplete-input`` we listen on this for when a new object is
created in the mapping modal. That object is created even if we cancel
the modal.

.. _mapping-and-global-search:

Mapping and global search modals:
---------------------------------

Mapping modal allow us search objects use :ref:`advanced-search` and
map them to context one.

Architecture of modals that contain ``Advanced Search`` functionality:
.. figure:: /_static/res/mapping-advanced-search.png
