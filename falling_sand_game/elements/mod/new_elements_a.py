# -*- coding: utf-8 -*-
from ..base import Element, Powder, Liquid, Solid, Gas, StaticSolid, Movable
import random
import curses
import math

# 1. 炸药 (Explosive)
class Explosive(Solid):
    key = 'D'
    name = '炸药'
    char = 'D'
    color = (curses.COLOR_RED, curses.COLOR_BLACK, curses.A_BOLD) # 醒目的红色
    density = 15
    is_static = True
    is_solid = True
    is_flammable = True # 可以被点燃
    dissolvable_by_acid = True
    blast_radius = 5 # 爆炸半径
    fuse_frames = 5 # 点燃后几帧爆炸

    # 内部状态
    is_lit = False
    lit_timer = 0

    def __init__(self, y, x):
        super().__init__(y, x)
        self.is_lit = False
        self.lit_timer = 0

    # 检查是否被点燃（例如，旁边是火、余烬、导火索或燃烧中的炸药）
    def _check_ignition(self, grid):
        if self.is_lit:
            return True

        # 检查周围（正交+对角）是否有热源或可点燃物
        check_coords = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dy, dx in check_coords:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if neighbor and not neighbor.processed:
                    # 检查热源属性
                    if neighbor.is_heat_source:
                         return True
                    # 检查是否是导火索
                    if neighbor.key == 'U':
                         return True
                    # 检查是否是燃烧中的炸药或炸弹
                    if (neighbor.key == 'D' and getattr(neighbor, 'is_lit', False)) or \
                       (neighbor.key == 'B' and getattr(neighbor, 'is_lit', False)):
                         return True

        return False

    def run_interactions(self, grid):
        if self.processed: return

        # 如果未点燃，检查是否需要点燃
        if not self.is_lit:
            if self._check_ignition(grid):
                self.is_lit = True
                self.lit_timer = self.fuse_frames
                # 可选：改变外观 indicating it's lit
                # self.char = '*' # Example visual change
                self.tags.append("lit") # Add a tag for visual distinction in Game.draw

        # 如果已点燃，处理计时和爆炸
        if self.is_lit:
            self.lit_timer -= 1
            if self.lit_timer <= 0:
                # --- 爆炸！ ---
                # 移除自身
                grid.set_element(self.y, self.x, None)
                self.processed = True # 自己消失了

                # 在爆炸半径内生成火
                for dy in range(-self.blast_radius, self.blast_radius + 1):
                    for dx in range(-self.blast_radius, self.blast_radius + 1):
                        # 只在圆形半径内
                        dist = math.sqrt(dy**2 + dx**2)
                        if dist <= self.blast_radius:
                            ny, nx = self.y + dy, self.x + dx
                            if grid.is_valid(ny, nx):
                                target_element = grid.get_element(ny, nx)
                                # 只在空地或可燃物上生成火，避免替换墙壁等
                                if target_element is None or (target_element.is_flammable and target_element.key != 'F'):
                                    # 使用工厂方法创建火
                                    new_fire = grid.create_element('F', ny, nx)
                                    if new_fire:
                                         # 将新生成的火标记为已处理，避免连锁反应
                                         new_fire.processed = True
                                         grid.set_element(ny, nx, new_fire)
                return # 爆炸完成

        # 如果没有爆炸，且没有被点燃，标记为已处理
        if not self.processed:
             self.processed = True

    # 可选：如果需要根据状态改变绘制字符或颜色
    def get_drawing_info(self):
        if self.is_lit:
            # 闪烁效果可以在 Game.draw 中根据 tags 实现
            return '*', self.color_pair_index # 点燃后用 '*' 字符表示
        else:
            return self.char, self.color_pair_index

