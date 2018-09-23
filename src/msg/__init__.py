import msg.mem
import config.general
import config.mem

MemMsg4B = MemMsg(config.mem.OPAQUE_SIZE, config.general.XLEN, 32)
MemMsg8B = MemMsg(config.mem.OPAQUE_SIZE, config.general.XLEN, 64)
MemMsg16B = MemMsg(config.mem.OPAQUE_SIZE, config.general.XLEN, 128)
