import zmq
import config
from network import *
import sys


class Game:

    def __init__(self):
        # Technical setup
        self.network = Network()

        # Init stuff
        self.grid = {} # id_cell = y * self.SIZE_X + x
        self.guards = []
        self.students = []

        # Grab init data
        self.network.send('token ' + config.token)
        data = self.network.read()
        if data[0] != 'INIT':
            print('[GAME]', 'Init error: not INIT:', data[0], file=sys.stderr)
            exit()

        # Grab map size
        self.SIZE_X, self.SIZE_Y = map(int, data[1].split())

        # Parse grid data[2]

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
        action = [['MF', 1, 2], [None, -1]]

        # Send actions
        action_str = ' '.join((str(i) for i in action[0])) + '\n'
        if action[1][0]:
            action_str += ' '.join((str(i) for i in action[1])) + '\n'
        action_str += 'EOI'
        self.network.send(action_str)


game = Game()
while 1:
    game.play_turn()