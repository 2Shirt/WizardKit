"""WizardKit: Config - Windows Builds"""
# vim: sts=2 sw=2 ts=2


OLDEST_SUPPORTED_BUILD = 19041 # Windows 10 20H1
OUTDATED_BUILD_NUMBERS = (
  9600,   # Windows 8.1 Update
  18363,  # Windows 10 19H2
  )
WINDOWS_BUILDS = {
  # Windows 7
  '6.1.7600':   'RTM "Vienna"',
  '6.1.7601':   'SP1 "Vienna"',

  # Windows 8
  '6.2.9200':   'RTM',

  # Widnows 8.1
  '6.3.9200':   '"Blue"',
  '6.3.9600':   '"Update"',

  # Windows 10
  '10.0.10240': '1507 "Threshold 1"',
  '10.0.10586': '1511 "Threshold 2"',
  '10.0.14393': '1607 "Redstone 1"',
  '10.0.15063': '1703 "Redstone 2"',
  '10.0.16299': '1709 "Redstone 3"',
  '10.0.17134': '1803 "Redstone 4"',
  '10.0.17763': '1809 "Redstone 5"',
  '10.0.18362': '1903 / 19H1',
  '10.0.18363': '1909 / 19H2',
  '10.0.19041': '2004 / 20H1',
  '10.0.19042': '20H2',
  '10.0.19043': '21H1',
  '10.0.19044': '21H2',
}
