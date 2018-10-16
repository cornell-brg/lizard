from pytml import *
from msg import MemMsg4B
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import *
from core.dataflow.fl import DataFlowUnitFL
from core.fetch.fl import FetchFL
from core.dispatch.fl import DispatchFL
from core.issue.fl import IssueFL
from core.functional.fl import FunctionalFL
from core.result.fl import ResultFL
from core.commit.fl import CommitFL


class CoreFL(Model):
    def __init__(s):
        s.mem_req = OutValRdyBundle(MemMsg4B.req)
        s.mem_resp = InValRdyBundle(MemMsg4B.resp)

        s.mngr2proc = InValRdyBundle(Bits(XLEN))
        s.proc2mngr = OutValRdyBundle(Bits(XLEN))

        s.dataflow = DataFlowUnitFL()
        s.fetch = FetchFL()
        s.dispatch = DispatchFL()
        s.issue = IssueFL(dataflow)
        s.functional = FunctionalFL(dataflow)
        s.result = ResultFL(dataflow)
        s.commit = CommitFL(dataflow)

        s.connect(s.mngr2proc, s.dataflow.mngr2proc)
        s.connect(s.proc2mngr, s.dataflow.proc2mngr)

        s.connect(s.mem_req, s.fetch.mem_req)
        s.connect(s.mem_resp, s.fetch.mem_resp)
        s.connect(s.fetch.instrs, s.dispatch.instr)
        s.connect(s.dispatch.decoded, s.issue.decoded)
        s.connect(s.issue.issued, s.functional.issued)
        s.connect(s.functional.result, s.result.result_in)
        s.connect(s.result.result_out, s.commit.result_in)
