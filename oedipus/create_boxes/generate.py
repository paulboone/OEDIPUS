from random import random

from oedipus import config
from oedipus.db import Box

def new_boxes(run_id, gen):
    """
    
    Args:
        run_id (str): identification string for run.

    Returns:
 
    """
    boxes = []
    for i in range(config['children_per_generation']):
        box = Box(run_id)
        box.generation  = gen
        [box.x, box.y, box.z] = [random(), random(), random()]
        boxes.append(box)
    return boxes
