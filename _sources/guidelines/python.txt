Python
======

We try to keep our code style as close as we can to
`Google Code Style <https://google.github.io/styleguide/pyguide.html>`_.

Unfortunately, because of our legacy code, there are a few exceptions,
by far the biggest being the two space indent.

To ensure consistency of our code we use
`flake8 <https://github.com/google/ggrc-core/blob/develop/setup.cfg#L1>`_
and `pylint <https://github.com/google/ggrc-core/blob/develop/pylintrc>`_
(both of which should specify what style issues are present when
opening a pull request).

A notable **exception** to this are **docstrings** as those **aren't
validated** and therefore **both authors and pull request reviewers**
should verify that docstrings match Google's format.

An example of Google docstring format
(from `Google's Code Style Comment <https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments>`_
section, revision  `2.59 on date 9/26/2016 <https://github.com/google/styleguide/blob/b4e1659acd92e4470944928ce1bf27c0f01d6e12/pyguide.html>`_)
for a function:

..  code-block:: python

    def fetch_bigtable_rows(big_table, keys, other_silly_variable=None):
        """Fetches rows from a Bigtable.

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            big_table: An open Bigtable Table instance.
            keys: A sequence of strings representing the key of each table row
                to fetch.
            other_silly_variable: Another optional variable, that has a much
                longer name than the other args, and which does nothing.

        Returns:
            A dict mapping keys to the corresponding table row data
            fetched. Each row is represented as a tuple of strings. For
            example:

            {'Serak': ('Rigel VII', 'Preparer'),
             'Zim': ('Irk', 'Invader'),
             'Lrrr': ('Omicron Persei 8', 'Emperor')}

            If a key from the keys argument is missing from the dictionary,
            then that row was not found in the table.

        Raises:
            IOError: An error occurred accessing the bigtable.Table object.
        """
        pass

For a class:

..  code-block:: python

    class SampleClass(object):
        """Summary of class here.

        Longer class information....
        Longer class information....

        Attributes:
            likes_spam: A boolean indicating if we like SPAM or not.
            eggs: An integer count of the eggs we have laid.
        """

        def __init__(self, likes_spam=False):
            """Inits SampleClass with blah."""
            self.likes_spam = likes_spam
            self.eggs = 0

        def public_method(self):
            """Performs operation blah."""


See `Google Code Style <https://google.github.io/styleguide/pyguide.html>`_
for explanations and more examples.

Misleading pylint's complaints
------------------------------

Next pylint errors can mean something more than pylint explains in its' error messages.

duplicate-code (R0801): \*Similar lines in %s files*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see such error about lines with import statements, it means that maybe you've missed next Code Style rule:

**Use imports for packages and modules only.** (`Google Code Style Import section, revision 2.59 <https://google.github.io/styleguide/pyguide.html?showone=Imports#Imports>`_)

Probably you have >= 4 duplicate lines in 2 source files import statements' section.
