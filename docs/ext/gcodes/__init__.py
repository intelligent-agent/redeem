__version__ = '0.1.0'
__author__ = '@ajmirsky'
__license__ = 'LGPLv3'


def setup(app):

    from . import gcodes

    app.add_node(gcodes.GCodeListNode, html=(gcodes.gcode_list_visit, gcodes.gcode_list_depart))
    app.add_node(gcodes.GCodeNode, html=(gcodes.gcode_node_visit, gcodes.gcode_node_depart))
    app.add_node(gcodes.GCodeNameNode, html=(gcodes.gcode_name_node_visit, gcodes.gcode_name_node_depart))
    app.add_directive('gcodes', gcodes.GCodeDirective)
