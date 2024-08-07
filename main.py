import re

import sympy as sp

from assets.netlist import DIFFERENTIAL_ACM
from utils.symbolic_expression import symbolic_expression


# Step 1: Parse the input component-wise and node-wise
def parse_spice_netlist(netlist):
    components = {
        "resistors": {},
        "capacitors": {},
        "inductors": {},
        "voltage_sources": {},
        "current_sources": {},
        "dependent_sources": {},
    }
    nodes = set()
    components_set = set()

    lines = netlist.split("\n")

    for line in lines:
        line = line.strip()
        if line and not line.startswith("*"):
            parts = re.split(r"\s+", line)

            component = parts[0]
            components_set.add(component)

            component_nodes = parts[1:-1]
            nodes.update(component_nodes)

            value = parts[-1]

            if component.startswith("R"):
                components["resistors"].update(
                    {component: {"value": value, "nodes": component_nodes}}
                )
            elif component.startswith("C"):
                components["capacitors"].update(
                    {component: {"value": value, "nodes": component_nodes}}
                )
            elif component.startswith("L"):
                components["inductors"].update(
                    {component: {"value": value, "nodes": component_nodes}}
                )
            elif component.startswith("V"):
                if "*" in value:
                    components["dependent_sources"].update(
                        {component: {"value": value, "nodes": component_nodes}}
                    )
                else:
                    components["voltage_sources"].update(
                        {component: {"value": value, "nodes": component_nodes}}
                    )
            elif component.startswith("I"):
                if "*" in value:
                    components["dependent_sources"].update(
                        {component: {"value": value, "nodes": component_nodes}}
                    )
                else:
                    components["current_sources"].update(
                        {component: {"value": value, "nodes": component_nodes}}
                    )

    return components, components_set, nodes


components, components_set, nodes = parse_spice_netlist(DIFFERENTIAL_ACM)


# Step 2: Create node voltages symbolic variables
def create_node_symbols(nodes):
    node_symbols = {}

    node_symbols["0"] = 0
    for node in nodes:
        if node != "0":
            node_symbols[node] = sp.symbols(node)

    return node_symbols


node_symbols = create_node_symbols(nodes)


# Step 3: Create symbolic variables
def create_component_symbols(components, node_symbols, nodes):
    component_symbols = {}
    toIgnore = ["voltage_sources"]

    for component_type in components:
        if component_type in toIgnore:
            continue

        components_list = components[component_type]
        for component_name in components_list:
            if component_type in ["resistors", "capacitors", "inductors"]:
                component_symbols[component_name] = sp.symbols(component_name)

            elif component_type == "dependent_sources":
                component_value = components_list[component_name]["value"]

                gain = component_value.split("*")[0]
                symbolic_expr, symbolic_nodes = symbolic_expression(component_value.split("*")[1])

                for var in symbolic_nodes:
                    if var not in nodes:
                        node_symbols[str(var)] = sp.symbols(var)

                component_symbols[component_name] = sp.symbols(gain) * (symbolic_expr)

    return component_symbols


component_symbols = create_component_symbols(components, node_symbols, nodes)


# Step 4: Components connections through nodes
def create_nodes_to_components_connections(components, nodes):
    node_connections = {node: [] for node in nodes}
    for component_type in components:

        components_list = components[component_type]
        for component_name in components_list:
            component_nodes = components_list[component_name]["nodes"]
            component_value = components_list[component_name]["value"]
            for node in component_nodes:
                if node in node_connections:
                    node_connections[node].append(
                        (component_name, component_nodes, component_value)
                    )
    return node_connections


node_connections = create_nodes_to_components_connections(components, nodes)


# Step 5: KCL equations
def write_kcl_equations(node_connections, node_voltages, symbols):
    def current_through_resistor(v1, v2, resistance):
        return (v1 - v2) / resistance

    def current_through_capacitor(v1, v2, capacitance, s):
        return s * capacitance * (v1 - v2)

    def current_through_inductor(v1, v2, inductance, s):
        return (v1 - v2) / (s * inductance)

    s = sp.symbols("s")
    kcl_equations = {}
    for node, connections in node_connections.items():
        if node == "0":
            continue

        node_current = 0
        for comp_name, comp_nodes, _ in connections:
            if comp_name.startswith("R"):
                # Resistor
                node_current += (
                    current_through_resistor(
                        node_voltages[comp_nodes[0]],
                        node_voltages[comp_nodes[1]],
                        symbols[comp_name],
                    )
                    if comp_nodes[0] == node
                    else current_through_resistor(
                        node_voltages[comp_nodes[1]],
                        node_voltages[comp_nodes[0]],
                        symbols[comp_name],
                    )
                )

            elif comp_name.startswith("C"):
                # Capacitor
                node_current += (
                    current_through_capacitor(
                        node_voltages[comp_nodes[0]],
                        node_voltages[comp_nodes[1]],
                        symbols[comp_name],
                        s,
                    )
                    if comp_nodes[0] == node
                    else current_through_capacitor(
                        node_voltages[comp_nodes[1]],
                        node_voltages[comp_nodes[0]],
                        symbols[comp_name],
                        s,
                    )
                )

            elif comp_name.startswith("L"):
                # Inductor
                node_current += (
                    current_through_inductor(
                        node_voltages[comp_nodes[0]],
                        node_voltages[comp_nodes[1]],
                        symbols[comp_name],
                        s,
                    )
                    if comp_nodes[0] == node
                    else current_through_inductor(
                        node_voltages[comp_nodes[1]],
                        node_voltages[comp_nodes[0]],
                        symbols[comp_name],
                        s,
                    )
                )
            elif comp_name.startswith("V"):
                # Independent voltage source
                pass
            elif comp_name.startswith("I"):
                # Independent current source
                if comp_nodes[0] == node:
                    node_current += (
                        symbols[comp_name] if comp_name in symbols else sp.symbols(comp_name)
                    )
                else:
                    node_current -= (
                        symbols[comp_name] if comp_name in symbols else sp.symbols(comp_name)
                    )

        if node_current != 0:
            kcl_equations[node] = sp.Eq(node_current, 0)
        else:
            kcl_equations[node] = sp.Eq(node_voltages[node], 0)

    return kcl_equations


kcl_equations = write_kcl_equations(node_connections, node_symbols, component_symbols)
print("\nKCL Equations:")
for node, eq in kcl_equations.items():
    print(node)
    sp.pprint(eq)


# Step 6: calculate the transfer function
def calculate_tf_from_kcl(kcl_equations, input, output, node_symbols):
    eq_list = list(kcl_equations.values())
    solutions = sp.solve(eq_list, node_symbols)
    transfer_function = sp.simplify(solutions[output] / solutions[input])
    return transfer_function


transfer_function = calculate_tf_from_kcl(
    kcl_equations, node_symbols["V_IN_DIF"], node_symbols["V_OUT"], node_symbols
)
print("\nLiteral Transfer Function:")
sp.pprint(transfer_function)
