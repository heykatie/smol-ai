"""Drive the richer reorder prep + post-approve steps in tests."""


def advance_reorder(app, through="confirm"):
    """Run reorder actions through the named step (inclusive).

    Steps: simulate_email → review_continue → negotiate_accept → draft_send →
    approve → submit_order → confirm → receive_full
    """
    order = [
        "simulate_email",
        "review_continue",
        "negotiate_accept",
        "draft_send",
        "approve",
        "submit_order",
        "confirm",
        "receive_full",
    ]
    if through not in order:
        raise ValueError("Unknown reorder step: {0}".format(through))
    for action in order:
        app.apply(action)
        if action == through:
            return