# 2. 炸弹 (Bomb)
class Bomb(Solid):
    key = 'B' # 使用 B，余烬是 'b'
    name = '炸弹'
    char = 'B'
    color = (curses.COLOR_YELLOW, curses.COLOR_BLACK, curses.A_BOLD) # 黄色
    density = 20 # 比炸药略重
    is_static = False # 可以被点燃后下落，所以不是完全静态
    is_solid = True
    is_flammable = True # 可以被点燃
    dissolvable_by_acid = True

    # 内部状态
    is_lit = False
    lit_timer = 20 # 点燃后 20 帧爆炸
    blast_radius = 7 # 爆炸半径比炸药大
    fall_speed = 1 # 点燃后每帧尝试下落的距离

    def __init__(self, y, x):
        super().__init__(y, x)
        self.is_lit = False
        self.lit_timer = 0
        self.is_static = False # 默认设置为可移动 (被点燃后)

    # 检查是否被点燃（与炸药类似）
    def _check_ignition(self, grid):
        if self.is_lit:
            return True
        check_coords = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dy, dx in check_coords:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if neighbor and not neighbor.processed:
                    if neighbor.is_heat_source: return True
                    if neighbor.key == 'U': return True
                    if (neighbor.key == 'D' and getattr(neighbor, 'is_lit', False)) or \
                       (neighbor.key == 'B' and getattr(neighbor, 'is_lit', False)): return True
        return False

    def update(self, grid):
        if self.processed: return

        # 如果未点燃，检查是否需要点燃
        if not self.is_lit:
            if self._check_ignition(grid):
                self.is_lit = True
                self.lit_timer = self.lit_timer # 启动计时器
                self.is_static = False # 点燃后变为非静态，可以下落
                self.tags.append("lit") # 添加标签

        # 如果已点燃
        if self.is_lit:
            self.lit_timer -= 1

            # --- 尝试下落 ---
            moved = False
            # 尝试直线下落
            potential_y = self.y + self.fall_speed
            # 检查下落路径上的所有格子
            check_ys = range(self.y + 1, potential_y + 1) if potential_y > self.y else []

            target_y = self.y # 默认停留在原地
            can_fall = True

            for cy in check_ys:
                 if not grid.is_valid(cy, self.x):
                     can_fall = False
                     break # 撞到底部边界
                 element_at_check = grid.get_element(cy, self.x)
                 if element_at_check is not None:
                     # 撞到非空元素，检查是否能穿过或替换
                     # 炸弹比较重，可以替换液体和气体
                     if element_at_check.is_liquid or element_at_check.is_gas:
                         # 理论上可以替换，但为了简单，这里只实现穿过空地
                         # 如果需要替换，逻辑会复杂一点 (swap)
                         pass # 暂时忽略替换逻辑，只检查能否穿过 None
                     else:
                         # 撞到固体或粉末，停在上一个空地
                         target_y = cy - 1 if cy > self.y else self.y
                         can_fall = False
                         break
                 else:
                     target_y = cy # 可以落到这个空地

            if can_fall and target_y > self.y:
                 # 移动到目标位置
                 if self._move_to(grid, target_y, self.x):
                     moved = True

            # 如果没有成功直线下落，尝试对角线？
            # 简单起见，燃烧中的炸弹只尝试直线下落，不左右流动或对角线
            # 如果需要对角线，可以参考 Powder 或 Liquid 的移动逻辑

            # --- 检查是否爆炸 ---
            if self.lit_timer <= 0:
                # --- 爆炸！ ---
                grid.set_element(self.y, self.x, None) # 移除自身
                self.processed = True # 自己消失了

                # 在爆炸半径内生成火
                for dy in range(-self.blast_radius, self.blast_radius + 1):
                    for dx in range(-self.blast_radius, self.blast_radius + 1):
                        dist = math.sqrt(dy**2 + dx**2)
                        if dist <= self.blast_radius:
                            ny, nx = self.y + dy, self.x + dx
                            if grid.is_valid(ny, nx):
                                target_element = grid.get_element(ny, nx)
                                if target_element is None or (target_element.is_flammable and target_element.key != 'F'):
                                    new_fire = grid.create_element('F', ny, nx)
                                    if new_fire:
                                         new_fire.processed = True
                                         grid.set_element(ny, nx, new_fire)
                return # 爆炸完成

        # 如果未被点燃，或者点燃后未爆炸且未移动，标记为已处理
        # 如果点燃后移动了，_move_to 会设置 processed=True
        if not self.processed:
             self.processed = True


    def get_drawing_info(self):
        if self.is_lit:
            # 点燃后闪烁或改变颜色？例如，橙色闪烁
            # curses.A_BLINK 属性在 Game.draw 中根据 tags 实现
            return self.char, self.color_pair_index # 仍然使用原字符和颜色对，通过 tag 添加视觉效果
        else:
            return self.char, self.color_pair_index


