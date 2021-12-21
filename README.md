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
$ pip install git+https://github.com/caracalai/caracal.git
```

## Core concepts
### Dataflow conception
In architectures with data flow control, there is no concept of "sequence of instructions", there is no Instruction Pointer. A program in a flow system is not a set of commands, but a computational graph. Each node of the graph represents an operator or a set of operators, and the branches reflect the dependencies of the nodes on the data. The next node starts executing as soon as all its input data is available. This is one of the main principles of dataflow: the execution of instructions for data readiness.

### Node
Node is a minimum executable element. Suppose, you want to calculate the exponent of the number.
```
result = exp(input_value)
```
Such function can be defined in terms of nodes the following way:
```
class Exp(Node):
    result = Event("result", caratypes.Float())

    @handler("input_value", caratypes.Float())
    def input_value(self, msg):
        self.result.fire(exp(msg.value))
```
As you can see, class Exp  is inherited from class Node. We also defined event result.
The Function input_value was decorated by handler. In this case, Caracal will understand that this method is a handler of the node.

### How to execute node
Execution of nodes is performed within sessions. Like here:
```
with Session() as session:
    exp_node = Exp()
    session.run()
```
A session is a place where the node should be executed. All nodes nested within the operator with will be automatically registered within the current session.
After the moment we executed session.run() all nodes instantiated within this session became live. You can consider them as microservices.

### Execution of multiple nodes
Suppose you want to perform several operations.  E.g. something like this:
```
a = exp(x)
b = x + 10
```
Here is how it can be expressed in terms of block:
```
class Exp(Node):
    result = Event("result", caratypes.Float())

    @handler("process", caratypes.Float())
    def process(self, msg):
        self.result.fire(exp(msg.value))

class Increment(Node):
    result = Event("result", caratypes.Float())

    @handler("process", caratypes.Float())
    def process(self, msg):
        self.result.fire(msg.value + 10)

with Session() as session:
    exp_node = Exp()
    increment_node = Increment()
    increment_node.process.connect(exp_node.result)
    session.run()
```

We used ```node.<handler_name>.connect(node.<event_name>)``` method to link the event of one node with a handler of another node. Every time the event is generated, all connected methods will be generated.

### Executing as soon as all inputs has been received

Based on the definition of data flow: "The next node starts executing as soon as all its input data are available", you need to understand how to ensure that all data is received from the nodes connected to the handler in the correct order. For this, we introduced another type of handlers, which we called multiple handler. You can learn more about it in docs, but you can see a conceptual example below:

```
import logging

from caracal.declaration import datatypes
from caracal.execution import Event, handler, Node, Session


class Synchronizer(Node):
    tick = Event("tick", datatypes.Tuple(datatypes.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)


class DoSmth(Node):
    output = Event("output", datatypes.Tuple(datatypes.Int()))

    @handler("input_number", datatypes.Tuple(datatypes.Int()))
    def input_numbers(self, msg):
        self.fire(self.output, msg.value, msg.id)


class Summator(Node):
    def __init__(self):
        super().__init__()
        self.result = 0

    @handler("input_numbers", datatypes.Tuple(datatypes.Object()), True)
    def input_numbers(self, msgs):
        self.result += sum((msg.value for msg in msgs.value))
        if self.result == 15:
            self.terminate()
            logging.critical(self.result)  # expected 15


if __name__ == "__main__":
    with Session() as session:
        synchronizer = Synchronizer()
        action1 = DoSmth(id_="action1")
        action2 = DoSmth(id_="action2")
        result = Summator()

        action1.input_numbers.connect(synchronizer.tick)
        action2.input_number.connect(synchronizer.tick)

        result.input_numbers.connect(action1.output)
        result.input_numbers.connect(action2.output)

        session.run()
```

### Node properties
If you want to parameterize your node, you can define a property. Let's check again our Increment node:

```
class Increment(Node):
    term = Property("term", caratypes.Int(), default_value=10) #  Defining property
    result = Event("result", caratypes.Int())

    @handler("process", caratypes.Float())
    def process(self, msg):
        self.result.fire(msg.value + self.term.value)

with Session() as session:
    increment_node = Increment()
    increment_node.term = 12 #  Changing property value dynamically
    ...
```
The ```term``` attribute is our property with default value ```10```. If you want to define the value of the property at runtime, you can do that within a Session.


## Tests running

```
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
