__version__ = '0.1.0'
__author__ = '@ajmirsky'
__license__ = 'LGPLv3'


def setup(app):

    import directives
    import nodes

    app.add_node(nodes.GCodeNode, html=(nodes.gcode_node_visit, nodes.gcode_node_depart))
    app.add_node(nodes.GCodeDescriptionNode, html=(nodes.gcode_description_node_visit, nodes.gcode_description_node_depart))
    app.add_node(nodes.GCodeLongDescriptionNode, html=(nodes.gcode_long_description_node_visit, nodes.gcode_long_description_node_depart))
    app.add_node(nodes.GCodeFormattedDescriptionNode, html=(nodes.gcode_formatted_description_node_visit, nodes.gcode_formatted_description_node_depart))
    app.add_directive('gcodes', directives.GCodeDirective)
    app.add_directive('mcodes', directives.MCodeDirective)
    app.add_directive('tcodes', directives.TCodeDirective)
