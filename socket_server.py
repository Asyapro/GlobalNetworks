import math
import socket
import numpy

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 12345))
server.listen(1)
conn, addr = server.accept()
conn.send('connected'.encode('utf-8'))
print('connected:', addr)

data_bit = []
answer_ = ''
count_recieved_words = 0
count_error_words = 0
count_corrected_words = 0
address = ''

def decode_hamming(bin_data_list):
    bin_data_list_ = bin_data_list.copy()

    amount_control_bits = int(math.ceil(numpy.log2(len(bin_data_list_))))
    control_bits = [0] * amount_control_bits

    for i in range(1, len(bin_data_list_)):
        number = bin(i)[2::][::-1]
        for j in range(0, len(number)):
            control_bits[j] += int(number[j]) * bin_data_list_[i]

    for i in range(0, len(control_bits)):
        control_bits[i] = control_bits[i] % 2

    global count_error_words
    global count_corrected_words

    control_ones = sum(control_bits)
    general_ones = sum(bin_data_list_) % 2
    try:
        if (control_ones !=0 and general_ones == 0):
            count_error_words += 1
            #print('multiple errors')
        elif (control_ones != 0 and general_ones == 1):
            count_error_words += 1
            index = 0
            for i in range(0, len(control_bits)):
                index += int(control_bits[i]) * (2 ** i)
            #print(index, 'bit error')
            bin_data_list_[index] = 0 if bin_data_list_[index] == 1 else 1
            count_corrected_words += 1
        elif (control_ones == 0 and general_ones == 0):
            pass
            #print('no error')
        elif (control_ones == 0 and general_ones == 1):
            #pass
            count_error_words += 1
            count_corrected_words += 1
            #print('zero bit error')
    except:
        pass

    del bin_data_list_[0]
    count = int(2 ** amount_control_bits)
    while (count > 1):
        count = int(count / 2)
        del bin_data_list_[count - 1]

    return bin_data_list_

def decoding(list):
    data_list = []
    while len(data_bit) >= 16:
        value = ''
        for j in range(0, 16):
            value += str(data_bit[j])
        del data_bit[0:16]
        data_list.append(int(int(value, base=2)))

    answer = ''
    for i in range(0, len(data_list)):
        answer += chr(data_list[i])
    return answer

flag = True
while flag:
    data = conn.recv(71)

    if data.find('c'.encode('utf-8')) != -1:
        flag = False
        data_ = data[:len(data) - 1]
    else:
        data_ = data

    bin_data_list = [int(x) for x in ((str(data_).replace('b', '')).replace("\'", '')).replace(r"\x0", '')]
    if len(bin_data_list) != 0:
        count_recieved_words += 1
        decoded_data = decode_hamming(bin_data_list)
        data_bit.extend(decoded_data)
        answer_ += decoding(data_bit)

print('message:', '\n',  answer_)
info = 'Number of recieved words: ' + str(count_recieved_words) + ', number of wrong words: ' + str(count_error_words) + ', number of corrected words: ' + str(count_corrected_words)
conn.send(info.encode('utf-8'))

server.close()
