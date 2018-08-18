# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for keeping constants for ACR propagation rules

DO NOT MODIFY THESE VALUES.

These are just the common propagation dictionaries, that are used in different
migration files.

For migration consistency, do not update these values once they are merged.
If a modification is needed feel free to use these and modify them inside the
migration file, or add new common roles and propagation rules.
"""

WORKFLOW_PROPAGATION = {
    "Workflow": {
        "Admin": {
            "Relationship RUD": {
                "TaskGroup RUD": {
                    "Relationship RUD": {
                        "TaskGroupTask RUD": {},
                        "TaskGroupObject RUD": {},
                    },
                },
                "Cycle RUD": {
                    "Relationship RUD": {
                        "CycleTaskGroup RUD": {
                            "Relationship RUD": {
                                "CycleTaskGroupObjectTask RUD": {
                                    "Relationship RUD": {
                                        "CycleTaskEntry RUD": {
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "Workflow Member": {
            "Relationship R": {
                "TaskGroup R": {
                    "Relationship R": {
                        "TaskGroupTask R": {},
                        "TaskGroupObject R": {},
                    },
                },
                "Cycle R": {
                    "Relationship R": {
                        "CycleTaskGroup R": {
                            "Relationship R": {
                                "CycleTaskGroupObjectTask R": {
                                    "Relationship R": {
                                        "CycleTaskEntry R": {},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}
