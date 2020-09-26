import cell


class Wall(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, master_cell):
        super().__init__(x, y, cell_id, neighbours, type_cell, master_cell)
        self.browseable = False
