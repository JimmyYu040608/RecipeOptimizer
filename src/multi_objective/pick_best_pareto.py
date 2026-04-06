""" Includes different functions which pick the final 'best' solution among the set of Pareto solutions obtained from multi-objective optimization quantitatively """

from typing import List
import math

def pick_utopia(utopia_point: List[int], optimal_points: List[List[int]]):
    """
    Utopia point refers to the usually unreachable point which each coordinate is taken to be the best possible value of each objective (known by doing single-objective optimization respectively)
    """
    dimension = len(utopia_point)
    if dimension != len(optimal_points[0]):
        raise ValueError("Dimension mismatch")
    best_index = 0
    best_dist = -1
    for i, optimum in enumerate(optimal_points):
        dist = math.dist(utopia_point, optimum)
        if dist < best_dist or best_dist == -1:
            best_dist = dist
            best_index = i
    if best_dist < 0:
        raise ValueError("Fail to locate best Pareto optimum")
    print(f"Best Pareto optimum found: {best_index}, whose value is {optimal_points[best_index]} with distance {best_dist} to utopia point {utopia_point}")
    return best_index