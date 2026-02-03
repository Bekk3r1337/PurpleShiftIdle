# ===============================
# ФИОЛЕТОВАЯ СМЕНА: IDLE 3.0 
# ===============================

import pygame
import sys
import random
import time
import json
import os
import math
from dataclasses import dataclass


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# -------------------------
# CONFIG
# -------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

SAVE_FILE = "save.json"
BG_IMAGE = "bg.jpg"
MUSIC_FILE = "bg_music.mp3"
FONT_FILE = "Noto Sans.ttf"

def load_bg(name):
    try:
        img = pygame.image.load(resource_path(name)).convert()
        return pygame.transform.scale(img, (WIDTH, HEIGHT))
    except:
        return None

bg_novice = load_bg("bg_novice.jpg")
bg_worker = load_bg("bg_worker.jpg")
bg_taicher = load_bg("bg_taicher.jpg")
bg_legend = load_bg("bg_legend.jpg")
bg_god = load_bg("bg_god.jpg")

# Game constants
CLICK_SALARY = 10
AUTO_CLICK_COST = 5000
KPI_UP_COST = 1000
PRESTIGE_MIN_SALARY = 100000

# UI colors
COL_PANEL = (30, 0, 50)
COL_PANEL_BORDER = (170, 0, 255)
COL_TEXT = (255, 255, 255)
COL_TEXT_DIM = (220, 220, 220)

COL_BTN = (90, 0, 170)
COL_BTN_HOVER = (130, 0, 240)
COL_BTN_BORDER = (255, 0, 255)
COL_GOLD = (255, 215, 0)

# -------------------------
# INIT
# -------------------------
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Фиолетовая Смена: Idle 3.0")

def load_bg(name):
    try:
        img = pygame.image.load(name).convert()
        return pygame.transform.scale(img, (WIDTH, HEIGHT))
    except:
        print("Не удалось загрузить:", name)
        return None

bg_novice = load_bg("bg_novice.jpg")
bg_worker = load_bg("bg_worker.jpg")
bg_taicher = load_bg("bg_taicher.jpg")
bg_legend = load_bg("bg_legend.jpg")
bg_god = load_bg("bg_god.jpg")
clock = pygame.time.Clock()

# -------------------------
# ASSETS (safe load)
# -------------------------
def safe_load_image(path: str, size=None):
    try:
        img = pygame.image.load(resource_path(path)).convert()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception as e:
        print(f"[WARN] Image load failed: {path} -> {e}")
        return None

def safe_load_music(path: str, volume=0.4):
    try:
        pygame.mixer.music.load(resource_path(path))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        return True
    except Exception as e:
        print(f"[WARN] Music load failed: {path} -> {e}")
        return False

def safe_font(path: str, size: int):
    try:
        return pygame.font.Font(resource_path(path), size)
    except Exception:
        return pygame.font.SysFont("arial", size)

bg = safe_load_image(BG_IMAGE, (WIDTH, HEIGHT))
music_volume = 0.4
music_ok = safe_load_music(MUSIC_FILE, music_volume)

font = safe_font(FONT_FILE, 22)
big_font = safe_font(FONT_FILE, 40)

# -------------------------
# UTILS
# -------------------------
def fmt_int(n):
    try:
        n = int(n)
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ")

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def draw_panel(surface, rect, color=COL_PANEL, alpha=170, radius=14, border=COL_PANEL_BORDER, border_w=2):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((*color, alpha))
    surface.blit(panel, rect)
    pygame.draw.rect(surface, border, rect, border_w, border_radius=radius)

def draw_progress(surface, rect, value01, fill=(255, 0, 255), back=(40, 0, 70), border=(200, 0, 255)):
    value01 = clamp01(value01)
    pygame.draw.rect(surface, back, rect, border_radius=10)
    fill_rect = pygame.Rect(rect.x, rect.y, int(rect.w * value01), rect.h)
    pygame.draw.rect(surface, fill, fill_rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 2, border_radius=10)

