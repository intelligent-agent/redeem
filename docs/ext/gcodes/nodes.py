import copy
from docutils import nodes


# G CODE NODE ####################
from docutils.core import publish_parts
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
    self.body.append(node['raw'])
    self.body.append("</div>")


def gcode_description_node_depart(self, node):
    pass


# GCODE LONG DESCRIPTION NODE #############
class GCodeLongDescriptionNode(nodes.General, nodes.Element):
    pass


def gcode_long_description_node_visit(self, node):
    self.body.append("<div class='col-xs-8'>")

    lines = node['raw'].split('\n')

    template = Template("""
        {% for line in lines %}
        <p>{{ line }}</p>
        {% endfor %}
    """)

    self.body.append(template.render({'lines': lines}))


    self.body.append("</div>")


def gcode_long_description_node_depart(self, node):
    pass


# GCODE FORMATTED DESCRIPTION NODE #########
class GCodeFormattedDescriptionNode(nodes.General, nodes.Element):
    pass


def gcode_formatted_description_node_visit(self, node):
    self.body.append("<div class='col-xs-8'>")

    # doesn't seem the directive which instantiates this node gets the full set of settings
    # add the necessary ones that the rst admonition parser relies on
    settings = copy.copy(node.document.settings)

    settings.traceback = True
    settings.tab_width = 4
    settings.pep_references = False
    settings.rfc_references = False
    settings.smartquotes_locales = None
    settings.env.temp_data['docname'] = 'gcodes'
    settings.language_code = 'en'

    # since we're using docutils directly, it doesn't support '.. versionadded::' directive
    # patch the language file so it displays correctly
    import docutils
    docutils.languages.en.labels['versionmodified'] = 'New in Version'

    published = publish_parts(node['raw'], writer_name='html', settings=settings)['html_body']
    self.body.append(published)

    self.body.append("</div>")


def gcode_formatted_description_node_depart(self, node):
    pass
