"""Wizard Kit: Check, and possibly repair, system file health via SFC"""
# vim: sts=2 sw=2 ts=2

import wk


def main():
  """Run SFC and report result."""
  title = f'{wk.cfg.main.KIT_NAME_FULL}: SFC Tool'
  try_print = wk.std.TryAndPrint()
  wk.std.clear_screen()
  wk.std.set_title(title)
  wk.std.print_info(title)
  print('')

  # Ask
  if not wk.std.ask('Run a SFC scan now?'):
    wk.std.abort()
  print('')

  # Run
  try_print.run('SFC scan...', wk.os.win.run_sfc_scan)

  # Done
  print('Done')
  wk.std.pause('Press Enter to exit...')


if __name__ == '__main__':
  try:
    main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
