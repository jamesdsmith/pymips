from exceptions import duplicate_label_found, multiple_label_definitions, label_not_found

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
