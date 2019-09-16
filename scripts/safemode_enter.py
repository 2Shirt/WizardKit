"""Wizard Kit: Enter SafeMode by editing the BCD"""
# vim: sts=2 sw=2 ts=2

import wk


def main():
  """Prompt user to enter safe mode."""
  title = f'{wk.cfg.main.KIT_NAME_FULL}: SafeMode Tool'
  try_print = wk.std.TryAndPrint()
  wk.std.clear_screen()
  wk.std.set_title(title)
  wk.std.print_info(title)
  print('')

  # Ask
  if not wk.std.ask('Enable booting to SafeMode (with Networking)?'):
    wk.std.abort()
  print('')

  # Configure SafeMode
  try_print.run('Set BCD option...', wk.os.win.enable_safemode)
  try_print.run('Enable MSI in SafeMode...', wk.os.win.enable_safemode_msi)

  # Done
  print('Done.')
  wk.std.pause('Press Enter to reboot...')
  wk.std.run_program('shutdown -r -t 3'.split(), check=False)


if __name__ == '__main__':
  try:
    main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
