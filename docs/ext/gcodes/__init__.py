__version__ = '0.1.0'
__author__ = '@ajmirsky'
__license__ = 'LGPLv3'


def setup(app):

    from . import gcodes

    app.add_node(gcodes.GCodeNode, html=(gcodes.visit, gcodes.depart))
    app.add_directive('gcodes', gcodes.GCodeDirective)
