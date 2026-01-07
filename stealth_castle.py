import random
import math
from pygame import Rect

##################
##### CONFIG #####
##################

music.play('background')
music.set_volume(0.2)

TITLE = "Stealth Castle"

WIDTH = 900
HEIGHT = 600

TILE = 20
PLAYER_SIZE = 18
ENEMY_SIZE = 18
SPEED = 4

CHEST_SAFE_RADIUS = 60

##################
###### MENU ######
##################
game_state = "menu"

menu_options = ["Iniciar", "Mutar Som", "Sair"]
menu_index = 0
sound_muted = False

##################
#### BUTTONS #####
##################
btn_start = Rect(WIDTH // 2 - 110, 240, 220, 45)
btn_mute  = Rect(WIDTH // 2 - 110, 300, 220, 45)
btn_exit  = Rect(WIDTH // 2 - 110, 360, 220, 45)

btn_pause = Rect(100, 10, 110, 40)
lbl_level = Rect(10, 10, 80, 30)

btn_resume = Rect(WIDTH // 2 - 100, 260, 200, 45)
btn_p_mute  = Rect(WIDTH // 2 - 100, 320, 200, 45)
btn_menu = Rect(WIDTH // 2 - 100, 380, 200, 45)

###################
# CASTLE_SETTINGS #
###################
CASTLE_X = 220
CASTLE_W = WIDTH - CASTLE_X
WALL_THICKNESS = 20
DOOR_HEIGHT = 25

door_top = Rect(CASTLE_X,(HEIGHT // 2 - DOOR_HEIGHT // 2) // TILE * TILE,WALL_THICKNESS,DOOR_HEIGHT)
door_bottom = Rect(CASTLE_X,door_top.bottom,WALL_THICKNESS,DOOR_HEIGHT)

doors = [door_top, door_bottom]
door_open = False

chest = Rect(CASTLE_X + CASTLE_W - 80, HEIGHT // 2 - 15, 30, 30)
chest_taken = False

####################
# PLAYER_n_OBJECTS #
####################
player = Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
walls = []
enemies = []

blocks = []
floor_tiles = []
outside_tiles = []
wall_tiles = []

PLAYER_OUTSIDE = (40, HEIGHT // 2)

##################
### ANIMATIONS ###
##################
class Animator:
    def __init__(self, frames, speed=6, loop=True):
        self.frames = frames
        self.speed = speed
        self.loop = loop
        self.index = 0
        self.timer = 0
        self.finished = False

    def update(self):
        if self.finished:
            return

        self.timer += 1
        if self.timer >= self.speed:
            self.timer = 0
            self.index += 1

            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True

    def reset(self):
        self.index = 0
        self.timer = 0
        self.finished = False

    def get_frame(self):
        return self.frames[self.index]
    
chest_anim = Animator(
    ["tiles/chest_closed", "tiles/chest_opening", "tiles/chest_open"],
    speed=20,
    loop=False
)

DOOR_BOTTOM = ["door_b_01", "door_b_02", "door_b_03", "door_b_04"]
DOOR_TOP = ["door_u_01", "door_u_02", "door_u_03", "door_u_04"]
door_anim = Animator(
    frames=[0, 1, 2, 3],
    speed=8,
    loop=False
)

player_anims = {
    "idle": Animator([
        "player/player_idle_0",
        "player/player_idle_1",
        "player/player_idle_2",
        "player/player_idle_3",
        "player/player_idle_4",
        "player/player_idle_5",
        "player/player_idle_6",
    ], speed=6),

    "walk": Animator([
        "player/player_walk_0",
        "player/player_walk_1",
        "player/player_walk_2",
        "player/player_walk_3",
        "player/player_walk_4",
        "player/player_walk_5",
        "player/player_walk_6",
        "player/player_walk_7",
    ], speed=6),
}

enemy_anims = {
    "walk": Animator([
        "enemy/enemy_0",
        "enemy/enemy_1",
        "enemy/enemy_2",
        "enemy/enemy_3",
        "enemy/enemy_4",
        "enemy/enemy_5",
        "enemy/enemy_6",
        "enemy/enemy_7",
    ], speed=8)
}

player_state = "idle"
enemy_state = "walk"

player_anim = player_anims[player_state]
enemy_anim = enemy_anims["walk"]


#################
##### UTILS #####
#################
def ray_hits_wall(x1, y1, x2, y2, step=4):
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    steps = int(dist / step)

    for i in range(steps):
        x = x1 + dx * i / steps
        y = y1 + dy * i / steps
        for w in walls:
            if w.collidepoint(x, y):
                return True
    return False

def play_sound(snd, loop=False):
    if sound_muted:
        return

    if loop:
        snd.play(-1)
    else:
        snd.play()

##################
##### ENEMY #####
##################
class Enemy:
    def __init__(self, x, y):
        self.rect = Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        self.dir = random.choice(["left", "right", "up", "down"])
        self.range = 75
        self.fov = math.pi / 2
        self.speed = 2
        self.timer = 0
        self.state = "walk"
        self.anims = {
            "walk": [
                "enemy/enemy_0",
                "enemy/enemy_1",
                "enemy/enemy_2",
                "enemy/enemy_3",
                "enemy/enemy_4",
                "enemy/enemy_5",
                "enemy/enemy_6",
                "enemy/enemy_7"]
        }
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 8

    # Movement n Vision
    def facing_angle(self):
        return {
            "right": 0,
            "left": math.pi,
            "up": -math.pi / 2,
            "down": math.pi / 2
        }[self.dir]

    def move(self):
        self.timer += 1
        if self.timer > 60:
            self.dir = random.choice(["left", "right", "up", "down"])
            self.timer = 0

        old = self.rect.topleft

        if self.dir == "left":
            self.rect.x -= self.speed
        elif self.dir == "right":
            self.rect.x += self.speed
        elif self.dir == "up":
            self.rect.y -= self.speed
        elif self.dir == "down":
            self.rect.y += self.speed

        for w in walls:
            if self.rect.colliderect(w):
                self.rect.topleft = old
                self.dir = random.choice(["left", "right", "up", "down"])
                return

        inner_left = CASTLE_X + WALL_THICKNESS
        inner_right = CASTLE_X + CASTLE_W - WALL_THICKNESS
        inner_top = WALL_THICKNESS
        inner_bottom = HEIGHT - WALL_THICKNESS

        if (
            self.rect.left < inner_left or
            self.rect.right > inner_right or
            self.rect.top < inner_top or
            self.rect.bottom > inner_bottom
        ):
            self.rect.topleft = old
            self.dir = random.choice(["left", "right", "up", "down"])

    def can_see_player(self):
        dx = player.centerx - self.rect.centerx
        dy = player.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > self.range:
            return False

        angle_to_player = math.atan2(dy, dx)
        facing = self.facing_angle()

        diff = abs((angle_to_player - facing + math.pi) % (2 * math.pi) - math.pi)
        if diff > self.fov / 2:
            return False

        for i in range(int(dist / 4)):
            x = self.rect.centerx + dx * i / dist
            y = self.rect.centery + dy * i / dist
            for w in walls:
                if w.collidepoint(x, y):
                    return False

        return True

    # Draw n Animation
    def draw_vision(self):
        cx, cy = self.rect.center
        facing = self.facing_angle()

        for i in range(15):
            angle = facing - self.fov / 2 + self.fov * i / 14
            x = cx + math.cos(angle) * self.range
            y = cy + math.sin(angle) * self.range

            if not ray_hits_wall(cx, cy, x, y):
                screen.draw.line((cx, cy), (x, y), (100,140,0))
    
    def update_anim(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.anims[self.state])
            self.frame_timer = 0

    def draw(self):
        frame = self.anims[self.state][self.frame_index]
        screen.blit(frame, self.rect.topleft)

##################
##### LEVEL ######
##################
def generate_level():
    global door_open, chest_taken

    walls.clear()
    blocks.clear()
    enemies.clear()
    floor_tiles.clear()
    outside_tiles.clear()
    wall_tiles.clear()

    door_open = False
    chest_taken = False
    chest_anim.reset()
    door_anim.reset()
    player.topleft = PLAYER_OUTSIDE

    # OUTSIDE FLOOR
    for x in range(0, CASTLE_X, TILE):
        for y in range(0, HEIGHT, TILE):
            selected_tale = random.choices(["out_01","out_02","out_03"], weights=[20, 40,40])
            outside_tiles.append(((x, y), selected_tale[0]))

    # INSIDE FLOOR
    for x in range(CASTLE_X+WALL_THICKNESS, CASTLE_X+CASTLE_W-WALL_THICKNESS, TILE):
        for y in range(WALL_THICKNESS, HEIGHT-WALL_THICKNESS, TILE):
            floor_tiles.append(((x, y), "inner_04"))

    # CASTLE
    for x in range(CASTLE_X, CASTLE_X + CASTLE_W, TILE):  # UP
        wall_tiles.append(((x, 0), "wall_x"))
    for x in range(CASTLE_X, CASTLE_X + CASTLE_W, TILE): # DOWN
        wall_tiles.append(((x, HEIGHT - WALL_THICKNESS), "wall_x")) 
    for y in range(0, HEIGHT, TILE): # RIGHT
        wall_tiles.append(((CASTLE_X + CASTLE_W - WALL_THICKNESS, y), "wall_y"))
    for y in range(0, door_top.top, TILE): # LEFT (up door)
        wall_tiles.append(((CASTLE_X, y), "wall_y"))
    for y in range(door_top.bottom, HEIGHT, TILE): # LEFT (bottom door)
        wall_tiles.append(((CASTLE_X, y), "wall_y"))

    # HITBOX
    walls.extend([
        Rect(CASTLE_X, 0, CASTLE_W, WALL_THICKNESS),  # UP  
        Rect(CASTLE_X, HEIGHT - WALL_THICKNESS, CASTLE_W, WALL_THICKNESS),  # DOWN
        Rect(CASTLE_X + CASTLE_W - WALL_THICKNESS, 0, WALL_THICKNESS, HEIGHT), # RIGHT
        Rect(CASTLE_X, 0, WALL_THICKNESS, door_top.top-20), # LEFT (up door)
        Rect(CASTLE_X, door_top.bottom+20, WALL_THICKNESS, HEIGHT - door_top.bottom), # LEFT (bottom door)
    ])

    # INTERNAL BLOCKS
    for _ in range(60):
        while True:
            x = random.randrange(CASTLE_X + 40, CASTLE_X + CASTLE_W - 60, TILE)
            y = random.randrange(40, HEIGHT - 60, TILE)
            r = Rect(x, y, TILE, TILE)
            if not r.colliderect(chest.inflate(CHEST_SAFE_RADIUS, CHEST_SAFE_RADIUS)):
                selected_tale = random.choices(["block_01","block_02"], weights=[60,40])
                blocks.append((r, selected_tale[0]))
                walls.append(r)
                break

    # ENEMIES
    for _ in range(num_enemy):
        while True:
            x = random.randint(CASTLE_X + 60, CASTLE_X + CASTLE_W - 60)
            y = random.randint(60, HEIGHT - 60)
            r = Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
            if not any(r.colliderect(w) for w in walls):
                enemies.append(Enemy(x, y))
                break

##################
##### PLAYER #####
##################
def move_player():
    fixed_x = player.x
    fixed_y = player.y

    if keyboard.left:
        player.x -= SPEED
    if keyboard.right:
        player.x += SPEED

    player.left = max(0, player.left)
    player.right = min(WIDTH, player.right)

    for w in walls:
        if player.colliderect(w):
            player.x = fixed_x
            break

    if keyboard.up:
        player.y -= SPEED
    if keyboard.down:
        player.y += SPEED

    player.top = max(0, player.top)
    player.bottom = min(HEIGHT, player.bottom)

    for w in walls:
        if player.colliderect(w):
            player.y = fixed_y
            break

##################
### GAME LOOP ####
##################
def update():
    global chest_taken, level, num_enemy, door_open, player_state, player_anim

    if game_state != "playing":
        return

    # Movement
    move_player()
    moving = (keyboard.left or keyboard.right or keyboard.up or keyboard.down)

    if moving:
        if player_state != "walk":
            player_state = "walk"
            player_anim = player_anims["walk"]
            player_anim.reset()
            play_sound(sounds.walk, loop=True)
    else:
        if player_state != "idle":
            player_state = "idle"
            player_anim = player_anims["idle"]
            player_anim.reset()
            sounds.walk.stop()

    player_anim.update()
    enemy_anim.update()

    # Collisions - DOOR
    if any(player.colliderect(d) for d in doors):
        if not door_open:
            play_sound(sounds.door_open)
        door_open = True

    if door_open:
        door_anim.update()

    # CHEST
    if player.colliderect(chest) and not chest_taken:
        chest_taken = True
        chest_anim.reset()
        play_sound(sounds.chest_open)

    if chest_taken:
        prev_finished = chest_anim.finished
        chest_anim.update()
        if chest_anim.finished and not prev_finished:
            play_sound(sounds.coins)

    if chest_taken and player.right < CASTLE_X:
        level += 1
        num_enemy += 1
        play_sound(sounds.wins)
        generate_level()
    
    # ENEMY
    for e in enemies:
        e.move()
        e.update_anim()
        if e.can_see_player():
            play_sound(sounds.die)
            sounds.walk.stop()
            door_open = False
            chest_taken = False
            chest_anim.reset()
            door_anim.reset()
            player.topleft = PLAYER_OUTSIDE
            return

##################
##### INPUT ######
##################
def on_mouse_down(pos):
    global game_state, sound_muted, level, num_enemy

    play_sound(sounds.click)

    # MENU
    if game_state == "menu":
        if btn_start.collidepoint(pos):
            level = 1
            num_enemy = 1
            generate_level()
            game_state = "playing"
            if not sound_muted:
                music.play('background')
                music.set_volume(0.2)

        elif btn_mute.collidepoint(pos):
            sound_muted = not sound_muted

            if sound_muted:
                music.stop()
            else:
                music.play('background')
                music.set_volume(0.2)

        elif btn_exit.collidepoint(pos):
            quit()

    # PLAYING
    elif game_state == "playing":
        if btn_pause.collidepoint(pos):
            game_state = "pause"

    # PAUSE
    elif game_state == "pause":
        if btn_resume.collidepoint(pos):
            game_state = "playing"

        elif btn_mute.collidepoint(pos):
            sound_muted = not sound_muted

            if sound_muted:
                music.stop()
            else:
                music.play('background')
                music.set_volume(0.2)

        elif btn_menu.collidepoint(pos):
            game_state = "menu"

#################
##### DRAW ######
#################
def draw():
    screen.clear()

    # MENU
    if game_state == "menu":
        screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (20, 20, 20))

        # título
        screen.draw.text(
            "STEALTH CASTLE",
            center=(WIDTH // 2, 160),
            fontsize=60,
            color="white"
        )

        # botões
        screen.draw.filled_rect(btn_start, (90, 90, 90))
        screen.draw.text("INICIAR", center=btn_start.center, fontsize=32)

        screen.draw.filled_rect(btn_mute, (90, 90, 90))
        screen.draw.text(
            "DESMUTAR SOM" if sound_muted else "MUTAR SOM",
            center=btn_mute.center,
            fontsize=26
        )

        screen.draw.filled_rect(btn_exit, (90, 90, 90))
        screen.draw.text("SAIR", center=btn_exit.center, fontsize=32)

        return
    
    if game_state == "pause":
        screen.draw.filled_rect(
            Rect(0, 0, WIDTH, HEIGHT),
            (0, 0, 0, 150)
        )

        # botões
        screen.draw.filled_rect(btn_resume, (90, 90, 90))
        screen.draw.text("RETOMAR", center=btn_resume.center, fontsize=32)

        screen.draw.filled_rect(btn_p_mute, (90, 90, 90))
        screen.draw.text(
            "DESMUTAR SOM" if sound_muted else "MUTAR SOM",
            center=btn_p_mute.center,
            fontsize=26
        )

        screen.draw.filled_rect(btn_menu, (90, 90, 90))
        screen.draw.text("MENU", center=btn_menu.center, fontsize=32)

        return


    for pos, tile in outside_tiles:
        screen.blit("tiles/"+tile, pos)


    for (x, y), tile in floor_tiles:
        tile_rect = Rect(x, y, TILE, TILE)
        if not any(tile_rect.colliderect(w) for w in walls):
            screen.blit("tiles/"+tile, (x, y))

    for r, tile in blocks:
        screen.blit("tiles/"+tile, r.topleft)

    for pos, tile in wall_tiles:
        screen.blit("tiles/" + tile, pos)

    frame = door_anim.index
    screen.blit("tiles/" + DOOR_TOP[frame], door_top.topleft)
    screen.blit("tiles/" + DOOR_BOTTOM[frame], door_bottom.topleft)

    screen.blit(chest_anim.get_frame(), chest.topleft)

    for e in enemies:
        e.draw_vision()
        e.draw()
    
    screen.blit(player_anim.get_frame(), player.topleft)

    screen.draw.filled_rect(lbl_level, (80, 80, 80))
    screen.draw.text(f"Level {level}", center=lbl_level.center, fontsize=23)

    # Botão pause
    screen.draw.filled_rect(btn_pause, (80, 80, 80))
    screen.draw.text("PAUSE", center=btn_pause.center, fontsize=24)

    

# ==================================================
# START
# ==================================================
