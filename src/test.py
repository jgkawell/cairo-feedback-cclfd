import nltk

from planners.tree import Node, Tree
from planners.process_user_input import ProcessInput

# Make sure wordnet is downloaded
nltk.download('wordnet', quiet=True)

# Easy sentences
sentences = [
    'You should have kept the cup upright',
    'You should have moved more slowly when holding the mug',
    'You should have kept the cup over the table',
    'You should have kept the mug farther away from john',
    'You should not have pushed the block so quickly',
    'You should not have flipped the glass upside down',
    'Do not upend the cup'
]

# Hard sentences
sentences = [
    'You were too close',
    'You moved to fast',
    'The cup',
    'Knife'
]

# Threshold for scoring
threshold = 0.75


def nlp():
    # Iterate through sentences
    for sentence in sentences:
        print('-' * 50)
        print("Sentence: {}".format(sentence))

        # Create tree
        tree = Tree()
        tree.build('../config/constraints.yml', '../config/parameters.yml')

        # Create word processor
        processor = ProcessInput('../config/dictionaries.yml')
        processor.buildDicts()

        # Get the word similarity scores for working dictionary
        word_similarity_scores = processor.processUserInput(sentence)

        # Create question nodes from all leaves
        question_nodes = []
        for node in tree.nodes.values():
            if node.leaf:
                question_nodes.append(node)

        # Score nodes
        for node in question_nodes:
            node = score_node(node, word_similarity_scores)

        # Sort nodes
        question_nodes = sorted(question_nodes, key=lambda x: x.score, reverse=True)

        # Iterate over all questions to ask
        corrected = iterate_over_nodes(tree, question_nodes)

        # If the user responds no to everything
        if not corrected:
            print("Couldn't find a correction. Was your feedback correct?")


def tree():
    # Iterate through sentences
    for sentence in sentences:
        print('-' * 50)
        print("Sentence: {}".format(sentence))

        # Create tree
        tree = Tree()
        tree.build('../config/constraints.yml', '../config/parameters.yml')

        # Get root of tree
        root = tree.nodes[('root')]

        # Get best question to ask from scored tree
        question_nodes = []
        for child in root.children:
            question_nodes.append(tree.nodes[child])

        # Iterate over all questions to ask
        corrected = iterate_over_nodes(tree, question_nodes)

        # If the user responds no to everything
        if not corrected:
            print("Couldn't find a correction. Was your feedback correct?")


def tree_nlp():
    # Iterate through sentences
    for sentence in sentences:
        print('-' * 50)
        print("Sentence: {}".format(sentence))

        # Create tree
        tree = Tree()
        tree.build('../config/constraints.yml', '../config/parameters.yml')

        # Create word processor
        processor = ProcessInput('../config/dictionaries.yml')
        processor.buildDicts()

        # Get the word similarity scores for working dictionary
        word_similarity_scores = processor.processUserInput(sentence)

        # Score each node in the tree based of word similarity score
        # tree.score_the_tree(threshold, word_similarity_scores)
        tree.new_scoring(word_similarity_scores)

        # Get best question to ask from scored tree
        question_nodes = tree.get_questions()

        # Iterate over all questions to ask
        corrected = iterate_over_nodes(tree, question_nodes)

        # If the user responds no to everything
        if not corrected:
            print("Couldn't find a correction. Try rephrasing your feedback?")


def iterate_over_nodes(tree, question_nodes):
    # Display question that will be asked
    corrected = False
    for node in question_nodes:
        # Recursively traverse questions in tree
        result = node_handle(tree, node)
        # Alert user and finish if solution is found
        if result:
            print("Correcting skill with given feedback!\n")
            corrected = True
            break

    return corrected


def node_handle(tree, node):
    # Generate and print question and ask for response
    query = tree.generate_query(node)
    print("Question: {}".format(query))
    print("Confidence: {}".format(node.score))
    response = str(raw_input("Yes or no? (Y/n)\n"))
    if response == "":
        response = "y"

    # If question was correct, ask constraint question if leaf or
    # recursively ask children if not leaf
    if response.lower() == 'y':
        if node.leaf:
            # Ask followup question (if exists)
            if node.followup != "":
                query = node.followup
                for param in node.params:
                    if param in tree.parameters['object']:
                        query = query.replace('object', param, 1)
                    if param in tree.parameters['human']:
                        query = query.replace('human', param, 1)
                    if param in tree.parameters['robot']:
                        query = query.replace('robot', param, 1)
                print("Followup: {}".format(query))
                response = str(raw_input("Give your response:\n"))
                return True
            else:
                return True
        else:
            # Iterate through children recursively if needed
            children = tree.get_best_children(node.params)
            for child in children:
                result = node_handle(tree, child)
                if result:
                    return True
    else:
        # If user responds no
        return False


def score_node(node, prob_dict):
    score = 0
    for param in node.params:
        try:
            score += prob_dict[param]
        except KeyError as e:
            # print("Bad key: {}".format(param))
            pass

    node.score = score
    return node


if __name__ == "__main__":
    # Get case for testing
    case = int(input("Which case to run? (1=nlp, 2=tree, 3=tree nlp)\n"))

    # Run selected case option
    if case == 1:
        nlp()
    elif case == 2:
        tree()
    elif case == 3:
        tree_nlp()
    else:
        print("Not valid option: {}".format(case))
