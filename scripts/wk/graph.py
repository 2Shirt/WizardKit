"""WizardKit: Graph Functions"""
# pylint: disable=bad-whitespace
# vim: sts=2 sw=2 ts=2

import logging

from wk.std import color_string


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
ALT_TEST_SIZE_FACTOR = 0.01
BLOCK_SIZE = 512 * 1024
CHUNK_SIZE = 32 * 1024**2
GRAPH_HORIZONTAL = ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█')
GRAPH_WIDTH = 40
GRAPH_VERTICAL = (
    '▏',    '▎',    '▍',    '▌',
    '▋',    '▊',    '▉',    '█',
    '█▏',   '█▎',   '█▍',   '█▌',
    '█▋',   '█▊',   '█▉',   '██',
    '██▏',  '██▎',  '██▍',  '██▌',
    '██▋',  '██▊',  '██▉',  '███',
    '███▏', '███▎', '███▍', '███▌',
    '███▋', '███▊', '███▉', '████',
  )
MINIMUM_TEST_SIZE = 10 * 1024**3
# SCALE_STEPS: These scales allow showing differences between HDDs and SSDs
#              on the same graph.
SCALE_STEPS = {
  8:  [2**(0.56*(x+1))+(16*(x+1)) for x in range(8)],
  16: [2**(0.56*(x+1))+(16*(x+1)) for x in range(16)],
  32: [2**(0.56*(x+1)/2)+(16*(x+1)/2) for x in range(32)],
  }
# THRESHOLDS: These are the rate_list (in MB/s) used to color graphs
THRESH_FAIL =          65 * 1024**2
THRESH_WARN =         135 * 1024**2
THRESH_GREAT =        750 * 1024**2


# Functions
def generate_horizontal_graph(rate_list, oneline=False):
  """Generate horizontal graph from rate_list, returns list."""
  graph = ['', '', '', '']
  scale = 8 if oneline else 32

  # Build graph
  for rate in merge_rates(rate_list):
    step = get_graph_step(rate, scale=scale)

    # Set color
    rate_color = None
    if rate < THRESH_FAIL:
      rate_color = 'RED'
    elif rate < THRESH_WARN:
      rate_color = 'YELLOW'
    elif rate > THRESH_GREAT:
      rate_color = 'GREEN'

    # Build graph
    full_block = color_string((GRAPH_HORIZONTAL[-1],), (rate_color,))
    if step >= 24:
      graph[0] += color_string((GRAPH_HORIZONTAL[step-24],), (rate_color,))
      graph[1] += full_block
      graph[2] += full_block
      graph[3] += full_block
    elif step >= 16:
      graph[0] += ' '
      graph[1] += color_string((GRAPH_HORIZONTAL[step-16],), (rate_color,))
      graph[2] += full_block
      graph[3] += full_block
    elif step >= 8:
      graph[0] += ' '
      graph[1] += ' '
      graph[2] += color_string((GRAPH_HORIZONTAL[step-8],), (rate_color,))
      graph[3] += full_block
    else:
      graph[0] += ' '
      graph[1] += ' '
      graph[2] += ' '
      graph[3] += color_string((GRAPH_HORIZONTAL[step],), (rate_color,))

  # Done
  if oneline:
    graph = graph[-1:]
  return graph


def get_graph_step(rate, scale=16):
  """Get graph step based on rate and scale, returns int."""
  rate_in_mb = rate / (1024**2)
  step = 0

  # Iterate over scale_steps backwards
  for _r in range(scale-1, -1, -1):
    if rate_in_mb >= SCALE_STEPS[scale][_r]:
      step = _r
      break

  # Done
  return step


def merge_rates(rates, graph_width=GRAPH_WIDTH):
  """Merge rates to have entries equal to the width, returns list."""
  merged_rates = []
  offset = 0
  slice_width = int(len(rates) / graph_width)

  # Merge rates
  for _i in range(graph_width):
    merged_rates.append(sum(rates[offset:offset+slice_width])/slice_width)
    offset += slice_width

  # Done
  return merged_rates


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
