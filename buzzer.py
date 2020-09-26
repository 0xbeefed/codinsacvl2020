import cell


class Buzzer(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, power, master_type):
        super().__init__(x, y, cell_id, neighbours, type_cell, master_type)
        self.power = power
        self.activated = False
        self.browseable = True
