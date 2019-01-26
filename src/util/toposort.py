# Modified from: https://pypi.org/project/toposort/
from functools import reduce


class CircularDependencyError(ValueError):

  def __init__(self, data):
    s = 'No toposort exists due to a cycle: {}'.format(', '.join(
        '{!r}:{!r}'.format(key, value) for key, value in sorted(data.items())))
    super(CircularDependencyError, self).__init__(s)


def toposort(data):
  """Returns a toposort of a graph, or raises an exception if not possible.
  
  The graph is expressed as a dictionary. A directed edge from i to j exists
  if i in data and j in data[i].
  
  Item i is dependent on item j if there exists a directed path from j 
  to i in the graph.

  Output is a list of items, in topological order. Precisely, if item
  i is at index a in the output, and item j is at index b (where i != j
  and a != b), then if b < a, there exists no directed path in the graph
  from i to j. Simply, the least dependent items are first and the
  most dependent items are last. Note that given a graph, there may
  be many orderings which satisfy the above requirement. The ordering
  output by this algorithm is unspecified.
  """

  if len(data) == 0:
    return []

  data = data.copy()

  # Find all items that don't depend on anything.
  extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
  # Add empty dependences where needed.
  data.update({item: set() for item in extra_items_in_deps})
  groups = []
  while True:
    ordered = set(item for item, dep in data.items() if len(dep) == 0)
    if not ordered:
      break
    groups.append(ordered)
    data = {
        item: (dep - ordered)
        for item, dep in data.items()
        if item not in ordered
    }

  if len(data) != 0:
    raise CircularDependencyError(data)

  result = []
  for d in groups:
    result.extend(sorted(d))
  return result


if __name__ == '__main__':
  graph = {'a': {'b', 'c'}, 'b': {'d'}, 'c': {'d'}, 'd': {'e'}, 'e': {}}

  print(toposort(graph))

  bad = {
      'a': {'b', 'c'},
      'b': {'d'},
      'c': {'d'},
      'd': {'e'},
      'e': {},
      'f': {'g'},
      'g': {'f'},
  }
  print(toposort(bad))
