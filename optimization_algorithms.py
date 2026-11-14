"""Basic algorithms for choosing nodes to patch."""


def risk_reduction(node):
    """Calculate how much risk is removed by patching a node."""
    return node["vulnerability"] * node["degree"]


def priority_ratio(node):
    """Calculate risk reduction divided by patch cost."""
    if node["cost"] == 0:
        # free node with positive value has infinite priority, not zero
        return float("inf") if risk_reduction(node) > 0 else 0
    return risk_reduction(node) / node["cost"]


def sort_nodes(nodes):
    """Sort nodes by priority ratio (desc), tie-break by risk reduction (desc)."""
    sorted_nodes = []

    for node in nodes:
        position = 0
        new_ratio = priority_ratio(node)          # hoisted out of the loop
        new_risk = risk_reduction(node)

        while position < len(sorted_nodes):
            old_node = sorted_nodes[position]
            old_ratio = priority_ratio(old_node)

            if new_ratio > old_ratio:
                break
            if new_ratio == old_ratio:
                if new_risk > risk_reduction(old_node):
                    break
            position += 1

        sorted_nodes.insert(position, node)

    return sorted_nodes


def choose_small_group(nodes, budget):
    """Choose nodes from a small group using the priority ratio."""
    selected = []
    left = budget
    sorted_nodes = sort_nodes(nodes)

    for node in sorted_nodes:
        if node["cost"] <= left:
            selected.append(node["id"])
            left -= node["cost"]

    return selected


def divide_and_conquer_patch(network, budget=120):
    """Split the nodes into groups and solve each group recursively."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    def solve(node_list, group_budget):
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

        selected = solve(left_nodes, left_budget)
        right_selected = solve(right_nodes, right_budget)
        for node_id in right_selected:
            selected.append(node_id)

        # NOTE: left_budget + right_budget == group_budget, so the total
        # cannot exceed group_budget — no trim loop needed.

        return selected

    return solve(network["nodes"], budget)


def greedy_patch(network, budget=120):
    """Choose the best risk-per-cost nodes first."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    selected = []
    left = budget
    sorted_nodes = sort_nodes(network["nodes"])

    for node in sorted_nodes:
        if node["cost"] <= left:
            selected.append(node["id"])
            left -= node["cost"]

    return selected


def dynamic_programming_patch(network, budget=120):
    """Use a simple 0-1 knapsack table to choose the best nodes."""
    if budget < 0:
        raise ValueError("budget must be non-negative")

    node_list = network["nodes"]
    node_count = len(node_list)
    table = [[0] * (budget + 1) for _ in range(node_count + 1)]

    for i in range(1, node_count + 1):
        node = node_list[i - 1]
        for j in range(budget + 1):
            table[i][j] = table[i - 1][j]
            if node["cost"] <= j:
                old_value = table[i - 1][j - node["cost"]]
                new_value = old_value + risk_reduction(node)
                if new_value > table[i][j]:
                    table[i][j] = new_value

    selected = []
    left = budget

    i = node_count
    while i > 0:
        if table[i][left] != table[i - 1][left]:
            node = node_list[i - 1]
            selected.append(node["id"])
            left -= node["cost"]
        i -= 1

    selected.reverse()
    return selected


def selection_summary(network, selected_ids):
    """Return the total cost and risk for selected node ids."""
    by_id = {node["id"]: node for node in network["nodes"]}   # O(n) build
    total_cost = 0
    total_risk = 0

    for node_id in selected_ids:
        node = by_id.get(node_id)
        if node is None:
            continue
        total_cost += node["cost"]
        total_risk += risk_reduction(node)

    return total_cost, total_risk
