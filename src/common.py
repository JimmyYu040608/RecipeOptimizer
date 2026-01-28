def custom_round_float(value: float) -> float:
    """ Round float to at least 2 decimal places or fewer decimal places if possible """
    value = round(value, 2)
    if value == int(value):
        return int(value)
    elif round(value, 1) == value:
        return round(value, 1)
    else:
        return value