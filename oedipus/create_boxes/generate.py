from random import random

from oedipus.db import Box

def new_box(run_id, gen):
    """
    
    Args:
        run_id (str): identification string for run.

    Returns:
 
    """
    box = Box(run_id)
    box.generation  = gen
    [box.x, box.y, box.z] = [random(), random(), random()]

    return box
