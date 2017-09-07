=============
Documentation
=============

`ReStructured Text (RST) <http://www.sphinx-doc.org/en/stable/rest.html>`_ is a markdown language
with additional directives for table of contents, tables and footnotes, among other things. It can also be
configured to pull docstrings directly from the code base. `Sphinx <http://www.sphinx-doc.org/en/stable/>`_
is a python-based document generator which converts RST into HTML docs for browsing
and searching. Gulp is used as a makefile and to convert LESS stylesheets into CSS.

To begin, you'll need to install a few node-based tools: `Node Package Manager <https://www.npmjs.com/>`_ and `Yarn <https://yarnpkg.com/en/>`_.

``brew install npm yarn`` (for mac osx) or ``apt-get install npm yarn`` (for linux)

Assuming you have the redeem git repo already cloned, install the remainder of the node packages:

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

--------------------
Commonly Used Syntax
--------------------

~~~~~~~~
Emphasis
~~~~~~~~

*emphasis* is rendered as italics

**strong emphasis** is rendered as bold

~~~~
Code
~~~~

``literal`` is used for highlighting code or commands inline.

::

    def blockOfCode(a, b):
        return a + b


~~~~~~~~~~
Hyperlinks
~~~~~~~~~~

`Display Name <http://link/to/external/site/>`_ is a link to an external site; it will open in a new window.

:doc:`../replicape/index` is used to reference another piece of the same documentation using the title of that doc.

Or it can be used to name the link to something different :doc:`Go to Replicape </replicape/index>` uses an alternative displayed name.

~~~~~
Lists
~~~~~

- a
- list
- of
- unordered
- things

1. a
2. list
3. of
4. ordered
5. things

~~~~~~~~~~~~~~~~~~~~~
Footnotes : reference
~~~~~~~~~~~~~~~~~~~~~

Here is a paragraph that has two footnotes [#f1]_; the actual footnote is displayed at the end of this document [#f2]_

~~~~~
Table
~~~~~

======  =====  == ==== === =======
Simple  Table  Of Rows and Columns
======  =====  == ==== === =======
Item 1  a      b  c    d   e
Item 2  f      g  h    i   j
Item 3  k      l  m    n   o
Item 4  p      q  r    s   t
======  =====  == ==== === =======

~~~~~~~~~~~~
Highlighting
~~~~~~~~~~~~

..  important:: a piece of information to be highlighted

..  note:: information that is thought of as a best practice. read more about it :doc:`here <documentation>`.

..  warning:: this should be used to highlight a backwards incompatible change

..  danger:: do not do ``this`` as something maybe damaged or lost

..  versionadded:: X.Y.Z

~~~~~~
Images
~~~~~~

An image is shown as a thumbnail; full size is viewable by clicking on it:

..  image:: images/replicapelogo.png

Figures have other options, including using a caption:

..  figure:: images/replicapelogo.png

    A caption describing this figure.

~~~~~~~~~~~~~~~~
Footnotes: notes
~~~~~~~~~~~~~~~~

..  [#f1] Text of the first footnote.
..  [#f2] Text of the second footnote.
