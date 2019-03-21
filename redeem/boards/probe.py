import replicape
import revolve


def probe_all_boards(printer):
  replicape.probe_replicape(printer)
  if hasattr(printer, "board"):
    return

  revolve.probe_revolve(printer)
