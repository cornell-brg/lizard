from model.hardware_model import HardwareModel


class CLModel(HardwareModel):

  def __init__(s, interface):
    super(CLModel, s).__init__(interface)

    s.methods = s.interface.methods.values()
    s.index_map = {methods[i].name: i for i in s.methods}

  def _pre_call(func, method):
    index = s.index_map[func.__name__]
    # if the method was a prior method
    if index < s.sequence_method:
      raise ValueError('Illegal method order: {} called after {}'.format(
          func.__name__, s.methods[s.sequence_method].name))
    # if same method ensure it has calls left
    elif index == s.sequence_method:
      limit = s.methods[s.sequence_method].num_permitted_calls()
      if s.sequence_call >= limit:
        raise ValueError('Too many calls on method: {} limit: {}'.format(
            s.methods[s.sequence_method].name, limit))
    else:
      # a future method has been called
      # advance to it, calling any methods without a call
      # signal in between
      s._drain_to(index)

    # call this method
    s.sequence_call += 1

  def _pre_cycle(s):
    # initialize to the first method in the interface
    s.sequence_method = 0
    # initialize to 0 calls of that method
    s.sequence_call = 0

  def _post_cycle(s):
    # drain all remaining methods
    s._drain_to(len(s.methods))

  def _drain_to(index):
    while s.sequence_method < index:
      current_method = s.methods[s.sequence_method]
      if not current_method.call:
        # Default all the arguments to 0
        arg_dict = {}
        for name, pymtl_type in current_method.args.iteritems():
          arg_dict[name] = _gen_zero(pymtl_type)
        for call in range(s.sequence_call,
                          current_method.num_permitted_calls()):
          # invoke the method
          s.model_methods[current_method.name](**arg_dict)
      s.sequence_method += 1
      s.sequence_call = 0
