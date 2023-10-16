import time

from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGraphicsScene, QGraphicsView, \
    QGraphicsPixmapItem, QGroupBox, QRadioButton
from PySide2.QtCore import Qt, QRectF, QByteArray
from PySide2.QtGui import QBrush, QColor, QPen
from PySide2.QtGui import QPixmap
from Agent import Agent
import random
import copy
from PySide2.QtCore import QRectF, QPoint
from PySide2.QtGui import QPainter
from PySide2.QtCore import QPointF, QPropertyAnimation

# 定义颜色
WHITE = QColor(255, 255, 255)
BLACK = QColor(0, 0, 0)
GREY = QColor(200, 200, 200)
BLUE = QColor(0, 0, 255)
light_blue = QColor(173, 216, 230)
brown = QColor(210, 180, 140)
gray = QColor(128, 128, 128)


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


class WumpusWorld(QMainWindow):
    def __init__(self):
        super().__init__()
        # 主体：
        self.Map = [[Room() for _ in range(6)] for _ in range(6)]  # 地图
        self.init_grids()
        self.agent = Agent()  # 智能体
        self.win = 0  # 记录输赢
        self.ratio_back = 0.6

        # 箭
        self.shoot = 0
        self.a_x = 0
        self.a_y = 0

        # 设置窗口大小和标题
        self.window_width = 1024
        self.window_height = 720
        self.resize(self.window_width, self.window_height)
        self.setWindowTitle("Wumpus World")

        # 创建模式选择框
        self.mode_group = QGroupBox("Mode Selection", self)
        self.mode_group.setGeometry(780, 50, 180, 80)

        # 创建复选框
        self.conservative_mode = QRadioButton("Conservative", self.mode_group)
        self.conservative_mode.setGeometry(10, 20, 160, 20)
        self.conservative_mode.setChecked(True)  # 默认选择保守模式

        self.aggressive_mode = QRadioButton("Aggressive", self.mode_group)
        self.aggressive_mode.setGeometry(10, 45, 160, 20)

        # 创建按钮
        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(780, 150, 180, 50)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setGeometry(780, 220, 180, 50)

        self.start_button.clicked.connect(self.explore)
        self.reset_button.clicked.connect(self.reset)
        self.conservative_mode.toggled.connect(self.update_mode)
        self.aggressive_mode.toggled.connect(self.update_mode)

        # 创建显示分数的标签
        self.score_label = QLabel("Score: 0", self)
        self.score_label.setGeometry(780, 280, 180, 50)
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("QLabel{color: rgb(65,105,255);font-size: 20px; font-weight: bold;}")

        # 显示输赢：
        self.win_label = QLabel("", self)
        self.win_label.setGeometry(780, 350, 180, 50)
        self.win_label.setAlignment(Qt.AlignCenter)
        self.win_label.setStyleSheet("QLabel{color: rgb(255,97,3);font-size: 25px; font-weight: bold;}")

        # 小地图标签：
        self.minimap_label = QLabel("Knowledge-Base", self)
        self.minimap_label.setGeometry(780, 420, 180, 50)
        self.minimap_label.setAlignment(Qt.AlignCenter)

        # 设置网格参数
        self.grid_size = 6
        self.cell_size = int(self.window_height * 0.9) // self.grid_size  # 更新单元格大小以适应窗口高度
        self.grid_offset_x = 50  # X轴偏移
        self.grid_offset_y = (self.window_height - (self.cell_size * self.grid_size)) // 2
        # 制定每个网格左上角点的位置
        x = self.grid_offset_x
        y = self.grid_offset_y
        self.cell_loc = [[[] for _ in range(6)] for _ in range(6)]
        for i in range(6):
            for j in range(6):
                self.cell_loc[i][j] = [x + self.cell_size * i, y + self.cell_size * j]

        # 加载图片
        agent_image = QPixmap('img/agent.PNG')
        wumpus_image = QPixmap('img/wumpus.PNG')
        stench_image = QPixmap('img/stench.PNG')
        pit_image = QPixmap('img/pit.PNG')
        breeze_image = QPixmap('img/breeze.PNG')
        dead_image = QPixmap('img/dead.PNG')
        find_gold_image = QPixmap('img/findgold.PNG')
        gold_image = QPixmap('img/gold.PNG')
        shoot_image = QPixmap("img/shoot.PNG")
        scared_img = QPixmap("img/scared.png")
        bump_iamge = QPixmap("img/bump.png")

        self.img = {
            "agent": agent_image,
            "wumpus": wumpus_image,
            "stench": stench_image,
            "pit": pit_image,
            "breeze": breeze_image,
            "dead": dead_image,
            "findgold": find_gold_image,
            "gold": gold_image,
            "shoot": shoot_image,
            "scared": scared_img,
            "bump": bump_iamge
        }

        for key in self.img:
            img = self.img[key]
            img = img.scaled(self.cell_size // 2, self.cell_size // 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img[key] = img

    def update_mode(self):
        if self.conservative_mode.isChecked():
            self.ratio_back = 0.6
        elif self.aggressive_mode.isChecked():
            self.ratio_back = 0.9

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), WHITE)
        self.draw_grid()
        self.draw_minimap()
        self.paint_map()
        self.score_label.setText("Score: " + str(self.agent.score))
        if self.win == 1:
            self.win_label.setText("YOU WIN !!!")
        elif self.agent.life == 0:
            self.win_label.setText("YOU Died !!!")
        painter.end()

    def draw_grid(self):
        painter = QPainter(self)
        # 设置网格线的颜色和宽度
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(1)

        for i in range(self.grid_size + 1):
            # 绘制垂直线
            painter.drawLine(self.grid_offset_x + self.cell_size * i, self.grid_offset_y + 0,
                             self.grid_offset_x + self.cell_size * i,
                             self.grid_offset_y + self.cell_size * self.grid_size)

            # 绘制水平线
            painter.drawLine(0 + self.grid_offset_x, self.cell_size * i + self.grid_offset_y,
                             self.cell_size * self.grid_size + self.grid_offset_x,
                             self.cell_size * i + self.grid_offset_y)

            # 填充网格背景色
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                rect = QRectF(i * self.cell_size + self.grid_offset_x, j * self.cell_size + self.grid_offset_y,
                              self.cell_size, self.cell_size)
                if i == 0 or j == 0 or i == 5 or j == 5:
                    color = gray
                else:
                    color = WHITE
                brush = QBrush(color)
                painter.setPen(pen)
                painter.setBrush(brush)
                painter.drawRect(rect)

    def draw_minimap(self):
        painter = QPainter(self)
        # 设置小地图在第9个区域中心，边长为200
        minimap_size = 200
        minimap_x = self.window_width - 50 - minimap_size
        minimap_y = self.window_height - 50 - minimap_size

        # 绘制小地图的网格
        cell_size = minimap_size // 6
        for i in range(6):
            for j in range(6):
                cell_x = minimap_x + i * cell_size
                cell_y = minimap_y + j * cell_size
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawRect(cell_x, cell_y, cell_size, cell_size)

        def draw_state():
            for i in range(6):
                for j in range(6):
                    grid_x = minimap_x + (i) * cell_size
                    grid_y = minimap_y + (j) * cell_size
                    if (i, j) in self.agent.knowledge_base:
                        if self.agent.knowledge_base[(i, j)]["iswall"] == 1:
                            painter.setBrush(GREY)
                            painter.drawRect(grid_x, grid_y, cell_size, cell_size)
                        elif self.agent.knowledge_base[(i, j)]["stench"] == 1:
                            painter.setBrush(brown)
                            painter.drawRect(grid_x, grid_y, cell_size, cell_size)
                        elif self.agent.knowledge_base[(i, j)]["breeze"] == 1:
                            painter.setBrush(light_blue)
                            painter.drawRect(grid_x, grid_y, cell_size, cell_size)
                        painter.setBrush(GREY)
                        painter.drawEllipse(grid_x + cell_size // 2 - 5, grid_y + cell_size // 2 - 5,
                                            10, 10)
        draw_state()
        # 绘制Agent在小地图上的位置
        agent_x = self.agent.x
        agent_y = self.agent.y
        agent_pos = self.cell_loc[agent_x][agent_y]
        agent_minimap_x = minimap_x + (agent_x) * cell_size
        agent_minimap_y = minimap_y + (agent_y) * cell_size
        painter.setBrush(QColor(65, 105, 255))
        painter.drawEllipse(agent_minimap_x + cell_size // 2 - 5, agent_minimap_y + cell_size // 2 - 5, 10, 10)

    # 重新生成对象
    def reset(self):
        self.agent = Agent()
        self.win = 0
        self.Map = [[Room() for _ in range(6)] for _ in range(6)]
        self.init_grids()
        self.win_label.setText("")

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
                # 设置pit
                elif (i != gold_x and j != gold_y) and (i != 1 and j != 1):
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
        self.repaint()

    def get_cell_loc(self, i, j):
        return self.cell_loc[i][j]

    def draw_pit(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x = x + 1.2 / 4 * self.cell_size
        y = y + 2 / 3 * self.cell_size
        img = self.img["pit"]
        img = img.scaled(self.cell_size // 2, self.cell_size // 4, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter = QPainter(self)
        painter.drawPixmap(QPoint(x, y), img)

    def draw_shoot(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["shoot"])
        painter.end()

    def draw_agent(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["agent"])
        painter.end()

    def draw_bump(self, i, j):  # 撞墙反应
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["bump"])
        painter.end()

    def draw_scared(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["scared"])
        painter.end()

    def draw_wumpus(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["wumpus"])
        painter.end()

    def draw_gold(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["gold"])
        painter.end()

    def draw_find_gold(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["findgold"])
        painter.end()

    def draw_dead(self, i, j):
        x, y = self.get_cell_loc(i, j)
        x += 1 / 4 * self.cell_size
        y += 1 / 4 * self.cell_size
        painter = QPainter(self)
        painter.drawPixmap(x, y, self.img["dead"])
        painter.end()

    def draw_breeze(self, i, j):
        x, y = self.get_cell_loc(i, j)
        light_blue = QColor(173, 216, 230)

        painter = QPainter(self)
        painter.setPen(light_blue)

        for line_y in range(y + 2, y + self.cell_size - 1, 4):
            painter.drawLine(x + 1, line_y, x - 1 + self.cell_size, line_y)

        painter.end()

    def draw_stench(self, i, j):
        x, y = self.get_cell_loc(i, j)
        brown = QColor(139, 69, 19)

        painter = QPainter(self)
        painter.setPen(brown)

        for line_x in range(x + 2, x + self.cell_size - 1, 4):
            painter.drawLine(line_x, y + 1, line_x, y + self.cell_size - 1)

        painter.end()

    def paint_map(self):
        for i in range(6):
            for j in range(6):
                x = self.get_cell_loc(i, j)[0]
                y = self.get_cell_loc(i, j)[1]
                # 墙：
                if self.Map[i][j].iswall == 1:
                    painter = QPainter(self)
                    painter.setBrush(QBrush())
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(x, y, self.cell_size, self.cell_size)
                    painter.end()
                    continue
                # 画物体
                if self.Map[i][j].pit == 1:
                    self.draw_pit(i, j)
                if self.Map[i][j].stench == 1:
                    self.draw_stench(i, j)
                if self.Map[i][j].breeze == 1:
                    self.draw_breeze(i, j)
                if self.Map[i][j].wumpus == 1:
                    self.draw_wumpus(i, j)
                if self.Map[i][j].gold == 1:
                    self.draw_gold(i, j)

        if self.agent.life == 1:
            if self.agent.sense["stench"] == 1 or self.agent.sense["breeze"] == 1:
                self.draw_scared(self.agent.x, self.agent.y)
            elif self.agent.sense["iswall"] == 1:
                self.draw_bump(self.agent.x, self.agent.y)
            elif self.agent.life == 1:
                self.draw_agent(self.agent.x, self.agent.y)
        else:
            self.draw_dead(self.agent.x, self.agent.y)
        if self.agent.sense["flicker"] == 1:
            self.draw_find_gold(self.agent.x, self.agent.y)
        if self.shoot == 1:
            self.draw_shoot(self.a_x, self.a_y)

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
        self.shoot = 1
        self.a_x = arrow_x
        self.a_y = arrow_y
        time.sleep(0.5)
        self.repaint()
        time.sleep(0.7)

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
        self.shoot = 0
        self.repaint()

    def grab(self):
        self.agent.grab()
        curx, cury = self.agent.x, self.agent.y
        self.agent.isGold = 1
        self.Map[curx][cury].flicker = 0
        self.Map[curx][cury].gold = 0
        self.agent.score += 1000

    def move_forward(self):
        self.agent.move_forward()
        self.check_environment()
        self.repaint()

    def check_environment(self):
        x, y = self.agent.x, self.agent.y
        current_room = self.Map[x][y]
        # 更新agent感知
        self.agent.sense["stench"] = current_room.stench
        self.agent.sense["breeze"] = current_room.breeze
        self.agent.sense["flicker"] = current_room.flicker
        self.agent.sense["iswall"] = current_room.iswall
        # 更新知识库
        c_sense = copy.deepcopy(self.agent.sense)
        self.agent.update_knowledge_base(x, y, senses=c_sense)
        # 检查是否掉入陷阱或遇到Wumpus
        if current_room.pit or current_room.wumpus:
            self.agent.life = 0
            self.agent.score -= 1000  # 掉入陷阱或遇到Wumpus会导致分数减少1000分
            self.repaint()
        # 检查是否撞墙
        if current_room.iswall:
            self.agent.sense["iswall"] = 1
        if current_room.gold:
            self.repaint()

    # 寻找金子的策略为逻辑判断
    def search_gold_dfs(self):
        self.repaint()
        if self.agent.life == 0:
            return
        if self.agent.isGold == 1:
            return
        x, y = self.agent.x, self.agent.y
        self.check_environment()  # 检查环境
        # 是否已死
        if not self.agent.life:
            self.agent.score -= 1000
            return
        # 是否撞墙
        if self.agent.sense["iswall"] == 1:
            self.agent.turn_right()
            self.agent.turn_right()
            self.move_forward()
            return
        # 如果有金子
        if self.agent.sense["flicker"] == 1:
            self.grab()
            self.Map[x][y].gold = 0
            self.Map[x][y].flicker = 0
            self.agent.sense["flicker"] = 0
            self.check_environment()
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
            # 如果怪物没死，以概率返回
            if self.agent.sense["scream"] == 0 and (x != 1 or y != 1):
                prob = random.random()
                if prob <= self.ratio_back:
                    self.agent.turn_right()
                    self.agent.turn_right()
                    self.move_forward()
                    return
        # 如果当前格子有风，以概率返回
        if self.agent.sense["breeze"] and (x != 1 or y != 1):
            prob = random.random()
            if prob <= self.ratio_back:
                self.agent.turn_right()
                self.agent.turn_right()
                self.move_forward()
                return
        # 加深搜索：
        available = []  # 可用路径
        direction = [  [0, 1],[-1, 0],[0, -1],[1, 0]]
        random.shuffle(direction)
        for move in direction:
            # 计算如果按某个方向走了之后的位置
            nx=x+move[0]
            ny=y+move[1]
            # 如果是墙，直接跳过
            if (nx,ny) in self.agent.knowledge_base and self.agent.knowledge_base[(nx,ny)]["iswall"]==1:
                continue
            # 如果没有走过，就可以走，加入available列表
            elif (nx,ny) not in self.agent.visited:
                available.insert(0,move)
            # 如果走过，但不是墙，也可以加入,但是往后排
            else:
                available.append(move)
        # available = []
        # direction = [[0, 1], [-1, 0], [0, -1], [1, 0]]
        # random.shuffle(direction)
        #
        # # 不同类别的走向
        # safe_visited = []
        # not_visited = []
        # unsafe_visited = []
        #
        # for move in direction:
        #     # 计算如果按某个方向走了之后的位置
        #     nx = x + move[0]
        #     ny = y + move[1]
        #     # 如果是墙，直接跳过
        #     if (nx, ny) in self.agent.knowledge_base and self.agent.knowledge_base[(nx, ny)]["iswall"] == 1:
        #         continue
        #     # 如果没有走过，就可以走，加入available列表
        #     elif (nx, ny) not in self.agent.visited:
        #         not_visited.append(move)
        #     # 如果走过，但不是墙，也可以加入
        #     else:
        #         # 如果已经走过的格子没有stench或breeze，加入safe_visited
        #         if (nx, ny) in self.agent.knowledge_base and not self.agent.knowledge_base[(nx, ny)]["stench"] and not \
        #         self.agent.knowledge_base[(nx, ny)]["breeze"]:
        #             safe_visited.append(move)
        #         else:
        #             unsafe_visited.append(move)
        #
        # # 将safe_visited加到available列表的前面
        # available = not_visited + safe_visited + unsafe_visited

        # 逼着agent一定走一个方向，不然可能就停着不动了
        while self.agent.life:
            # 拿出available中的每一个方案
            for move_ in available:
                nx_ = x + move_[0]
                ny_ = y + move_[1]
                if (nx_, ny_) in self.agent.knowledge_base and self.agent.knowledge_base[(nx_, ny_)]["iswall"] == 1:
                    continue
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
                self.move_forward()
                self.search_gold_dfs()
                if self.agent.life == 0:
                    return
                if self.agent.isGold == 1:
                    return

    # 返回时采用启发式
    def leave_world(self):
        # 根据到起点距离排序
        def manhattan(item):
            x = self.agent.x
            y = self.agent.y
            nx = x + item[0]
            ny = y + item[1]
            dis = nx - 1 + ny - 1  # 计算距离
            return dis

        back_visit = set()
        back_visit.add((self.agent.x, self.agent.y))  # 初始化
        while (1):
            x = self.agent.x
            y = self.agent.y
            available = []  # 可用路径
            direction = [[-1, 0], [1, 0], [0, -1], [0, 1]]
            random.shuffle(direction)
            for move in direction:
                nx = x + move[0]
                ny = y + move[1]
                if (nx, ny) in self.agent.visited and \
                        ((nx, ny) in self.agent.knowledge_base and self.agent.knowledge_base[(nx, ny)][
                            "iswall"] == 0):  # and\
                    # ((nx, ny) not in back_visit):
                    available.append(move)

            # 如果都不可用，则随便选一个：
            # if not available:
            #     random.shuffle(direction)
            #     for move in direction:
            #         nx = x + move[0]
            #         ny = y + move[1]
            #         if (nx, ny) in self.agent.visited and self.agent.knowledge_base[(nx, ny)]["iswall"] == 0:
            #             available.append(move)
            # 利用曼哈顿距离排序
            available = sorted(available, key=manhattan)
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
            self.move_forward()
            self.repaint()
            if self.agent.x == 1 and self.agent.y == 1:
                break

    def explore(self):
        self.search_gold_dfs()
        if self.agent.life:
            self.leave_world()
        if self.agent.x == 1 and self.agent.y == 1:
            self.win = 1


if __name__ == "__main__":
    app = QApplication([])
    wumpus_world = WumpusWorld()
    wumpus_world.show()
    app.exec_()
