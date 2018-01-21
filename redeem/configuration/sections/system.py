from redeem.configuration.sections import BaseConfig


class SystemConfig(BaseConfig):

    loglevel = 20  # CRITICAL=50, # ERROR=40, # WARNING=30,  INFO=20,  DEBUG=10, NOTSET=0
    log_to_file = True
    logfile = '/home/octo/.octoprint/logs/plugin_redeem.log'
    data_path = "/etc/redeem"  # location to look for data files (temperature charts, etc)
    plugins = ''  # Plugin to load for redeem, comma separated (i.e. HPX2Max,plugin2,plugin3)
    machine_type = 'Unknown'  # Machine type is used by M115 to identify the machine connected.
