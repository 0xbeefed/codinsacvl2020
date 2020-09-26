import config
import zmq


class Network:

    def __init__(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.REQ)
        self.socket.connect('tcp://' + config.IP + ':' + str(config.port))

    def send(self, content):
        if config.DEBUG_NETWORK:
            print('[NETWORK]', 'Sending "' + content + '\"')
        self.socket.send(content.encode('UTF-8'))

    def read(self):
        buffer = self.socket.recv().decode('UTF-8').split('\n')
        if config.DEBUG_NETWORK:
            print('[NETWORK]', 'Received lines:\n' + '\n'.join(buffer) + '\n[NETWORK] ------------')
        return buffer