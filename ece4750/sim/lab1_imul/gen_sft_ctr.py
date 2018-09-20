#! /usr/bin/env python2

from argparse import ArgumentParser

header="""
//=========================================================================
// Integer Multiplier Shift Counter
//=========================================================================

`ifndef LAB1_IMUL_INT_MUL_SFT_CTR_V
`define LAB1_IMUL_INT_MUL_SFT_CTR_V

`include "vc/trace.v"

//=========================================================================
// Integer Multiplier Shift Counter Implementation
//=========================================================================

module lab1_imul_IntMulSftCtrVRT
(
  input  logic [31:0] val,
  output logic [4:0] sft 
);

  always_comb begin
"""

footer="""
  end 

endmodule

`endif /* LAB1_IMUL_INT_MUL_SFT_CTR_V */
"""

if __name__ == '__main__':
  parser = ArgumentParser(description='generates IntMulSftCtr.v with the specified number of skips and optional short circuiting')
  parser.add_argument('skips', help='number of skips')
  parser.add_argument('-c', '--short-circuit', help='include short circuit logic', action='store_true')
  args = parser.parse_args()
  
  result = []
  if args.short_circuit:
    result += ['if (val == 32\'b0 || val == 32\'b1) sft = 5\'d0;']
  for i in range(1, int(args.skips) + 1):
    result += ['if (val[{}] == 1\'b1) sft = 5\'d{};'.format(i, i)]
  result += ['sft = 5\'d{};'.format(int(args.skips) + 1)]
  ladder = '\n'.join(['    {}'.format(x) for x in '\nelse '.join(result).split('\n')])
  print(header + ladder + footer)
