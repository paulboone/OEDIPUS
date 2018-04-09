def run(box):
    """
    Args:
        box

    Returns:
        results (dict)

    """
    results = {}
    results['beta'] = box.x * box.y * box.z

    return results
