# Enterprise Worm Defense Dashboard

An interactive educational project that demonstrates how Data Structures and Algorithms can be used to protect a computer network from worm or malware infection.

The application represents a network as a graph, simulates infection spreading between connected nodes, and compares different algorithms for selecting nodes to patch under a limited budget.

## Features

- Interactive 2D network visualization.
- Random network with 15 nodes and a small number of connections.
- Custom network creation with user-defined nodes and edges.
- Custom patching budget.
- Node labels showing ID, patch cost, and vulnerability:

  ```text
  N0 C5 V2
  ```

  - `N` = Node ID
  - `C` = Patch cost
  - `V` = Vulnerability

- Worm infection simulation starting from Node 0.
- Zoom in, zoom out, reset zoom, and mouse-wheel zooming.
- Step-by-step pages for every algorithm.
- Previous Step and Next Step navigation.
- Dynamic explanations based on the selected network and current node.
- Performance comparison using execution time, memory, budget usage, and risk reduction.

## Project Objective

The objective is to reduce network risk by selecting important nodes for patching while staying within a limited budget.

The risk reduction of a node is calculated as:

```text
Risk Reduction = Vulnerability × Degree
```

The degree is the number of connections a node has. A highly vulnerable and highly connected node usually provides more risk reduction when patched.

## Network and Infection Simulation

The network is represented as a graph:

- Nodes represent computers or devices.
- Edges represent connections between devices.
- Each node has a vulnerability score, patch cost, and degree.

Node 0 is initially infected and acts as Patient Zero. During each simulation step, infected nodes check their neighbors. A healthy neighbor may become infected according to:

```text
Infection Probability = Beta × Vulnerability / 10
```

The dashboard uses a default beta value of `0.85`.

Node colors represent their current state:

- **White:** Healthy
- **Red:** Infected
- **Green:** Patched or selected for patching

## Algorithms

### Greedy Algorithm

The Greedy algorithm calculates:

```text
Priority Ratio = Risk Reduction / Patch Cost
```

It sorts nodes by priority ratio and selects the best affordable nodes first.

The Greedy algorithm is fast and uses little memory, but it is a heuristic and is not guaranteed to find the globally optimal solution.

### Divide and Conquer

The Divide and Conquer approach:

1. Divides the nodes into smaller groups.
2. Recursively processes each group.
3. Solves groups of four or fewer nodes directly.
4. Combines the selected nodes from the smaller groups.

This demonstrates the Divide, Solve, and Combine strategy. The current implementation is a heuristic because it divides the budget between groups and is not guaranteed to produce the globally optimal selection.

### Dynamic Programming

The Dynamic Programming algorithm uses a 0/1 Knapsack-style table.

For every node and budget amount, it compares:

- The best result without selecting the node.
- The result after selecting the node, if its cost fits.

The table stores the highest possible risk reduction. Under the project’s additive risk model, this method produces the optimal budget-constrained selection.

## Step-by-Step Algorithm Pages

Each algorithm has a dedicated explanation page containing:

- The current 2D network.
- Current infection state.
- Current algorithm step.
- Selected nodes.
- Remaining budget.
- Previous Step and Next Step buttons.
- A dynamic algorithm explanation.

The explanation changes according to the actual network and step:

- Divide and Conquer shows the group containing the current node.
- Greedy shows the node's risk reduction, cost, priority ratio, and budget context.
- Dynamic Programming shows the node's cost, risk reduction, and whether it belongs to the final optimal combination.

The infection simulation also moves with the algorithm steps. Previous Step restores the previous infection state, time, infection curve, and infected nodes.

## Custom Network Mode

Custom mode allows users to enter:

- Number of nodes.
- Maximum number of edges.
- Vulnerability score for every node.
- Patch cost for every node.
- Connections between nodes.
- Custom patching budget.

The custom budget is used by all algorithms, benchmarks, patch selection, and step explanations.

Random mode uses the default budget of `120`.

## Performance Comparison

The Performance HUD displays:

- Algorithm execution time.
- Peak memory usage.
- Budget used.
- Total risk reduction.

This demonstrates the trade-offs between fast heuristic methods and more memory-intensive optimization methods.

## Project Structure

```text
adsa_mini_mtech/
├── dashboard.html
├── dashboard_server.py
├── infection_simulation.py
├── network_graph.py
├── optimization_algorithms.py
├── benchmarking.py
├── requirements.txt
└── Procfile
```

### Main Files

- `dashboard.html` - Web interface, network visualization, controls, and step pages.
- `dashboard_server.py` - HTTP server, API endpoints, application state, custom configuration, and algorithm steps.
- `infection_simulation.py` - Infection initialization, infection steps, and infection statistics.
- `network_graph.py` - Random and custom graph creation.
- `optimization_algorithms.py` - Greedy, Divide and Conquer, Dynamic Programming, and risk calculations.
- `benchmarking.py` - Execution time, memory, budget, and risk comparison.

## Technologies Used

- Python
- HTML
- CSS
- JavaScript
- Graph data structures
- Adjacency lists
- Greedy algorithm
- Divide and Conquer
- Dynamic Programming
- 0/1 Knapsack technique
- Python HTTP server

## Installation

Clone the repository:

```bash
git clone https://github.com/shubhamKumbhar05/adsa_mini.git
cd adsa_mini
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

Start the dashboard server:

```bash
python dashboard_server.py
```

Open the application in a browser:

```text
http://localhost:8000
```

## How to Use

### Random Network

1. Select **Random Network**.
2. View the generated 2D network.
3. Use the simulation or algorithm buttons.
4. Open an algorithm page.
5. Use **Next Step** to move forward.
6. Use **Previous Step** to return to an earlier state.
7. Use the zoom controls to inspect the network.

### Custom Network

1. Select **Custom Network**.
2. Enter the node count, edge limit, and patch budget.
3. Enter vulnerability and cost values for each node.
4. Add the desired edges.
5. Select **Use This Network**.
6. Run and compare the algorithms.

## Limitations

- The infection model is simplified for educational purposes.
- Infection outcomes are probabilistic.
- Greedy does not guarantee an optimal solution.
- Divide and Conquer is implemented as a heuristic and does not guarantee a globally optimal solution.
- Dynamic Programming assumes that risk reduction is additive.
- Application state is kept in memory and is not permanently stored.

## Educational Purpose

This project connects theoretical DSA concepts with a practical cybersecurity problem. It demonstrates how algorithms can be used to:

- Represent a network as a graph.
- Simulate infection propagation.
- Calculate node importance.
- Select nodes under a budget.
- Compare approximate and optimal strategies.
- Visualize decisions step by step.

The project makes abstract algorithm concepts easier to understand by showing their decisions directly on a changing network.
