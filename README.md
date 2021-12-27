<h1 align="center">Caracal -Release Your AI-Powered Products To the Market Faster.  </h1>

<p align="center">
<img align="center" src="https://caracal.ai/img/blocks3.35b077cf.png" alt="Program in Caracal" width="400"/>
</p>
<p align="center"><b>Low-Code framework to make AI prototyping, diagnostics and development faster.</b></p>

<p align="center">
  <a href="https://docs.caracal.ai/">Docs</a>
  |
  <a href="">Join Discord</a>
  |
  <a href="">Newsletter</a>
  |
  <a href="">Blog</a>
  |
  <a href="">Twitter</a>
</p>

## What is it?
Caracal contains
 - <a href="https://app.caracal.ai">WebApp</a> providing funtionality that helps to set up the AI project structure visually.
 - Collection of open-sourced blocks which can be used in your project.
 - Library that helps run project with your own implementation of nodes

## Installing from PyPI
### Windows, MAC OS and Linux
BroutonBlocks is available as a PyPI package. To install it using pip package manager, run:
```sh
pip install git+https://github.com/caracalai/caracal.git
```

## Dataflow conception
In architectures with data flow control, there is no concept of "sequence of instructions", there is no Instruction Pointer. A program in a flow system is not a set of commands, but a computational graph. Each node of the graph represents an operator or a set of operators, and the edges reflect the dependencies of the nodes on the data. The next node starts executing as soon as all its input data is available. This is one of the main principles of dataflow: the execution of instructions for data readiness.
### Node
Node is a minimum executable element. Suppose, you want to calculate the exponent of the number.
```python
result = exp(input_value)
```
Such function can be defined in terms of nodes the following way:
```python
import caracal.declaration.datatypes as caratypes
from caracal.execution import (
    Event,
    handler,
    Node,
)

from math import exp


class Generator(Node):
    value = Event("value", caratypes.Tuple(caratypes.Float()))

    def run(self):
        self.fire(self.value, 0.5)


class Exp(Node):

    @handler("input_value", caratypes.Float())
    def input_value(self, msg):
        print(exp(msg.value))
```
As you can see, the ``Exp`` class inherits from the Node class. We have also determined the outcome of the event. The ``Generator`` class also inherits from the Node class and has an event ``output_value``, which is called when the node is started.
The ``input_value`` function was framed by the handler. In this case, Caracal will understand that this method is a node handler.
### How to Сonnect and Execute Nodes

We used ``node.<handler>.connect(node.<event>)`` method to link the event of one node with a handler of another node. When an event is fired, all the handlers connected to it are executed.
 Execution of nodes is performed within sessions. Like here:
 ```python
from caracal.execution import Session
if __name__ == "__main__":
    with Session() as session:
        gen_node = Generator()
        exp_node = Exp()
        exp_node.input_value.connect(gen_node.value)
        session.run()
```
A session is a place where the node should be executed. All nodes nested within the operator with will be automatically registered within the current session.
After the moment we executed ``session.run()`` all nodes instantiated within this session became live. You can consider them as microservices.

### Executing as soon as all inputs have been received
Based on the definition of data flow: "The next node starts executing as soon as all its input data are available", you need to understand how to ensure that all data is received from the nodes connected to the handler in the correct order. For this, we introduced another type of handlers, which we called multiple handler. You can learn more about it in the Multiple handler section, but you can see a conceptual example below.
Before starting work, we import the necessary modules:
```python
from caracal.declaration import datatypes
from caracal.execution import Event, handler, Node, Session
```
The node described below is a data generator, for each call to fire(), a message id is requested on the Name Server, this is necessary to maintain the DataFlow concept, the message id is transmitted through subsequent nodes to the endpoint:
```python
class Synchronizer(Node):
    tick = Event("tick", datatypes.Tuple(datatypes.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)
```
The node described below is just an intermediate node that receives the message and passes it on unchanged:
```python
class DoSmth(Node):
    output = Event("output", datatypes.Tuple(datatypes.Int()))

    @handler("input_number", datatypes.Tuple(datatypes.Int()))
    def input_numbers(self, msg):
        # The third argument is passed message id
        self.fire(self.output, msg.value, msg.id)
```
In the node described below, multiple handler is used, it aggregates all incoming messages into tuple, only messages with the same message id are combined (this ensures that the received messages were created based on the same generator data), if one of the nodes missed a message with a certain id, then messages with a missed id from other nodes are discarded. In tuple, messages are added in the order of event connection.
```python
class Summator(Node):
    def __init__(self):
        super().__init__()
        self.result = 0

    @handler("input_numbers", datatypes.Tuple(datatypes.Object()), receives_multiple=True)
    def input_numbers(self, msgs):
        self.result += sum((msg.value for msg in msgs.value))
        if self.result == 15:
            self.terminate()
            print(self.result)  # expected 15
```
To run the pipeline, write the following code:
```python
if __name__ == "__main__":
    with Session() as session:
        synchronizer = Synchronizer()
        action1 = DoSmth(id_="action1")
        action2 = DoSmth(id_="action2")
        result = Summator()

        action1.input_numbers.connect(synchronizer.tick)
        action2.input_numbers.connect(synchronizer.tick)

        result.input_numbers.connect(action1.output)
        result.input_numbers.connect(action2.output)

        session.run()
```
## Tests running

```python
python -m unittest discover --verbose
```

## Contributing
### Steps to make a pull request
- Create a personal fork of the project on Github.
- Setup environment and install requirements.
- Run ```pip install -r requirements_dev.txt ```.
- Run ``` pre-commit install ``` to set up the git hook scripts.
- Implement/fix you feature, comment your code.
- Write/adapt tests as needed.
- Write/adapt the documentation as needed.
- Open a pull request from your fork in the correct branch.



Made with :heart: by founders of <a href="https://broutonlab.com">BroutonLab</a>.
