import copy
import random
import pygame


class Room:
    def __init__(self, x=0, y=0, gold=0, pit=0, wumpus=0, breeze=0, stench=0, flicker=0, iswall=0):
        # 位置：
        self.x = x
        self.y = y
        # room里的东西：
        self.gold = gold
        self.pit = pit
        self.wumpus = wumpus
        # room的可感知值：
        self.breeze = breeze
        self.stench = stench
        self.flicker = flicker
        self.iswall = iswall


class World:
    def __init__(self):
        # 主体：
        self.Map = [[Room() for _ in range(6)] for _ in range(6)]  # 地图
        self.init_grids()
        self.agent = Agent()  # 智能体
        self.win = 0  # 记录输赢


    def init_grids(self):
        # 设置gold
        # 随机选择一个房间，但排除位置（1,1）的房间
        # 从剩余的房间中随机选择一个房间
        gold_x = random.randint(1, 4)
        gold_y = random.randint(1, 4)
        while gold_x == 1 and gold_y == 1:
            gold_x = random.randint(1, 4)
            gold_y = random.randint(1, 4)
        self.Map[gold_x][gold_y].gold = 1
        # 房间发光
        self.Map[gold_x][gold_y].flicker = 1
        # 设置wumpus
        wum_x = random.randint(1, 4)
        wum_y = random.randint(1, 4)
        while (wum_x == 1 and wum_y == 1) or (wum_x == gold_x and wum_y == gold_y):
            wum_x = random.randint(1, 4)
            wum_y = random.randint(1, 4)
        self.Map[wum_x][wum_y].wumpus = 1
        # 周围有stench
        self.Map[wum_x - 1][wum_y].stench = 1
        self.Map[wum_x + 1][wum_y].stench = 1
        self.Map[wum_x][wum_y - 1].stench = 1
        self.Map[wum_x][wum_y + 1].stench = 1

        for i in range(6):
            for j in range(6):
                # 周围的一圈是墙，每次应该先识别墙
                if i == 0 or j == 0 or i == 5 or j == 5:
                    self.Map[i][j].iswall = 1
                    continue
                # 设置pit
                if (i != wum_x and j != wum_y) and (i != gold_x and j != gold_y):
                    prob = random.random()
                    if prob <= 0.2:
                        self.Map[i][j].pit = 1
                        # 设置周围有breeze
                        self.Map[i - 1][j].breeze = 1
                        self.Map[i + 1][j].breeze = 1
                        self.Map[i][j - 1].breeze = 1
                        self.Map[i][j + 1].breeze = 1
                    else:
                        self.Map[i][j].pit = 0

    def print_map(self):
        for y in range(5, -1, -1):
            for x in range(6):
                room = self.Map[x][y]
                if room.iswall:
                    print("#", end=" ")
                elif room.gold:
                    print("G", end=" ")
                elif room.wumpus:
                    print("W", end=" ")
                elif room.pit:
                    print("P", end=" ")
                else:
                    print(".", end=" ")
            print()

    def shoot_arrow(self):
        self.agent.shoot_arrow()
        # 确定箭路径
        arrow_x, arrow_y = self.agent.x, self.agent.y
        arrow_dire = self.agent.face
        if arrow_dire == "r":
            arrow_x += 1
        elif arrow_dire == "l":
            arrow_x -= 1
        elif arrow_dire == "u":
            arrow_y += 1
        elif arrow_dire == "d":
            arrow_y -= 1
        # 检查有没有射中
        if self.Map[arrow_x][arrow_y].wumpus == 1:
            # 杀死wumpus：
            self.Map[arrow_x][arrow_y].wumpus = 0
            # 移除臭气：
            self.Map[arrow_x - 1][arrow_y].stench = 0
            self.Map[arrow_x + 1][arrow_y].stench = 0
            self.Map[arrow_x][arrow_y - 1].stench = 0
            self.Map[arrow_x][arrow_y + 1].stench = 0
            # 尖叫
            self.agent.sense["scream"] = 1


    def grab(self):
        self.agent.grab()
        curx, cury = self.agent.x, self.agent.y
        if self.Map[curx][cury].gold == 1:
            self.agent.isGold = 1
            self.Map[curx][cury].flicker = 0
            self.Map[curx][cury].gold = 0
            self.agent.score += 1000

    def check_environment(self):
        x, y = self.agent.x, self.agent.y
        current_room = self.Map[x][y]
        # 更新agent感知
        self.agent.sense["stench"] = current_room.stench
        self.agent.sense["breeze"] = current_room.breeze
        self.agent.sense["flicker"] = current_room.flicker
        self.agent.sense["iswall"] = current_room.iswall
        # 检查是否掉入陷阱或遇到Wumpus
        if current_room.pit or current_room.wumpus:
            self.agent.life = 0
            self.agent.score -= 1000  # 掉入陷阱或遇到Wumpus会导致分数减少1000分
        # 检查是否撞墙
        if current_room.iswall:
            self.agent.sense["iswall"] = 1

    # 寻找金子的策略为逻辑判断
    def search_gold(self):
        while (self.agent.isGold != 1):
            x, y = self.agent.x, self.agent.y
            self.agent.visited.add((x, y))
            self.check_environment()  # 检查环境
            # 是否已死
            if not self.agent.life:
                self.agent.score -= 1000
                return

            # 更新知识库
            c_sense = copy.deepcopy(self.agent.sense)
            self.agent.update_knowledge_base(x, y, senses=c_sense)

            # 是否撞墙
            if self.agent.sense["iswall"] == 1:
                self.agent.turn_right()
                self.agent.turn_right()
                self.agent.move_forward()
                continue
            # 如果有金子
            if self.agent.sense["flicker"] == 1:
                self.grab()
                return
            # 如果当前格子有臭味，以0.5的概率射箭，射箭之后检查
            if self.agent.sense["stench"]:
                if self.agent.arrow > 0:  # 如果有箭
                    prob = random.random()
                    if prob >= 0.0:  # 事实上，一旦有臭味就射出是赢的概率最大的
                        self.shoot_arrow()
                        if self.agent.sense["scream"] == 1:  # 如果射中了，更新环境
                            self.check_environment()
                            c_sense = copy.deepcopy(self.agent.sense)
                            self.agent.update_knowledge_base(x, y, senses=c_sense)
                # 如果怪物没死，以0.99的概率返回
                if self.agent.sense["scream"] == 0 and (x != 1 or y != 1):
                    prob = random.random()
                    if prob >= 0.01:
                        self.agent.turn_right()
                        self.agent.turn_right()
                        self.agent.move_forward()
                        continue
            # 如果当前格子有风，以0.99概率返回
            if self.agent.sense["breeze"] and (x != 1 or y != 1):
                prob = random.random()
                if prob >= 0.01:
                    self.agent.turn_right()
                    self.agent.turn_right()
                    self.agent.move_forward()
                    continue
            # 加深搜索：
            nx, ny = x, y
            for turn in range(4):
                # 转弯
                if turn == 0:
                    pass
                elif turn == 1:
                    self.agent.turn_right()
                elif turn == 2:
                    self.agent.turn_left()
                else:
                    self.agent.turn_right()
                    self.agent.turn_right()
                if self.agent.face == "r":
                    nx = x + 1
                    ny = y
                elif self.agent.face == "l":
                    nx = x - 1
                    ny = y
                elif self.agent.face == "u":
                    ny = y + 1
                    nx = x
                elif self.agent.face == "d":
                    ny = y - 1
                    nx = x
                # 如果这个位置已经走过了，就不走了
                # 这里可能陷入死循环，所以要设置一个概率让他可以访问走过来的路
                if (nx, ny) in self.agent.visited:
                    prob = random.random()
                    # 有0.7的概率返回，有0.3的概率直接往前走
                    if prob >= 0.3:
                        continue
                self.agent.move_forward()
                break

    # 返回时采用启发式
    def leave_world(self):
        # 根据到起点距离排序
        def manhattan(item):
            x = self.agent.x
            y = self.agent.y
            nx = x + move[0]
            ny = y + move[1]
            dis = nx - 1 + ny - 1  # 计算距离
            return dis

        back_visit = set()
        back_visit.add((self.agent.x, self.agent.y))  # 初始化
        while (self.agent.x != 1 or self.agent.y != 1):
            x = self.agent.x
            y = self.agent.y
            available = []  # 可用路径
            direction = [[-1, 0], [1, 0], [0, -1], [0, 1]]
            for move in direction:
                nx = x + move[0]
                ny = y + move[1]
                if (nx, ny) in self.agent.visited and self.agent.knowledge_base[(nx, ny)]["iswall"] == 0 and (
                        (nx, ny) not in back_visit):
                    available.append(move)
            # 利用曼哈顿距离排序
            available = sorted(available, key=manhattan)
            # 如果都不可用，则随便选一个：
            if not available:
                random.shuffle(direction)
                for move in direction:
                    nx = x + move[0]
                    ny = y + move[1]
                    if (nx, ny) in self.agent.visited and self.agent.knowledge_base[(nx, ny)]["iswall"] == 0:
                        available.append(move)

            move_ = available[0]
            # 加入返回时遍历过的set
            back_visit.add((x + move_[0], y + move_[1]))
            if move_ == [-1, 0]:
                if self.agent.face == "u":
                    self.agent.turn_left()
                elif self.agent.face == "d":
                    self.agent.turn_right()
                elif self.agent.face == "l":
                    pass
                elif self.agent.face == "r":
                    self.agent.turn_right()
                    self.agent.turn_right()
            elif move_ == [1, 0]:
                if self.agent.face == "u":
                    self.agent.turn_right()
                elif self.agent.face == "d":
                    self.agent.turn_left()
                elif self.agent.face == "l":
                    self.agent.turn_right()
                    self.agent.turn_right()
                elif self.agent.face == "r":
                    pass
            elif move_ == [0, -1]:
                if self.agent.face == "u":
                    self.agent.turn_left()
                    self.agent.turn_left()
                elif self.agent.face == "d":
                    pass
                elif self.agent.face == "l":
                    self.agent.turn_left()
                elif self.agent.face == "r":
                    self.agent.turn_right()
            elif move_ == [0, 1]:
                if self.agent.face == "u":
                    pass
                elif self.agent.face == "d":
                    self.agent.turn_right()
                    self.agent.turn_right()
                elif self.agent.face == "l":
                    self.agent.turn_right()
                elif self.agent.face == "r":
                    self.agent.turn_left()
            self.agent.move_forward()

    def explore(self):
        self.search_gold()
        if self.agent.life:
            self.leave_world()
        if self.agent.x == 1 and self.agent.y == 1:
            self.win = 1


