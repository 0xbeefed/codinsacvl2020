import cell


class Buzzer(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, power):
        super().__init__(x, y, cell_id, neighbours, type_cell)
        self.power = power
        self.activated = False
        self.browseable = True
