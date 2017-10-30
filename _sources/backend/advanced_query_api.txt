.. _advanced-query-api:

Advanced Query API
==================

Quick overview of the Query API behavior.

API endpoint is ``/query`` and in the future it should replace the
current ``/search``. Due to expected bigger queries it listens for
POST requests.

Payload contains an array of queries:

..  code:: python

    request = [
      {...}, # query 1
      {...}, # query 2
      {...}, # query 3
      ...
    ]

Response is an array of objects containing results of the
corresponding query:

..  code:: python

    result = [
      {...}, # response to query 1
      {...}, # response to query 2
      {...}, # response to query 3
      ...
    ]

Query Structure
---------------

In this section we will assume that the request has the following
structure with a single query and all results will be for it.

..  code:: python

    request = [ query ]

All queries have a query type which can be: values (default), count,
ids.  If query type is not specified the values type is be used.

-  values: Returns a list of serialized matched items.
-  count: Returns only the number of matched items.
-  ids: Returns only the ids of matched items.

Basic Query
-----------

To get any results from the query, we need to add a filter with an
expression. An empty expression will match all objects of a certain
type:

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
    }

Result:

..  code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <some number>,
            "count": <equal to total>,
            "values": [<list of objects>],
        }
    }]

Filtered Query
--------------

values
~~~~~~

The default query type is "values", so

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
    }

is same as

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
        "type": "values",
    }

Result:

..  code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <some number>,
            "count": <equal to total>,
            "values": [<list of objects>],
        }
    }]

ids
~~~

For "ids" query type the result object will contain the ids instead of
values:

.. code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
        "type": "ids",
    }

result:

.. code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <some number>,
            "count": <equal to total>,
            "ids": [1, 4, <other ids>],
        }
    }]


count
~~~~~

For "count" query type the result object will not contain the values:

.. code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
        "type": "count",
    }

result:

.. code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <some number>,
            "count": <equal to total>,
        }
    }]

Paginated Query
---------------

To apply paging, "limit" argument should be provided:

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
        "limit": [0, 10],
    }

Same as Python slices, left boundary is inclusive, right boundary is
exclusive.

Result:

..  code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <total count of matched entries>,
            "count": <count of entries returned>,
            "values": [<objects from 0 to 10>],
        }
    }]

Notes:

- if you request items from 50 to 100 and ``total`` is less than 100,
  the response will contain fewer than ``100 - 50`` items;
- if you provide negative indices or if the right boundary is less or
  equal to the left boundary, an error will be returned.

Ordered Queries
---------------

To apply ordering, "order_by" argument should be provided:

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {}},
        "order_by": [{"name": "<field name>", "desc": <bool, optional>}],
    }

Result:

..  code:: python

    result = [{
        "<object name>": {
	    "object_name": "<object name>",
            "total": <some number>,
            "count": <equal to total>,
            "values": [<ordered objects>],
        }
    }]

Notes:

- the value provided in "order_by" is transformed to SQL ``ORDER BY``
  retaining SQL ordering semantics: ``"order_by": [{"name": "title"},
  {"name": "id", "desc": True}]`` → ``ORDER BY title ASC, id DESC``.

Querying multiple types with a single query object
--------------------------------------------------

**Is not supported yet.**

.. _filter-expressions:

Filter Expressions
------------------

The filter expression is a parsed AST with a user's input for a search
field. Each node must contain ``"op": {"name": "<operator name>"}``,
and the set of operands differ from one operator to another.

The types of operators supported:

- field operators,
- logical operators,
- object operators.

Field operators
~~~~~~~~~~~~~~~

- ``=`` equal,
- ``!=`` not equal,
- ``~`` contains,
- ``!~`` does not contain,
- ``<`` is less than,
- ``<=`` is less than or equal to,
- ``>`` is greater than,
- ``>=`` is greater or equal to,
- ``is empty`` is not defined or is filled with an empty value.

Each of the operators accept the same operands: ``"left": "<field
name"`` and ``"right": "<value>"``.

