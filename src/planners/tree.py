
import yaml

from itertools import combinations


class Constraint():
    def __init__(self, constraint_type, name, params):
        self.constraint_type = constraint_type
        self.name = name
        self.params = params

    def __str__(self):
        return "Type: {} | Name: {} | Params: {}".format(
            self.constraint_type, self.name, str(self.parameters))


class Node():
    def __init__(self, params, parents=[], children=[]):
        self.params = params  # tuple
        self.parents = parents  # list
        self.children = children  # list
        self.leaf = False
        self.name = ""

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{} | {} | {}".format(
            str(self.parents), str(self.params), str(self.children))


class Tree():
    def __init__(self):
        self.nodes = {}

    # Build the tree
    def build(self, constraints_file, parameters_file):

        print("Reading constraints...")
        constraints, parameters = self.setup(constraints_file, parameters_file)

        print("Building tree...")
        self.initialize(parameters)

        self.add_pairs_and_triples(constraints, parameters)

        self.add_leaves(constraints, parameters)

        self.prune()

        # self.display()

    # Read in constraint and parameter data from files
    def setup(self, constraints_file, parameters_file):
        # read in constraints from file
        constraints = []
        with open(constraints_file) as file:
            file_data = yaml.load(file, Loader=yaml.FullLoader)

            for key, value in file_data.items():
                constraint_type = key

                for file_data in value:
                    name = list(file_data.keys())[0]
                    parameters = file_data[name]['parameters']
                    constraints.append(Constraint(
                        constraint_type, name, parameters))

        # read in parameters from file
        print("Reading parameters...")
        parameters = {}
        with open(parameters_file) as file:
            parameters = yaml.load(file, Loader=yaml.FullLoader)

        return constraints, parameters

    # Initialize tree with root and basic parameters
    def initialize(self, parameters):
        # Initialize root
        self.add(('root'), [], [])

        # Initialize bases
        self.add(('object'), [('root')], [])
        self.add(('human'), [('root')], [])
        self.add(('robot'), [('root')], [])
        for cont in parameters['continuous']:
            self.add((cont), [('root')], [])

        print("Size after initialization: {}".format(
            len(self.nodes.keys())))

        # Populate objects
        for obj in parameters['object']:
            self.add((obj), [('object')], [])
        # Populate humans
        for human in parameters['human']:
            self.add((human), [('human')], [])
        # Populate robots
        for robot in parameters['robot']:
            self.add((robot), [('robot')], [])

        print("Size after expanding sets: {}".format(
            len(self.nodes.keys())))

    # Add pairs and triples of parameters to tree
    def add_pairs_and_triples(self, constraints, parameters):
        # Flatten lists of parameters
        basic_params = [el for sublist in parameters.values()
                        for el in sublist]

        # Pairs of params
        pairs = list(combinations(basic_params, 2))
        for p in pairs:
            params = tuple(sorted(p))
            parents = [(p[0]), (p[1])]
            self.add(params, parents, [])

        print("Size after pairs of params: {}".format(
            len(self.nodes.keys())))

        # Triples of params
        triples = list(combinations(basic_params, 3))
        for t in triples:
            params = tuple(sorted(t))
            parents = list(combinations(t, 2))
            for i in range(len(parents)):
                parents[i] = tuple(sorted(parents[i]))
            self.add(params, parents, [])

        print("Size after triples of params: {}".format(
            len(self.nodes.keys())))

    # Add the leaves (constraints) to the tree
    def add_leaves(self, constraints, parameters):
        leaves = self.create_leaves(constraints, parameters)
        for leaf in leaves:
            try:
                # check attachment point (should only fail on doubles)
                self.nodes[tuple(leaf.params)]
                new_params = leaf.params + (leaf.name, )
                self.add(new_params, [leaf.params], [])
                self.nodes[new_params].leaf = True
            except KeyError as e:
                # print("Couldn't find attach point for: {}".format(str(leaf)))
                pass

        print("Size after additions of leaves: {}".format(
            len(self.nodes.keys())))

    # Create leaves from parameters
    def create_leaves(self, constraints, parameters):
        # Build upward from constraint leaf nodes
        leaves = []
        for constraint in constraints:
            # Expand first parameter
            param_1 = constraint.params[0]
            for x in parameters[param_1]:
                try:
                    # Expand second parameter
                    param_2 = constraint.params[1]
                    if param_2 not in parameters['continuous']:
                        for y in parameters[param_2]:
                            temp_node = Node(
                                params=[x, y], parents=[], children=[])
                            try:
                                param_3 = constraint.params[2]
                                temp_node.params.append(param_3)
                            except IndexError as e:
                                # No third parameter
                                pass
                            temp_node.leaf = True
                            temp_node.name = "{}/{}".format(
                                constraint.constraint_type, constraint.name)
                            temp_node.params = tuple(sorted(temp_node.params))
                            leaves.append(temp_node)
                    else:  # No parameter expansion needed
                        temp_node = Node(
                            params=[x, param_2], parents=[], children=[])
                        temp_node.leaf = True
                        temp_node.name = "{}/{}".format(
                            constraint.constraint_type, constraint.name)
                        temp_node.params = tuple(sorted(temp_node.params))
                        leaves.append(temp_node)

                except IndexError as e:
                    # No second parameter: unsupported for now
                    pass

        return leaves

    # Prune out extra nodes after original tree formation
    def prune(self):
        old_count = 1
        new_count = -1

        # Keep pruning until no effect
        while old_count != new_count:
            old_count = len(self.nodes.keys())
            delete = []
            for key, value in self.nodes.items():
                if len(value.children) == 0 and not value.leaf:
                    delete.append(key)

            for key in delete:
                del self.nodes[key]

            for key, value in self.nodes.items():
                value.children = [x for x in value.children if x not in delete]

            new_count = len(self.nodes.keys())

        print("Size after pruning: {}".format(len(self.nodes.keys())))

    # Add a node to the tree
    def add(self, params, parents=[], children=[]):
        # Create and add new node
        self.nodes[params] = Node(params, parents, children)

        # Update parents
        for parent in parents:
            self.nodes[parent].children.append(params)

        # Update children
        for child in children:
            self.nodes[child].parents.append(params)

    # Remove references to a node by key
    def remove(self, key):
        try:
            # Remove references to node so it creates it's own tree
            for parent in self.nodes[key].parents:
                parent.children.remove(key)
            print("Removing: {}".format(str(key)))
            del self.nodes[key]
        except KeyError as e:
            # Double delete
            pass

    # Display all nodes in tree
    def display(self, ):
        for key, value in sorted(self.nodes.iteritems()):
            print(str(key) + " : " + str(value))
        print("\n")

    # Count current number of accessible nodes
    def count(self, current_node):
        # NOTE: This doesn't work since each node can have multiple parents
        if len(current_node.children) > 0:
            counter = 0
            for child in current_node.children:
                try:
                    counter += self.count(self.nodes[child])
                except KeyError as e:
                    # child has been removed
                    pass
            return counter + 1
        else:
            return 1


if __name__ == "__main__":
    tree = Tree()
    tree.build('../../config/constraints.yml', '../../config/parameters.yml')