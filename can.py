import numpy
import cv2
from queue import Queue
import statistics

class Movement():
    def __init__(self, sender_node, point):
        self.sender = (sender_node.rect[0] + sender_node.rect[2]) / 2, (sender_node.rect[1] + sender_node.rect[3]) / 2
        self.node = sender_node
        self.point = point
        self.n_steps = 0


class Node():
    def __init__(self, id, rect):
        self.id = id
        self.rect = rect
        self.table = dict()
        self.new_moves = []
        self.moves = Queue()

    def add_neighbor(self, neighbor):
        self.table[neighbor.id] = neighbor

    def remove_neighbor(self, neighbor_id):
        self.table.pop(neighbor_id)

    def add_move(self, move):
        move.node = self
        self.new_moves.append(move)

    def make_step(self):
        if not self.moves.empty():
            move = self.moves.get()
            if calculate_distance(move.point, self.rect) > 0:
                min_distance = 1.1
                best_neighbor = None
                move.n_steps += 1

                for key in self.table.keys():
                    current_distance = calculate_distance(move.point, self.table[key].rect)
                    if current_distance < min_distance:
                        min_distance = current_distance
                        best_neighbor = self.table[key]

                if best_neighbor is None:
                    move.status = "error"
                else:
                    best_neighbor.add_move(move)
                return False
            else:
                return True
        else:
            return False

    def update(self):
        for move in self.new_moves:
            self.moves.put(move)
        self.new_moves = []