# 4. 虫 (Bug)
class Bug(Movable): # 虫子是可移动的活物
    key = 'w'
    name = '虫'
    char = 'w'
    color = (curses.COLOR_YELLOW, curses.COLOR_GREEN, curses.A_DIM) # 黄色在绿色背景上 (虫子在草地/泥土上)
    density = 0.5 # 虫子很轻
    is_static = False # 虫子会移动
    is_solid = True # 占据一个格子，不像气体或液体流动
    is_flammable = True # 可以被烧死
    dissolvable_by_acid = True # 酸可以腐蚀虫子

    move_chance = 0.3 # 每帧移动的几率
    reproduce_chance = 0.001 # 繁殖几率 (低)
    reproduce_min_neighbors = 1 # 需要至少一个相邻的虫子才能繁殖

    # 移动和繁殖检查方向 (正交)
    MOVE_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    REPRODUCE_CHECKS = MOVE_DIRECTIONS # 繁殖检查正交方向

    def run_interactions(self, grid):
        if self.processed: return

        # --- 繁殖 ---
        bug_neighbors = []
        for dy, dx in self.REPRODUCE_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # 检查是否是另一个虫子 (key == 'W') 并且未被处理
                if neighbor and neighbor.key == 'W' and not neighbor.processed:
                    bug_neighbors.append((ny, nx, neighbor))

        if len(bug_neighbors) >= self.reproduce_min_neighbors:
            # 检查是否有空闲的相邻格子用于繁殖
            empty_spots = []
            for dy, dx in self.REPRODUCE_CHECKS:
                 ny, nx = self.y + dy, self.x + dx
                 if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
                      empty_spots.append((ny, nx))

            if empty_spots and random.random() < self.reproduce_chance:
                gy, gx = random.choice(empty_spots)
                # 使用工厂方法创建新的虫子实例
                new_bug = Bug(gy, gx) # 或者 grid.create_element('W', gy, gx)
                if new_bug:
                    new_bug.tags = list(self.tags) # 复制标签
                    grid.set_element(gy, gx, new_bug)
                    # 新生成的虫子不立即处理，下一帧自然更新

        # --- 移动 --- (在繁殖后尝试移动)
        if random.random() < self.move_chance:
            random.shuffle(self.MOVE_DIRECTIONS)
            for dy, dx in self.MOVE_DIRECTIONS:
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    target_element = grid.get_element(ny, nx)
                    # 虫子可以移动到空地，或者挤走气体/液体 (密度判断)
                    if target_element is None or target_element.is_gas or target_element.is_liquid: # 或者 self._can_displace(target_element):
                        if self._move_to(grid, ny, nx):
                            # 成功移动，标记为已处理
                            self.processed = True
                            return # 移动完成，退出交互和更新

                    # 可选：虫子是否可以爬上墙壁或挤开非常轻的粉末？这里先不实现。

        # 如果没有移动 (包括移动失败)，标记为已处理
        if not self.processed:
            self.processed = True

    # Bug 不会自己因为重力下落，所以覆盖 update 方法，只调用 run_interactions
    # 或者从 Solid 继承而不是 Movable，但 Solid 通常是静态的。
    # 从 Element 继承，然后实现自己的移动逻辑更合适。
    # 但是现有的 Movable 提供了 _move_to/_swap_with，所以继承 Movable 并覆盖 update 是一个选项。
    # 考虑到 Bug 不需要像 Powder/Liquid 那样复杂的重力/流动逻辑，
    # 继承 Movable 并覆盖 update 来实现随机行走更简洁。

    def update(self, grid):
        """Bug's update logic: primarily handles interactions (reproduction) and random movement."""
        if self.processed:
            return

        # Run interactions (includes reproduction check)
        self.run_interactions(grid)

        # Note: run_interactions might set self.processed = True if it successfully moves.
        # If it didn't move, we check processed status again before potential re-processing.

        # If not processed by interaction (e.g., didn't move or reproduce), mark processed.
        # The movement logic is inside run_interactions for Bug.
        if not self.processed:
            self.processed = True


