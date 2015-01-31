"""
Plugin loading system for having custom behaviour of custom hardware
for printers


Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import inspect
import logging
import re
import importlib
from plugins import AbstractPlugin


class PluginsController:
    def __init__(self, printer):
        self.printer = printer

        self.plugins = {}

        # Load the plugins specified by the config
        pluginsToLoad = [v.strip() for v in self.printer.config.get('System', 'plugins', '').split(',')]
        pluginClasses = PluginsController.get_plugin_classes()

        for plugin in pluginsToLoad:
            if plugin == '':
                continue

            pluginClassName = plugin+'Plugin'

            if  pluginClassName in pluginClasses:
                pluginInstance = pluginClasses[pluginClassName](self.printer)
                self.plugins[plugin] = pluginInstance
            else:
                logging.error('Unable to find plugin \''+plugin+'\'. This plugin won\'t be loaded.')

    def path_planner_initialized(self, path_planner):
        """ Hook method called when the path planner has been initalized """
        for pluginName in self.plugins:
            self.plugins[pluginName].path_planner_initialized(path_planner)

    def exit(self):
        """ Shutdown all plugins for exiting Redeem """
        for pluginName in self.plugins:
            self.plugins[pluginName].exit()

    def get_plugin(self, pluginName):
        """ Return the plugin loaded instance named pluginName """
        return self.plugins[pluginName]

    def __getitem__(self, pluginName):
        """ Return the plugin loaded instance named pluginName """
        return self.plugins[pluginName]

    @staticmethod
    def get_plugin_classes():
        try:
            module = __import__("plugins", locals(), globals())
        except ImportError: 
            module = importlib.import_module("redeem.plugins")

        pluginClasses = {}

        PluginsController.load_classes_in_module(module, pluginClasses)
        return pluginClasses

    @staticmethod
    def load_classes_in_module(module, classes):
        for module_name, obj in inspect.getmembers(module):
            if inspect.ismodule(obj) and (obj.__name__.startswith('plugins')
                or obj.__name__.startswith('redeem.plugins')):
                PluginsController.load_classes_in_module(obj, classes)
            elif inspect.isclass(obj) and \
                    issubclass(obj, AbstractPlugin.AbstractPlugin) and \
                    module_name != 'AbstractPlugin':
                classes[module_name] = obj

    @staticmethod
    def get_supported_plugins_and_description():

        plugins = PluginsController.get_plugin_classes()

        ret = {}
        for pluginName in plugins:
            plugin = plugins[pluginName]

            ret[pluginName] = plugin.get_description()

        return ret


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    print "Available plugins:"

    descriptions = PluginsController.get_supported_plugins_and_description()

    def _natural_key(string_):
        """See http://www.codinghorror.com/blog/archives/001018.html"""
        return [int(s) if s.isdigit() else
                s for s in re.split(r'(\d+)', string_)]

    for name in sorted(descriptions, key=_natural_key):
        print name + "\t\t" + descriptions[name]
