def run(box):
    """
    Args:
        box

    Returns:
        results (dict)

    """
    results = {}
    results['alpha'] = (box.x + box.y + box.z) / 3

    return results
