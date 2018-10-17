
from random import random
import numpy as np
from numpy.random import choice

from scipy.spatial import Delaunay


def perturb_length(x, mutation_strength, perturbation_method):
    if perturbation_method=="weighted":
        dx = mutation_strength * (random() - x)
        return x + dx
    elif perturbation_method=="unweighted":
        fraction = choice([-mutation_strength, mutation_strength]) * random()
        if fraction < 0:
            return x + x * fraction
        else:
            return x + (1 - x) * fraction
    elif perturbation_method=="wrapped":
        fraction = choice([-mutation_strength, mutation_strength]) * random()
        return (x + fraction) % 1.0

def mutate_box_random_all(parent_box, mutation_strength, perturbation_method):
    return ([
        perturb_length(parent_box[0], mutation_strength, perturbation_method),
        perturb_length(parent_box[1], mutation_strength, perturbation_method),
        perturb_length(parent_box[2], mutation_strength, perturbation_method),
        -1.0, -1.0])

def mutate_box_random_one_dof(parent_box, mutation_strength, perturbation_method):
    child = [parent_box[0], parent_box[1], parent_box[2], -1.0, -1.0]
    dof = choice([0,1,2])
    child[dof] = perturb_length(child[dof], mutation_strength, perturbation_method)
    return child


# def choose_parents_hull(triang, box_range, num_parents):
#     hull_point_indices = np.unique(triang.convex_hull.flatten())
#
#     # choose parents
#     point_weights = {i:0.0 for i in hull_point_indices}
#     total_weight = 0.0
#     for edge in triang.convex_hull:
#         distance = np.sqrt(np.sum((box_range[edge[0]] - box_range[edge[1]]) ** 2))
#         point_weights[edge[0]] += distance
#         point_weights[edge[1]] += distance
#         total_weight += 2 * distance
#
#     point_weights = {k:point_weights[k] / total_weight for k in point_weights}
#     parent_indices = choice(list(point_weights.keys()), num_parents, p=list(point_weights.values()))
#     return list(parent_indices)

def choose_parents_hull(triang, box_range, num_parents):
    hull_point_indices = np.unique(triang.convex_hull.flatten())

    point_weights = {i:0.0 for i in hull_point_indices}
    distances = [np.sqrt(np.sum((box_range[edge[0]] - box_range[edge[1]]) ** 2))for edge in triang.convex_hull]
    distances.sort()

    for edge in triang.convex_hull:
        distance = np.sqrt(np.sum((box_range[edge[0]] - box_range[edge[1]]) ** 2))
        point_weights[edge[0]] += distance
        point_weights[edge[1]] += distance

    point_weight_arr = [[point_weights[i], i] for i in point_weights.keys()]
    point_weight_arr.sort(key=lambda x: x[0])
    point_weight_arr = np.array(point_weight_arr)[-num_parents:]

    total_weight = point_weight_arr[:,0].sum()
    point_weight_arr[:, 0] /= total_weight

    parent_indices = choice(point_weight_arr[:,1], num_parents, p=point_weight_arr[:,0])
    parent_indices.sort()
    parent_indices = [int(i) for i in parent_indices]

    return parent_indices

def triangle_area(p1, p2, p3):
    return (p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])) / 2

def choose_parents_simplices(triang, box_range, num_parents, num_best_triangles):
    areas = [[triangle_area(box_range[p1], box_range[p2], box_range[p3]), p1, p2, p3] for p1, p2, p3 in triang.simplices]
    num_best_triangles = min(len(areas), num_best_triangles) # necessary for small generations
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
    parent_indices = choose_parents_hull(triang, box_range, hull_parents)
    # parent_indices = choose_parents_simplices(triang, box_range, num_parents - hull_parents, num_parents)
    return [boxes[i] for i in parent_indices]


def new_boxes(gen, children_per_generation, boxes, config={}):
    mutation_strength = config['mutation_strength']
    perturbation_method = config['perturbation_method']
    parents = choose_parents(children_per_generation, boxes, config['fraction_hull'])
    if config['mutate_method'] == "random_all":
        children = np.array([mutate_box_random_all(p, mutation_strength, perturbation_method) for p in parents])
    elif config['mutate_method'] == "random_one_dof":
        children = np.array([mutate_box_random_one_dof(p, mutation_strength, perturbation_method) for p in parents])
    else:
        raise(Exception("Please add a mutate_method to the config"))


    return children, parents
