
Documentation Primer
====================

ReStructured Text (``.rst``) is a markdown-like language with additional directives
for table of contents, tables and footnotes, among other things. Sphinx
is a python-based document generator which converts ``rst`` into HTML docs for browsing
and searching. Gulp is used as a makefile and convert LESS stylesheets into CSS.

To begin, you'll need to install a few node-based tools:

``brew install npm yarn`` (for mac osx) or ``apt-get install npm yarn`` (for linux)

Assuming you have the redeem git repo already cloned, install the node dependencies:

::

    $ cd redeem/docs
    $ yarn

To build the docs use ``gulp docs``. Or if you'd like it to build every time a change is made, use ``gulp watch``.




---------------------
Example section title
---------------------

Example section title

~~~~~~~~~~~~~~~~~~~~~~~~~
Example sub-section title
~~~~~~~~~~~~~~~~~~~~~~~~~

Example sub-section title.
