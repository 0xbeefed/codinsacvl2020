import cell


class Sand(cell.Cell):

    def __init__(self, x, y, cell_id, neighbours, type_cell, master_cell):
        super().__init__(x, y, cell_id, neighbours, type_cell, master_cell)
        # Add whatever you want
