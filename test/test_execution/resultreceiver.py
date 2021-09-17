from bblocks.execution.node import *
from bblocks.declaration.graph import *

class ResultReceiver:
    def __init__(self, addr):
        self.ctx = zmq.Context()
        self.addr = addr
        self.sock = self.ctx.socket(zmq.REP)
        self.port = self.sock.bind_to_random_port(addr)

    def wait_results(self):
        return json.loads(self.sock.recv().decode("utf-8"))

    @property
    def endpoint(self):
        return "{endpoint}:{port}".format(endpoint=self.addr, port=self.port)