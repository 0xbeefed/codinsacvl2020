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

        # Calculating floodfills
        self.sub_floodfill_maps = {}
        self.captured_buzzers = []
        for buzzer in self.buzzers:
            print('[PROPAGATE]', 'Propagating buzzer at cell ' + str(buzzer))

            self.sub_floodfill_maps[buzzer] = {}
            seen = []
            queue = []
            queue.append([buzzer, 0])

            while queue:
                cell_id, level = queue.pop(0)

                #print('[PROPAGATE]', 'Iterative call on', cell_id, level, '| seen:', len(seen))

                score = level
                if cell_id not in self.sub_floodfill_maps[buzzer]:
                    self.sub_floodfill_maps[buzzer][cell_id] = score
                self.sub_floodfill_maps[buzzer][cell_id] = min(self.sub_floodfill_maps[buzzer][cell_id], score)

                for direction in [1, 2, 3, 4, 5, 6]:
                    new_cell_id = self.next_cell(cell_id, direction)
                    if new_cell_id not in seen and new_cell_id in self.grid.keys() and self.grid[new_cell_id].browseable:
                        seen.append(new_cell_id)
                        queue.append([new_cell_id, level + self.grid[new_cell_id].coef])

            print('[PROPAGATE]', 'Calculated flood map from buzzer')

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

        # Current cell: have we captured a new buzzer?
        current_cell, type_cell = data[1].split()
        current_cell = int(current_cell)

        for buzzer in self.buzzers:
            if current_cell == buzzer:
                self.captured_buzzers.append(buzzer)

        current_power = data[2]  
        suspected = data[3]  

        if data[4].split()[0] == 'Q':
            door = data[4].split()[1]
            del data[4]

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
        best_move = self.flood_fill_min(current_cell, enemies)
        action = [['M', best_move[0]], [None, -1]]

        # Send actions
        action_str = ' '.join((str(i) for i in action[0])) + '\n'
        if action[1][0]:
            action_str += ' '.join((str(i) for i in action[1])) + '\n'
        action_str += 'EOI'
        self.network.send(action_str)

    def propagate(self, center, max_dist, value, factor):
        output = {}
        seen = []
        queue = []
        queue.append([center, 0])

        while queue:
            cell_id, level = queue.pop(0)

            # print('[PROPAGATE]', 'Iterative call on', cell_id, level, '| seen:', len(seen))

            score = value / (max(0.01, level) * factor)
            if cell_id not in output:
                output[cell_id] = score
            output[cell_id] = min(output[cell_id], score)

            for direction in [1, 2, 3, 4, 5, 6]:
                new_cell_id = self.next_cell(cell_id, direction)
                if new_cell_id not in seen and new_cell_id in self.grid.keys() and self.grid[new_cell_id].browseable:
                    seen.append(new_cell_id)
                    queue.append([new_cell_id, level + 1])

        return output

    def flood_fill_min(self, current_cell, enemies):
        # Guards
        enemy_propagated = {}
        for enemy in enemies:
            enemy_type, enemy_cell = enemy
            enemy_cell = int(enemy_cell)

            if enemy_type == 'G':
                # Propagate from any guard, dist max 10
                enemy_propagated[enemy_cell] = self.propagate(enemy_cell, 8, 100, 1.2)


        # Pick the cell with the lowest score
        possible_moves = []
        for direction in [1, 2, 3, 4, 5, 6]:
            new_cell_id = self.next_cell(current_cell, direction)

            if new_cell_id in self.grid.keys() and self.grid[new_cell_id].browseable:
                # For a direction, we take the smallest of all buzzer maps
                move = [direction, new_cell_id, float('inf'), self.grid[new_cell_id].type_cell]

                # Cell modifier from guards
                value_modifier = 0
                for k in enemy_propagated.keys():
                    value_modifier += enemy_propagated[k][new_cell_id]
                print('[PROPAGATE]', 'value_modifier:', value_modifier)

                # Calculate worthyness from floodfill
                for buzzer in self.buzzers:
                    if buzzer not in self.captured_buzzers:
                        if move[2] > self.sub_floodfill_maps[buzzer][new_cell_id] + value_modifier:
                            move[2] = self.sub_floodfill_maps[buzzer][new_cell_id] + value_modifier
                possible_moves.append(list(move))

        possible_moves = sorted(possible_moves, key=lambda a: a[2])
        print('[PROPAGATE]', 'Possible moves:', possible_moves)
        print('[PROPAGATE]', 'Best pick: ', possible_moves[0])
        return possible_moves[0]

    def pos_to_x_y(self, pos):
        x = pos % self.SIZE_X
        y = pos // self.SIZE_X
        return (x, y)

    def x_y_to_pos(self, pos1):
        x, y = pos1
        pos2 =y * self.SIZE_X + x
        return pos2

    def cube_to_oddr(self, pos1):
        x1, y1, z1 = pos1
        col = x1 + (z1 - (z1&1)) // 2
        row = z1
        return (col, row)
        
    def oddr_to_cube(self, pos1):
        col, row = pos1
        x2 = col - (row - (row&1))//2
        z2 = row
        y2 = -x2-z2
        return (x2, y2, z2)

    def distance_cube(self, pos1, pos2):
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        return (abs(x1-x2) + abs(y1-y2) + abs(z1-z2)) // 2

    def distance(self, pos1, pos2):
        return self.distance_cube(self.oddr_to_cube(self.pos_to_x_y(pos1)), self.oddr_to_cube(self.pos_to_x_y(pos2)))

    def next_cell(self, pos, move):
        i, j = self.pos_to_x_y(pos)
        x, y, z = self.oddr_to_cube((i, j))
        if move == 1:
            x += 1
            z -= 1
        elif move == 2:
            x += 1
            y -= 1
        elif move == 3:
            y -= 1
            z +=1
        elif move == 4:
            x -= 1
            z += 1
        elif move == 5:
            x -= 1
            y += 1
        elif move == 6:
            y += 1
            z -= 1
        return self.x_y_to_pos(self.cube_to_oddr((x, y, z)))

game = Game()
while 1:
    game.play_turn()