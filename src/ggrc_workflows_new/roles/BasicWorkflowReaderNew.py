# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Contains basic reader's WorkflowNew rights."""
# pylint: skip-file
scope = "WorkflowNew Implied"
description = " "
permissions = {
    "read": [
        "WorkflowNew",
        "UserRole",
        "Context",
        "Document",
        "ObjectDocument",
        "ObjectFolder",
        "ObjectFile",
    ],
    "create": [
        "WorkflowNew",
    ],
    "update": [
    ],
    "delete": [
    ],
    "view_object_page": [
        "WorkflowNew",
    ],
}
