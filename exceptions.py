class duplicate_label_found(Exception):
    def __init__(self, label):
        Exception.__init__(self, 'Label "' + label + '" already defined')

class incorrect_number_of_parameters(Exception):
    def __init__(self, name, found, expected):
        Exception.__init__(self, "Incorrect number of parameters for " + name + ", found " + found + " expected " + expected)

class invalid_parameter(Exception):
    def __init__(self):
        Exception.__init__(self, "Invalid parameter")

class invalid_register_name(Expcetion):
    def __init__(self, name):
        Exception.__init__(self, "Invalid register name: " + name)

class multiple_label_definitions(Exception):
    def __init__(self, label_name):
        Exception.__init__(self, 'Multiple definitions for label "' + label + '" found')

class branch_out_of_range(Exception):
    def __init__(self):
        Exception.__init__(self, "Branch address out of range")

class translate_num_out_of_range(Exception):
    def __init__(self, value, min_value, max_value):
        Exception.__init__(self, "Translated number " + value + " not in range [" + min_value + ", " + max_value + "]")
