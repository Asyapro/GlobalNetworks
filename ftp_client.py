import socket
import os

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = True
while flag:
    print('Enter host or "CLOSE" to exit')
    host = input()
    if host == 'CLOSE':
        exit()
    elif len(host.split(' ')) == 1:
        try:
            client.connect((host, 21))
            answer = client.recv(8192).decode('utf-8')
            print (answer)
            flag = False
        except Exception:
            print('Try again')
    else:
        print('Try again')


while True:
    command = input()
    answer = ''

    if command.split(' ')[0] == 'RETR':
        filenames = command.split(' ')
        del filenames[0]
        pathnames = []
        for filename in filenames:
            pathname = (os.path.join('C:\\', 'ftp_client', os.path.basename(filename)))
            pathnames.append(pathname)

        if len(pathnames) != 0:
            client.send(command.encode('utf-8'))
            permission = client.recv(1024).decode('utf-8')
            print(permission)
            if permission == '125 Data connection already open; transfer starting.\r\n':

                for pathname in pathnames:
                    file_data = client.recv(1024).decode('utf-8')
                    with open(pathname, 'w') as f:
                        f.write(file_data)


        continue

    elif command.split(' ')[0] == 'STOR':
        filenames = command.split(' ')
        del filenames[0]
        pathnames = []
        for file_ in filenames:

            pathname = (os.path.join('C:\\', 'ftp_client', file_))
            if not os.path.exists(pathname):
                print ('550 Could not find file %s.\r\n' % file_)
            else:
                pathnames.append(pathname)
        if len(pathnames) != 0:
            client.send(command.encode('utf-8'))
            permission = client.recv(1024).decode('utf-8')
            print(permission)
            if permission == '125 Data connection already open; transfer starting.\r\n':

                for pathname in pathnames:
                    file = open(pathname, 'r')
                    file_data = file.read()
                    if not file_data:
                        client.send(' '.encode('utf-8'))
                    else:
                        client.send(file_data.encode('utf-8'))
                    file.close()

        continue


    client.send(command.encode('utf-8'))
    answer = client.recv(8192).decode('utf-8')

    if command == 'CLOSE':
        break
    print(answer)

client.close()
print('Connection closed')

