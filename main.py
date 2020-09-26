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