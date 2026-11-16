"""Algorithms for choosing the most valuable nodes to patch."""


def risk_reduction(node):
    """Return the risk reduced by patching ``node``."""
    return node["vulnerability"] * node["degree"]


def priority_ratio(node):
    """Return a node's risk reduction per unit of patching cost."""
    if node["cost"] == 0:
        # A free node with positive risk reduction should be considered first.
        return float("inf") if risk_reduction(node) > 0 else 0
    return risk_reduction(node) / node["cost"]


def sort_nodes(nodes):
    """Sort by priority ratio, then use risk reduction to break ties."""
    prioritized_nodes = []

    for node in nodes:
        position = 0
        node_ratio = priority_ratio(node)
        node_risk = risk_reduction(node)

        while position < len(prioritized_nodes):
            current_node = prioritized_nodes[position]
            current_ratio = priority_ratio(current_node)

            if node_ratio > current_ratio:
                break
            if node_ratio == current_ratio:
                if node_risk > risk_reduction(current_node):
                    break
            position += 1

        prioritized_nodes.insert(position, node)

    return prioritized_nodes


def choose_small_group(nodes, budget):
    """Choose affordable nodes from a small group by priority."""
    selected = []
    remaining_budget = budget
    prioritized_nodes = sort_nodes(nodes)

    for node in prioritized_nodes:
        if node["cost"] <= remaining_budget:
            selected.append(node["id"])
            remaining_budget -= node["cost"]

    return selected


def divide_and_conquer_patch(network, budget=120):
    """Split nodes into groups and choose patches recursively."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    def select_from_group(node_list, group_budget):
        if len(node_list) == 0:
            return []
        if len(node_list) <= 4:
            return choose_small_group(node_list, group_budget)

        middle = len(node_list) // 2
        left_nodes = node_list[:middle]
        right_nodes = node_list[middle:]

        left_cost = 0
        for node in left_nodes:
            left_cost += node["cost"]
        left_budget = min(group_budget, left_cost)
        right_budget = group_budget - left_budget

        selected = select_from_group(left_nodes, left_budget)
        right_selected = select_from_group(right_nodes, right_budget)
        for node_id in right_selected:
            selected.append(node_id)

        return selected

    return select_from_group(network["nodes"], budget)


def greedy_patch(network, budget=120):
    """Choose the best risk-per-cost nodes first."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    selected = []
    remaining_budget = budget
    prioritized_nodes = sort_nodes(network["nodes"])

    for node in prioritized_nodes:
        if node["cost"] <= remaining_budget:
            selected.append(node["id"])
            remaining_budget -= node["cost"]

    return selected


def dynamic_programming_patch(network, budget=120):
    """Use a 0-1 knapsack table to maximize total risk reduction."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    node_list = network["nodes"]
    node_count = len(node_list)
    risk_table = [[0] * (budget + 1) for _ in range(node_count + 1)]

    for i in range(1, node_count + 1):
        node = node_list[i - 1]
        for j in range(budget + 1):
            risk_table[i][j] = risk_table[i - 1][j]
            if node["cost"] <= j:
                previous_risk = risk_table[i - 1][j - node["cost"]]
                candidate_risk = previous_risk + risk_reduction(node)
                if candidate_risk > risk_table[i][j]:
                    risk_table[i][j] = candidate_risk

    selected = []
    remaining_budget = budget

    i = node_count
    while i > 0:
        if risk_table[i][remaining_budget] != risk_table[i - 1][remaining_budget]:
            node = node_list[i - 1]
            selected.append(node["id"])
            remaining_budget -= node["cost"]
        i -= 1

    selected.reverse()
    return selected


def selection_summary(network, selected_ids):
    """Return the total patching cost and risk reduction for selected nodes."""
    nodes_by_id = {node["id"]: node for node in network["nodes"]}
    total_cost = 0
    total_risk = 0

    for node_id in selected_ids:
        node = nodes_by_id.get(node_id)
        if node is None:
            continue
        total_cost += node["cost"]
        total_risk += risk_reduction(node)

    return total_cost, total_risk
