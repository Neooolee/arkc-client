import socket
import logging
import asyncore

# Need to switch to asyncio


class clientcontrol(asyncore.dispatcher):

    """ a standard client service dispatcher """

    def __init__(self, control, clientip, clientport, backlog=5):
        self.control = control
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((clientip, clientport))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        logging.info('Client_recv_Accept from %s' % str(addr))
        clientreceiver(conn, self.control)


class clientreceiver(asyncore.dispatcher):

    def __init__(self, conn, control):
        self.control = control
        asyncore.dispatcher.__init__(self, conn)
        self.idchar = self.control.register(self)
        if self.idchar is None:
            self.close()
        self.from_remote_buffer = {}
        self.from_remote_buffer_index = 100
        self.to_remote_buffer = b''
        self.to_remote_buffer_index = 100

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        logging.debug('%04i from client ' % len(read) + self.idchar)
        self.to_remote_buffer += read

    def writable(self):
        if self.from_remote_buffer_index + 6 in self.from_remote_buffer:
            logging.warning("lost frame at connection " + self.idchar)
        #    self.close()
        return self.from_remote_buffer_index in self.from_remote_buffer

    def handle_write(self):
        sent = 0
        while self.writable():
            sent = sent + \
                self.send(
                    self.from_remote_buffer.pop(self.from_remote_buffer_index))
            self.next_from_remote_buffer()
        logging.debug('%04i to client ' % sent + self.idchar)

    def handle_close(self):
        self.control.remove(self.idchar)
        self.close()

    def next_to_remote_buffer(self):
        self.to_remote_buffer_index += 1
        if self.to_remote_buffer_index == 1000:
            self.to_remote_buffer_index = 100

    def next_from_remote_buffer(self):
        self.from_remote_buffer_index += 1
        if self.from_remote_buffer_index == 1000:
            self.from_remote_buffer_index = 100
