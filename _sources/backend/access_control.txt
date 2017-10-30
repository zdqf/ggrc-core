Access Control
==============

Role Based Access Control & Access Control List
-----------------------------------------------

⚠️ GGRC is currently in the process of refactoring the role based access control
permission system (RBAC) to access control list (ACL).

The progress is tracked in the `ACL technical design document
<https://docs.google.com/document/d/1i-iutQOHzfgAIizgRzTGGMUb7PyS7LfwUTAvcPiTFwg/edit#heading=h.xgjl2srtytjt>`_.


Roles
-----

Below is a complete list of roles a user can have in GGRC

- **Global Roles** No access, Creator, Reader, Editor, Administrator, Superuser
- **Program roles** Program Manager, Program Editor, Program Reader
- **Workflows roles** Workflow Manager, Workflow Member
- **Assessment Object roles** Assignees (Creator, Assessor, Verifier)
- **Object Roles** Object Admins, Primary contacts, Secondary contacts, Primary Assessors, Secondary Assessors

Global Roles
~~~~~~~~~~~~

GGRC has 6 global roles:

- **No Role** - users with no access are not allowed to get passed the login page. They are marked as Inactive users inside the app.
- **Creator** users are allowed to create any GGRC object, but they are only allowed to see their own objects or objects where they were explicitly given access to by another role (object owner, program manager, assignee, …).
- **Reader** users have READ access to all the objects in GGRC. In addition to this, they also have the ability to CREATE any object much like users with the Creator role. Currently there is no way to give a user READ only access to the app. Every user (except for the ones with No access role) are allowed to create their own objects.
- **Editor** users can READ & EDIT all objects in GGRC and similar to Reader and Creator roles they can also CREATE their own objects.
- **Administrator** users can do all of the above plus they are granted access to the admin dashboard where they can grant System wide roles to other users. They can also add global custom attributes to GGRC objects.
- **Superuser** that is set in the app config (GGRC_BOOTSTRAP_ADMIN_USERS). It behaves completely the same as the Administrator role, but it can’t be unassigned through the application interface (a change in the config is required).

Program and Workflow roles
~~~~~~~~~~~~~~~~~~~~~~~~~~

Program & Workflow roles grant access only in the context of the Program/Workflow.

- **No access** will not grant any permissions in the program/workflow context, however, if the user has access to the object (e.g. has system wide Editor role) this role WILL NOT prevent access to the object even though the name/description implies it.
- **Workflow Member** have access to update/delete some workflow objects (cycle tasks, attachments, comments), but they only have READ access to objects on workflow setup tab (task groups, task group tasks) and the workflow object itself.
- **Workflow Manager** have complete access to all objects in the workflow scope. They can also have permission to assign workflow/program level roles to users.
- **Program Reader** have READ access to the program and all the objects related to the program. This includes all objects mapped to the program (e.g. Regulations, Controls, Sections, Systems, etc.) as well as Audits and all objects mapped to the audit (Assessments, Issues, Requests, …)
- **Program Editor** have EDIT access to the program and all the objects related to the program.
- **Program Manager** have EDIT access and can assign program roles to users.
- **Auditor** is a special role on the audit object that grants the user READ access to the audit and program as well as read access to all the mapped objects


RBAC Implementation
-------------------

All the roles described above are scattered through multiple database tables.

Database Tables
~~~~~~~~~~~~~~~

- `roles` table stores all the possible system wide and object level roles (e.g. Editor, WorkflowMember). The permissions that the roles grant are stored in the code, where each role in the database has a corresponding python file with a list of permissions that the role grants, e.g. workflow member.
- `user_roles`  connects users in the system to a specific role
- `contexts` Programs, Audits and Workflows have their own context. A ProgramEditor role gives the user edit access to all the objects with that specific context_id.
- `context_implications` Because certain roles span over multiple contexts (ProgramEditor should have edit access on all audits attached to the parent program) we use the context_implications to propagate permissions from the program context to the audit context.

Performance issues
~~~~~~~~~~~~~~~~~~

On every request to the server we have to calculate which objects the user has access to. This includes multiple queries to the database to fetch all the user roles, contexts, implications, owners etc and then combining the results with the roles defined in the python code.

From a performance standpoint the roles that grant access to mapped objects are the worst as they require expensive joins to the relationship table to get a list of currently active mapped objects.

Because the access data is scattered throughout multiple tables in the database and the python source code, creating efficient search queries has proven to be extremely difficult. Creating joins through that many tables is slow and error prone.

Usability issues
~~~~~~~~~~~~~~~~
Because of the way we currently gather permissions, there is no easy way to figure out how or why the current user has access to a particular object and because our permissions rules are very complex, this has caused many false bug reports and confused multiple users trying to use the system.

ACL Implementation
------------------

The idea behind the new ACL system is to greatly simplify the implementation by reducing the number of places where roles are defined and stored. Instead of querying multiple tables and computing a list of possible roles/contexts/implications all necessary state is going to be stored in a single table (`access_control_list`). The table is going to be optimized for READ access because it will be queried on almost every request.

We will accomplish this by sacrificing some performance on object creation (e.g. creating a mapping will have to add one or multiple rows to the access_control_list table), but by so doing we will not have to compute those permissions on every GET request.

Object level permissions will give the user access to one particular object. In the `access_control_list` table these permissions will have a valid object set in the resource_id and resource_type columns. The permissions granted will depend on the role specified e.g. object owner role will grant read/write/delete access on the object, while object contact role might only grant read access.

Database Tables
~~~~~~~~~~~~~~~

- `access_control_roles` stores role definitions.
- `access_control_list` stores user <-> role <-> object mappings.
