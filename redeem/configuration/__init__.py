from ConfigParser import SafeConfigParser

from redeem.configuration.factories.ConfigFactoryV19 import ConfigFactoryV19
from redeem.configuration.factories.ConfigFactoryV20 import ConfigFactoryV20


def get_config_factory(config_files):

    config_parser = SafeConfigParser()
    config_parser.read(config_files)

    version = None
    if config_parser.has_option('System', 'version'):
        version = config_parser.get('System', 'version')

    factory = ConfigFactoryV19()
    if version == 2.0:
        factory = ConfigFactoryV20()

    return factory