# 5. 玻璃粉末 (GlassPowder) - 可熔化成玻璃，被火烧或岩浆接触
class GlassPowder(Powder):
    key = 'g' # 使用小写 g
    name = '玻璃粉末'
    char = 'g'
    color = (curses.COLOR_CYAN, -1, curses.A_DIM) # 淡青色
    density = 6.2 # 比沙子略重
    melt_chance = 0.1 # 熔化几率
    dissolvable_by_acid = True

    # 检查热源方向 (正交+对角)
    HEAT_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def run_interactions(self, grid):
        """Glass Powder checks for heat sources to melt into Glass."""
        if self.processed: return

        is_heated = False
        for dy, dx in self.HEAT_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # 检查是否是热源 (火、岩浆、燃烧中的铝热剂等)
                if neighbor and neighbor.is_heat_source:
                    is_heated = True
                    break

        if is_heated and random.random() < self.melt_chance:
            # 熔化成玻璃 (key 'X')
            new_glass = grid.create_element('X', self.y, self.x)
            if new_glass:
                 new_glass.tags = list(self.tags) # 复制标签
                 grid.set_element(self.y, self.x, new_glass)
                 # 玻璃是静态的，不立即处理
            self.processed = True # 粉末消失
            return

        # Powder update logic will run after interactions if not processed

# 6. 腐蚀气体 (CorrosiveGas) - 向上飘散，腐蚀接触的元素
class CorrosiveGas(Gas):
    key = 'x' # 使用小写 x
    name = '腐蚀气体'
    char = 'x'
    color = (curses.COLOR_YELLOW, curses.COLOR_RED, curses.A_DIM) # 黄色在红色背景上，淡色
    density = -4.8 # 比蒸汽/烟略轻
    rise_speed = 1
    spread_factor = 2
    dissipate_chance = 0.01 # 会逐渐消散
    corrode_chance = 0.05 # 腐蚀几率

    # 腐蚀检查方向 (正交)
    CORRODE_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def run_interactions(self, grid):
        """Corrosive Gas attempts to corrode adjacent elements."""
        if self.processed: return

        # 1. 消散 ( Gas base class also has check_boundary_dissipation)
        if random.random() < self.dissipate_chance:
            grid.set_element(self.y, self.x, None)
            self.processed = True
            return

        # 2. 腐蚀邻居 (如果未消散)
        corroded_neighbor = False
        if random.random() < self.corrode_chance:
            possible_targets = []
            for dy, dx in self.CORRODE_CHECKS:
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    neighbor = grid.get_element(ny, nx)
                    # 检查邻居是否存在，是否可被酸腐蚀 (假设可被酸腐蚀的也可被腐蚀气体腐蚀)，并且未被处理
                    if neighbor and neighbor.dissolvable_by_acid and not neighbor.processed:
                        possible_targets.append((ny, nx, neighbor))

            if possible_targets:
                ny, nx, target_neighbor = random.choice(possible_targets)
                # 移除被腐蚀的邻居
                grid.set_element(ny, nx, None)
                # 腐蚀气体本身不消失
                corroded_neighbor = True

        # Gas base class update handles movement and final processing if not processed by interaction

# 7. 冰冷的金属 (FrozenMetal) - 不移动，逐渐融化成金属
class FrozenMetal(Solid):
    key = '_' # 使用下划线
    name = '冰冷金属'
    char = '_'
    color = (curses.COLOR_CYAN, -1, curses.A_BOLD | curses.A_DIM) # 亮青色，变暗
    density = 65 # 接近金属密度
    is_static = True # 不移动
    is_solid = True
    melt_chance = 0.005 # 缓慢融化几率

    def run_interactions(self, grid):
        """Frozen Metal gradually melts into Metal."""
        if self.processed: return

        if random.random() < self.melt_chance:
            # 融化成金属 (key 'M')
            new_metal = grid.create_element('M', self.y, self.x)
            if new_metal:
                 new_metal.tags = list(self.tags) # 复制标签
                 grid.set_element(self.y, self.x, new_metal)
                 # 金属是静态的，不立即处理
            self.processed = True # 冰冷金属消失
            return

        # Mark as processed if not melted
        if not self.processed:
            self.processed = True

