from docutils import nodes


# G CODE NODE ####################
from jinja2 import Template


class GCodeNode(nodes.General, nodes.Element):
    pass


def gcode_node_visit(self, node):
    self.body.append("<div class='row'>")


def gcode_node_depart(self, node):
    self.body.append("</div>")


# GCODE DESCRIPTION NODE #################


class GCodeDescriptionNode(nodes.General, nodes.Element):
    pass


def gcode_description_node_visit(self, node):
    self.body.append("<div class='col-xs-4'>")
    self.body.append(node['description'])
    self.body.append("</div>")


def gcode_description_node_depart(self, node):
    pass


# GCODE LONG DESCRIPTION NODE #############
class GCodeLongDescriptionNode(nodes.General, nodes.Element):
    pass


def gcode_long_description_node_visit(self, node):
    self.body.append("<div class='col-xs-8'>")

    lines = node['long-description'].split('\n')

    template = Template("""
        {% for line in lines %}
        <p>{{ line }}</p>
        {% endfor %}
    """)

    self.body.append(template.render({'lines': lines}))


    self.body.append("</div>")


def gcode_long_description_node_depart(self, node):
    pass

