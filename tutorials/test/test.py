from broutonblocks.execution import Property, Node, Session, Event, handler
import broutonblocks.declaration.datatypes as bbtypes


class Summator(Node):
    prop1 = Property(bbtypes.Int(), default_value=1, optional=True)
    event1 = Event("event1", bbtypes.List(bbtypes.Int()))

    @handler("value", bbtypes.Int())
    def handle(self, msg):
        self.fire(self.result, msg.value)


if __name__ == "__main__":
    with Session(name="default", serves_server=False, server_port=2001) as session:
        s = Summator()
        print(s.prop1)  # prints None
        print(s.event1)
        s.prop1 = 5
        print(s.prop1)  # prints 5
        print(Summator.prop1)
        # print(s.value)
        print(s.handlers)
