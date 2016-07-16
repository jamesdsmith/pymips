class duplicate_label_found(Exception):
    def __init__(self, label):
        Exception.__init__(self, 'Label "' + label + '" already defined')

class incorrect_number_of_parameters(Exception):
    def __init__(self, name, found, expected):
        Exception.__init__(self, "Incorrect number of parameters for " + name + ", found " + found + " expected " + expected)

class invalid_parameter(Exception):
    def __init__(self):
        Exception.__init__(self, "Invalid parameter")
