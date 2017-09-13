import inspect

from docutils import nodes
from docutils.parsers import rst


class GCodeNode(nodes.General, nodes.Element):
    pass


def visit(self, node):

    self.body.append("<p>gcode start</p>")


def depart(self, node):
    self.body.append("<p>gcode end</p>")


class GCodeDirective(rst.Directive):

    name = 'gcodes'
    node_class = GCodeNode

    def run(self):

        node = self.node_class()

        # from redeem import gcodes
        # inspect.getmembers(gcodes, inspect.isclass)

        return [node,]