class Agent:
    def __init__(self):
        # 设置属性
        # 状态值
        self.score = 0
        self.life = 1
        self.arrow = 1
        self.isGold = 0
        # 感官：
        self.sense = {"stench": 0, "breeze": 0, "flicker": 0, "iswall": 0, "scream": 0}
        # 位置信息
        self.x = 1
        self.y = 1
        self.face = "r"  # 设置四个朝向：l,r,u,d
        # agent的认知库
        self.knowledge_base = {}  # 存储已知房间的信息
        self.visited = set()
        self.path=[]  # 用字符串存储所有运动:"grab","shoot","forw","tr","tl"

    def update_knowledge_base(self, x, y, senses):
        self.knowledge_base[(x, y)] = senses

    def grab(self):
        self.score -= 1
        self.path.append("grab")

    def shoot_arrow(self):
        self.arrow -= 1
        self.score -= 10
        self.path.append("shoot")

    def move_forward(self):
        if self.face == "r":
            self.x += 1
        elif self.face == "l":
            self.x -= 1
        elif self.face == "u":
            self.y += 1
        elif self.face == "d":
            self.y -= 1
        self.score -= 1
        self.path.append("forw")

    def turn_left(self):
        if self.face == "r":
            self.face = "u"
        elif self.face == "u":
            self.face = "l"
        elif self.face == "l":
            self.face = "d"
        elif self.face == "d":
            self.face = "r"
        self.score -= 1
        self.path.append("tl")

    def turn_right(self):
        if self.face == "r":
            self.face = "d"
        elif self.face == "d":
            self.face = "l"
        elif self.face == "l":
            self.face = "u"
        elif self.face == "u":
            self.face = "r"
        self.score -= 1
        self.path.append("tr")


def performance_test(num):
    n_win = 0
    score=0
    score_win=0
    n_operate=0
    len_path=0
    for i in range(num):
        world = World()
        world.explore()
        score += world.agent.score
        if world.win == 1:
            n_win += 1
            score_win+=world.agent.score
            n_operate+=len(world.agent.path)
            len_path+=len([x for x in world.agent.path if x=="forw"])
    print("The succcess ratio is: " + str(n_win / num) )
    print("The Average score is: " + str(score / num) )
    print("The Average winning score is: " + str(score_win/ n_win))
    print("The Average winning Operate number is: " + str(n_operate / n_win))
    print("The Average winning path length is:"+ str(len_path / n_win))



def main():
    pass
    # world = World()
    # world.print_map()
    # world.display()
    # world.explore()
    # if world.win == 1:
    #     print("success")
    # else:
    #     print("Failed")


if __name__ == "__main__":
    main()
    performance_test(10000)