# 8. 粘液 (Goo) - 缓慢流动，可以粘住旁边的可移动元素
class Goo(Liquid):
    key = '~' # 使用波浪线，水是 'W'
    name = '粘液'
    char = '~'
    color = (curses.COLOR_MAGENTA, curses.COLOR_BLACK, curses.A_DIM) # 淡洋红色
    density = 1.8 # 比水稠
    flow_speed = 1 # 流速慢
    dissolvable_by_acid = True
    stick_chance = 0.4 # 粘住旁边可移动元素的几率

    # 粘住检查方向 (正交)
    STICK_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def run_interactions(self, grid):
        """Goo attempts to stick adjacent movable elements."""
        if self.processed: return

        stuck_neighbor = False
        if random.random() < self.stick_chance:
            possible_targets = []
            for dy, dx in self.STICK_CHECKS:
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    neighbor = grid.get_element(ny, nx)
                    # 检查邻居是否存在，是可移动的，不是粘液本身，并且未被处理
                    if neighbor and not neighbor.is_static and neighbor.key != '~' and not neighbor.processed:
                         possible_targets.append((ny, nx, neighbor))

            if possible_targets:
                # 选择一个可粘住的邻居
                ny, nx, target_neighbor = random.choice(possible_targets)
                # 将邻居标记为静态或添加一个“粘住”标签，使其暂时无法移动
                # 最简单的方式是添加一个标签，然后在 Base Movable 的 update 中检查这个标签
                # 复杂的实现可能需要覆盖邻居的 update 方法
                # 这里我们添加一个标签，并尝试让自身移动（如果可能的话，会将粘住的邻居也带上）
                target_neighbor.tags.append("stuck_to_goo") # 添加标签

        # Liquid update logic runs after interactions

# 9. 能量粒子 (EnergyParticle) - 短暂存在，碰到特定元素触发效果
class EnergyParticle(Movable): # 像气体一样飘散或短暂存在
    key = '{' # 使用点号，烟是 'K'
    name = '能量粒子'
    char = '{'
    color = (curses.COLOR_WHITE, -1, curses.A_BOLD | curses.A_BLINK) # 亮白色闪烁
    density = -0.1 # 几乎无重，略微向上飘或随机飘
    is_static = False
    is_solid = False # 类似气体，可以穿过固体间的缝隙
    is_gas = True # 标记为气体方便流动逻辑
    rise_speed = 1
    spread_factor = 3
    lifetime = 10 # 短暂存在，10 帧后消失

    # 内部状态
    timer = 0

    def __init__(self, y, x):
        super().__init__(y, x)
        self.timer = self.lifetime

    def run_interactions(self, grid):
        """Energy Particle interacts with neighbors and decays."""
        if self.processed: return

        # 1. 衰减消失
        self.timer -= 1
        if self.timer <= 0:
            grid.set_element(self.y, self.x, None)
            self.processed = True # 消失
            return

        # 2. 检查触发效果的邻居 (正交)
        trigger_checks = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        triggered = False
        for dy, dx in trigger_checks:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # 示例：碰到金属 ('M') 变成热源？ 碰到水 ('W') 变成蒸汽？ 碰到炸药 ('D') 引爆？
                if neighbor and not neighbor.processed:
                    if neighbor.key == 'M':
                         # 将金属变成热源或变成 lava? 复杂，先不实现
                         pass
                    elif neighbor.key == 'W':
                         # 水变成蒸汽
                         if random.random() < 0.3:
                              new_steam = grid.create_element('G', ny, nx)
                              grid.set_element(ny, nx, new_steam)
                              if new_steam: new_steam.processed = True
                              triggered = True; break
                    elif neighbor.key == 'D':
                         # 点燃炸药
                         if random.random() < 0.8:
                             if hasattr(neighbor, 'is_lit') and not neighbor.is_lit:
                                  neighbor.is_lit = True
                                  neighbor.lit_timer = neighbor.fuse_frames
                                  neighbor.tags.append("lit") # 添加点燃标签
                                  triggered = True; break

        # 如果触发了效果，自身消失
        if triggered:
            grid.set_element(self.y, self.x, None)
            self.processed = True # 消失
            return

        # Gas base class update handles movement if not processed by interaction/decay

