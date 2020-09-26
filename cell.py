class Cell:

    def __init__(self, x, y, cell_id, neighbours, type_cell, master_cell):
        self.x = x
        self.y = y
        self.cell_id = cell_id
        self.neighbours = list(neighbours)
        self.type_cell = type_cell
        self.browseable = True
        self.master_cell = master_cell
