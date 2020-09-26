import zmq
import config
from globals import *
from network import *
from cell import *
from wall import *
from buzzer import *
from door import *
from tar import *
from grass import *
from sand import *
from floor import *
import sys

directions = {
    1: -self.SIZE_X + 1,
    2: 1,
    3: self.SIZE_X + 1,
    4: self.SIZE_X - 1,
    5: -1,
    6: -self.SIZE_X - 1
}

class Game:

    def __init__(self):
        # Technical setup
        self.network = Network()
        self.propagate_grid = {}
        self.sub_propagate_grid = {}

        # Init stuff
        self.grid = {} # id_cell = y * self.SIZE_X + x
        self.guards = []
        self.students = []
        self.buzzers = []

        # Grab init data
        self.network.send('token ' + config.token)
        data = self.network.read()
        if data[0] != 'INIT':
            print('[GAME]', 'Init error: not INIT:', data[0], file=sys.stderr)
            exit()

        # Grab map size
        self.SIZE_X, self.SIZE_Y = map(int, data[1].split())

        # Parse grid data[2]
        for y in range(self.SIZE_Y):
            print('parsing:', data[2 + y])
            raw_map = data[2 + y].split()
            for x in range(self.SIZE_X):
                #print(y, x, len(raw_map))
                cell_id = y * self.SIZE_X + x
                cell_type = raw_map[x]

                if cell_type in [TYPE_BUZZGPE, TYPE_BUZZGM, TYPE_BUZZGC, TYPE_BUZZGMM, TYPE_BUZZGEI]:
                    # Buzzers
                    power = {TYPE_BUZZGPE: POWER_GPE, TYPE_BUZZGM: POWER_GM, TYPE_BUZZGC: POWER_GC, TYPE_BUZZGMM: POWER_GMM, TYPE_BUZZGEI: POWER_GEI}[cell_type]
                    self.grid[cell_id] = Buzzer(x, y, cell_id, {}, cell_type, power)
                    self.buzzers.append(cell_id)

                elif cell_type in [TYPE_P2GEI, TYPE_P1GEI, TYPE_P1GM, TYPE_P2GM, TYPE_P1GMM, TYPE_P2GMM, TYPE_P1GC, TYPE_P2GC, TYPE_P1GPE, TYPE_P2GPE]:
                    # Doors
                    self.grid[cell_id] = Door(x, y, cell_id, {}, cell_type, True)

                elif cell_type in [TYPE_GPE, TYPE_GM, TYPE_GC, TYPE_GMM, TYPE_GEI]:
                    # Floors
                    self.grid[cell_id] = Floor(x, y, cell_id, {}, cell_type)

                elif cell_type in [TYPE_WALL, TYPE_CONCRETE, TYPE_TREE, TYPE_BORDER]:
                    # Walls
                    self.grid[cell_id] = Wall(x, y, cell_id, {}, cell_type)

                elif cell_type == TYPE_TAR:
                    # Tar
                    self.grid[cell_id] = Tar(x, y, cell_id, {}, cell_type)

                elif cell_type == TYPE_SAND:
                    # Sand
                    self.grid[cell_id] = Sand(x, y, cell_id, {}, cell_type)

                elif cell_type == TYPE_GRASS:
                    # Grass
                    self.grid[cell_id] = Grass(x, y, cell_id, {}, cell_type)

                else:
                    print('[GAME]', 'Unable to map "' + cell_type + '" to a known cell type')

        print('[GAME]', 'Map parsed')

        # Parse player count and self player id
        self.player_count, self.player_id = map(int, data[2 + self.SIZE_Y].split())

        # Debug
        self.network.send('ok')
        print('[GAME]', 'Init done')

    def play_turn(self):
        # Receive turn data from server
        data = self.network.read()

        if data[0].split()[0] != 'TURN':
            print('[GAME]', 'Turn error: not TURN', data[0], file=sys.stderr)
            exit()
        turn = int(data[0].split()[1])
        print('[GAME]', 'Turn', turn)

        # CURRENT DATA
        current_cell, type_cell = None, None  # <id>, <type>={W, R, G, T, S, L}
        current_power = None  # <power>={0, 1, 2, 3, 4, 5}
        suspected = None  # <suspected>={0 = innocent, 1=suspected, 2=catched}
        door = None  # None or in {0, 1} if someone is in the batiment
        N = None  # number of cells in sight
        seeing = None  # cells in sight
        M = None  # number of enemies in sight
        enemies = None  # enemies in sight
        EOT = None  # last line, if != 'EOT':exit()

        current_cell, type_cell = data[1].split()
        current_power = data[2]  
        suspected = data[3]  

        if data[4].split()[0] == 'Q':
            door = data[4].split()[1]
            data.remove(4)

        N = int(data[4])
        seeing = []
        for i in range(5, 5+N):
            seeing.append(data[i].split())

        M = int(data[N+5])
        enemies = []
        for i in range(6+N, 6+N+M):
            enemies.append(data[i].split())

        EOT = data[6+N+M]
        if EOT != 'EOT':
            print('[GAME]', 'EOT Error', EOT)
            exit()

        # Compute actions [0]: Move | [1]: Power ('P' or 'S')
        self.flood_fill_buzzers()
        action = [['MF', 1, 2], [None, -1]]

        # Send actions
        action_str = ' '.join((str(i) for i in action[0])) + '\n'
        if action[1][0]:
            action_str += ' '.join((str(i) for i in action[1])) + '\n'
        action_str += 'EOI'
        self.network.send(action_str)

    def flood_fill_buzzers(self):
        print('[PROPAGATE]', 'Starting propagation algo')

        directions = {
            1: -self.SIZE_X + 1,
            2: 1,
            3: self.SIZE_X + 1,
            4: self.SIZE_X - 1,
            5: -1,
            6: -self.SIZE_X - 1
        }

        for buzzer in self.buzzers:
            print('[PROPAGATE]', 'Propagating buzzer at cell ' + str(buzzer))

            seen = []
            queue = []
            queue.append([buzzer, 0])

            while queue:
                cell_id, level = queue.pop(0)

                #print('[PROPAGATE]', 'Iterative call on', cell_id, level, '| seen:', len(seen))

                score = level * level
                if cell_id not in self.sub_propagate_grid:
                    self.sub_propagate_grid[cell_id] = score
                self.sub_propagate_grid[cell_id] = min(self.sub_propagate_grid[cell_id], score)

                for direction in directions.keys():
                    new_cell_id = cell_id + directions[direction]
                    if new_cell_id not in seen and new_cell_id in self.grid.keys() and self.grid[new_cell_id].browseable:
                        seen.append(new_cell_id)
                        queue.append([new_cell_id, level + 1])

            print('[PROPAGATE]', 'Propagated buzzer', buzzer, '| merging matrixes')

            for cell in self.sub_propagate_grid.keys():
                if cell not in self.propagate_grid:
                    self.propagate_grid[cell] = 0
                self.propagate_grid[cell] += self.sub_propagate_grid[cell]

        print('[PROPAGATE]', 'Propagation ended')
        print(self.sub_propagate_grid)

game = Game()
while 1:
    game.play_turn()