# 10. 吸收块 (Absorber) - 静态固体，会吸收触碰到的可移动元素
class Absorber(StaticSolid):
    key = '$' # 使用 @，奇点是 '*'
    name = '吸收块'
    char = '$'
    color = (curses.COLOR_YELLOW, curses.COLOR_BLACK, curses.A_BOLD) # 黄色在黑色背景上
    density = 100 # 极高密度
    is_static = True # 不移动
    is_solid = True
    absorb_chance = 0.5 # 吸收几率

    # 吸收检查方向 (正交+对角)
    ABSORB_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def run_interactions(self, grid):
        """Absorber attempts to absorb adjacent movable elements."""
        if self.processed: return

        absorbable_neighbors = []
        for dy, dx in self.ABSORB_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # 检查邻居是否存在，是可移动的，不是吸收块本身，并且未被处理
                if neighbor and not neighbor.is_static and neighbor.key != '@' and not neighbor.processed:
                     absorbable_neighbors.append((ny, nx, neighbor))

        if absorbable_neighbors and random.random() < self.absorb_chance:
            # 选择一个可吸收的邻居
            ny, nx, target_neighbor = random.choice(absorbable_neighbors)
            # 吸收邻居 (移除它)
            grid.set_element(ny, nx, None)
            # 吸收块本身不消失，也不标记为 processed=True (因为它是一个静态固体，它的 processed 状态由 StaticSolid 基类在 update 中处理)
            # 如果希望吸收块每帧都尝试吸收，可以在这里设置 self.processed = True
            # 但 StaticSolid 的 update 方法会确保它每帧都被标记 processed，所以这里不需要。
            pass # 吸收完成，继续检查其他邻居或等待下一帧

        # Mark as processed if no absorption occurred (StaticSolid update does this)
        if not self.processed:
             self.processed = True


# 添加新的元素到 ElementManager 的原始顺序中（如果需要让它们在选择列表中可见且按指定顺序）
# 你需要在 element_manager.py 的 _ORIGINAL_ORDER 列表中手动添加这些新元素的 key。
# 例如，将 _ORIGINAL_ORDER 修改为：
# _ORIGINAL_ORDER = [
#     'S', '#', 'W', 'L', 'I', 'A', 'J', 'Z', 'O', 'D', 'C', 'P', 'E', 'M',
#     'X', 'U', 'T', 'N', 'Y', 'H', 'B', 'R', 'G', 'K', 'F', 'V', '?',
#     'D', 'B', 'W', 'g', 'x', '_', '~', '.', '@' # 新元素的键
# ]
# 注意：这里的 'D' 和 'B' 键与现有元素冲突了，需要修改。我前面已经修改了炸药和炸弹的键，现在根据修改后的键更新这里。
# 修改后的 _ORIGINAL_ORDER 示例:
# _ORIGINAL_ORDER = [
#      ... (原有元素键) ...
#     'D', 'B', 'W', 'g', 'x', '_', '~', '.', '@' # 新元素的键
# ]
# 请注意，虫子使用了 'W' 键，这与水冲突。需要为虫子分配一个新的键。
# 我为虫子分配了新的键 'w'。水保持 'W'。
# 现在更新 _ORIGINAL_ORDER:
# _ORIGINAL_ORDER = [
#      'S', '#', 'W', 'L', 'I', 'A', 'J', 'Z', 'O', 'D', 'C', 'P', 'E', 'M',
#      'X', 'U', 'T', 'N', 'Y', 'H', 'b', 'R', 'G', 'K', 'F', 'V', '?', # 这里的 'b' 之前是 Ember，现在 Ember 是 'b'
#      'D', 'B', 'w', 'g', 'x', '_', '~', '.', '@' # 炸药(D), 炸弹(B), 虫(w), 玻璃粉末(g), 腐蚀气体(x), 冰冷金属(_), 粘液(~), 能量粒子(.), 吸收块(@)
# ]
# 注意：原始列表中有 'b' (Ember)，我使用了小写 'w' 给虫。
# 新的完整的 _ORIGINAL_ORDER 列表：
# _ORIGINAL_ORDER = [
#     'S', '#', 'W', 'L', 'I', 'A', 'J', 'Z', 'O', 'D', 'C', 'P', 'E', 'M',
#     'X', 'U', 'T', 'N', 'Y', 'H', 'b', 'R', 'G', 'K', 'F', 'V', '?', # 原有元素键 (Ember 改为 'b')
#     'D', 'B', 'w', 'g', 'x', '_', '~', '.', '@' # 新元素的键
# ]
