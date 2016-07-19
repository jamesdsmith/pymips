class AssemblerException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class function_not_implemented(AssemblerException):
    def __init__(self):
        AssemblerException.__init__(self, "Function not implemented")

class duplicate_label_found(AssemblerException):
    def __init__(self, label):
        AssemblerException.__init__(self, 'Label "{0}" already defined'.format(label))

class label_not_found(AssemblerException):
    def __init__(self, label):
        AssemblerException.__init__(self, 'Label "{0}" not found'.format(label))

class address_not_found(AssemblerException):
    def __init__(self, addr):
        AssemblerException.__init__(self, 'Could not find a label associated with address "{0}"'.format(addr))

class incorrect_number_of_parameters(AssemblerException):
    def __init__(self, name, found, expected):
        AssemblerException.__init__(self, "Incorecct number of parameters for {0}, found {1} but expected {2}".format(name, found, expected))

class invalid_parameter(AssemblerException):
    def __init__(self):
        AssemblerException.__init__(self, "Invalid parameter")

class invalid_register_name(AssemblerException):
    def __init__(self, name):
        AssemblerException.__init__(self, "Invalid register name: {0}".format(name))

class multiple_label_definitions(AssemblerException):
    def __init__(self, label_name):
        AssemblerException.__init__(self, 'Multiple definitions for label "{0}" found'.format(label_name))

class branch_out_of_range(AssemblerException):
    def __init__(self):
        AssemblerException.__init__(self, "Branch address out of range")

class translate_num_out_of_range(AssemblerException):
    def __init__(self, value, min_value, max_value):
        AssemblerException.__init__(self, "Translated number {0} not in range [{1}, {2}]".format(value, min_value, max_value))

class translate_num_error(AssemblerException):
    def __init__(self, number):
        AssemblerException.__init__(self, "Error translating number {0}".format(number))

class translate_inst_error(AssemblerException):
    def __init__(self, name, args):
        AssemblerException.__init__(self, "{0}".format(name + " " + " ".join(args)))

