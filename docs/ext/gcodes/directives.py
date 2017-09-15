import inspect

from docutils import nodes
from sphinx import addnodes
from docutils.parsers import rst

from docs.ext.gcodes.nodes import GCodeNode, GCodeDescriptionNode, GCodeLongDescriptionNode
from redeem.gcodes.GCodeCommand import GCodeCommand
from redeem import gcodes as gcode_module


class GCodeDirective(rst.Directive):

    name = 'gcodes'

    designator = 'G'

    # def get_designator(self):
    #     return 'G'

    def __init__(self, *args, **kwargs):
        super(GCodeDirective, self).__init__(*args, **kwargs)
        self.gcodes = {}

    # code borrowed from redeem.gcodeprocessor.Processor
    def load_classes_in_module(self, module_to_load, designator):

        for module_name, obj in inspect.getmembers(module_to_load):

            if inspect.ismodule(obj) and (obj.__name__.startswith('gcodes') or obj.__name__.startswith('redeem.gcodes')):
                self.load_classes_in_module(obj, designator)

            elif inspect.isclass(obj) and issubclass(obj, GCodeCommand) and module_name != 'GCodeCommand' and module_name != 'ToolChange' and obj.__name__.startswith(designator):

                # create the key to sort the classes
                code_name = obj.__name__
                designation = code_name[0]  # G/M/T
                identifier = code_name[1:]  # number

                # since some gcodes have trailing _1,_2,etc let's add _0 so that we can still alphabetize
                if '_' not in identifier:
                    identifier = "{}_0".format(identifier)

                # want to make sure G2 is followed by G3, not G29, so pad with zeros
                if len(identifier):
                    identifier = identifier.zfill(5)

                sortable_key = "{}{}".format(designation, identifier)
                self.gcodes[sortable_key] = obj

    def create_gcode_node(self, gcode):
        gcode_node = GCodeNode()
        gcode_node['gcode'] = gcode

        description = GCodeDescriptionNode()
        description['description'] = gcode.get_description()
        gcode_node += description

        long_description = GCodeLongDescriptionNode()
        long_description['long-description'] = gcode.get_long_description()
        gcode_node += long_description

        return gcode_node

    def create_gcode_entry(self, gcode):

        gcode_node = self.create_gcode_node(gcode)

        section = nodes.section()
        section += nodes.title(type(gcode).__name__, type(gcode).__name__)

        target = nodes.target()
        lineno = self.state_machine.abs_line_number()
        self.state.add_target(type(gcode).__name__, '', target, lineno)

        return [target, section, gcode_node]

    def run(self):
        node_list = []

        self.load_classes_in_module(gcode_module, self.designator)

        for id in sorted(self.gcodes.keys()):
            gcode_cls = self.gcodes[id]

            try:
                node_list += self.create_gcode_entry(gcode_cls(None))
            except AttributeError:
                pass

        return node_list


class MCodeDirective(GCodeDirective):
    designator = 'M'


class TCodeDirective(GCodeDirective):
    designator = 'T'