The field name in ``"left"`` should preferably contain the
user-visible field label, like "Code" instead of "slug" or "Effective
Date" instead of "start_date".

Example request:

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {
            "op": {"name": "<"},
            "left": "Last Assessment Date",
            "right": "10/17/2017",
        }},
    }

Notes:

- when searching for dates and timestamps, ``~`` and ``!~`` are
  synonymous to ``=`` and ``!=`` respectively;
- when searching for dates and timestamps, you can provide partial
  dates: ``date = 2017`` is the same as ``date >= 01/01/2017 AND date
  <= 12/31/2017``, ``date < 06/2017`` is the same as ``date <
  01/06/2017``;
- when searching for dates and timestamps, you can provide dates
  either in ``mm/dd/YYYY`` and ``YYYY-mm-dd`` formats;
- when searching for non-date fields, ``~`` and ``!~`` accept
  wildcards: ``_`` matches any character, ``%`` matches any number of
  any characters;
- ``is empty`` is technically a binary operator "is" that accepts only
  "empty" in its "right" operand: ``{"op": {"name": "is"}, "left":
  "<field name>", "right": "empty"}``.

Logical operators
~~~~~~~~~~~~~~~~~

- ``OR`` logical or,
- ``AND`` logical and.

You can group any filter expression with any other filter expression
with ``OR`` or ``AND`` operators. They both accept the same operands:
``"left": {<expression tree>}`` and ``"right": {<expression tree>}``.

Example request:

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {
            "op": {"name": "AND"},
            "left": {
                "op": {"name": "~"},
                "left": "title",
                "right": "ISO",
            },
            "right": {
                "op": {"name": "OR"},
                "left": {
                     "op": {"name": "is"},
                     "left": "description",
                     "right": "empty",
                },
                "right": {
                     "op": {"name": "~"},
                     "left": "description",
                     "right": "TBD",
                },
            },
        }},
    }


Object operators
~~~~~~~~~~~~~~~~

- ``relevant`` is mapped or logically related,
- ``similar`` has common mapped objects,
- ``owned`` has a certain person with any object-level role,
- ``related_people`` special mapped people list,
- ``text_search`` has some value in any indexed field,
- ``cascade_unmappable`` specific to Issue-Assessment unmapping.

These operators operate with objects as a whole (primarily based on
mappings). Each has its own set of operands.

``relevant``
............

There are two main cases of relevant expressions.

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {
            "op": {"name": "relevant"},
            "object_name": "Program",
            "ids": [1, 2],
        }},
    }

Filters objects that are mapped or related to ``"Program"`` with id 1
or 2.

..  code:: python

    query = [
        {
            "object_name": "Control",
            "filters": {"expression": {...}},
        },
        {
            "object_name": "<object name>",
            "filters": {"expression": {
                "op": {"name": "relevant"},
                "object_name": "__previous__",
                "ids": [0],  # index of a previous query starting with 0
            }},
        },
    ]

Filters objects that are mapped or related any object from the result
set of the first query object.

Notes:

- the definition of "relevance" has no solid definition, objects can
  be relevant if they are directly mapped or mapped to a relevant
  program, and people can be relevant if they are stored in a custom
  attribute, have a role in the current object or the parent program;
- ``"ids": [1]`` can be passed as ``"ids: 1`` (value instead of a
  singleton list).

``similar``
...........

Applicable only to query Assessments ``similar`` to Assessments,
Assessments ``similar`` to Issues and vice versa.

..  code:: python

    query = {
        "object_name": "Assessment",
        "filters": {"expression": {
            "op": {"name": "similar"},
            "object_name": "Assessment",
            "ids": [2],
        }},
    }

Returns Assessment with the same ``Assessment Type`` that are mapped
to any snapshots of the same snapshottable objects whose snapshots are
mapped to ``"Assessment"`` with id 2.


``owned``
.........

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {
            "op": {"name": "owned"},
            "ids": [1, 2],
        }},
    }

Returns objects that are "owned" by either Person with id 1 or Person
with id 2.

Criteria for "owned":

