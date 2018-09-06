
from random import random
import numpy as np
from numpy.random import choice

from scipy.spatial import Delaunay


def perturb_length(x, ms):
    dx = ms * (random() - x)
    return x + dx

# def mutate_box(parent_box, mutation_strength):
#     return ([
#         perturb_length(parent_box[0], mutation_strength),
#         perturb_length(parent_box[1], mutation_strength),
#         perturb_length(parent_box[2], mutation_strength),
#         -1.0, -1.0])

def mutate_box(parent_box, mutation_strength):
    child = [parent_box[0], parent_box[1], parent_box[2], -1.0, -1.0]
    dof = choice([0,1,2])
    child[dof] = perturb_length(child[dof], mutation_strength)
    return child

def choose_parents_hull(triang, box_range, num_parents):
    hull_point_indices = np.unique(triang.convex_hull.flatten())

    # choose parents
    point_weights = {i:0 for i in hull_point_indices}
    total_weight = 0
    for edge in triang.convex_hull:
        distance = np.sqrt(np.sum((box_range[edge[0]] - box_range[edge[1]]) ** 2))
        point_weights[edge[0]] += distance
        point_weights[edge[1]] += distance
        total_weight += 2 * distance

    point_weights = {k:point_weights[k] / total_weight for k in point_weights}
    parent_indices = choice(list(point_weights.keys()), num_parents, p=list(point_weights.values()))
    return list(parent_indices)

def triangle_area(p1, p2, p3):
    return (p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])) / 2

def choose_parents_simplices(triang, box_range, num_parents, num_best_triangles=10):
    areas = [[triangle_area(box_range[p1], box_range[p2], box_range[p3]), p1, p2, p3] for p1, p2, p3 in triang.simplices]
    areas.sort()
    areas = np.array(areas[-num_best_triangles:])
    total_area = areas[:,0].sum()
    areas[:,0] /= total_area
    triangle_indices = choice(range(num_best_triangles), num_parents, p=areas[:,0])
    parent_indices = [int(areas[t, choice([0,1,2]) + 1]) for t in triangle_indices]
    return parent_indices


def choose_parents(num_parents, boxes, fraction_hull):
    # calculate convex hull
    box_range = boxes[:,3:5]
    triang = Delaunay(box_range)
    hull_parents = round(fraction_hull * num_parents)
    parent_indices = choose_parents_hull(triang, boxes, hull_parents)

    new_parents = choose_parents_simplices(triang, box_range, num_parents - hull_parents)
    print(parent_indices, new_parents)
    parent_indices += choose_parents_simplices(triang, box_range, num_parents - hull_parents)
    return [boxes[i] for i in parent_indices]


def new_boxes(gen, children_per_generation, boxes, config={}):
    mutation_strength = config['mutation_strength']
    parents = choose_parents(children_per_generation, boxes, config['fraction_hull'])
    children = np.array([mutate_box(p, mutation_strength) for p in parents])
    return children, parents
