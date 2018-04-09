def run(box):
    """
    Args:
        box

    Returns:
        results (dict)

    """
    results = {}
    results['beta'] = (box.y * box.z) ** 2

    return results
