import cell


class Door(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, open, master_cell):
        super().__init__(x, y, cell_id, neighbours, type_cell, master_cell)
        self.open = True
        self.browseable = open