import numpy as np

# Y-axis options
def default_kg(self, ylist):
    return ylist
def default_kg_ylabel():
    return 'Mass (kg)'

def percent_of_value(self, ylist):
    return ylist/self.user_weight
def percent_of_value_ylabel(value, desc):
    if desc=='body weight':
        return '/% of '
