# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Contains workflow owner's WorkflowNew rights."""
# pylint: skip-file
scope = "WorkflowNew"
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
        "UserRole",
        "Document",
        "ObjectDocument",
        "ObjectFolder",
        "ObjectFile",
    ],
    "update": [
        "WorkflowNew",
        "UserRole",
        "Document",
        "ObjectDocument",
        "ObjectFolder",
        "ObjectFile",
    ],
    "delete": [
        "WorkflowNew",
        "UserRole",
        "Document",
        "ObjectDocument",
        "ObjectFolder",
        "ObjectFile",
    ],
    "view_object_page": [
        "WorkflowNew",
    ],
}