- the Person is directly mapped,
- the Person is stored in any custom attribute,
- the Person is Assessment Creator, Assignee or Verifier,
- the Person has a role on the object or, for Audit, a role in the
  parent Program,
- the Person has an object-level role.


``text_search``
...............

..  code:: python

    query = {
        "object_name": "<object name>",
        "filters": {"expression": {
            "op": {"name": "text_search"},
            "text": "Some free text entered into a search field",
        }},
    }

Returns objects that contain the provided ``"text"`` in any of the
indexed fields (basically, in any field that can be shown on the info
pane or in the tree view).


``related_people``
..................

Special operator to return people for People tab. Can be used to get
the list of objects where a person will be displayed in people tab.

..  code:: python

    query = {
        "object_name": "Person",
        "filters": {"expression": {
            "op": {"name": "text_search"},
	    "object_name": "<object name>",
            "ids": [1]
        }},
    }

Will return the list of people who should be displayed in People tab
for ``"<object name>"`` with id 1.

The people returned are either directly mapped, or:

- for Program: have a Program-level role,
- for Audit: have a Program-level role or an Audit-level
  role,
- for Workflow: have a Workflow-level role.


``cascade_unmappable``
......................

Special operator to return a list of objects that will be unmapped is
process of cascade unmapping of Assessment from Issue.

..  code:: python

    query = {
        "object_name": "Audit",
        "filters": {"expression": {
            "op": {"name": "cascade_unmappable"},
	    "issue": {"id": 1},
	    "assessment": {"id": 2},
        }},
    }

The only allowed ``"object_name"`` values are "Snapshot" and "Audit".

Full example
------------

Request
~~~~~~~

..  code:: python

    [
        {
            "object_name": "Control",
            "type": "ids",
            "filters": {"expression": { "op": {"name": "~"}, "left": "admin", "right": "Example User" } }
        },
        {
            "object_name": "Program",
            "type": "ids",
            "filters": {"expression": { "op": {"name": "~"}, "left": "title", "right": "PCI" } }
        },
        {
            "object_name": "System",
            "type": "ids",
            "filters": {
                "expression": { "op": {"name": "AND"},
                                "left": {"op": {"name": "~"}, "left": "title", "right": "example.com" },
                                "right": {"op": {"name": "relevant"}, "object_name": "__previous__", "ids": [1] } }
            }
        },
        {
            "object_name": "Product",
            "type": "ids",
            "filters": {
                "expression": { "op": {"name": "AND"},
                                "left": {"op": {"name": "~"}, "left": "title", "right": "Mail" },
                                "right": {"op": {"name": "relevant"}, "object_name": "__previous__", "ids": [2] } }
            }
        },
        {
            "object_name": "Regulation",
            "type": "values",
	    "limit": [0, 20],
	    "order_by": [{"name": "Primary Contacts"}, {"name": "title", "desc": True}],
            "filters": {
                "expression": { "op": {"name": "AND"},
                                "left": {
                                    "op": {"name": "AND"},
                                    "left": {
                                        "op": {"name": "OR"}, "left": {
                                            "op": {"name": "="}, "left": "state", "right": "Draft"
                                        },
                                        "right": {
                                            "op": {"name": "="}, "left": "state", "right": "Effective"
                                        }
                                    },
                                    "right": {
                                        "op": {"name": "OR"},
                                        "left": {"op": {"name": "~"}, "left": "title", "right": "Access"},
                                        "right": {"op": {"name": "~"}, "left": "title", "right": "Permission"}
                                    }
                                },
                                "right": {
                                    "op": {"name": "OR"},
                                    "left": {"op": {"name": "relevant"}, "object_name": "__previous__", "ids": [0]},
                                    "right": {"op": {"name": "relevant"}, "object_name": "__previous__", "ids": [3] }
                                } }
            }
        }
    ]

0. We find every Control that has "Example User" as an Admin.

1. We find every Program that contains "PCI" in the title.

2. We find every System that features two parameters:

   - contains "example.com" in the title,
   - is related to any of the Programs from block 1.

3. We find every Product that features two parameters:

   - contains "Mail" in the title
   - is related to any of the Systems from block 2

