def run(box):
    """
    Args:
        box

    Returns:
        results (dict)

    """
    results = {}
    results['alpha'] = (box.x + box.y) / 2

    return results
