import copy
import random
import time
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
        self.path = []  # 用字符串存储所有运动:"grab","shoot","forw","tr","tl"
        self.visited.add((1,1))


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
        time.sleep(0.9)
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
        self.visited.add((self.x,self.y))

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