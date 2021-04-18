import socket
import threading
import os
from datetime import datetime

commands = ['STOR', 'RETR', 'MKD', 'CDUP', 'PWD', 'LIST', 'CWD', 'QUIT', 'CLOSE']



class FTP_server(threading.Thread):
    def __init__(self, commSock, address):
        threading.Thread.__init__(self)
        self.authenticated = False
        self.pasv_mode     = False
        self.rest          = False
        self.cwd           = '\\ftp'
        self.cwd_home = '\\ftp'
        self.commSock      = commSock
        self.address       = address
        self.users = [['anonymous', '', 'elr'], ['user1', 'p1', 'elmrw'], ['user2', 'p2', 'elm']]


    def login(self, username, password):
        flag = False
        index = 0
        while not flag and index < len(self.users):
            flag = (username == self.users[index][0] and password == self.users[index][1]) or username == 'anonymous'
            if flag:
                break
            index += 1
        if flag:
            answer = '230 User %s logged in.' %username
            self.log(username, answer)
            self.commSock.send((answer + '\r\n').encode('utf-8'))
            self.authenticated = True
            self.cwd = self.cwd_home
            return True
        else:
            self.log(username, '430 Invalid username or password.')
            self.commSock.send('430 Invalid username or password.\r\n'.encode('utf-8'))
            self.authenticated = False
            return False

    def check_permission(self, username, password, permission):
        flag = False
        index = 0
        while not flag and index < len(self.users):
            flag = (username == self.users[index][0] and password == self.users[index][1] and permission in
                    self.users[index][2]) or (username == 'anonymous' and permission in self.users[0][2])
            if flag:
                break
            index += 1
        if flag:
            return True
        else:
            self.commSock.send('550 Permission denied'.encode('utf-8'))
            return False

    def LIST(self, username, password, dirpath):
        try:
            if not dirpath:
                pathname = os.path.abspath(os.path.join(self.cwd, '.'))
            elif dirpath.startswith(os.path.sep):
                pathname = os.path.abspath(dirpath)
            else:
                pathname = os.path.abspath(os.path.join(self.cwd, dirpath))
        except Exception:
            return Exception

        if not self.authenticated:
            self.log(username, '530 User not logged in.')
            return
        elif not self.check_permission(username, password, 'l'):
            self.log(username, '550 Permission denied')
            return
        elif not os.path.exists(pathname):
            self.commSock.send('550 LIST failed Path name not exists.\r\n'.encode('utf-8'))
            self.log(username, '550 LIST failed Path name not exists.')
            return
        else:
            self.log(username, '150 Here is listing.')
            try:
                answer = ''
                with os.scandir(pathname) as entries:
                    for entry in entries:
                        if entry.is_file():
                            answer += entry.name + '\n'
                        if entry.is_dir():
                            answer += entry.name + '\n'
                if answer == '':
                    answer = 'Empty directory.\r\n'
                self.commSock.send(answer.encode('utf-8'))

                #print(answer)
            except Exception:
                print(Exception)
            self.log(username, '226 List done.')

    def CWD(self, username, password, dirpath):
        if not self.check_permission(username, password, 'e'):
            self.log(username, '550 Permission denied')
            return
        pathname = dirpath.endswith(os.path.sep) and dirpath or os.path.join(self.cwd, dirpath)

        if not os.path.exists(pathname) or not os.path.isdir(pathname):
            self.commSock.send('550 CWD failed Directory not exists.\r\n'.encode('utf-8'))
            self.log(username, '550 CWD failed Directory not exists.')
            return
        self.cwd = pathname
        self.commSock.send('250 OK.\r\n'.encode('utf-8'))
        self.log(username, '250 CWD Command successful.')

    def PWD(self, username, password):
        if not self.check_permission(username, password, 'l'):
            self.log(username, '550 Permission denied.\r\n')
            return
        self.commSock.send(('257 ' + self.cwd + '\r\n').encode('utf-8'))
        self.log(username, '257 PWD Command successful.')


    def CDUP(self, username, password):
        if not self.check_permission(username, password, 'e'):
            self.log(username, '550 Permission denied.')
            return
        if self.cwd == self.cwd_home or os.path.abspath(os.path.join('C:\\', self.cwd_home)) == self.cwd:
            self.commSock.send('502 Command not implemented. You are in home directory.\r\n'.encode('utf-8'))
            self.log(username, '502 Command not implemented.')
            return
        self.cwd = os.path.abspath(os.path.join(self.cwd, '..'))
        self.commSock.send('200 Ok.\r\n'.encode('utf-8'))
        self.log(username, '200 Ok.')

    def MKD(self, username, password, dirname):
        if not self.check_permission(username, password, 'm'):
            self.log(username, '550 Permission denied.')
            return
        pathname = dirname.endswith(os.path.sep) and dirname or os.path.join(self.cwd, dirname)


        if not self.authenticated:
            self.log(username, '530 User not logged in.')
            return

        else:
            try:
                os.mkdir(pathname)
                self.commSock.send('257 Directory created.\r\n'.encode('utf-8'))
                self.log(username, '257 Directory created.')
            except OSError:
                answer = '550 MKD failed Directory "%s" already exists.' % pathname
                self.commSock.send((answer + '\r\n').encode('utf-8'))
                self.log(username, answer)

    def RETR(self, username, password,  filenames):
        if not self.check_permission(username, password, 'r'):
            self.log(username, '550 Permission denied.')
            return
        pathnames = []
        for file_ in filenames:
            pathname = (os.path.join(self.cwd, file_))
            if not os.path.exists(pathname):
                answer = '550 Could not find file %s.' %file_
                self.commSock.send((answer + '\r\n').encode('utf-8'))
                self.log(username, answer)
            else:
                pathnames.append(pathname)

        self.commSock.send('125 Data connection already open; transfer starting.\r\n'.encode('utf-8'))
        self.log(username, '150 Opening data connection.')
        try:
            for i in range(0, len(pathnames)):
                file = open(pathnames[i], 'r')
                file_data = file.read()
                if not file_data:
                    self.commSock.send(' '.encode('utf-8'))
                else:
                    self.commSock.send(file_data.encode('utf-8'))
            if len(pathnames) != 0 :
                self.log(username, '226 Transfer complete.')


        except OSError as err:
            self.commSock.send(err.encode('utf-8'))
            self.log(username, err)
        except Exception:
            self.commSock.send('502 Command not implemented.\r\n'.encode('utf-8'))
            self.log(username, '502 Command not implemented.')

    def STOR(self, username, password, filenames):
        if not self.check_permission(username, password, 'w'):
            self.log(username, '550 Permission denied.')
            return
        if not self.authenticated:
            self.log(username, '530 STOR failed User not logged in.')
            return


        pathnames = []
        targets = []

        for i in range(0, len(filenames)):
            if not filenames[i]:
                pass
            else:

                filename = os.path.basename(filenames[i])
                pathname = os.path.join(self.cwd, filename)
                pathnames.append(pathname)

        try:
            self.log(username, '125 Data connection already open; transfer starting.')
            self.commSock.send('125 Data connection already open; transfer starting.\r\n'.encode('utf-8'))
            for i in range(0, len(pathnames)):

                file_data = self.commSock.recv(1024).decode('utf-8')
                with open(pathnames[i], 'w') as f:
                    f.write(file_data)

            self.log(username, '226 Transfer completed.')

        except OSError as err:
            print(err)
            self.commSock.send('502 Command not implemented.\r\n'.encode('utf-8'))

    def QUIT(self, username):
        if not self.authenticated:
            self.commSock.send('530 STOR failed User not logged in.\r\n'.encode('utf-8'))
            self.log(username, '530 STOR failed User not logged in.')
            return

        self.authenticated = False
        answer = '231 User %s logged out.' % username
        self.commSock.send((answer + '\r\n').encode('utf-8'))
        self.log(username, answer)



    def CLOSE(self):
        self.commSock.send('221 Goodbye.\r\n'.encode('utf-8'))
        self.log(username, '221 Goodbye.')

    def log(self, username, message):
        dt_string = (datetime.now()).strftime("%d/%m/%Y %H:%M:%S")
        log_message = dt_string + ' [' + username + '] '  + message
        print(log_message)

