"""Wizard Kit: Check or repair the %SYSTEMDRIVE% filesystem via CHKDSK"""
# vim: sts=2 sw=2 ts=2

import os
import wk


def main():
  """Run or schedule CHKDSK and show result."""
  menu = wk.std.Menu(title=title)
  title = f'{wk.cfg.main.KIT_NAME_FULL}: Check Disk Tool'
  try_print = wk.std.TryAndPrint()
  wk.std.clear_screen()
  wk.std.set_title(title)
  print('')

  # Add menu entries
  menu.add_option('Offline scan')
  menu.add_option('Online scan')

  # Show menu and make selection
  selection = menu.simple_select()

  # Run or schedule scan
  if 'Offline' in selection[0]:
    function = wk.os.win.run_chkdsk_offline
    msg_good = 'Scheduled'
  else:
    function = wk.os.win.run_chkdsk_online
    msg_good = 'No issues detected'
  try_print.run(f'CHKDSK (
    message={os.environ.get("SYSTEMDRIVE})...',
    function=function,
    msg_good=msg_good,
    )

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
