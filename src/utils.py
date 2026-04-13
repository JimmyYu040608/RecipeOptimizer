class MethodTypes:
    SINGLE = 'single_opt'
    MULTIPLE = 'multiple_opts'

class ObjMethods:
    S_VALUE = 's_value'
    S_WASTE = 's_waste'
    S_VALUE_WASTE = 's_value_waste'
    S_VALUE_POWER = 's_value_power'
    S_VALUE_WASTE_POWER = 's_value_waste_power'
    M_VALUE_WASTE = 'm_value_waste'
    M_VALUE_WASTE_POWER = 'm_value_waste_power'
    
    @staticmethod
    def mode_type(obj_method) -> MethodTypes:
        if obj_method in (ObjMethods.S_VALUE, ObjMethods.S_WASTE, ObjMethods.S_VALUE_WASTE, ObjMethods.S_VALUE_POWER, ObjMethods.S_VALUE_WASTE_POWER):
            return MethodTypes.SINGLE
        else:
            return MethodTypes.MULTIPLE
    

def custom_round_float(value: float) -> float:
    """ Round float to at least 2 decimal places or fewer decimal places if possible """
    value = round(value, 2)
    if value == int(value):
        return int(value)
    elif round(value, 1) == value:
        return round(value, 1)
    else:
        return value


def integer_simplex(k, n):
    """
    Generate weight matrix for different weights to be tested on multiple objections
    k: dimension
    n: resolution
    """
    if k == 1:
        return [[n]]
    
    solutions = []
    for i in range(n + 1):
        for tail in integer_simplex(k - 1, n - i):
            solutions.append([i] + tail)
    
    return solutions


def to_float(value) -> float:
    """ Convert a value to float, or return NaN if the value is None """
    if value is None:
        return float("nan")
    return float(value)