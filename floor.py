import cell


class Floor(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell):
        super().__init__(x, y, cell_id, neighbours, type_cell)
        # Add whatever you want
