import cell


class Door(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, open, master_type):
        super().__init__(x, y, cell_id, neighbours, type_cell, master_type)
        self.open = True
        self.browseable = open