=============
Documentation
=============

`ReStructured Text (RST) <http://www.sphinx-doc.org/en/stable/rest.html>`_ is a markdown language
with additional directives for table of contents, tables and footnotes, among other things. It can also be
configured to pull docstrings directly from the code base. `Sphinx <http://www.sphinx-doc.org/en/stable/>`_
is a python-based document generator which converts RST into HTML docs for browsing
and searching. Gulp is used as a makefile and to convert LESS stylesheets into CSS.

To beign, you'll need to install a few python modules (assuming you're building locally and not on a BeagleBone).
This is required because Sphinx reads docstrings from the code base and adds them to the documentation::

    pip install tests/modules.rst
    pip install docs/requirements.rst

Next you'll need to install a few node-based tools which are used to process the visual theme: `Node Package Manager <https://www.npmjs.com/>`_ and `Yarn <https://yarnpkg.com/en/>`_.

``brew install npm yarn`` (for mac osx) or ``apt-get install npm yarn`` (for linux)

Assuming you have the redeem git repo already cloned, install the remainder of the node packages:

::

    $ cd redeem/docs
    $ yarn

To build the docs::

    ``$ gulp docs``

Or if you'd like it to build every time a change is made to code or docs, use ``gulp watch``.

The output is placed in the `/docs/_build/html` directory and, since it's static, can be opened
directly from a browser.

Mediawiki to RST
----------------

`Pandoc`__ is a tool that converts between multiple different markup and markdown formats. When converting from
mediawiki to restructured text, it converts about 90% of the formatting without need for manual refactoring.

__ https://pandoc.org/

To install: ``brew install pandoc``

To convert from mediawiki:

#. go to the mediawiki page and click `Edit`

#. copy and paste the content into a text file. eg. mywikipage.mw

#. run pandoc: ``pandoc -r mediawiki -w rst mywikipage.mw > mywikipage.rst``

#. edit as needed

Release Build (Versions)
------------------------

The build process which produces the current and past versions of the documentation requires
that all files are committed, pushed and have a tag with the format of `X.X` or `X.X.X`. There
is a gulp command that handles all of the configuration::

    $ gulp build-versions


Example section title
---------------------

Example section title


Example sub-section title
~~~~~~~~~~~~~~~~~~~~~~~~~

Example sub-section title.


Commonly Used Syntax
--------------------


Emphasis
~~~~~~~~

*emphasis* is rendered as italics

**strong emphasis** is rendered as bold


Code
~~~~

``literal`` is used for highlighting code or commands inline.

::

    def blockOfCode(a, b):
        return a + b



Hyperlinks
~~~~~~~~~~

`Display Name <http://link/to/external/site/>`_ is a link to an external site; it will open in a new window.

:doc:`../replicape/index` is used to reference another piece of the same documentation using the title of that doc.

Or it can be used to name the link to something different :doc:`Go to Replicape </replicape/index>` uses an alternative displayed name.


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


Footnotes : reference
~~~~~~~~~~~~~~~~~~~~~

Here is a paragraph that has two footnotes [#f1]_; the actual footnote is displayed at the end of this document [#f2]_


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


Highlighting
~~~~~~~~~~~~

..  important:: a piece of information to be highlighted

..  note:: information that is thought of as a best practice. read more about it :doc:`here <documentation>`.

..  warning:: this should be used to highlight a backwards incompatible change

..  danger:: do not do ``this`` as something maybe damaged or lost

..  versionadded:: X.Y.Z


Images
~~~~~~

An image is shown as a thumbnail; full size is viewable by clicking on it:

..  image:: images/replicapelogo.png

Figures have other options, including using a caption:

..  figure:: images/replicapelogo.png

    A caption describing this figure.


Footnotes: notes
~~~~~~~~~~~~~~~~

..  [#f1] Text of the first footnote.
..  [#f2] Text of the second footnote.


Code Documentation
------------------

Docstrings should use the NumPY format. Source code for these examples can be found at :doc:`examplepy`

..  autofunction:: example.function_with_types_in_docstring

..  autofunction:: example.module_level_function

..  autofunction:: example.example_generator

..  autoexception:: example.ExampleError

..  autoclass:: example.ExampleClass
    :members:
