from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import numpy as np
from scipy.spatial import Delaunay

def delaunay_figure(boxes, convergence_bins, output_path, triang=None, children=[], parents=[],
                    bins=[], new_bins=[], title=""):

    if not triang:
        triang = Delaunay(boxes[:,3:5])

    hull_point_indices = np.unique(triang.convex_hull.flatten())
    hull_points = np.array([boxes[p] for p in hull_point_indices])

    # plot visualization
    fig = plt.figure(figsize=(12,12), tight_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks(np.array(range(0,convergence_bins + 1))/convergence_bins)
    ax.set_yticks(np.array(range(0,convergence_bins + 1))/convergence_bins)
    ax.tick_params(labelbottom=False, labelleft=False)
    ax.grid(linestyle='-', color='0.5', zorder=0)

    dbin = 1.0 / convergence_bins
    bin_rects = [Rectangle((b[0] * dbin, b[1] * dbin), dbin, dbin) for b in bins]
    pc = PatchCollection(bin_rects, facecolor='0.75')
    ax.add_collection(pc)

    new_bin_rects = [Rectangle((b[0] * dbin, b[1] * dbin), dbin, dbin) for b in new_bins]
    pc2 = PatchCollection(new_bin_rects, facecolor='#82b7b7')
    ax.add_collection(pc2)

    # plot all points as triangulation
    ax.triplot(boxes[:,3], boxes[:,4], triang.simplices.copy(), color='#78a7cc', lw=1)

    # plot hull and labels
    ax.plot(hull_points[:,3], hull_points[:,4], color='#78a7cc', marker='o', linestyle='None', zorder=10)
    # for p in hull_points:
    #     ax.annotate(i, (p[0], p[1] - 0.01), zorder=30, ha="center", va="top", size=9)

    # plot children
    ax.plot(children[:,3], children[:,4], color='#81ff6b', marker='o', linestyle='None', zorder=12)

    # plot chosen parents with proportional circles and label
    if len(parents) > 0:
        parent_counter = Counter([tuple(x) for x in parents]) #need tuples because they are hashable
        unique_parents = np.array([[x[3], x[4], num] for x, num in parent_counter.items()])
        ax.scatter(unique_parents[:,0], unique_parents[:,1], s=40*unique_parents[:,2], color='#ffbe6b', marker='o', linestyle='None', zorder=15)
        for p in unique_parents:
            x, y, parent_count = p
            if parent_count > 5:
                ax.annotate(str(int(parent_count)), (x, y), zorder=30, ha="center", va="center", size=9)

    ax.set_title(title)
    fig.savefig(output_path)
    plt.close(fig)
