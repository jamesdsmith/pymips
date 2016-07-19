from exceptions import duplicate_label_found, multiple_label_definitions, label_not_found, address_not_found

def write_inst_hex(output, instruction):
    output += ["{:08x}".format(instruction)]

def write_file_from_list(filename, string_list):
    with open(filename, 'w') as f:
        for line in string_list:
            f.write(line + '\n')
    pass

def read_file_to_list(filename):
    output = []
    with open(filename, 'r') as f:
        for line in f:
            output += [line]
    return output

class SymbolTable:
    def __init__(self, allow_dupes):
        self.allow_dupes = allow_dupes
        self.table = []

    def add(self, name, addr):
        if self.allow_dupes or self.label_count(name) == 0:
            self.table += [(name, addr)]
        else:
            raise duplicate_label_found(name)

    def get_addr(self, name):
        address = None
        for label, addr in self.table:
            if label == name:
                if address != None:
                    raise multiple_label_definitions(name)
                address = addr
        if address == None:
            raise label_not_found(name)
        return address

    def get_label(self, address):
        for label, addr in self.table:
            if addr == address:
                return label
        raise address_not_found(address)

    def label_count(self, name):
        count = 0
        for label, addr in self.table:
            if label == name:
                count += 1
        return count

    def to_string(self):
        output = []
        for k, v in self.table:
            output += [str(v) + "\t" + k]
        return output
