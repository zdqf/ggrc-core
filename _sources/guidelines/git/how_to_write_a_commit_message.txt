How to Write a Commit Message
=============================

This is all shamelessly based on
`chris.beams.io <http://chris.beams.io/posts/git-commit/>`_.

1. Separate subject from body with a blank line
2. Limit the subject line to 50 characters
3. Capitalize the subject line
4. Do not end the subject line with a period
5. Use the imperative mood in the subject line (spoken or written as if
   giving a command or instruction)
6. Wrap the body at 72 characters
7. Use the body to explain what and why vs. how

A properly formed git commit subject line should always be able to
complete the following sentence:

**If applied, this commit will *your subject line here***

Good: If applied, this commit will **refactor subsystem X for
readability**

Bad: If applied, this commit will **fixes for broken stuff**

Commit message should be summary line and description of what you have
done in the imperative mode, that is as if you were commanding someone.
Write "fix", "add", "change" instead of "fixed", "added", "changed".

Examples
--------

Bad
~~~

1. Fixed bug with {something}.
2. changing behavior of {something}
3. more fixes for broken stuff
4. sweet new API methods
5. Removing stuff

Good
~~~~

1. Fix bug when {something_else} doesn't exist
2. Change behavior of {something} to do {behavior_x}
3. [don't do this, fix one specific thing in a commit]
4. Add {method_a}, {method_b} and {method_c} methods to API
5. Remove unused {method_a}, {method_b}...


Before Issuing a New Pull Request
---------------------------------

While every pull request is automatically checked on a continuous
integration server, it is better to catch issues early, resulting in
less broken builds and reduced time before the PR is merged. You should
thus run a few tests locally before submitting the PR for a review.

It is OK to defer some of the checks if they take too much time to be
feasible to run them locally (as a rule of thumb: 10+ minutes). These
checks can be deferred until the CI server runs them.

You are still encouraged to run them yourself, though, if you can afford
the waiting, e.g. just before taking a longer break (lunch, meeting...).


Checking the front-end code
---------------------------

Code style checks
~~~~~~~~~~~~~~~~~

The `ESLint <http://eslint.org/>`_ tool is used for checking the
Javascript code quality. You must assure that your pull request does not
increase the number of ESLint issues found.

To check the code quality of a particular file, run the following in the
development container's console:

..  code-block:: bash

    eslint path/to/some/file.js

You will see a list of all issues found and the corresponding line
numbers. Sample output::

    ...
    105:23  error    Strings must use singlequote                         quotes
    112:7   warning  Identifier name 'fooBaa...ar' is too long. (> 25)    id-length
    112:48  error    Missing space before function parentheses            space-before-function-paren
    114:23  error    Strings must use singlequote                         quotes
    120:3   error    Split 'var' declarations into multiple statements    one-var
    ...

    ✖ 74 problems (73 errors, 1 warning)

You need to resolve at least the issues in the line(s) you have
modified, but it is strongly encouraged to also improve *all* the lines
in every function/method you have touched.

When you submit a new pull request, a script will check how many
Javascript code issues there are on the PR branch, and how many there
were at the point when the PR branch was forked from the target branch
(i.e. the *merge base*). The target branch is the one the PR will be
sent to, usually ``develop``.

If the issue count difference is positive, the check will fail, because
new code should not increase the number of Javascript issues. To avoid
that and preemptively perform the same check locally, do the following:

-   Make sure that you are currently on a branch containing the changes
    that will be submitted with the pull request (the PR branch), and
    that you have these changes committed,
-   Make sure that you don't have any pending local file modifications.
    Use ``git stash`` if necessary,
-   Run the following in the development container's console:

    ..  code-block:: bash

        check_eslint_diff

    If the PR branch was forked from (and will be sent to) a branch other
    than ``develop``, you should specify this with a ``-t`` (or
    ``--merge-target``) option when running the script:

    ..  code-block:: bash

        check_eslint_diff -t release/foo-0.0.1

Running the tests
~~~~~~~~~~~~~~~~~

Run the following in the development container's console:

..  code-block:: bash

    run_karma

When the Karma server (a Javascript test runner) starts, open
``http://localhost:9876/`` in a browser. The browser will connect to the
Karma server and run all Javascript unit tests. The outcome of the tests
will be printed to the console, make sure they all pass.

*NOTE: The officially supported browser by the application is Chrome. It
is thus strongly recommended that you, too, use Chrome for running the
tests locally.*


Checking the back-end code
--------------------------

Code style checks
~~~~~~~~~~~~~~~~~

At the moment, no automatic Python coding style checks are performed -
yet. You should nevertheless make your best effort to write `PEP8
compliant <https://www.python.org/dev/peps/pep-0008/>`_ code to make it
more future compatible for when such automatic checks are introduced and
enforced.

Running the tests
~~~~~~~~~~~~~~~~~

To run the Python unit and integration tests, run the following in the
development container's console:

..  code-block:: bash

    run_pytests

*NOTE: Python integration tests take a while to run, around 20 minutes
(give or take) on a decent laptop.*


End-to-end tests
----------------

To run the full-fledged end-to-end system tests, go to the project root
directory **on the host machine** and run the following from its
console:

..  code-block:: bash

    ./bin/jenkins/run_selenium

Please keep in mind that, for various technical reasons, Selenium tests
**should not** be run from inside a container!

*NOTE: These tests only work with Docker-based development environments,
since they require Docker prerequisites to be installed on the host
machine. Vagrant is not supported.*


Pull Request Titles
-------------------

For pull request titles we should use the same rules as for the subject
line of a commit, but we need to prefix the issue id (or QUICK-FIX or
DOCS if there is no issue id).

A pull request title must also reflect on what changes have been done.
If the pull request title states that it contains test modifications, it
must not contain any code changes outside of tests. If there are logic
changes in the PR, the title must reflect those and the changes in the
tests are implied with the code changes.

Examples::

    CORE-9999 Fix performance issues on bulk operations
    QUICK-FIX Break test cases into smaller parts
    DOCS Add section that explains client side mappings