class CAN():
    def __init__(self, n):
        self.n = n
        self.max_neighbors = 10
        self.spaces = []
        self.moves = []

        self.nodes = []
        self.nodes.append(Node(0, (0.0, 0.0, 1.0, 1.0)))
        self.spaces.append(1)
        for i in range(self.n - 1):
            node_id = self.spaces.index(max(self.spaces))
            flag = self.add_node(node_id)
            if flag:
                space = (self.nodes[node_id].rect[3] - self.nodes[node_id].rect[1]) * (
                            self.nodes[node_id].rect[2] - self.nodes[node_id].rect[0])
                self.spaces.append(space)
                self.spaces[node_id] = space


    def add_node(self, node_id):

        for key in list(self.nodes[node_id].table.keys()):
            if len(self.nodes[node_id].table[key].table) == 10:
                return False

        def check_if_neighbor(rect1, rect2):
            if rect1 == rect2:
                return False
            x1, y1, x2, y2 = rect1
            x12 = (x1 + x2) / 2
            y12 = (y1 + y2) / 2
            flag = False
            flag =  (calculate_distance((x1, y1), rect2) == 0
                                  and calculate_distance((x1, y2), rect2) == 0
                                  and calculate_distance((x1, y12), rect2) == 0)
            flag = flag or (calculate_distance((x1, y2), rect2) == 0
                                  and calculate_distance((x2, y2), rect2) == 0
                                  and calculate_distance((x12, y2), rect2) == 0)
            flag = flag or (calculate_distance((x2, y1), rect2) == 0
                                  and calculate_distance((x1, y1), rect2) == 0
                                  and calculate_distance((x12, y1), rect2) == 0)
            flag = flag or (calculate_distance((x2, y2), rect2) == 0
                                  and calculate_distance((x2, y1), rect2) == 0
                                  and calculate_distance((x2, y12), rect2) == 0)
            return flag


        if self.nodes[node_id].rect[2] - self.nodes[node_id].rect[0] == self.nodes[node_id].rect[3] - self.nodes[node_id].rect[1]:
            rect1 = self.nodes[node_id].rect[0], self.nodes[node_id].rect[1], self.nodes[node_id].rect[0] + (self.nodes[node_id].rect[2] - self.nodes[node_id].rect[0]) / 2, self.nodes[node_id].rect[3]
            rect2 = self.nodes[node_id].rect[0] + (self.nodes[node_id].rect[2] - self.nodes[node_id].rect[0]) / 2, self.nodes[node_id].rect[1], self.nodes[node_id].rect[2], self.nodes[node_id].rect[3]
        else:
            rect1 = self.nodes[node_id].rect[0], self.nodes[node_id].rect[1], self.nodes[node_id].rect[2], self.nodes[node_id].rect[1] + (self.nodes[node_id].rect[3] - self.nodes[node_id].rect[1]) / 2
            rect2 = self.nodes[node_id].rect[0], self.nodes[node_id].rect[1] + (self.nodes[node_id].rect[3] - self.nodes[node_id].rect[1]) / 2, self.nodes[node_id].rect[2], self.nodes[node_id].rect[3]


        self.nodes[node_id].rect = rect1

        table = self.nodes[node_id].table
        self.nodes.append(Node(len(self.nodes), rect2))

        for key in list(table.keys()):
            if check_if_neighbor(rect2, table[key].rect) or check_if_neighbor(table[key].rect, rect2):
                self.nodes[-1].add_neighbor(table[key])
                table[key].add_neighbor(self.nodes[-1])
            if not check_if_neighbor(rect1, table[key].rect) and not check_if_neighbor(table[key].rect, rect1):
                table[key].remove_neighbor(self.nodes[node_id].id)
                self.nodes[node_id].remove_neighbor(key)

        self.nodes[node_id].add_neighbor(self.nodes[-1])
        self.nodes[-1].add_neighbor(self.nodes[node_id])
        return True


    def start_move(self, target_position, sender_id):
        x, y = target_position
        move = Movement(self.nodes[sender_id], (x, y))
        self.moves.append(move)
        self.nodes[sender_id].add_move(move)

    def show(self):
        size = 512
        field = numpy.ones((513, 513, 3), numpy.uint8) * 255
        for node in self.nodes:
            field = cv2.rectangle(field, (int(node.rect[0] * size), int(node.rect[1] * size)), (int(node.rect[2] * size), int(node.rect[3] * size)), (0, 0, 0), 1)

        list_for_lenght_path = []
        target_point = (0, 0)

        shift = 10
        i = 0
        while True:
            flag = False
            for node in self.nodes:
               flag += node.make_step()
            for node in self.nodes:
                node.update()

            lenght_path = 0

            for move in self.moves:
                list_for_lenght_path.append(
                    ((move.node.rect[0] + move.node.rect[2]) / 2, (move.node.rect[1] + move.node.rect[3]) / 2))
                target_point = move.point
                print('node', move.node.id, (move.node.rect[0] + move.node.rect[2]) / 2,
                      (move.node.rect[1] + move.node.rect[3]) / 2, 'target point', move.point, 'step', move.n_steps)

                x, y, x2, y2 = move.node.rect
                if shift == 210:
                    shift = 10
                else:
                    shift += 10

                color = (225 - shift, 225 - shift, 0)

                field = cv2.rectangle(field, (int(x * size), int(y * size)), (int(x2 * size), int(y2 * size)), color, -1)
                field = cv2.circle(field, (int(move.point[0] * size), int(move.point[1] * size)), 10,
                                   (0, 225, 0), -1)

            if not flag:
                cv2.imshow("Step " + str(i), field)

            if flag:
                print('stop')
                cv2.imshow("Stop ", field)
                break
            i += 1

        del list_for_lenght_path[len(list_for_lenght_path) - 1]
        list_for_lenght_path.append(target_point)

        for i in range(0, len(list_for_lenght_path) - 1):
            lenght_path_ = (((list_for_lenght_path[i][0] - list_for_lenght_path[i+1][0]) ** 2) + ((list_for_lenght_path[i][1] - list_for_lenght_path[i+1][1]) ** 2)) ** 0.5
            lenght_path += lenght_path_

        print('path lenght', lenght_path)

        lenght_path_ideal = (((list_for_lenght_path[0][0] - list_for_lenght_path[len(list_for_lenght_path) - 1][0]) ** 2) + ((list_for_lenght_path[0][1] - list_for_lenght_path[len(list_for_lenght_path)-1][1]) ** 2)) ** 0.5
        print('ideal path lenght', lenght_path_ideal)
        list_amount_neighbors = []
        for node in self.nodes:
            list_amount_neighbors.append(len(node.table))

        #print('amount neighbors', list_amount_neighbors)
        print('amount neighbors min', min(list_amount_neighbors),
              'median', statistics.median(list_amount_neighbors),
              'max', max(list_amount_neighbors),
              'sum', sum(list_amount_neighbors))
        amount_moves = i
        print('amount steps', amount_moves)
        cv2.waitKey(0)
        return list_amount_neighbors, lenght_path_ideal, lenght_path, amount_moves

