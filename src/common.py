class MethodTypes:
    SINGLE = 'single_opt'
    MULTIPLE = 'multiple_opts'

class ObjMethods:
    VALUE = 's_value'
    WASTE = 's_waste'
    S_VALUE_WASTE = 's_value_waste'
    M_VALIE_WASTE = 'm_value_waste'
    
    @staticmethod
    def mode_type(obj_method) -> MethodTypes:
        if obj_method in (ObjMethods.VALUE, ObjMethods.WASTE, ObjMethods.S_VALUE_WASTE):
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