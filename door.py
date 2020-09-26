import cell


class Door(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, open):
        super().__init__(x, y, cell_id, neighbours, type_cell)
        self.open = True
        self.browseable = open