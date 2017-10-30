Automapping
===========

This is a process that automatically creates mappings based on user
created mappings.

``ggrc.automapper``
-------------------

This defines the entry point ``register_automapping_listeners`` that
registers an event listener that fires on every user-created mapping.
Based on the neighborhood of the two mapped objects it fires the
appropriate rules and creates new mappings. The process is then repeated
for newly created mappings. This effectively traverses the local
relevant subgraph as defined by the rules.

``ggrc.automapper.rules``
-------------------------

This defines rules for mapping creation as data. This approach allows
for automatic sanity checking of the rules which can help prevent
unintended blowups of the auto-mappings. In order to keep automatic
mappings under control we impose a tree structure on the mappings graph
as defined by ``type_ordering``. Then we only allow auto-mappings
between ``A`` and ``C`` if the ``ABC`` path is a minor of the mappings
tree.

The rules themselves come in two varieties: regular and attribute-link.

Regular rules
-------------

Regular rules are defined by ``Rule(name, top, mid, bottom)`` where name
is the for-humans name of the rule and top/mid/bottom are types or sets
of types. Their names correspond to the positioning in the mapping tree.

Example:

``Rule("example rule", "Program", "Regulation", "Objective")``

The above rule will fire in two cases:

-  a program ``p`` is mapped to a regulation ``r`` and the user adds a
   mapping between ``r`` and an objective ``o``. In this case the rule
   implies mapping ``p`` to ``o``.
-  a regulation ``r`` is mapped to an objective ``o`` and the user adds
   a mapping between ``r`` and a program ``p``. In this case the rule
   implies mapping ``p`` to ``o``.

Any or all types can be replaced by sets of type. This generates rules
for the cross product of sets.

Attribute-link rules
--------------------

Attribute-link rules regard special mappings that are not a part of the
``relationships`` table. They are defined by specifying the attribute
that links to the relevant object in an ``Attr`` instance.

Example:

``Rule("example rule", Attr("directive"), "Section", "Objective")``

The above rule will only fire in on case. When an objective ``o`` is
mapped to a section ``s`` it will map ``o`` to directive ``d``
accessible through ``s``'s ``directive`` attribute.
