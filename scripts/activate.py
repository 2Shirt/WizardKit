"""Wizard Kit: Activate Windows using a BIOS key"""
# vim: sts=2 sw=2 ts=2

import wk


def main():
  """Attempt to activate Windows and show result."""
  title = f'{wk.cfg.main.KIT_NAME_FULL}: Activation Tool'
  try_print = wk.std.TryAndPrint()
  wk.std.clear_screen()
  wk.std.set_title(title)
  wk.std.print_info(title)
  print('')

  # Attempt activation
  try_print.run('Attempting activation...', wk.os.win.activate_with_bios)

  # Done
  print('')
  print('Done.')
  wk.std.pause('Press Enter to exit...')


if __name__ == '__main__':
  try:
    main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
