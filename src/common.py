def round_float_to_2(value: float) -> float:
    """ Round float to at least 2 decimal places or few """
    value = round(value, 2)
    if value == int(value):
        return int(value)
    elif round(value, 1) == value:
        return round(value, 1)
    else:
        return value