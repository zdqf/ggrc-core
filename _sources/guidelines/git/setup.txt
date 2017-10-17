Setup
=====

All code on `ggrc-core repo <https://github.com/google/ggrc-core>`_ should go through a
proper pull request procedure. There should be no direct pushes to
google ggrc-core repo. Anyone with the privilege to push to the main
repo must configure their system to prevent that, in order to avoid any
"ninja commits".

This document is not a tutorial on how to use git forks and how to work
with multiple git remotes. It is only meant to help setting up your repo
to prevent pushes to google/ggrc-core.

1. create a fork on github

2. set up your repo

   1. Starting from a fresh clone:

      clone your repo

      ..  code-block:: bash

          git clone git@github.com:<nick>/ggrc-core.git

   2. Adding a remote to an existing clone

      delete the current origin remote

      ..  code-block:: bash

          git remote remove origin

      add your fork as origin

      ..  code-block:: bash

          git remote add origin git@github.com:<nick>/ggrc-core.git

3. add the upstream repo for easy fetching

   ..  code-block:: bash

       git remote add upstream git@github.com:google/ggrc-core.git

Extra:

get a pull request from google/ggrc-core without adding other remotes to
your repo:

make an alias (assuming upstream is pointing to google/ggrc-core.git)

..  code-block:: bash

    git config alias.pr '!f() { git fetch upstream dev; git checkout -B pr-$1 FETCH_HEAD; git fetch upstream pull/$1/head; git merge --no-ff FETCH_HEAD -m \"Automatic merge\"; }; f'

fetch a given pull request

..  code-block:: bash

    git pr 1234  # where the 1234 is a pull request number

Note: this method will fail to pull changes form the updated pull
request if the user uses force push to change any of the commits. In
that case you need to delete your local pr-1234 branch and run the
``git pr 1234`` again.
