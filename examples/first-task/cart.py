"""A deliberately broken checkout total for the Stackwich first-task walkthrough."""


def total(items, discount_percent=0):
    """Sum (price, quantity) pairs and apply a percentage discount, rounded to cents."""
    subtotal = sum(price * quantity for price, quantity in items)
    return round(subtotal - subtotal * discount_percent, 2)
