import inspect

from docutils import nodes
from sphinx import addnodes
from docutils.parsers import rst


# G CODE NODE ####################
class GCodeNode(nodes.General, nodes.Element):
    pass


def gcode_node_visit(self, node):
    self.body.append("<p>")


def gcode_node_depart(self, node):
    self.body.append("</p>")


# G CODE NAME NODE ################
class GCodeNameNode(nodes.General, nodes.Element):
    pass


def gcode_name_node_visit(self, node):
    self.body.append("<p>{}</p>".format(node.rawsource))


def gcode_name_node_depart(self, node):
        pass


# G CODE DESCRIPTION ###############


class GCodeDescriptionNode(nodes.General, nodes.Element):
    pass

# GCODE DETAIL NODE #################


class GCodeDetailNode(nodes.General, nodes.Element):
    pass

# GCODE LISTING NODE ################


class GCodeListNode(nodes.General, nodes.Element):
    pass


def gcode_list_visit(self, node):
    self.body.append("<table>".format(node.title))


def gcode_list_depart(self, node):
    self.body.append("</table>".format(node.title))


class GCodeDirective(rst.Directive):

    name = 'gcodes'
    node_class = GCodeNode

    def load_classes_in_module(self, module):
        from redeem.gcodes.GCodeCommand import GCodeCommand
        for module_name, obj in inspect.getmembers(module):

            if inspect.ismodule(obj) and (obj.__name__.startswith('gcodes') or obj.__name__.startswith('redeem.gcodes')):
                self.load_classes_in_module(obj)
            elif inspect.isclass(obj) and issubclass(obj, GCodeCommand) and module_name != 'GCodeCommand' and module_name != 'ToolChange':

                print("got gcode, wohoo {}".format(obj.__name__))

    def run(self):

        # node = self.node_class()
        #
        # # from redeem import gcodes
        # # self.load_classes_in_module(gcodes)
        #
        # targetnode1 = nodes.target('', '', ids=['gde1',], ismod=True)
        #
        # self.state.document.note_explicit_target(targetnode1)
        #
        #
        # gcodenode1 = GCodeNode('')
        # gcodenode1 += GCodeNameNode('code1a')
        # # gcodenode1 += GCodeDescriptionNode('short description of the first gcode')
        # # gcodenode1 += GCodeDetailNode('long description of the first gcode')
        #
        #
        # # targetnode2 = nodes.target('', '', ids=['gcode2'])
        # # gcodenode2 = GCodeNode('code2')
        # # gcodenode2 += nodes.title('code2a', 'code2b')
        # # gcodenode2 += addnodes.desc('short description of the second gcode')
        # # gcodenode2 += addnodes.desc_content('long description of the second gcode ')
        #
        # return [targetnode1, gcodenode1, ]

        list = GCodeListNode('')

        gcode = GCodeNode('')

        name = GCodeNameNode('gcode1')



        titleTxt = 'abc'
        lineno = self.state_machine.abs_line_number()
        target = nodes.target()
        section = nodes.section()

        # titleTxt appears to need to be same as the section's title text
        self.state.add_target(titleTxt, '', target, lineno)
        section += nodes.title("this is the best title ever", 'or wgat')

        return [target, section]