def calculate_distance(point, rect):
    def calculate_euclidean_distance(point, rect):

        def rect_point(rect):
            x1, y1, x2, y2 = rect
            x, y = point

            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            if y1 == y2:
                if x >= x1 and x <= x2:
                    return abs(y - y1)
                else:
                    return min((x - x1) ** 2 + (y - y1) ** 2,
                               (x - x2) ** 2 + (y - y2) ** 2)
            elif x1 == x2:
                if y >= y1 and y <= y2:
                    return abs(x - x1)
                else:
                    return min((x - x1) ** 2 + (y - y1) ** 2,
                               (x - x2) ** 2 + (y - y2) ** 2)

        x1, y1, x2, y2 = rect
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        if x1 <= point[0] and point[0] <= x2 and y1 <= point[1] and point[1] <= y2:
            return 0

        return min(rect_point((x1, y1, x1, y2)), rect_point((x1, y2, x2, y2)),
                   rect_point((x2, y2, x2, y1)), rect_point((x2, y1, x1, y1)))

    distance = 1.1
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            distance = min(distance, calculate_euclidean_distance((point[0] + i, point[1] + j), rect))
    return distance

test_list_amount_neighbors = []
test_lenght_path_ideal = []
test_lenght_path = []
test_amount_moves = []

graph25 = CAN(1000)
graph25.start_move((0.35, 0.45), 0)
list_amount_neighbors, lenght_path_ideal, lenght_path, amount_moves = graph25.show()
test_list_amount_neighbors.append(list_amount_neighbors)
test_lenght_path_ideal.append(lenght_path_ideal)
test_lenght_path.append(lenght_path)
test_amount_moves.append(amount_moves)

graph13 = CAN(1000)
graph13.start_move((0.25, 0.25), 0)
list_amount_neighbors, lenght_path_ideal, lenght_path, amount_moves = graph13.show()
test_list_amount_neighbors.append(list_amount_neighbors)
test_lenght_path_ideal.append(lenght_path_ideal)
test_lenght_path.append(lenght_path)
test_amount_moves.append(amount_moves)



graph10 = CAN(1000)
graph10.start_move((0.79, 0.1), 0)
list_amount_neighbors, lenght_path_ideal, lenght_path, amount_moves = graph10.show()
test_list_amount_neighbors.append(list_amount_neighbors)
test_lenght_path_ideal.append(lenght_path_ideal)
test_lenght_path.append(lenght_path)
test_amount_moves.append(amount_moves)

graph5 = CAN(1000)
graph5.start_move((0.08, 0.1), 0)
list_amount_neighbors, lenght_path_ideal, lenght_path, amount_moves = graph5.show()
test_list_amount_neighbors.append(list_amount_neighbors)
test_lenght_path_ideal.append(lenght_path_ideal)
test_lenght_path.append(lenght_path)
test_amount_moves.append(amount_moves)

total_deviation = 0
for i in range(0, len(test_lenght_path_ideal)):
    total_deviation += test_lenght_path[i] - test_lenght_path_ideal[i]
total_deviation /= len(test_lenght_path_ideal)

print('middle deviation path lenght', total_deviation)
print('amount neighbors min', min(min(x) for x in test_list_amount_neighbors),
              'median', statistics.median(statistics.median(x) for x in test_list_amount_neighbors),
              'max', max(max(x) for x in test_list_amount_neighbors))
print('amount moves', test_amount_moves)