4. We find, order by Primary Contacts list and title in descending
   order and return the full objects for objects starting with 1st and
   finishing with 20th Regulations that feature the following
   parameters:

   - is related to any of the Products from block 3 OR is related to any
     of the Controls from block 0,
   - has state in "Draft" or "Effective",
   - contains "Access" or "Permission" in the title.

Response:
~~~~~~~~~

.. code:: python

    [
        {
            "Control": {
                "total": 8,
                "ids": [
                    20,
                    22,
                    23,
                    2053,
                    2567,
                    3597,
                    3598,
                    6511
                ],
                "object_name": "Control",
                "count": 8
            }
        },
        {
            "Program": {
                "total": 3,
                "ids": [
                    446,
                    452,
                    1711
                ],
                "object_name": "Program",
                "count": 3
            }
        },
        {
            "System": {
                "total": 1,
                "ids": [
                    324
                ],
                "object_name": "System",
                "count": 1
            }
        },
        {
            "Product": {
                "total": 1,
                "ids": [
                    111
                ],
                "object_name": "Product",
                "count": 1
            }
        },
        {
            "Regulation": {
                "total": 2,
                "values": [
                    {
                        "scope": null,
                        "audit_duration": null,
                        "os_state": "Unreviewed",
                        "risks": [],
                        "description": "",
                        "object_people": [],
                        "audit_start_date": null,
                        "id": 4530,
                        "status": "Draft",
                        "type": "Regulation",
                        "viewLink": "/regulations/4530",
                        "modified_by": {
                            "context_id": null,
                            "type": "Person",
                            "href": "/api/people/150",
                            "id": 150
                        },
                        "task_group_objects": [],
                        "related_sources": [],
                        "notes": "",
                        "task_groups": [],
                        "organization": null,
                        "custom_attribute_definitions": [
                            {
                                "definition_type": "regulation",
                                "definition_id": null,
                                "title": "A Dropdown CA",
                                "selfLink": "/api/custom_attribute_definitions/1421",
                                "helptext": "",
                                "attribute_type": "Dropdown",
                                "context": null,
                                "updated_at": "2016-09-20T13:46:54",
                                "type": "CustomAttributeDefinition",
                                "id": 1421,
                                "modified_by": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/2",
                                    "id": 2
                                },
                                "placeholder": "",
                                "multi_choice_options": "a,b,c,d,e",
                                "mandatory": false,
                                "multi_choice_mandatory": null,
                                "created_at": "2016-09-20T13:46:54"
                            },
                            {
                                "definition_type": "regulation",
                                "definition_id": null,
                                "title": "myGCA",
                                "selfLink": "/api/custom_attribute_definitions/1432",
                                "helptext": "",
                                "attribute_type": "Dropdown",
                                "context": null,
                                "updated_at": "2016-09-21T14:59:23",
                                "type": "CustomAttributeDefinition",
                                "id": 1432,
                                "modified_by": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/230",
                                    "id": 230
                                },
                                "placeholder": "",
                                "multi_choice_options": "1st value,2nd value,3rd value",
                                "mandatory": false,
                                "multi_choice_mandatory": null,
                                "created_at": "2016-09-21T14:59:23"
                            }
                        ],
                        "slug": "REGULATION-4530",
                        "preconditions_failed": false,
                        "controls": [],
                        "end_date": null,
                        "related_destinations": [
                            {
                                "context_id": null,
                                "type": "Relationship",
                                "href": "/api/relationships/314025",
                                "id": 314025
                            }
                        ],
                        "title": "Expected Regulation 2 (has \"access\" word in the title)",
                        "selfLink": "/api/regulations/4530",
                        "context": null,
                        "updated_at": "2017-10-17T14:00:38",
                        "workflow_state": null,
                        "risk_objects": [],
                        "start_date": null,
                        "kind": "Regulation",
                        "people": [],
                        "custom_attribute_values": [],
                        "version": null,
                        "audit_frequency": null,
                        "access_control_list": [
                            {
                                "updated_at": "2017-10-17T14:00:38",
                                "type": "AccessControlList",
                                "modified_by": null,
                                "ac_role_id": 102,
                                "person": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/150",
                                    "id": 150
                                },
                                "person_id": 150,
                                "id": 31651,
                                "context": null,
                                "created_at": "2017-10-17T14:00:38"
                            }
                        ],
                        "created_at": "2017-10-17T14:00:38"
                    },
                    {
                        "scope": null,
                        "audit_duration": null,
                        "os_state": "Unreviewed",
                        "risks": [],
                        "description": "",
                        "object_people": [],
                        "audit_start_date": null,
                        "id": 4529,
                        "status": "Draft",
                        "type": "Regulation",
                        "viewLink": "/regulations/4529",
                        "modified_by": {
                            "context_id": null,
                            "type": "Person",
                            "href": "/api/people/150",
                            "id": 150
                        },
                        "task_group_objects": [],
                        "related_sources": [
                            {
                                "context_id": null,
                                "type": "Relationship",
                                "href": "/api/relationships/314024",
                                "id": 314024
                            }
                        ],
                        "notes": "",
                        "task_groups": [],
                        "organization": null,
                        "custom_attribute_definitions": [
                            {
                                "definition_type": "regulation",
                                "definition_id": null,
                                "title": "A Dropdown CA",
                                "selfLink": "/api/custom_attribute_definitions/1421",
                                "helptext": "",
                                "attribute_type": "Dropdown",
                                "context": null,
                                "updated_at": "2016-09-20T13:46:54",
                                "type": "CustomAttributeDefinition",
                                "id": 1421,
                                "modified_by": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/2",
                                    "id": 2
                                },
                                "placeholder": "",
                                "multi_choice_options": "a,b,c,d,e",
                                "mandatory": false,
                                "multi_choice_mandatory": null,
                                "created_at": "2016-09-20T13:46:54"
                            },
                            {
                                "definition_type": "regulation",
                                "definition_id": null,
                                "title": "myGCA",
                                "selfLink": "/api/custom_attribute_definitions/1432",
                                "helptext": "",
                                "attribute_type": "Dropdown",
                                "context": null,
                                "updated_at": "2016-09-21T14:59:23",
                                "type": "CustomAttributeDefinition",
                                "id": 1432,
                                "modified_by": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/230",
                                    "id": 230
                                },
                                "placeholder": "",
                                "multi_choice_options": "1st value,2nd value,3rd value",
                                "mandatory": false,
                                "multi_choice_mandatory": null,
                                "created_at": "2016-09-21T14:59:23"
                            }
                        ],
                        "slug": "REGULATION-4529",
                        "preconditions_failed": false,
                        "controls": [],
                        "end_date": null,
                        "related_destinations": [],
                        "title": "Expected Regulation 1 (\"permission in title\")",
                        "selfLink": "/api/regulations/4529",
                        "context": null,
                        "updated_at": "2017-10-17T14:12:03",
                        "workflow_state": null,
                        "risk_objects": [],
                        "start_date": null,
                        "kind": "Regulation",
                        "people": [],
                        "custom_attribute_values": [],
                        "version": null,
                        "audit_frequency": null,
                        "access_control_list": [
                            {
                                "updated_at": "2017-10-17T13:59:54",
                                "type": "AccessControlList",
                                "modified_by": null,
                                "ac_role_id": 102,
                                "person": {
                                    "context_id": null,
                                    "type": "Person",
                                    "href": "/api/people/150",
                                    "id": 150
                                },
                                "person_id": 150,
                                "id": 31650,
                                "context": null,
                                "created_at": "2017-10-17T13:59:54"
                            }
                        ],
                        "created_at": "2017-10-17T13:59:54"
                    }
                ],
                "object_name": "Regulation",
                "count": 2
            }
        }
    ]

Notes:

- every block is evaluated one by one, so they should be transformed
  from the form bottom-first;
- you can't reference the next blocks in the list;
- to make the queries reasonably fast, you should add ``"type":
  "ids"`` explicitly when you just need a query for a following
  ``__previous__`` filter.