# -------------------------
# UI: AnimButton (like your "ПИКАЙ", but reusable)
# -------------------------
class AnimButton:
    def __init__(self, base_rect: pygame.Rect, label_lines, base_color=COL_BTN, hover_color=COL_BTN_HOVER,
                 radius=14, font_obj=None, text_color=COL_TEXT, border_color=COL_BTN_BORDER):
        self.base_rect = pygame.Rect(base_rect)
        self.label_lines = label_lines if isinstance(label_lines, (list, tuple)) else [str(label_lines)]
        self.base_color = base_color
        self.hover_color = hover_color
        self.radius = radius
        self.font = font_obj or font
        self.text_color = text_color
        self.border_color = border_color

        # animation
        self.scale = 1.0
        self.target = 1.0
        self.speed = 0.22

    def bump(self, to=0.90):
        self.target = to

    def update(self):
        self.scale += (self.target - self.scale) * self.speed
        if abs(self.scale - self.target) < 0.01:
            self.target = 1.0

    def rect(self):
        w = max(1, int(self.base_rect.w * self.scale))
        h = max(1, int(self.base_rect.h * self.scale))
        return pygame.Rect(self.base_rect.centerx - w//2, self.base_rect.centery - h//2, w, h)

    def is_hover(self, mouse_pos):
        return self.rect().collidepoint(mouse_pos)

    def draw(self, surface, mouse_pos):
        r = self.rect()
        hover = r.collidepoint(mouse_pos)
        col = self.hover_color if hover else self.base_color

        pygame.draw.rect(surface, col, r, border_radius=self.radius)
        pygame.draw.rect(surface, self.border_color, r, 3, border_radius=self.radius)

        # center text (multi-line)
        total_h = len(self.label_lines) * self.font.get_height()
        y = r.centery - total_h // 2

        for line in self.label_lines:
            txt = self.font.render(str(line), True, self.text_color)
            tr = txt.get_rect(center=(r.centerx, y + self.font.get_height()//2))
            surface.blit(txt, tr)
            y += self.font.get_height()

    def hit(self, pos):
        return self.rect().collidepoint(pos)

# -------------------------
# DATA MODELS
# -------------------------
@dataclass
class Building:
    id: str
    name: str
    base_price: int
    bps: float
    count: int = 0

    def price(self, discount_mult: float = 1.0):
        return int(self.base_price * (1.15 ** self.count) * discount_mult)

# Rank logic
def rank_from_kpi(kpi_val):
    if kpi_val < 5:
        return "Новичок"
    elif kpi_val < 10:
        return "Стажёр"
    elif kpi_val < 20:
        return "Работяга"
    elif kpi_val < 35:
        return "Старший смены"
    elif kpi_val < 50:
        return "Тащер"
    elif kpi_val < 75:
        return "Мастер склада"
    elif kpi_val < 100:
        return "Легенда смены"
    elif kpi_val < 150:
        return "Архитектор логистики"
    elif kpi_val < 250:
        return "Повелитель мезонина"
    elif kpi_val < 400:
        return "Инспектор хаоса"
    else:
        return "Фиолетовый Бог"


# -------------------------
# GAME STATE (single dict to keep it clean)
# -------------------------
state = {
    "boxes": 0.0,
    "salary": 0.0,
    "kpi": 1,
    "upgrade_goal": 100,

    "auto_click": False,
    "auto_timer": 0,

    "prestige": 0,
    "prestige_mult": 1.0,

    # meta upgrades
    "meta": {"income": 0, "cheap": 0, "taisher": 0, "events": 0},

    # events
    "event_active": False,
    "event_text": "",
    "event_timer": 0,
    "event_mult": 1.0,
    "next_event_time": time.time() + random.randint(20, 35),
    
    "loot_active": False,
    "loot_timer": 0,
    "next_loot_time": time.time() + random.randint(20, 40),

    # stats
    "clicks": 0,
    "earned_salary": 0.0,
    "boss_wins": 0,

    # ui/feedback
    "rank": "Новичок",
    "prev_rank": "Новичок",
    "flash": 0,
    "particles": [],
    "level_up": False,
    "level_up_timer": 0,

    "toasts": [],          # [{text,timer}]
    "notifications": [],   # [{text,timer,y_offset,color}]
}

buildings = [
    Building("sorter", "Сортировщик", 150, 0.3),
    Building("buffer", "Буфер", 800, 1.5),
    Building("mezz", "Мезонин", 4500, 6.0),
    Building("autosort", "Автосорт", 25000, 25.0),
]

# -------------------------
# STATE HELPERS
# -------------------------
def recalc_prestige_mult():
    p = state["prestige"]
    meta_income = state["meta"]["income"]
    state["prestige_mult"] = 1.0 + 0.05 * p + 0.10 * meta_income

def discount_mult():
    # cheap meta: -10% each level
    lvl = state["meta"]["cheap"]
    return max(0.2, 1.0 - 0.10 * lvl)

def total_bps():
    return sum(b.bps * b.count for b in buildings)

def add_boxes(amount: float):
    state["boxes"] += amount

def add_salary(amount: float):
    state["salary"] += amount
    if amount > 0:
        state["earned_salary"] += amount

def toast(text: str, timer: int = 180):
    state["toasts"].append({"text": text, "timer": timer})

def notify(text: str, color=(255,255,255)):
    state["notifications"].append({
        "text": text,
        "timer": 160,
        "y_offset": -60,
        "color": color
    })

# -------------------------
# SAVE / LOAD
# -------------------------
def save_game():
    data = {
        "boxes": state["boxes"],
        "salary": state["salary"],
        "kpi": state["kpi"],
        "upgrade_goal": state["upgrade_goal"],
        "auto_click": state["auto_click"],
        "prestige": state["prestige"],
        "meta": state["meta"],
        "buildings": {b.id: b.count for b in buildings},
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[WARN] Save failed:", e)

def load_game():
    if not os.path.exists(SAVE_FILE):
        return
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        state["boxes"] = float(data.get("boxes", 0.0))
        state["salary"] = float(data.get("salary", 0.0))
        state["kpi"] = int(data.get("kpi", 1))
        state["upgrade_goal"] = int(data.get("upgrade_goal", 100))
        state["auto_click"] = bool(data.get("auto_click", False))
        state["prestige"] = int(data.get("prestige", 0))
        state["meta"].update(data.get("meta", {}))

        saved_b = data.get("buildings", {})
        for b in buildings:
            b.count = int(saved_b.get(b.id, 0))

        recalc_prestige_mult()
        r = rank_from_kpi(state["kpi"])
        state["rank"] = r
        state["prev_rank"] = r

    except Exception as e:
        print("[WARN] Load failed:", e)

load_game()
recalc_prestige_mult()

# -------------------------
# UI LAYOUT (buttons)
# -------------------------
btn_click = AnimButton(
    pygame.Rect(330, 230, 240, 170),
    ["ПИКАЙ"],
    base_color=(140, 0, 220),
    hover_color=(160, 0, 255),
    radius=18,
    font_obj=big_font,
    text_color=(255, 210, 255),  # читабельнее чем чисто белый
)

btn_prestige = AnimButton(pygame.Rect(650, 20, 220, 55), ["Перерождение"], radius=12, font_obj=font)
btn_kpi = AnimButton(pygame.Rect(650, 90, 220, 55), ["KPI +1 (1000Р)"], radius=12, font_obj=font)
btn_auto = AnimButton(pygame.Rect(650, 160, 220, 55), ["Авто (5000Р)"], radius=12, font_obj=font)

# right building buttons
building_btns = []
y0 = 240
for i, b in enumerate(buildings):
    base_rect = pygame.Rect(650, y0 + i * 70, 220, 60)
    building_btns.append(AnimButton(base_rect, [b.name], radius=14, font_obj=font))

# bottom left meta button (we will implement in Part 2)
btn_meta = AnimButton(pygame.Rect(20, 520, 200, 50), ["META SHOP"], radius=12, font_obj=font)
meta_open = False

# -------------------------
# ACHIEVEMENTS
# -------------------------
achievements = [
    {"id":"first_click", "name":"Первый пик", "desc":"Сделать первый клик",
     "cond": lambda st: st["clicks"] >= 1, "bonus": 0.02},
    {"id":"kpi_25", "name":"KPI 25", "desc":"Достичь KPI 25",
     "cond": lambda st: st["kpi"] >= 25, "bonus": 0.05},
    {"id":"build_10", "name":"Бригада", "desc":"Иметь 10 зданий",
     "cond": lambda st: st["total_buildings"] >= 10, "bonus": 0.03},
    {"id":"prestige_1", "name":"Перерождение", "desc":"Сделать престиж 1 раз",
     "cond": lambda st: st["prestige"] >= 1, "bonus": 0.05},
    {"id":"boss_win", "name":"Прошёл проверку", "desc":"Выиграть босса-проверку",
     "cond": lambda st: st["boss_wins"] >= 1, "bonus": 0.04},
]
unlocked = set()
ach_mult = 1.0  # мультик достижений, пересчитываем из unlocked

def recalc_ach_mult():
    global ach_mult
    m = 1.0
    for a in achievements:
        if a["id"] in unlocked:
            m *= (1.0 + a.get("bonus", 0.0))
    ach_mult = m

recalc_ach_mult()

# -------------------------
# META SHOP
# -------------------------
META_ITEMS = [
    {"key":"income", "title":"+10% общий доход", "desc":"Умножает всё: клики/пассив/авто", "base_cost": 3},
    {"key":"cheap",  "title":"-10% цены зданий", "desc":"Здания дешевле навсегда", "base_cost": 3},
    {"key":"taisher","title":"+2 сек Тащер-режим", "desc":"Тащер длится дольше", "base_cost": 2},
    {"key":"events", "title":"+25% длительность событий", "desc":"События держатся дольше", "base_cost": 2},
]

def meta_cost(key, base):
    lvl = state["meta"].get(key, 0)
    return int(base * (1.65 ** lvl))

# -------------------------
# EFFECTS / PARTICLES
# -------------------------
def spawn_levelup_particles(n=70):
    state["particles"].clear()
    for _ in range(n):
        state["particles"].append([
            WIDTH // 2,
            HEIGHT // 2,
            random.uniform(-6, 6),
            random.uniform(-6, 6),
            random.randint(4, 8)
        ])

def draw_warehouse_evolution(surface, kpi_val):
    # лёгкие «живые» квадраты на фоне
    evo = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    p = min(1.0, kpi_val / 60.0)
    alpha = int(35 + 85 * p)
    evo.fill((30, 0, 60, alpha))
    surface.blit(evo, (0, 0))

    count = int(6 + 18 * p)
    t = time.time()
    for i in range(count):
        x = int((i * 47 + 120 * math.sin(t*0.35 + i)) % WIDTH)
        y = int((i * 29 +  90 * math.cos(t*0.25 + i*0.7)) % HEIGHT)
        w = 26 + int(10 * p)
        h = 18 + int(8 * p)
        a = 18 + int(45 * p)
        pygame.draw.rect(surface, (160, 0, 220, a), (x, y, w, h), border_radius=6)

# -------------------------
# TAISHER WINDOW (with meta)
# -------------------------
def is_taisher_now():
    base = 3.0
    extra = state["meta"]["taisher"] * 2.0
    return (time.time() % 15.0) < (base + extra)

# -------------------------
# RANDOM EVENTS
# -------------------------
def start_random_event(now):
    etype = random.choice(["bonus", "debuff", "boost"])
    state["event_active"] = True
    state["event_mult"] = 1.0

    if etype == "bonus":
        bonus = random.randint(1000, 5000)
        add_salary(bonus)
        state["event_text"] = f"СРОЧНАЯ ПОСТАВКА! +{fmt_int(bonus)}Р"
        state["event_timer"] = 180
        notify(state["event_text"], (255, 255, 255))

    elif etype == "debuff":
        state["event_mult"] = 0.5
        state["event_text"] = "ПРОВЕРКА! -50% дохода"
        state["event_timer"] = 300
        notify(state["event_text"], (255, 170, 170))

    else:
        state["event_mult"] = 3.0
        state["event_text"] = "ГОРЯЧАЯ СМЕНА! x3 доход"
        state["event_timer"] = 300
        notify(state["event_text"], (255, 255, 0))

    # meta: longer events
    if state["meta"]["events"] > 0:
        state["event_timer"] = int(state["event_timer"] * (1.0 + 0.25 * state["meta"]["events"]))

    state["next_event_time"] = now + random.randint(25, 45)

# -------------------------
# BOSS CHECK
# -------------------------
boss_active = False
boss_timer = 0
boss_goal = 0
boss_progress = 0
total_boxes_earned = 0.0
boss_start_earned = 0.0
next_boss_time = time.time() + random.randint(120, 180)

def add_boxes_earned(amount):
    global total_boxes_earned
    total_boxes_earned += amount
    add_boxes(amount)

# -------------------------
# UI: right building button labels update helper
# -------------------------
def update_building_btn_labels():
    for i, b in enumerate(buildings):
        price = b.price(discount_mult())
        building_btns[i].label_lines = [
            f"{b.name} x{b.count}",
            f"{fmt_int(price)}Р | +{b.bps} к/сек"
        ]

update_building_btn_labels()

# -------------------------
# HOTKEY HELP TEXT
# -------------------------
def draw_hotkeys(surface):
    txt = font.render(f"M: пауза/играть  |  +/-: громк. {music_volume:.1f}", True, (220,220,220))
    surface.blit(txt, (20, HEIGHT - 28))

# -------------------------
# MAIN LOOP
# -------------------------

running = True
last_save_time = time.time()

while running:

    dt = clock.tick(FPS) / 1000.0
    now = time.time()
    mouse_pos = pygame.mouse.get_pos()
    if not state["loot_active"] and now >= state["next_loot_time"]:
        state["loot_active"] = True
        state["loot_timer"] = 600  # 10 сек

    # autosave
    if now - last_save_time >= 2:
        save_game()
        last_save_time = now

    # update taisher
    taisher_mode = is_taisher_now()

    # update button animations
    btn_click.update()
    btn_prestige.update()
    btn_kpi.update()
    btn_auto.update()
    btn_meta.update()
    for bb in building_btns:
        bb.update()

    # -------------------------
    # PASSIVE INCOME (bps)
    # -------------------------
    bps = total_bps() * state["prestige_mult"] * state["event_mult"] * ach_mult
    add_boxes_earned(bps * dt)
    add_salary((bps * CLICK_SALARY) * dt)

    # -------------------------
    # AUTO CLICK
    # -------------------------
    if state["auto_click"]:
        state["auto_timer"] += 1
        if state["auto_timer"] > 60:
            add_boxes_earned(state["kpi"] * state["prestige_mult"] * state["event_mult"] * ach_mult)
            add_salary(CLICK_SALARY * state["prestige_mult"] * state["event_mult"] * ach_mult)
            state["auto_timer"] = 0

    # -------------------------
    # RANDOM EVENT tick
    # -------------------------
    if (not state["event_active"]) and now >= state["next_event_time"]:
        start_random_event(now)

    if state["event_active"]:
        state["event_timer"] -= 1
        if state["event_timer"] <= 0:
            state["event_active"] = False
            state["event_mult"] = 1.0

    # -------------------------
    # BOSS spawn/tick
    # -------------------------
    if (not boss_active) and now >= next_boss_time:
        boss_active = True
        boss_timer = 10 * 60
        boss_goal = int(60 + (total_bps() * 10) + state["kpi"] * 5)
        boss_start_earned = total_boxes_earned
        toast("НАЧАЛЬСТВО: ПРОВЕРКА! УСПЕЙ!", 220)

    if boss_active:
        boss_timer -= 1
        boss_progress = int(total_boxes_earned - boss_start_earned)

        if boss_timer <= 0:
            boss_active = False
            if boss_progress >= boss_goal:
                reward = int(5000 + boss_goal * 8)
                add_salary(reward)
                state["boss_wins"] += 1
                toast(f"ПРОВЕРКА ПРОЙДЕНА! +{fmt_int(reward)}Р", 240)
                notify("Проверка пройдена!", (255, 255, 0))
            else:
                penalty = int(2000 + boss_goal * 3)
                add_salary(-penalty)
                toast(f"ПРОВАЛ! -{fmt_int(penalty)}Р", 240)
                notify("Провал проверки!", (255, 160, 160))
            next_boss_time = now + random.randint(120, 240)

    # -------------------------
    # BOX UPGRADE (kpi level)
    # -------------------------
    if state["boxes"] >= state["upgrade_goal"]:
        state["boxes"] -= state["upgrade_goal"]
        state["kpi"] += 1
        state["upgrade_goal"] = int(state["upgrade_goal"] * 1.22)

    # -------------------------
    # RANK UPDATE + effects
    # -------------------------
    new_rank = rank_from_kpi(state["kpi"])
    RANK_MULT = {
    "Новичок": 1.0,
    "Стажёр": 1.05,
    "Работяга": 1.10,
    "Старший смены": 1.15,
    "Тащер": 1.25,
    "Мастер склада": 1.35,
    "Легенда смены": 1.50,
    "Архитектор логистики": 1.75,
    "Повелитель мезонина": 2.0,
    "Инспектор хаоса": 2.5,
    "Фиолетовый Бог": 3.0,
}
    if new_rank != state["prev_rank"]:
        state["prev_rank"] = new_rank
        state["rank"] = new_rank
        state["level_up"] = True
        state["level_up_timer"] = 120
        state["flash"] = 18
        spawn_levelup_particles()
        toast(f"НОВОЕ ЗВАНИЕ: {state['rank']}", 220)

    # -------------------------
    # ACHIEVEMENTS CHECK
    # -------------------------
    ach_state = {
        "clicks": state["clicks"],
        "earned_salary": state["earned_salary"],
        "total_buildings": sum(b.count for b in buildings),
        "prestige": state["prestige"],
        "boss_wins": state["boss_wins"],
        "kpi": state["kpi"],
    }
    changed = False
    for a in achievements:
        if a["id"] not in unlocked and a["cond"](ach_state):
            unlocked.add(a["id"])
            toast(f"Достижение: {a['name']}", 240)
            notify(f"Достижение: {a['name']}", (255, 210, 255))
            changed = True
    if changed:
        recalc_ach_mult()

    # -------------------------
    # INPUT
    # -------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_m:
                # pause/unpause
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                except Exception:
                    pass

            elif event.key == pygame.K_MINUS:
                music_volume = max(0.0, music_volume - 0.1)
                try:
                    pygame.mixer.music.set_volume(music_volume)
                except Exception:
                    pass

            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                music_volume = min(1.0, music_volume + 0.1)
                try:
                    pygame.mixer.music.set_volume(music_volume)
                except Exception:
                    pass

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # meta open/close
            if btn_meta.hit((mx, my)):
                meta_open = not meta_open
                toast("META SHOP" + (" открыт" if meta_open else " закрыт"), 140)
                btn_meta.bump()

            # META SHOP click handling (if open)
            if meta_open:
                shop_x, shop_y = 240, 110
                for idx, item in enumerate(META_ITEMS):
                    rect = pygame.Rect(shop_x, shop_y + idx * 80, 420, 65)
                    buy_rect = pygame.Rect(rect.right - 120, rect.y + 14, 100, 36)
                    if buy_rect.collidepoint((mx, my)):
                        key = item["key"]
                        cost = meta_cost(key, item["base_cost"])
                        if state["prestige"] >= cost:
                            state["prestige"] -= cost
                            state["meta"][key] = state["meta"].get(key, 0) + 1
                            recalc_prestige_mult()
                            toast(f"Куплено: {item['title']}", 200)
                            notify(f"Куплено: {item['title']}", (255, 215, 0))
                            update_building_btn_labels()
                        else:
                            toast("Не хватает престижа", 160)
                continue

            # click main
            if btn_click.hit((mx, my)):
                mult = 5 if taisher_mode else 1
                earned_boxes = (state["kpi"] * mult) * state["prestige_mult"] * state["event_mult"] * ach_mult
                earned_money = (CLICK_SALARY * mult) * state["prestige_mult"] * state["event_mult"] * ach_mult
                add_boxes_earned(earned_boxes)
                add_salary(earned_money)
                state["clicks"] += 1
                btn_click.bump()

                # chance penalty
                if random.randint(1, 20) == 1:
                    add_salary(-50)

            # prestige
            elif btn_prestige.hit((mx, my)):
                can = state["salary"] >= PRESTIGE_MIN_SALARY
                if can:
                    gained = max(1, int(math.sqrt(int(state["salary"]) / PRESTIGE_MIN_SALARY)))
                    state["prestige"] += gained
                    recalc_prestige_mult()

                    notify(f"+{gained} жетонов престижа!", (255, 0, 200))
                    toast(f"Перерождение! +{gained} престиж", 240)

                    # reset progress
                    state["boxes"] = 0.0
                    state["salary"] = 0.0
                    state["kpi"] = 1
                    state["upgrade_goal"] = 100
                    state["auto_click"] = False
                    state["auto_timer"] = 0
                    for b in buildings:
                        b.count = 0

                    state["rank"] = "Новичок"
                    state["prev_rank"] = "Новичок"
                    state["flash"] = 18

                    update_building_btn_labels()
                    btn_prestige.bump()

            # KPI up
            elif btn_kpi.hit((mx, my)):
                if state["salary"] >= KPI_UP_COST:
                    add_salary(-KPI_UP_COST)
                    state["kpi"] += 1
                    btn_kpi.bump()

            # Auto buy
            elif btn_auto.hit((mx, my)):
                if state["salary"] >= AUTO_CLICK_COST:
                    add_salary(-AUTO_CLICK_COST)
                    state["auto_click"] = True
                    toast("Авто включён", 160)
                    notify("Авто включён", (255, 210, 255))
                    btn_auto.bump()

            # buildings buy
            else:
                disc = discount_mult()
                for i, b in enumerate(buildings):
                    if building_btns[i].hit((mx, my)):
                        price = b.price(disc)
                        if state["salary"] >= price:
                            add_salary(-price)
                            b.count += 1
                            update_building_btn_labels()
                            building_btns[i].bump()
                            toast(f"Куплено: {b.name}", 140)
                            notify(f"Куплено: {b.name}", (255, 215, 0))
                        else:
                            toast("Не хватает денег", 120)
                        break

    # -------------------------
    # RENDER
    # -------------------------
    # -------------------------
    # RENDER
    # -------------------------

    current_rank = state["rank"]

    if current_rank == "Новичок" and bg_novice:
        screen.blit(bg_novice, (0, 0))
    elif current_rank == "Работяга" and bg_worker:
        screen.blit(bg_worker, (0, 0))
    elif current_rank == "Тащер" and bg_taicher:
        screen.blit(bg_taicher, (0, 0))
    elif current_rank == "Легенда смены" and bg_legend:
        screen.blit(bg_legend, (0, 0))
    elif current_rank == "Фиолетовый Бог" and bg_god:
        screen.blit(bg_god, (0, 0))
    elif bg:
        screen.blit(bg, (0, 0))
    else:
        screen.fill((18, 0, 30))

    draw_warehouse_evolution(screen, state["kpi"])

    # subtle dark overlay
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((10, 0, 20, 110))
    screen.blit(dark, (0, 0))

    # LEFT: stats panel
    stats_panel = pygame.Rect(20, 20, 350, 250)
    draw_panel(screen, stats_panel)

    # progress bar to next KPI
    prog = state["boxes"] / max(1.0, float(state["upgrade_goal"]))
    draw_progress(screen, pygame.Rect(40, 75, 310, 16), prog)

    screen.blit(font.render(f"Звание: {state['rank']}", True, (255, 170, 255)), (40, 42))
    screen.blit(font.render(f"Пики: {fmt_int(state['boxes'])} / {fmt_int(state['upgrade_goal'])}", True, COL_TEXT), (40, 100))
    screen.blit(font.render(f"KPI: {state['kpi']}", True, COL_TEXT), (40, 125))
    screen.blit(font.render(f"Зарплата: {fmt_int(state['salary'])} Р", True, COL_TEXT), (40, 150))
    screen.blit(font.render(f"К/сек: {(total_bps() * state['prestige_mult'] * state['event_mult'] * ach_mult):.1f}", True, COL_TEXT), (40, 175))
    screen.blit(font.render(f"Престиж: {state['prestige']} (x{state['prestige_mult']:.2f})", True, COL_TEXT), (40, 200))
    screen.blit(font.render(f"Бонус достижений: x{ach_mult:.2f}", True, COL_TEXT_DIM), (40, 225))

    # Taishер text (keep inside screen)
    if taisher_mode:
        t = big_font.render("ТАЩЕР СМЕНЫ!", True, (255, 255, 0))
        s = big_font.render("ТАЩЕР СМЕНЫ!", True, (0, 0, 0))
        tr = t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 140))
        sr = s.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 137))
        screen.blit(s, sr)
        screen.blit(t, tr)

    # BOTTOM LEFT: meta
    btn_meta.draw(screen, mouse_pos)

    # RIGHT TOP: buttons
    # Prestige disabled look
    can_p = state["salary"] >= PRESTIGE_MIN_SALARY
    btn_prestige.base_color = (160, 0, 255) if can_p else (70, 0, 100)
    btn_prestige.hover_color = (180, 0, 255) if can_p else (80, 0, 120)

    btn_prestige.draw(screen, mouse_pos)
    btn_kpi.draw(screen, mouse_pos)
    btn_auto.draw(screen, mouse_pos)

    # CENTER: click
    btn_click.draw(screen, mouse_pos)

    # RIGHT: buildings
    disc = discount_mult()
    for i, b in enumerate(buildings):
        # highlight border if affordable
        price = b.price(disc)
        building_btns[i].draw(screen, mouse_pos)
        if state["salary"] >= price:
            pygame.draw.rect(screen, COL_GOLD, building_btns[i].rect(), 2, border_radius=14)

    # EVENT panel
    if state["event_active"]:
        evt = pygame.Rect(20, 285, 350, 45)
        draw_panel(screen, evt, color=(40, 0, 70), alpha=180, radius=12)
        screen.blit(font.render(state["event_text"], True, (255,255,255)), (evt.x + 12, evt.y + 12))

    # BOSS UI
    if boss_active:
        boss_panel = pygame.Rect(20, 340, 350, 85)
        draw_panel(screen, boss_panel, color=(50, 0, 80), alpha=190, radius=12)
        screen.blit(font.render("ПРОВЕРКА НАЧАЛЬСТВА", True, (255,255,255)), (boss_panel.x + 12, boss_panel.y + 10))
        time_left = boss_timer / 60.0
        screen.blit(font.render(f"Время: {time_left:0.1f} сек", True, (220,220,220)), (boss_panel.x + 12, boss_panel.y + 35))
        p = boss_progress / max(1, boss_goal)
        draw_progress(screen, pygame.Rect(boss_panel.x + 12, boss_panel.y + 60, 326, 14),
                      p, fill=(255, 80, 80), back=(40,0,50), border=(255,0,120))
        screen.blit(font.render(f"{boss_progress}/{boss_goal}", True, (255,255,255)), (boss_panel.x + 250, boss_panel.y + 33))

    # FLASH
    if state["flash"] > 0:
        fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fl.fill((255, 255, 255, 90))
        screen.blit(fl, (0, 0))
        state["flash"] -= 1

    # PARTICLES
    for p in state["particles"][:]:
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 0.12
        pygame.draw.circle(screen, (255, random.randint(120,255), 0),
                           (int(p[0]), int(p[1])), max(1, int(p[4])))
        if p[4] <= 0:
            state["particles"].remove(p)

    # LEVEL UP overlay
    if state["level_up"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 0, 40, 170))
        screen.blit(overlay, (0, 0))
        screen.blit(big_font.render("ПОВЫШЕНИЕ!", True, (255, 215, 0)), (285, 220))
        screen.blit(font.render(f"Новое звание: {state['rank']}", True, (255,255,255)), (300, 275))
        state["level_up_timer"] -= 1
        if state["level_up_timer"] <= 0:
            state["level_up"] = False

    # TOASTS (top-right, not over buttons)
    # рисуем левее правых кнопок, чтобы не перекрывать интерфейс
    toast_x = 390
    toast_w = 250
    for i, t in enumerate(state["toasts"][:]):
        y = 20 + i * 34
        r = pygame.Rect(toast_x, y, toast_w, 28)
        draw_panel(screen, r, color=(20,0,40), alpha=180, radius=10, border=(120,0,200))
        screen.blit(font.render(t["text"], True, (255,255,255)), (r.x + 10, r.y + 6))
        t["timer"] -= 1
        if t["timer"] <= 0:
            state["toasts"].remove(t)

    # NOTIFICATIONS (top center, animated, clean)
    for i, note in enumerate(state["notifications"][:]):
        note["timer"] -= 1
        if note["y_offset"] < 0:
            note["y_offset"] += 6

        w, h = 420, 44
        x = WIDTH//2 - w//2
        y = 14 + i * 54 + note["y_offset"]
        rect = pygame.Rect(x, y, w, h)

        draw_panel(screen, rect, color=(70, 0, 130), alpha=210, radius=12, border=(255, 0, 255))
        txt = font.render(note["text"], True, note["color"])
        screen.blit(txt, txt.get_rect(center=rect.center))

        if note["timer"] <= 0:
            state["notifications"].remove(note)

    # META SHOP overlay
    if meta_open:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 0, 20, 190))
        screen.blit(ov, (0, 0))

        title = big_font.render("META SHOP", True, (255, 120, 255))
        screen.blit(title, (240, 40))
        screen.blit(font.render(f"Престиж: {state['prestige']}", True, (255,255,255)), (240, 85))

        shop_x, shop_y = 240, 110
        for idx, item in enumerate(META_ITEMS):
            key = item["key"]
            lvl = state["meta"].get(key, 0)
            cost = meta_cost(key, item["base_cost"])

            rect = pygame.Rect(shop_x, shop_y + idx * 80, 420, 65)
            draw_panel(screen, rect, color=(30,0,50), alpha=170, radius=12, border=(170,0,255))
            screen.blit(font.render(f"{item['title']}  (ур. {lvl})", True, (255,255,255)), (rect.x + 14, rect.y + 10))
            screen.blit(font.render(item["desc"], True, (200,200,200)), (rect.x + 14, rect.y + 36))

            buy_rect = pygame.Rect(rect.right - 120, rect.y + 14, 100, 36)
            can = state["prestige"] >= cost
            col = (160, 0, 255) if can else (70, 0, 100)
            pygame.draw.rect(screen, col, buy_rect, border_radius=10)
            screen.blit(font.render(f"{cost}", True, (255,255,255)), (buy_rect.x + 12, buy_rect.y + 8))
            screen.blit(font.render("BUY", True, (255,255,255)), (buy_rect.x + 52, buy_rect.y + 8))

        screen.blit(font.render("Клик по META SHOP чтобы закрыть", True, (220,220,220)), (240, 520))

    draw_hotkeys(screen)

    pygame.display.flip()

# exit
save_game()
pygame.quit()
sys.exit()
