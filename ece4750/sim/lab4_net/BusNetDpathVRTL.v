`ifndef LAB4_NET_BUS_NET_DPATH_V
`define LAB4_NET_BUS_NET_DPATH_V

`include "vc/net-msgs.v"
`include "vc/queues.v"
`include "vc/buses.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab4_net_BusNetDpathVRTL
#(
  parameter p_payload_nbits = 32
)
(
  input  logic                                         clk,
  input  logic                                         reset,

  input  logic     [c_nports-1:0]                      in_val,
  output logic     [c_nports-1:0]                      in_rdy,
  input  net_hdr_t [c_nports-1:0]                      in_msg_hdr,
  input  logic     [c_nports-1:0][p_payload_nbits-1:0] in_msg_payload,

  output net_hdr_t [c_nports-1:0]                      out_msg_hdr,
  output logic     [c_nports-1:0][p_payload_nbits-1:0] out_msg_payload,

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define additional ports
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  output logic     [c_nports-1:0][1:0]                 inq_dest,
  output logic     [c_nports-1:0]                      inq_val,
  input  logic     [c_nports-1:0]                      inq_rdy,

  input  logic      [c_sel_width-1:0]                  sel
);
  // c_nports included for convenience to avoid having magic numbers, but
  // your design does not need to support other values of c_nports.
  localparam c_nports = 4;
  localparam c_sel_width = $clog2(c_nports);
  localparam num_entries = 2;
  localparam hdr_size = $bits(net_hdr_t);

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement datapath
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // logic [c_nports-1:0][(hdr_size+p_payload_nbits-1):0] deq_out;
  // logic [c_nports-1:0][p_payload_nbits-1:0] bus_in;
  // logic [c_nports-1:0][p_payload_nbits-1:0] bus_out;

  logic [c_nports-1:0][(hdr_size+p_payload_nbits-1):0] bus_in;
  logic [c_nports-1:0][(hdr_size+p_payload_nbits-1):0] bus_out;

  net_hdr_t [c_nports-1:0] inq_hdr;

  genvar i;
  generate
  for ( i = 0; i < c_nports; i = i + 1 ) begin: QUEUE

    // assign bus_in[i] = deq_out[i][p_payload_nbits-1:0];
    // assign out_msg_hdr =
    assign out_msg_hdr[i] = bus_out[i][(hdr_size+p_payload_nbits-1):p_payload_nbits];
    assign out_msg_payload[i] = bus_out[i][p_payload_nbits-1:0];
    assign inq_hdr[i] = bus_in[i][hdr_size+p_payload_nbits-1:p_payload_nbits];
    assign inq_dest[i] = inq_hdr[i].dest;

    vc_Queue #(`VC_QUEUE_NORMAL, (hdr_size+p_payload_nbits), num_entries) queue
    (
      .clk(clk),
      .reset(reset),

      .enq_val(in_val[i]),
      .enq_rdy(in_rdy[i]),
      .enq_msg({
        in_msg_hdr[i].dest,
        in_msg_hdr[i].src,
        in_msg_hdr[i].opaque,
        in_msg_payload[i]
        }),

      .deq_val(inq_val[i]),
      .deq_rdy(inq_rdy[i]),
      .deq_msg(bus_in[i]),
    );

  end
  endgenerate

  vc_Bus #((hdr_size+p_payload_nbits), c_nports) bus
  (
    .sel(sel),
    .in_(bus_in),
    .out(bus_out)
  );


endmodule

`endif /* LAB4_NET_BUS_NET_DPATH_V */
