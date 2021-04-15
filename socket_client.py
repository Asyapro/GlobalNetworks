
# client
import math
import socket
import random

count_words = 0
count_error_words = 0
count_error_multiple_words = 0
lenght_word = 63
data = bytearray()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 12345))
data_ = client.recv(1024)
print(data_.decode('utf-8'))


def preparation_message(message):
    bin_data_str = ''.join("{0:016b}".format(ord(x)) for x in message)
    bin_data_list = [int(x) for x in bin_data_str]

    bin_data_list_part = []
    global lenght_word
    count = int(len(bin_data_list) / lenght_word)
    for i in range(0, count * lenght_word, lenght_word):
        bin_data_list_part.append(bin_data_list[int(i):int(i + lenght_word)])
    bin_data_list_part.append(bin_data_list[int(count * lenght_word):int(len(bin_data_list))])
    return bin_data_list_part

def hamming(bin_data_list_part):
    # filling control bits
    for i in range(0, len(bin_data_list_part)):
        count = 1
        while (count <=  len(bin_data_list_part[i])):
            bin_data_list_part[i].insert(count - 1, 0)
            count *= 2

    # calculation control bits
    for i in range(0, len(bin_data_list_part)):
        for j in range(0, len(bin_data_list_part[i])):
            number = bin(j + 1)[2::][::-1]
            for k in range(0, len(number)):
                bin_data_list_part[i][2 ** k - 1] += int(number[k]) * bin_data_list_part[i][j]
        count = 1
        while (count <= len(bin_data_list_part[i])):
            bin_data_list_part[i][count - 1] = bin_data_list_part[i][count - 1] % 2
            count *= 2

    # calculation parity bit
    for i in range(0, len(bin_data_list_part)):
        sum_ = int(sum(bin_data_list_part[i])) % 2
        bin_data_list_part[i].insert(0, sum_)
    return bin_data_list_part

def insert_errors(mode, bin_data_list_part):
    global count_error_words
    global count_error_multiple_words
    if mode == '0':
        count_error_words = 0
        return True, bin_data_list_part
    elif mode == '1':
        index_errors_part = random.sample(range(0, len(bin_data_list_part)), math.ceil(len(bin_data_list_part) / 2))
        index_errors_part = list(set(index_errors_part))
        count_error_words = len(index_errors_part)

        for index in index_errors_part:
            index_ = random.randrange(0, len(bin_data_list_part[index]))
            #print('index', index_)
            bin_data_list_part[index][index_] = 0 if bin_data_list_part[index][index_] == 1 else 1
        print('Single errors were added into words')
        return True, bin_data_list_part
    elif mode == '2':
        amount_errors = 1
        while amount_errors < 2:
            print('Enter max amount of errors for words(min 2)')
            amount_errors = int(input())

        index_errors_part = random.sample(range(0, len(bin_data_list_part)), math.ceil(len(bin_data_list_part) / 2))
        index_errors_part = list(set(index_errors_part))
        count_error_multiple_words = len(index_errors_part)
        for index in range(0, len(index_errors_part)):

            amount_errors_ = random.randrange(2, amount_errors + 1)
            index_errors = random.sample(range(0, len(bin_data_list_part[index])), amount_errors_)
            index_errors = list(set(index_errors))

            if len(index_errors) < 2:
                index -= 1
                break
            for index_ in index_errors:
                #print('index', index_)
                bin_data_list_part[index_errors_part[index]][index_] = 0 if bin_data_list_part[index_errors_part[index]][index_] == 1 else 1
        print('Multiple errors were added into words')
        return True, bin_data_list_part
    else:
        print('Try again')
        return False, bin_data_list_part

try:
    print('Enter message')
    message = input()
    bin_data_list_part_ = preparation_message(message)
    bin_data_list_part = hamming(bin_data_list_part_)
    print('select sending data mode: [0] without errors, [1] single errors, [2] multiple errors')
    bin_data_list_part_for_send = []
    while True:
        mode = input()
        flag, bin_data_list_part_for_send = insert_errors(mode, bin_data_list_part)

        if flag:
            break

    for i in range(0, len(bin_data_list_part_for_send)):
        client.send(bytearray(bin_data_list_part_for_send[i]))
    client.send('c'.encode('utf-8'))

    count_words = len(bin_data_list_part_for_send)
    data_rec = client.recv(1024)
    print(data_rec.decode('utf-8'))
    print('Number of sent words:', count_words, ', number of single error words:', count_error_words, 'number of multiple error words:', count_error_multiple_words,)
except Exception:
    print('Something was wrong!')
finally:
    client.send('c'.encode('utf-8'))
    client.close()
