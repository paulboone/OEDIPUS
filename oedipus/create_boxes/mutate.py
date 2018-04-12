from random import random

import numpy as np
from sqlalchemy import func

from oedipus import config
from oedipus.db import Box, MutationStrength, session

def select_parent(run_id, max_generation, generation_limit):
    """Use bin-counts to preferentially select a list of 'rare' parents.

    Args:
        run_id (str): identification string for run.
        max_generation (int): latest generation to include when counting number
            of materials ub each bin.
        generation_limit (int): number of materials to query in each generation
            (as materials are added to database they are assigned an index
            within the generation to bound the number of materials in each
            generation).

    Returns:
        The material id(int) corresponding to some parent-material selected
        from database with a bias favoring materials in bins with the lowest
        counts.

    """
    queries = [Box.alpha_bin, Box.beta_bin]

    # Each bin is counted...
    bins_and_counts = session \
        .query(func.count(Box.id), Box.alpha_bin, Box.beta_bin) \
        .filter(
            Box.run_id == run_id,
            Box.generation <= max_generation,
        ) \
        .group_by(Box.alpha_bin, Box.beta_bin).all()[1:]
    bins = []
    for i in bins_and_counts:
        some_bin = {}
        for j in range(len(queries)):
            some_bin[queries[j]] = i[j + 1]
        bins.append(some_bin)
    total = sum([i[0] for i in bins_and_counts])
    # ...then assigned a weight.
    weights = [ total / float(i[0]) for i in bins_and_counts ]
    normalized_weights = [ weight / sum(weights) for weight in weights ]
    parent_bin = np.random.choice(bins, p = normalized_weights)
    parent_queries = [i == parent_bin[i] for i in queries]
    parent_query = session \
        .query(Box.id) \
        .filter(
            Box.run_id == run_id,
            *parent_queries,
            Box.generation <= max_generation,).all()
    potential_parents = [i[0] for i in parent_query]
    return int(np.random.choice(potential_parents))

def perturb_length(x, ms):
    dx = ms * (random() - x)
    return x + dx

def mutate_box(parent_box, mutation_strength, generation):
    """    
    Args:

    Returns:

    """
    ########################################################################
    # create box
    child_box = Box(parent_box.run_id)
    child_box.parent_id = parent_box.id
    child_box.generation = generation

    ########################################################################
    # perturb side lengths
    child_box.x = perturb_length(parent_box.x, mutation_strength)
    child_box.y = perturb_length(parent_box.y, mutation_strength)
    child_box.z = perturb_length(parent_box.z, mutation_strength)

    return child_box

def new_boxes(run_id, gen):
    boxes = []
    for i in range(config['children_per_generation']):
        parent_id = select_parent(run_id, max_generation=(gen - 1),
                                generation_limit=config['children_per_generation'])
        parent_box = session.query(Box).get(parent_id)
    
        if config['mutation_scheme'] == 'random':
            mutation_strength = 1.
        elif config['mutation_scheme'] == 'flat':
            mutation_strength = config['initial_mutation_strength']
        elif config['mutation_scheme'] == 'hybrid':
            mutation_strength = random.choice([1., config['initial_mutation_strength']])
        elif config['mutation_scheme'] == 'adaptive':
            mutation_strength_key = [run_id, gen] + parent_box.bin
            mutation_strength = MutationStrength.get_prior(*mutation_strength_key).clone().strength
        else:
            print("REVISE CONFIG FILE, UNSUPPORTED MUTATION SCHEME.")
    
        # mutate material
        box = mutate_box(parent_box, mutation_strength, gen)
        boxes.append(box)
    return boxes