def new_connection():
    flag = True
    username = ''
    password = ''
    while True:
        data = conn.recv(1024)
        if data.decode('utf-8').split(' ')[0] == 'login':
            if len(data.decode('utf-8').split(' ')) < 2:
                username = 'anonymous'
                if f.login(username, password):
                    break
            elif len(data.decode('utf-8').split(' ')) == 3:
                username, password = data.decode('utf-8').split(' ')[1], data.decode('utf-8').split(' ')[2]
                if f.login(username, password):
                    break
            else:
                conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
                f.log(data.decode('utf-8').split(' ')[1], '501 Syntax error in parameters or arguments.')


        elif data.decode('utf-8').split(' ')[0] == 'CLOSE':
            flag = False
            f.CLOSE()
            break
        else:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log('', '530 User not logged in.')

    return username, password, flag


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1'
server.bind((host, 21))
server.listen(1)
conn, addr = server.accept()
conn.send('connected to FTP server'.encode('utf-8'))
print('connected:', addr)
f = FTP_server(conn, addr)
f.start()
username = ''
password = ''
flag = False
while not flag:
    username, password, flag = new_connection()


while flag:
    data = conn.recv(1024)
    command = data.decode('utf-8')
    command_splitted = command.split(' ')

    if command_splitted[0].upper() not in commands:
        conn.send('502 Command does not exist.\r\n'.encode('utf-8'))
        f.log(username, '502 Command does not exist.')

    elif command_splitted[0].upper() == 'PWD':
        if len(command_splitted) > 1:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            f.PWD(username, password)

    elif command_splitted[0].upper() == 'LIST':
        if len(command_splitted) < 2:
            dirname = ''
        else:
            dirname = command_splitted[1]
        f.LIST(username, password, dirname)
    elif command_splitted[0].upper() == 'CDUP':
        if len(command_splitted) > 1:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            f.CDUP(username, password)

    elif command_splitted[0] == 'RETR':
        if len(command_splitted) < 2:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            filenames = command_splitted
            del filenames[0]
            f.RETR(username, password, filenames)

    elif command_splitted[0].upper() == 'STOR':
        if len(command_splitted) < 2:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            filenames = command_splitted
            del filenames[0]
            f.STOR(username, password, filenames)

    elif command_splitted[0].upper() == 'MKD':
        if len(command_splitted) < 2:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            f.MKD(username, password, command_splitted[1])

    elif command_splitted[0].upper() == 'CWD':
        if len(command_splitted) < 2:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            f.CWD(username, password, command_splitted[1])
    elif command_splitted[0].upper() == 'QUIT':
        if len(command_splitted) > 1:
            conn.send('501 Syntax error in parameters or arguments.\r\n'.encode('utf-8'))
            f.log(username, '501 Syntax error in parameters or arguments.')
        else:
            f.QUIT(username)

            username, password, flag = new_connection()
            if not flag:
                break


    elif command_splitted[0].upper() == 'CLOSE':
        flag = False
        f.CLOSE()
        break

    else:
        pass

server.close()
exit()
