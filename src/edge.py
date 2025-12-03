def calculate_edge(predicted_total, sportsbook_total):
    """
    If our model total is higher/lower than the book,
    we calculate the edge.
    """
    return round(predicted_total - sportsbook_total, 2)
