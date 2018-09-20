
//=========================================================================
// Integer Multiplier Sbits Counter
//=========================================================================

`ifndef LAB1_IMUL_INT_MUL_ONES_CTR_V
`define LAB1_IMUL_INT_MUL_ONES_CTR_V

`include "vc/trace.v"

//=========================================================================
// Integer Multiplier Shift Counter Implementation
//=========================================================================

module lab1_imul_IntMulOnesCtrVRTL
(
    input  logic [31:0] v,
    output logic [5:0] count
);
    // Note: by doing this in groups of two, everything can happen in parallel
    // So there is only logbase2(32)=5 back to back adders on critical path
    // These adders are only 2 bit, 3 bit, 4 bit and 5 bit, and 6 bit adders,
    // So they should not affect the critical path

    // This would be a lot easier if you would let us use forloops,
    // So i dont have to unroll the loop myself... :(
    assign count =
        {1'b0, ({1'b0, (( {1'b0, ({1'b0, v[0]} + {1'b0, v[1]})} + {1'b0, ({1'b0, v[2]} + {1'b0, v[3]})} ) +
            ({1'b0, ({1'b0, v[4]} + {1'b0, v[5]})} + {1'b0, ({1'b0, v[6]} + {1'b0, v[7]})} ))}

            + {1'b0, (( {1'b0, ({1'b0, v[8]} + {1'b0, v[9]})} + {1'b0, ({1'b0, v[10]} + {1'b0, v[11]})} ) +
            ({1'b0, ({1'b0, v[12]} + {1'b0, v[13]})}+ {1'b0, ({1'b0, v[14]} + {1'b0, v[15]})}))})}

            + {1'b0, ({1'b0, (( {1'b0, ({1'b0, v[16]} + {1'b0, v[17]})} + {1'b0, ({1'b0, v[18]} + {1'b0, v[19]})} ) +
                ({1'b0, ({1'b0, v[20]} + {1'b0, v[21]})} + {1'b0, ({1'b0, v[22]} + {1'b0, v[23]})} ))}

                + {1'b0, (( {1'b0, ({1'b0, v[24]} + {1'b0, v[25]})} + {1'b0, ({1'b0, v[26]} + {1'b0, v[27]})} ) +
                ({1'b0, ({1'b0, v[27]} + {1'b0, v[29]})}+ {1'b0, ({1'b0, v[30]} + {1'b0, v[31]})}))})};
endmodule

`endif /* LAB1_IMUL_INT_MUL_SFT_CTR_V */
