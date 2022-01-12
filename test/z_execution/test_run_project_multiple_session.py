import logging
import multiprocessing
import unittest

from caracal import (
    cara_types,
    Event,
    ExternalEvent,
    handler,
    Node,
    ProjectInfo,
    Property,
    Session,
)


class TicksGen(Node):
    tick = Event("tick", cara_types.Tuple(cara_types.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)


class DoSmth(Node):
    output = Event("output", cara_types.Tuple(cara_types.Int()))

    @handler("input_numbers", cara_types.Tuple(cara_types.Int()))
    def input_numbers(self, msg):
        self.fire(self.output, msg.value, msg.id)


class DoSmthWithErr(Node):
    output = Event("output", cara_types.Tuple(cara_types.Int()))

    @handler("input_numbers", cara_types.Tuple(cara_types.Int()))
    def input_numbers(self, msg):
        if msg.value not in [2, 3]:
            self.fire(self.output, msg.value, msg.id)


class Summat(Node):
    result = Property(
        cara_types.Int(),
        default_value=0,
    )

    @handler("input_numbers", cara_types.Tuple(cara_types.Object()), True)
    def input_numbers(self, msgs):
        print(f"{self.__class__.__name__} received")
        self.result += sum((msg.value for msg in msgs.value))
        if self.result == 15:
            print(self.result)
            self.terminate()


port = 2001
sours_code = """
    @namespace(name="global")
    node TicksGen:
        events:
            tick(value1: int)

    @namespace(name="global")
    node DoSmth:
        handlers:
            input_numbers(value1: int)
        events:
            output(value1: int)

    @namespace(name="global")
    node DoSmthWithErr:
        handlers:
            input_numbers(value1: int)
        events:
            output(value1: int)

    @namespace(name="global")
    node Summat:
        properties:
            result: int(0)
        handlers:
            input_numbers+(value1: object)
    """


def first_worker(project):
    with Session(
        name="first", server_port=port, external_nodes=["summator", "action_3"]
    ) as session:
        session.register_types([TicksGen, DoSmth, DoSmthWithErr])

        session.run_project(project)


def second_worker(return_dict, project):
    with Session(name="second", server_port=2001, serves_server=False) as session:
        session.register_types([DoSmth, Summat])

        session.run_project(project)

    return_dict["result"] = session.nodes["summator"].result


class RunProjectMultipleHandlers(unittest.TestCase):
    def test_run_project_multiple_handler_without_evt_id(self):
        # logging.basicConfig(level=logging.DEBUG)
        project = ProjectInfo()
        (
            tick_gen_type,
            do_smth_type,
            do_smth_with_error_type,
            summat_type,
        ) = project.parse_node_types_from_declaration(sours_code)

        sesion_info_1 = project.create_session("first")
        sesion_info_2 = project.create_session("second")

        gen = project.create_node(tick_gen_type, sesion_info_1)
        gen.set_uid("gen")

        action_1 = project.create_node(do_smth_type, sesion_info_1)
        action_1.set_uid("action_1")

        action_2 = project.create_node(do_smth_with_error_type, sesion_info_1)
        action_2.set_uid("action_2")

        action_3 = project.create_node(do_smth_type, sesion_info_2)
        action_3.set_uid("action_3")

        summat = project.create_node(summat_type, sesion_info_2)
        summat.set_uid("summator")

        project.connect(gen, "tick", action_1, "input_numbers")
        project.connect(gen, "tick", action_2, "input_numbers")
        project.connect(gen, "tick", action_3, "input_numbers")

        project.connect(action_1, "output", summat, "input_numbers")
        project.connect(action_2, "output", summat, "input_numbers")
        project.connect(action_3, "output", summat, "input_numbers")

        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        worker1 = multiprocessing.Process(target=first_worker, args=(project,))
        worker1.start()

        worker2 = multiprocessing.Process(
            target=second_worker, args=(return_dict, project)
        )
        worker2.start()

        worker1.join()
        worker2.join()

        self.assertEqual(return_dict["result"], 15)
