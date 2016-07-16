class duplicate_label_found(Exception):
    def __init__(self, label):
        Exception.__init__(self, 'Label "{0}" already defined'.format(label))

class incorrect_number_of_parameters(Exception):
    def __init__(self, name, found, expected):
        Exception.__init__(self, "Incorecct number of parameters for {0}, found {1} but expected {2}".format(name, found, expected))

class invalid_parameter(Exception):
    def __init__(self):
        Exception.__init__(self, "Invalid parameter")

class invalid_register_name(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Invalid register name: {0}".format(name))

class multiple_label_definitions(Exception):
    def __init__(self, label_name):
        Exception.__init__(self, 'Multiple definitions for label "{0}" found'.format(label_name))

class branch_out_of_range(Exception):
    def __init__(self):
        Exception.__init__(self, "Branch address out of range")

class translate_num_out_of_range(Exception):
    def __init__(self, value, min_value, max_value):
        Exception.__init__(self, "Translated number {0} not in range [{1}, {2}]".format(value, min_value, max_value))

class translate_num_error(Exception):
    def __init__(self, number):
        Exception.__init__(self, "Error translating number {0}".format(number))

class translate_inst_error(Exception):
    def __init__(self, name, args):
        Exception.__init__(self, "{0}".format(name + " " + " ".join(args)))

