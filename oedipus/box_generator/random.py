from random import random

from oedipus.db import Box

def new_boxes(run_id, gen, children_per_generation, config):
    """
    
    Args:
        run_id (str): identification string for run.

    Returns:
 
    """
    boxes = []
    for i in range(children_per_generation):
        if config['generator_type'] == 'mutate':
            box = Box(config['mutate']['initial_mutation_strength'], run_id)
        else:
            box = Box(0.0, run_id)
        box.generation  = gen
        [box.x, box.y, box.z] = [random(), random(), random()]
        boxes.append(box)
    return boxes
