import os
import stat
from configobj import ConfigObj
from redeem.configuration import ConfigurationFileList
from redeem.exceptions import UNIDENTIFIED_HARDWARE
import redeem.configuration as TheSystem

def get_hardware_devices():
  from redeem import HAL
  from factory import boards as the_boards

  from importlib import import_module

  print("List Boards")
  for board in the_boards:
    try:
      import factory
      # from factory.<board> import <board>_<revision> as board_class
      board_module = getattr(factory, "{}".format(board[0]))
    except:
      raise UNIDENTIFIED_HARDWARE("No {} board implementation found".format(board[0]))
    ConfigurationFileList.append(system_cf(board[0]))
    ConfigurationFileList.append(factory.local_cf(board[0]))
    try:
      if (len(board) > 2):
        board_class_name = "{}_{}".format(board[0], board[2])
      else:
        board_class_name = "{}_{}".format(board[0], board[1])
      board_class = getattr(board_module, board_class_name)
      ConfigurationFileList.append(system_cf(board_class_name))
      ConfigurationFileList.append(factory.local_cf(board_class_name))
    except:
      raise UNIDENTIFIED_HARDWARE("No revision {} of {} board found".format(board[1], board[0]))
    board_class("X")


def system_cf(x):
  the_file = os.path.normpath(
      os.path.join(os.path.dirname(__file__), '..', '..', 'configs', '{}.conf'.format(x))
  )
  return the_file


def standard_configuration():
  print("Start Standard Configuration")
  try:
    try:
      printer = ConfigObj(factory.local_cf('local'))['Configuration']['printer']
    except:
      printer = ConfigObj('/usr/local/etc/Select_A_Service.conf')['redeem']['printer']
      TheSystem.CurrentSettings().put('Software', 'selectable', True)
  except:
    printer = 'NoPrinter'
  TheSystem.CurrentSettings().put('Software', 'printer', printer)
  configuration_files = ConfigurationFileList
  configuration_files.clear()
  configuration_files.append(system_cf('system'))
  get_hardware_devices()
  configuration_files.append(system_cf(printer))
  import factory
  configuration_files.append(factory.local_cf(printer))
  filepath = factory.local_cf('local')
  if not os.path.exists(filepath):
    with open(filepath, "w") as file:
      print("{} does not exist, Creating it".format(filepath))
  configuration_files.append(factory.local_cf('local'))
  print("List of configuration_files:")
  for fn_cfg in configuration_files:
    print(fn_cfg)
    overrides = ConfigObj(fn_cfg)
    TheSystem.CurrentSettings().merge(overrides)
    TheSystem.LocalizedSettings().set_config_directory(factory.local_cf('local'))
