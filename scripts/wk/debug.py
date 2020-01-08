"""WizardKit: Debug Functions"""
# pylint: disable=invalid-name
# vim: sts=2 sw=2 ts=2


# Classes
class Debug():
  # pylint: disable=too-few-public-methods
  """Object used when dumping debug data."""
  def method(self):
    """Dummy method used to identify functions vs data."""


# STATIC VARIABLES
DEBUG_CLASS = Debug()
METHOD_TYPE = type(DEBUG_CLASS.method)


# Functions
def generate_object_report(obj, indent=0):
  """Generate debug report for obj, returns list."""
  report = []

  # Dump object data
  for name in dir(obj):
    attr = getattr(obj, name)

    # Skip methods and private attributes
    if isinstance(attr, METHOD_TYPE) or name.startswith('_'):
      continue

    # Add attribute to report (expanded if necessary)
    if isinstance(attr, dict):
      report.append(f'{name}:')
      for key, value in sorted(attr.items()):
        report.append(f'{"  "*(indent+1)}{key}: {str(value)}')
    else:
      report.append(f'{"  "*indent}{name}: {str(attr)}')

  # Done
  return report


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
