import math
import time
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from OpenGL.GLU import *

#WORLD 

MAP_SIZE = 1000
ROAD_WIDTH = 100
SIDEWALK_WIDTH = 22
BLOCK_SPACING = 300
STREET_CHARACTER_COUNT = 50

street_characters = []

# radius used for player-vs-building collision checks
PLAYER_RADIUS = 14
# radius used for car-vs-building collision checks
CAR_RADIUS = 24

buildings = []
building_colors = [
    (0.78, 0.68, 0.62),
    (0.64, 0.70, 0.74),
    (0.76, 0.62, 0.52),
    (0.58, 0.65, 0.69),
    (0.82, 0.78, 0.68),
    (0.68, 0.57, 0.52),
    (0.74, 0.72, 0.64)
]

interactive_zones = {
    "gas_station": (-300, -300, 120, 120),
    "safe_house": (300, 300, 120, 120)
}

random.seed(8)

# generate a building for every city block
for road_x in range(-MAP_SIZE, MAP_SIZE, BLOCK_SPACING):
    for road_y in range(-MAP_SIZE, MAP_SIZE, BLOCK_SPACING):
        x = road_x + BLOCK_SPACING / 2
        y = road_y + BLOCK_SPACING / 2
        bw = random.randint(110, 140)
        bh = random.randint(110, 140)
        h = random.randint(140, 320)
        r, g, b = random.choice(building_colors)
        buildings.append((x, y, bw, bh, r, g, b, h))


def get_solid_boxes():
    # returns every axis-aligned solid box in the world as (x, y, width, height)
    boxes = [(bx, by, bw, bh) for bx, by, bw, bh, r, g, b, h in buildings]

    gx, gy, gw, gh = interactive_zones["gas_station"]
    boxes.append((gx, gy + 25, 70, 36))

    sx, sy, sw, sh = interactive_zones["safe_house"]
    boxes.append((sx, sy, 86, 71))

    return boxes


def is_colliding(x, y, radius):
    # circle-vs-rectangle test against every solid box, used to block movement through walls
    for bx, by, bw, bh in get_solid_boxes():
        half_w = bw / 2
        half_h = bh / 2
        closest_x = max(bx - half_w, min(x, bx + half_w))
        closest_y = max(by - half_h, min(y, by + half_h))
        dx = x - closest_x
        dy = y - closest_y
        if dx * dx + dy * dy < radius * radius:
            return True
    return False


def get_building_boxes():
    # returns only the actual city buildings (not the gas station / safe house),
    # used for car-vs-building damage detection
    return [(bx, by, bw, bh) for bx, by, bw, bh, r, g, b, h in buildings]


def is_colliding_building(x, y, radius):
    # circle-vs-rectangle test against city buildings only
    for bx, by, bw, bh in get_building_boxes():
        half_w = bw / 2
        half_h = bh / 2
        closest_x = max(bx - half_w, min(x, bx + half_w))
        closest_y = max(by - half_h, min(y, by + half_h))
        dx = x - closest_x
        dy = y - closest_y
        if dx * dx + dy * dy < radius * radius:
            return True
    return False


def draw_cube(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glutSolidCube(1)
    glPopMatrix()


def draw_ground():
    # grass
    glColor3f(0.28, 0.48, 0.25)
    glBegin(GL_QUADS)
    glVertex3f(-MAP_SIZE, -MAP_SIZE, -2)
    glVertex3f(MAP_SIZE, -MAP_SIZE, -2)
    glVertex3f(MAP_SIZE, MAP_SIZE, -2)
    glVertex3f(-MAP_SIZE, MAP_SIZE, -2)
    glEnd()

    # sidewalks
    glColor3f(0.72, 0.71, 0.67)
    for i in range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING):
        glBegin(GL_QUADS)

        glVertex3f(i - ROAD_WIDTH / 2 - SIDEWALK_WIDTH, -MAP_SIZE, 1)
        glVertex3f(i - ROAD_WIDTH / 2, -MAP_SIZE, 1)
        glVertex3f(i - ROAD_WIDTH / 2, MAP_SIZE, 1)
        glVertex3f(i - ROAD_WIDTH / 2 - SIDEWALK_WIDTH, MAP_SIZE, 1)

        glVertex3f(i + ROAD_WIDTH / 2, -MAP_SIZE, 1)
        glVertex3f(i + ROAD_WIDTH / 2 + SIDEWALK_WIDTH, -MAP_SIZE, 1)
        glVertex3f(i + ROAD_WIDTH / 2 + SIDEWALK_WIDTH, MAP_SIZE, 1)
        glVertex3f(i + ROAD_WIDTH / 2, MAP_SIZE, 1)

        glVertex3f(-MAP_SIZE, i - ROAD_WIDTH / 2 - SIDEWALK_WIDTH, 1)
        glVertex3f(MAP_SIZE, i - ROAD_WIDTH / 2 - SIDEWALK_WIDTH, 1)
        glVertex3f(MAP_SIZE, i - ROAD_WIDTH / 2, 1)
        glVertex3f(-MAP_SIZE, i - ROAD_WIDTH / 2, 1)

        glVertex3f(-MAP_SIZE, i + ROAD_WIDTH / 2, 1)
        glVertex3f(MAP_SIZE, i + ROAD_WIDTH / 2, 1)
        glVertex3f(MAP_SIZE, i + ROAD_WIDTH / 2 + SIDEWALK_WIDTH, 1)
        glVertex3f(-MAP_SIZE, i + ROAD_WIDTH / 2 + SIDEWALK_WIDTH, 1)

        glEnd()

    # roads
    glColor3f(0.09, 0.10, 0.12)
    glBegin(GL_QUADS)
    for i in range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING):
        glVertex3f(i - ROAD_WIDTH / 2, -MAP_SIZE, 2)
        glVertex3f(i + ROAD_WIDTH / 2, -MAP_SIZE, 2)
        glVertex3f(i + ROAD_WIDTH / 2, MAP_SIZE, 2)
        glVertex3f(i - ROAD_WIDTH / 2, MAP_SIZE, 2)

        glVertex3f(-MAP_SIZE, i - ROAD_WIDTH / 2, 2)
        glVertex3f(MAP_SIZE, i - ROAD_WIDTH / 2, 2)
        glVertex3f(MAP_SIZE, i + ROAD_WIDTH / 2, 2)
        glVertex3f(-MAP_SIZE, i + ROAD_WIDTH / 2, 2)
    glEnd()

    draw_road_lines()


def draw_road_lines():
    # dashed center lines
    glColor3f(0.92, 0.82, 0.28)
    for road in range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING):
        for p in range(-MAP_SIZE, MAP_SIZE, 80):
            glBegin(GL_QUADS)
            glVertex3f(road - 2, p, 2.4)
            glVertex3f(road + 2, p, 2.4)
            glVertex3f(road + 2, p + 38, 2.4)
            glVertex3f(road - 2, p + 38, 2.4)

            glVertex3f(p, road - 2, 2.4)
            glVertex3f(p + 38, road - 2, 2.4)
            glVertex3f(p + 38, road + 2, 2.4)
            glVertex3f(p, road + 2, 2.4)
            glEnd()


def draw_building_windows(bx, by, bw, bh, h):
    ww = 18
    wh = 22
    gap = 35
    vgap = 40
    border = 5
    cols_x = max(2, int(bw // gap))
    cols_y = max(2, int(bh // gap))
    floors = max(2, int(h // vgap))
    start_x = bx - ((cols_x - 1) * gap) / 2

    for floor in range(1, floors):
        z = floor * vgap
        for column in range(cols_x):
            wx = start_x + column * gap

            # front
            draw_cube(wx, by - bh / 2 - 0.8, z, ww + border, 2, wh + border, (0.08, 0.10, 0.12))
            draw_cube(wx, by - bh / 2 - 1.9, z, ww, 2, wh, (0.30, 0.67, 0.88))

            # back
            draw_cube(wx, by + bh / 2 + 0.8, z, ww + border, 2, wh + border, (0.08, 0.10, 0.12))
            draw_cube(wx, by + bh / 2 + 1.9, z, ww, 2, wh, (0.30, 0.67, 0.88))

    start_y = by - ((cols_y - 1) * gap) / 2

    for floor in range(1, floors):
        z = floor * vgap
        for column in range(cols_y):
            wy = start_y + column * gap

            # left
            draw_cube(bx - bw / 2 - 0.8, wy, z, 2, ww + border, wh + border, (0.08, 0.10, 0.12))
            draw_cube(bx - bw / 2 - 1.9, wy, z, 2, ww, wh, (0.30, 0.67, 0.88))

            # right
            draw_cube(bx + bw / 2 + 0.8, wy, z, 2, ww + border, wh + border, (0.08, 0.10, 0.12))
            draw_cube(bx + bw / 2 + 1.9, wy, z, 2, ww, wh, (0.30, 0.67, 0.88))


def draw_tree(x, y):
    glPushMatrix()
    glColor3f(0.28, 0.17, 0.08)
    glTranslatef(x, y, 2)
    gluCylinder(gluNewQuadric(), 5, 4, 34, 10, 5)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.12, 0.42, 0.16)
    glTranslatef(x, y, 45)
    gluSphere(gluNewQuadric(), 18, 12, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.16, 0.50, 0.20)
    glTranslatef(x, y, 58)
    gluSphere(gluNewQuadric(), 14, 12, 10)
    glPopMatrix()


def draw_street_light(x, y):
    glPushMatrix()
    glColor3f(0.18, 0.20, 0.22)
    glTranslatef(x, y, 2)
    gluCylinder(gluNewQuadric(), 2.5, 2, 45, 8, 4)
    glPopMatrix()

    draw_cube(x, y, 48, 4, 4, 7, (0.95, 0.90, 0.62))


def draw_street_details():
    # trees and lamps inside block edges
    for x in range(-850, 851, 300):
        for y in range(-850, 851, 300):
            draw_tree(x + 85, y + 85)
            draw_street_light(x - 85, y + 85)


def draw_gas_station():
    zx, zy, zw, zh = interactive_zones["gas_station"]

    glPushMatrix()
    glColor3f(0.66, 0.67, 0.65)
    glTranslatef(zx, zy, 2.5)
    glBegin(GL_QUADS)
    glVertex3f(-zw / 2, -zh / 2, 0)
    glVertex3f(zw / 2, -zh / 2, 0)
    glVertex3f(zw / 2, zh / 2, 0)
    glVertex3f(-zw / 2, zh / 2, 0)
    glEnd()
    glPopMatrix()

    draw_cube(zx, zy + 25, 20, 70, 35, 40, (0.92, 0.90, 0.82))
    draw_cube(zx, zy + 6, 28, 50, 2, 10, (0.18, 0.48, 0.68))

    # canopy
    draw_cube(zx, zy - 25, 36, 98, 58, 6, (0.88, 0.12, 0.12))
    draw_cube(zx, zy - 25, 39.5, 98, 58, 2, (0.96, 0.96, 0.92))

    for px in (zx - 35, zx + 35):
        draw_cube(px, zy - 25, 18, 6, 6, 36, (0.88, 0.88, 0.84))

    # pumps
    for px in (zx - 20, zx + 20):
        draw_cube(px, zy - 25, 10, 8, 10, 20, (0.86, 0.12, 0.12))
        draw_cube(px, zy - 30.5, 13, 5, 1, 6, (0.15, 0.18, 0.20))

def draw_brac_university():
    bx, by = BRAC_POS
    bw, bh = BRAC_W, BRAC_H

    #main building body — covers the exact measured footprint
    draw_cube(bx, by, 100, bw, bh, 200, (0.88, 0.94, 0.84))   # tall white-green body

    # dark base band
    draw_cube(bx, by, 8,  bw + 4, bh + 4, 16, (0.30, 0.52, 0.24))

    # roof slab
    draw_cube(bx, by, 204, bw + 6, bh + 6, 8,  (0.30, 0.52, 0.24))

    # roof structure
    draw_cube(bx, by, 210, bw * 0.6, bh * 0.3, 14, (0.24, 0.44, 0.18))

    #BRAC UNIVERSITY banner — long green slab across the south face
    # south face is at y = by - bh/2
    south_y = by - bh / 2
    draw_cube(bx, south_y - 3, 75, bw + 10, 6, 22, (0.10, 0.40, 0.10))
    # white stripe below banner
    draw_cube(bx, south_y - 3, 61, bw + 10, 6,  4, (0.95, 0.95, 0.95))
    
    # BRAC UNIVERSITY lettering, sitting on the green banner
    draw_text_3d(bx - 60, south_y - 6, 78, "BRAC UNIVERSITY")

    #gate opening in south face
    # left pillar
    draw_cube(bx - 22, south_y - 2, 30, 14, 6, 60, (0.30, 0.52, 0.24))
    # right pillar
    draw_cube(bx + 22, south_y - 2, 30, 14, 6, 60, (0.30, 0.52, 0.24))
    # arch over gate
    draw_cube(bx, south_y - 2, 64, 58, 6, 10, (0.30, 0.52, 0.24))

    #
    for wx2 in (-45, 0, 45):
        for wz in (25, 60, 100, 140, 175):
            draw_cube(bx + wx2, south_y - 1, wz, 18, 2, 20, (0.08, 0.10, 0.12))
            draw_cube(bx + wx2, south_y - 2, wz, 14, 2, 16, (0.30, 0.67, 0.88))

    #corner columns
    for cx2 in (-bw/2 + 8, bw/2 - 8):
        for cy2 in (-bh/2 + 8, bh/2 - 8):
            draw_cube(bx + cx2, by + cy2, 102, 12, 12, 204, (0.75, 0.88, 0.70))


    #bomb plant marker — outside the gate, while the bomb still needs planting
    if final_mission_state == "plant_bomb":
        gx, gy = BRAC_GATE_POS
        glPushMatrix()
        glColor3f(1.0, 0.15, 0.15)
        glTranslatef(gx, gy, 60)
        glutSolidSphere(14, 12, 8)
        glPopMatrix()
        glPushMatrix()
        glColor3f(1.0, 0.15, 0.15)
        glTranslatef(gx, gy, 2)
        gluCylinder(gluNewQuadric(), 2, 2, 58, 8, 2)
        glPopMatrix()

    #planted dynamite — red cylinder + fuse, sitting outside the gate
    if bomb_planted:
        gx, gy = BRAC_GATE_POS
        glPushMatrix()
        glColor3f(0.75, 0.05, 0.05)
        glTranslatef(gx, gy, 4)
        gluCylinder(gluNewQuadric(), 6, 6, 18, 12, 4)
        glPopMatrix()
        glPushMatrix()
        glColor3f(0.15, 0.10, 0.05)
        glTranslatef(gx, gy, 22)
        gluCylinder(gluNewQuadric(), 0.8, 0.4, 10, 6, 2)
        glPopMatrix()

def draw_safe_house():
    zx, zy, zw, zh = interactive_zones["safe_house"]

    draw_cube(zx, zy, 30, 85, 70, 60, (0.70, 0.64, 0.54))
    draw_cube(zx, zy, 64, 95, 80, 8, (0.25, 0.19, 0.15))
    draw_cube(zx, zy - 35.5, 18, 20, 2, 35, (0.20, 0.12, 0.07))

    # windows
    draw_cube(zx - 25, zy - 35.8, 34, 16, 2, 18, (0.08, 0.10, 0.12))
    draw_cube(zx - 25, zy - 37, 34, 12, 2, 14, (0.30, 0.67, 0.88))
    draw_cube(zx + 25, zy - 35.8, 34, 16, 2, 18, (0.08, 0.10, 0.12))
    draw_cube(zx + 25, zy - 37, 34, 12, 2, 14, (0.30, 0.67, 0.88))


def draw_city():
    for bx, by, bw, bh, r, g, b, h in buildings:
        # main building
        draw_cube(bx, by, h / 2, bw, bh, h, (r, g, b))

        # bottom trim
        draw_cube(bx, by, 7, bw + 3, bh + 3, 14, (r * 0.72, g * 0.72, b * 0.72))

        # rooftop
        draw_cube(bx, by, h + 8, bw * 0.45, bh * 0.45, 16, (r * 0.72, g * 0.72, b * 0.72))

        # roof cap
        draw_cube(bx, by, h + 17, bw * 0.50, bh * 0.50, 3, (0.34, 0.35, 0.34))

        draw_building_windows(bx, by, bw, bh, h)

        if int(h) % 3 == 0:
            glPushMatrix()
            glColor3f(0.30, 0.30, 0.32)
            glTranslatef(bx, by, h + 17)
            gluCylinder(gluNewQuadric(), 2.5, 1, 42, 8, 4)
            glPopMatrix()

    draw_gas_station()
    draw_safe_house()
    draw_brac_university()
    draw_street_details()


def drawWORLD():
    draw_ground()
    draw_city()


#PLAYER MODEL

# scales the whole player model down so it looks right next to the city (original height ~270 units)
PLAYER_SCALE = 0.15


def draw_player(player_pos, player_angle, first_person, game_over):
    px, py, pz = player_pos

    # base dimensions, scaled by PLAYER_SCALE below rather than hardcoded small
    body_width = 80
    body_depth = 40
    body_height = 120

    head_radius = 35

    leg_height = 80
    leg_top_radius = 15
    leg_bottom_radius = 5

    arm_radius = 10
    arm_length = 55

    gun_length = 100

    GREEN = (0, 0.35, 0.05)
    BLUE = (0, 0, 1)
    SKIN = (1, 0.75, 0.55)
    BLACK = (0.05, 0.05, 0.05)
    RED = (1, 0, 0)
    GRAY = (0.5, 0.5, 0.5)

    glPushMatrix()

    # move to the player's world position
    glTranslatef(px, py, pz)

    # lie the model down when the game is over, otherwise face the movement angle
    if game_over:
        glRotatef(90, 1, 0, 0)
    else:
        glRotatef(player_angle, 0, 0, 1)

    # everything drawn below this line is scaled down to PLAYER_SCALE
    glScalef(PLAYER_SCALE, PLAYER_SCALE, PLAYER_SCALE)

    # body
    glColor3f(*GREEN)
    glPushMatrix()
    glTranslatef(0, 0, leg_height + body_height / 2)
    glScalef(body_width, body_depth, body_height)
    glutSolidCube(1)
    glPopMatrix()

    # head, hidden in first person so it doesn't block the view
    if not first_person:
        glColor3f(*BLACK)
        glPushMatrix()
        glTranslatef(0, 0, leg_height + body_height + head_radius)
        gluSphere(gluNewQuadric(), head_radius, 12, 8)
        glPopMatrix()

    # eyes
    if not first_person:
        glColor3f(*RED)
        for x in (-12, 12):
            glPushMatrix()
            glTranslatef(x, head_radius - 5, leg_height + body_height + head_radius + 5)
            gluSphere(gluNewQuadric(), 6, 8, 6)
            glPopMatrix()

    # legs
    glColor3f(*BLUE)
    for x in (-25, 25):
        glPushMatrix()
        glTranslatef(x, 0, leg_height / 2)
        gluCylinder(gluNewQuadric(), leg_top_radius, leg_bottom_radius, leg_height, 10, 6)
        glPopMatrix()

    # arms
    glColor3f(*SKIN)

    glPushMatrix()
    glTranslatef(-18, 25, leg_height + body_height - 40)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), arm_radius, arm_radius, arm_length, 10, 6)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(18, 25, leg_height + body_height - 40)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), arm_radius, arm_radius, arm_length, 10, 6)
    glPopMatrix()

    # gun
    glColor3f(*GRAY)
    glPushMatrix()
    glTranslatef(0, 100, leg_height + body_height - 40)
    glScalef(20, gun_length, 20)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()


#GAME MAIN GLOBALS

# camera
camera_radius = 120
camera_angle = 0
camera_height = 85
first_person = False
fovY = 120

# screen
screen_width = 0
screen_height = 0

# game stats
player_life_remaining = 5
game_score = 0
player_money = 25

# player
player_pos = [200, 100, 0]
player_angle = 0
player_speed = 8
rotation_speed = 5
PLAYER_LIMIT = MAP_SIZE - 30
RUN_SPEED = player_speed * 2

# bullets
bullets = []
bullet_speed = 1000
bullet_size = 2

# firing mode: toggled with 'b' between single-shot and automatic spray
spray_mode = False
mouse_fire_held = False
spray_fire_rate = 8      # bullets per second while spraying
spray_fire_timer = 0.0

# enemies
enemies = []
MAX_ENEMIES = 5
enemy_speed = 20
enemy_body_radius = 35
enemy_head_radius = 20
enemy_spawn_distance = 250

# game state
game_over = False
game_paused = False
last_time = time.perf_counter()
game_menu_open = True
menu_buttons = {}

# cheat mode
cheat_mode         = False
cheat_waypoints    = []      # list of (x, y) road intersections to follow
cheat_target       = None    # "pickup" or "dropoff"
CHEAT_SPEED        = 8       # steady cruise speed
CHEAT_ARRIVE_DIST  = 30      # how close to a waypoint before moving to next


#Mission Syste
MISSION_DEFS = [
    {"pickup": (200, 785), "dropoff": ( -687, -689)},
    {"pickup": (   494, 966), "dropoff": (-690,  -113)},
    {"pickup": ( -322,  -412), "dropoff": (-236,    499)},
]

MISSION_TRIGGER_RADIUS  = 80   
PICKUP_RADIUS           = 70   
DROPOFF_RADIUS          = 70   


mission_state       = "idle"
current_mission_idx = 0        
missions_completed  = 0
drug_picked_up      = False
mission_hint        = ""       

# car
car_x = 160
car_y = 150
car_z = 0
car_angle = 0
car_speed = 0
car_max_speed = 20
car_acceleration = 0.5
car_friction = 0.3
car_turn_speed = 3

# fuel
car_fuel          = 100.0   # current fuel 0-100
CAR_FUEL_MAX      = 100.0
CAR_FUEL_DRAIN    = 0.04    # units lost per frame while moving
CAR_FUEL_IDLE     = 0.005   # tiny drain even while idling in car
FUEL_COST_PER_L   = 2       # $ per unit of fuel
GAS_STATION_RADIUS = 110    # how close car must be to refuel
fuel_hint         = ""      # shown near gas station

# car health (damaged by colliding with buildings)
car_health              = 100
CAR_HEALTH_MAX          = 100
CAR_HEALTH_DAMAGE       = 5      # lost per collision with a building
car_was_colliding_building = False   # tracks previous frame so damage is applied once per hit, not every frame



#SHOP
SHOP_PANEL_W = 800
SHOP_PANEL_H = 600
SHOP_BORDER  = 8

shop_open    = False
shop_message = ""
shop_buttons = {}

SHOP_REFUEL_PRICE     = 10
SUSPICION_CLEAR_PRICE = 30
SHOP_REPAIR_PRICE     = 2

BULLET_DAMAGE_BASE      = 1
BULLET_DAMAGE_MAX_LEVEL = 3
BULLET_DAMAGE_PRICES    = [50, 100, 150]
bullet_damage           = BULLET_DAMAGE_BASE
bullet_damage_level     = 0

RUN_SPEED_BASE          = RUN_SPEED
STAMINA_MAX_LEVEL       = 3
STAMINA_BOOST_PER_LEVEL = 4
STAMINA_PRICES          = [40, 80, 120]
stamina_level           = 0

CAR_MAX_SPEED_BASE        = car_max_speed
CAR_SPEED_MAX_LEVEL       = 3
CAR_SPEED_BOOST_PER_LEVEL = 5
CAR_SPEED_PRICES          = [60, 120, 200]
car_speed_level            = 0



#steering
steering_wheel_angle = 0
STEER_MAX = 33
STEER_STEP = 6

# pressed_keys is shared by on-foot movement and car movement
player_in_car = False
pressed_keys = set()

#JUMP + RUN

jumping = False
jump_velocity = 0.0

JUMP_HEIGHT = 40.0
JUMP_GRAVITY = 400.0
JUMP_VELOCITY = (2.0 * JUMP_GRAVITY * JUMP_HEIGHT) ** 0.5

RUN_SPEED = player_speed * 2

#NPC CARS

NPC_CAR_COUNT   = 20     # how many NPC cars to spawn
NPC_CAR_SPEED   = 6.0    # cruising speed
NPC_TURN_RATE   = 2.5    # degrees per frame when steering
NPC_STUCK_TIME  = 1.8    # seconds before declaring stuck and forcing a turn


#K9 and HEAT

K9_RADIUS         = 120     
SAFEHOUSE_ESCAPE  = 130     

K9_POSITIONS = [
    (-300,  150),
    ( 300, -150),
    (   0,  450),
    (-600,    0),
    ( 600,  300),
    ( 150, -450),
]

suspicion_level  = 0       
heat_level       = 0        
k9_cooldown      = {}       

# police car state
police_active    = False
police_x         = 0.0
police_y         = 0.0
police_angle     = 0.0
POLICE_SPEED     = 4


#FINAL MISSION
BRAC_POS         = (51.0, -551.0)
BRAC_W           = 127
BRAC_H           = 180

# Gate is on the south face (low y side), just outside
BRAC_GATE_POS    = (51.0, -648.0)
BRAC_GATE_RADIUS = 60

BOMB_PICKUP_POS    = (-414.0, 509.0)
BOMB_PICKUP_RADIUS = 70


FINAL_SAFEHOUSE_RADIUS = 130

final_mission_state   = "locked"
bomb_picked_up        = False
bomb_planted          = False
bomb_cooldown_timer   = 0.0
POLICE_RESPONSE_DELAY = 2.0   # seconds of quiet time after planting before cops show up

final_police_cars     = []
FINAL_POLICE_SPEED    = 5

building_cops         = []
BUILDING_COP_COUNT    = 10
building_cops_spawned = False



def draw_k9_dog(x, y):
    glPushMatrix()
    glTranslatef(x, y, 10)   # lift the whole dog up so legs sit on ground

    BROWN = (0.55, 0.35, 0.15)
    DARK  = (0.30, 0.18, 0.08)

    # legs — drawn first at z=0 (ground level relative to base)
    glColor3f(*BROWN)
    for lx in (-5, 5):
        for ly in (-7, 5):
            glPushMatrix()
            glTranslatef(lx, ly, -6)
            glScalef(4, 4, 10)
            glutSolidCube(1)
            glPopMatrix()

    # body sits on top of legs
    glColor3f(*BROWN)
    glPushMatrix()
    glTranslatef(0, 0, 6)
    glScalef(14, 22, 10)
    glutSolidCube(1)
    glPopMatrix()

    # head
    glColor3f(*BROWN)
    glPushMatrix()
    glTranslatef(0, 13, 12)
    glScalef(10, 10, 10)
    glutSolidCube(1)
    glPopMatrix()

    # snout
    glColor3f(*DARK)
    glPushMatrix()
    glTranslatef(0, 18, 10)
    glScalef(6, 4, 5)
    glutSolidCube(1)
    glPopMatrix()

    # ears
    glColor3f(*DARK)
    for ex in (-5, 5):
        glPushMatrix()
        glTranslatef(ex, 12, 18)
        glScalef(4, 3, 6)
        glutSolidCube(1)
        glPopMatrix()

    # tail
    glColor3f(*DARK)
    glPushMatrix()
    glTranslatef(0, -12, 10)
    glRotatef(40, 1, 0, 0)
    glScalef(3, 3, 12)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

def draw_k9_zones():
    for i, (kx, ky) in enumerate(K9_POSITIONS):
        draw_k9_dog(kx, ky)

        # only show the danger radius when player is carrying drugs
        if not drug_picked_up:
            continue

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)

        glColor4f(1.0, 0.05, 0.05, 0.18)
        segs = 48
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(kx, ky, 3)
        for s in range(segs + 1):
            a = 2 * math.pi * s / segs
            glVertex3f(kx + math.cos(a) * K9_RADIUS,
                       ky + math.sin(a) * K9_RADIUS, 3)
        glEnd()

        glColor4f(1.0, 0.1, 0.1, 0.7)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        for s in range(segs):
            a = 2 * math.pi * s / segs
            glVertex3f(kx + math.cos(a) * K9_RADIUS,
                       ky + math.sin(a) * K9_RADIUS, 3)
        glEnd()
        glLineWidth(1)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

def draw_police_car():
    if not police_active:
        return

    glPushMatrix()
    glTranslatef(police_x, police_y, 0)
    glRotatef(police_angle, 0, 0, 1)

    # white body
    glColor3f(0.95, 0.95, 0.95)
    draw_car_body()

    # hood
    glPushMatrix()
    glColor3f(0.95, 0.95, 0.95)
    glTranslatef(0, 20, 10)
    glRotatef(-7, 1, 0, 0)
    glScalef(30, 25, 3)
    glutSolidCube(1)
    glPopMatrix()

    # cabin
    glPushMatrix()
    glColor3f(0.06, 0.08, 0.12)
    glTranslatef(0, -6, 16)
    glScalef(25, 27, 10)
    glutSolidCube(1)
    glPopMatrix()

    # blue/red light bar on roof
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.9)
    glTranslatef(-5, -5, 25)
    glScalef(7, 12, 4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.9, 0.05, 0.05)
    glTranslatef(5, -5, 25)
    glScalef(7, 12, 4)
    glutSolidCube(1)
    glPopMatrix()

    # side stripes — blue
    for sx in (-20, 20):
        glPushMatrix()
        glColor3f(0.1, 0.2, 0.9)
        glTranslatef(sx, -1, 7)
        glScalef(2, 45, 4)
        glutSolidCube(1)
        glPopMatrix()

    # wheels
    q = gluNewQuadric()
    for wx in (-18, 18):
        for wy in (-20, 20):
            glPushMatrix()
            glColor3f(0.03, 0.03, 0.03)
            glTranslatef(wx, wy, 6)
            glRotatef(90, 0, 1, 0)
            gluCylinder(q, 6, 6, 3, 16, 3)
            glPopMatrix()
            glPushMatrix()
            glColor3f(0.7, 0.7, 0.72)
            glTranslatef(wx * (18.2/18), wy, 6)
            glRotatef(90, 0, 1, 0)
            gluDisk(gluNewQuadric(), 0, 3.5, 12, 1)
            glPopMatrix()

    # headlights
    for lx in (-10, 10):
        glPushMatrix()
        glColor3f(1.0, 0.95, 0.75)
        glTranslatef(lx, 32, 8)
        glScalef(8, 2, 3)
        glutSolidCube(1)
        glPopMatrix()

    glPopMatrix()

def draw_building_cops():
    """Foot cops inside the BRAC building."""
    for cop in building_cops:
        if cop.get("dead"):
            continue
        glPushMatrix()
        glTranslatef(cop["x"], cop["y"], 0)
        glRotatef(cop["angle"], 0, 0, 1)
        glScalef(0.15, 0.15, 0.15)

        # body — dark blue uniform
        glColor3f(0.10, 0.14, 0.45)
        glPushMatrix()
        glTranslatef(0, 0, 92)
        glScalef(80, 40, 120)
        glutSolidCube(1)
        glPopMatrix()

        # head
        glColor3f(1.0, 0.80, 0.60)
        glPushMatrix()
        glTranslatef(0, 0, 185)
        gluSphere(gluNewQuadric(), 35, 10, 8)
        glPopMatrix()

        # hat
        glColor3f(0.10, 0.14, 0.45)
        glPushMatrix()
        glTranslatef(0, 0, 220)
        glScalef(60, 60, 20)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()


def draw_final_police_cars():
    for pc in final_police_cars:
        glPushMatrix()
        glTranslatef(pc["x"], pc["y"], 0)
        glRotatef(pc["angle"], 0, 0, 1)

        glColor3f(0.95, 0.95, 0.95)
        draw_car_body()

        # light bar
        glPushMatrix()
        glColor3f(0.1, 0.1, 0.9)
        glTranslatef(-5, -5, 25)
        glScalef(7, 12, 4)
        glutSolidCube(1)
        glPopMatrix()
        glPushMatrix()
        glColor3f(0.9, 0.05, 0.05)
        glTranslatef(5, -5, 25)
        glScalef(7, 12, 4)
        glutSolidCube(1)
        glPopMatrix()

        # side stripes
        for sx in (-20, 20):
            glPushMatrix()
            glColor3f(0.1, 0.2, 0.9)
            glTranslatef(sx, -1, 7)
            glScalef(2, 45, 4)
            glutSolidCube(1)
            glPopMatrix()

        # wheels
        q = gluNewQuadric()
        for wx in (-18, 18):
            for wy in (-20, 20):
                glPushMatrix()
                glColor3f(0.03, 0.03, 0.03)
                glTranslatef(wx, wy, 6)
                glRotatef(90, 0, 1, 0)
                gluCylinder(q, 6, 6, 3, 16, 3)
                glPopMatrix()
                glPushMatrix()
                glColor3f(0.7, 0.7, 0.72)
                glTranslatef(wx * (18.2 / 18), wy, 6)
                glRotatef(90, 0, 1, 0)
                gluDisk(gluNewQuadric(), 0, 3.5, 12, 1)
                glPopMatrix()

        glPopMatrix()

def update_final_mission(delta_time):
    # game_over must be declared global here too, otherwise these assignments
    global final_mission_state, bomb_picked_up, bomb_planted
    global building_cops, building_cops_spawned, game_over, bomb_cooldown_timer
    

    # only active after all 3 normal missions done
    if missions_completed < 3:
        return

    if final_mission_state == "locked":
        final_mission_state = "get_bomb"
        mission_hint = "FINAL MISSION: Go pick up the bomb package!"
        return

    px, py = _player_world_pos()
    bx, by = BRAC_POS
    sx, sy, _, _ = interactive_zones["safe_house"]

    #phase 1: pick up the bomb
    if final_mission_state == "get_bomb":
        dist = math.hypot(px - BOMB_PICKUP_POS[0], py - BOMB_PICKUP_POS[1])
        mission_hint = f"FINAL: Pick up the bomb  ({dist:.0f} away)"
        if dist < BOMB_PICKUP_RADIUS:
            bomb_picked_up      = True
            final_mission_state = "drive_to_brac"
            mission_hint        = "FINAL: Drive to BRAC University!"

    #phase 2: drive to the marker outside the BRAC gate
    elif final_mission_state == "drive_to_brac":
        dist = math.hypot(px - BRAC_GATE_POS[0], py - BRAC_GATE_POS[1])
        mission_hint = f"FINAL: Reach the marker outside BRAC University  ({dist:.0f} away)"
        if dist < BRAC_GATE_RADIUS:
            final_mission_state = "plant_bomb"
            mission_hint        = "FINAL: Press F to plant the bomb!"

    #phase 3: plant the bomb at the marker
    elif final_mission_state == "plant_bomb":
        dist = math.hypot(px - BRAC_GATE_POS[0], py - BRAC_GATE_POS[1])
        if dist < BRAC_GATE_RADIUS:
            mission_hint = "FINAL: Press F to plant the bomb!"
        else:
            final_mission_state = "drive_to_brac"  # walked away from the marker

    #phase 4: cops incoming — short delay before they respond to the blast 
    elif final_mission_state == "cops_incoming":
        bomb_cooldown_timer -= delta_time
        mission_hint = f"FINAL: BOMB PLANTED! Cops incoming in {max(0, bomb_cooldown_timer):.1f}s..."
        if bomb_cooldown_timer <= 0:
            final_mission_state = "fight_out"

    #phase 5: fight out — cops attack, player must kill them
    elif final_mission_state == "fight_out":
        if not building_cops_spawned:
            building_cops_spawned = True
            # spawn cops in a ring around the building
            for i in range(BUILDING_COP_COUNT):
                angle = 2 * math.pi * i / BUILDING_COP_COUNT
                ox = math.cos(angle) * 55
                oy = math.sin(angle) * 55
                building_cops.append({
                    "x": bx + ox, "y": by + oy,
                    "angle": 0.0,
                    "hp": 2,
                    "dead": False,
                })
            # spawn 2 police cars on roads nearby
            for spawn in [(-300, -450), (300, -450)]:
                final_police_cars.append({
                    "x": float(spawn[0]), "y": float(spawn[1]),
                    "angle": float(random.choice([0, 90, 180, 270])),
                    "stuck_timer": 0.0,
                })

        mission_hint = (
            f"FINAL: Kill the cops ({sum(1 for c in building_cops if not c['dead'])}"
            f" remaining) then escape to Safe House!"
        )

        # update cops — chase and shoot player
        for cop in building_cops:
            if cop["dead"]:
                continue
            dx = px - cop["x"]
            dy = py - cop["y"]
            dist = math.hypot(dx, dy)
            if dist > 0:
                cop["angle"] = math.degrees(math.atan2(-dx, dy))
                step = min(3.0, dist)
                cop["x"] += (dx / dist) * step
                cop["y"] += (dy / dist) * step

            if dist < 25:
                game_over = True   # cop caught the player
                return

    
        all_dead = all(c["dead"] for c in building_cops)
        if all_dead:
            final_mission_state = "escape"
            mission_hint = "FINAL: Cops down! Get to the Safe House NOW!"

        # update final police cars — road-following same as main police
        _update_final_police_cars(delta_time, px, py)

        # final police car catch
        for pc in final_police_cars:
            catch_r = CAR_RADIUS * 2 if player_in_car else 22
            if math.hypot(px - pc["x"], py - pc["y"]) < catch_r:
                game_over = True
                return

    #phase 6: escape to safe house
    elif final_mission_state == "escape":
        mission_hint = "FINAL: Reach the Safe House to WIN!"
        _update_final_police_cars(delta_time, px, py)

        for pc in final_police_cars:
            catch_r = CAR_RADIUS * 2 if player_in_car else 22
            if math.hypot(px - pc["x"], py - pc["y"]) < catch_r:
                game_over = True
                return

        if math.hypot(px - sx, py - sy) < FINAL_SAFEHOUSE_RADIUS:
            final_mission_state = "victory"
            final_police_cars.clear()
            mission_hint = ""

    elif final_mission_state == "victory":
        pass   # handled by show_status


def _update_final_police_cars(delta_time, px, py):
    """Road-following chase for final mission police cars."""
    ROAD_COORDS    = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    SNAP_THRESHOLD = 10
    limit          = MAP_SIZE - 50

    for pc in final_police_cars:
        cur_angle = pc["angle"] % 360
        rad       = math.radians(pc["angle"])
        fx        = -math.sin(rad)
        fy        =  math.cos(rad)

        new_px = pc["x"] + fx * FINAL_POLICE_SPEED
        new_py = pc["y"] + fy * FINAL_POLICE_SPEED

        blocked = (
            abs(new_px) > limit or abs(new_py) > limit or
            is_colliding(new_px, new_py, CAR_RADIUS)
        )

        if blocked:
            best_angle = pc["angle"]
            best_dot   = -999
            for turn in [90, -90, 180]:
                candidate = (pc["angle"] + turn) % 360
                r2 = math.radians(candidate)
                fx2, fy2 = -math.sin(r2), math.cos(r2)
                tx = pc["x"] + fx2 * FINAL_POLICE_SPEED
                ty = pc["y"] + fy2 * FINAL_POLICE_SPEED
                if abs(tx) > limit or abs(ty) > limit or is_colliding(tx, ty, CAR_RADIUS):
                    continue
                to_px = px - pc["x"]
                to_py = py - pc["y"]
                length = math.hypot(to_px, to_py)
                if length == 0:
                    continue
                dot = (fx2 * to_px + fy2 * to_py) / length
                if dot > best_dot:
                    best_dot   = dot
                    best_angle = candidate
            pc["angle"] = float(best_angle)
            new_cur = pc["angle"] % 360
            if new_cur in (0, 180):
                pc["x"] = float(min(ROAD_COORDS, key=lambda r: abs(r - pc["x"])))
            else:
                pc["y"] = float(min(ROAD_COORDS, key=lambda r: abs(r - pc["y"])))
        else:
            pc["x"] = new_px
            pc["y"] = new_py

            on_x = any(abs(pc["x"] - rx) < SNAP_THRESHOLD for rx in ROAD_COORDS)
            on_y = any(abs(pc["y"] - ry) < SNAP_THRESHOLD for ry in ROAD_COORDS)
            if on_x and on_y:
                dx = px - pc["x"]
                dy = py - pc["y"]
                if cur_angle in (0, 180):
                    if abs(dx) > abs(dy) * 0.5:
                        wanted = 90 if dx > 0 else 270
                        r2 = math.radians(wanted)
                        if not is_colliding(pc["x"] + (-math.sin(r2)) * FINAL_POLICE_SPEED,
                                            pc["y"] + math.cos(r2) * FINAL_POLICE_SPEED,
                                            CAR_RADIUS):
                            pc["angle"] = float(wanted)
                            pc["y"] = float(min(ROAD_COORDS, key=lambda r: abs(r - pc["y"])))
                else:
                    if abs(dy) > abs(dx) * 0.5:
                        wanted = 0 if dy > 0 else 180
                        r2 = math.radians(wanted)
                        if not is_colliding(pc["x"] + (-math.sin(r2)) * FINAL_POLICE_SPEED,
                                            pc["y"] + math.cos(r2) * FINAL_POLICE_SPEED,
                                            CAR_RADIUS):
                            pc["angle"] = float(wanted)
                            pc["x"] = float(min(ROAD_COORDS, key=lambda r: abs(r - pc["x"])))



def update_heat(delta_time):
    global suspicion_level, heat_level, police_active
    global police_x, police_y, police_angle
    global k9_cooldown, mission_state, drug_picked_up, game_over

    px, py = _player_world_pos()

    # tick down cooldowns
    for idx in list(k9_cooldown):
        k9_cooldown[idx] -= delta_time
        if k9_cooldown[idx] <= 0:
            del k9_cooldown[idx]

    # k9 sniff — only when carrying drugs
    if drug_picked_up:
        for i, (kx, ky) in enumerate(K9_POSITIONS):
            if i in k9_cooldown:
                continue
            if math.hypot(px - kx, py - ky) < K9_RADIUS:
                suspicion_level += 1
                k9_cooldown[i] = 4.0
                if suspicion_level >= 3 and not police_active:
                    heat_level    = 1
                    police_active = True
                    # spawn police on the nearest road behind the player
                    ROAD_COORDS   = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
                    spawn_dist    = 250
                    angle_rad     = math.radians(car_angle if player_in_car else player_angle)
                    raw_sx        = px - (-math.sin(angle_rad)) * spawn_dist
                    raw_sy        = py - ( math.cos(angle_rad)) * spawn_dist
                    # snap spawn to the nearest road intersection
                    police_x      = float(min(ROAD_COORDS, key=lambda r: abs(r - raw_sx)))
                    police_y      = float(min(ROAD_COORDS, key=lambda r: abs(r - raw_sy)))
                    police_angle  = float(random.choice([0, 90, 180, 270]))
                break

    if not police_active:
        return

    #road-following pathfinde
    ROAD_COORDS    = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    SNAP_THRESHOLD = 10
    limit          = MAP_SIZE - 50

    cur_angle = police_angle % 360

    angle_rad  = math.radians(police_angle)
    forward_x  = -math.sin(angle_rad)
    forward_y  =  math.cos(angle_rad)

    new_px = police_x + forward_x * POLICE_SPEED
    new_py = police_y + forward_y * POLICE_SPEED

    blocked = (
        abs(new_px) > limit or
        abs(new_py) > limit or
        is_colliding(new_px, new_py, CAR_RADIUS)
    )

    if blocked:
        # forced turn — try each 90° and pick the one that faces the player most
        best_angle = police_angle
        best_dot   = -999
        for turn in [90, -90, 180]:
            candidate = (police_angle + turn) % 360
            rad = math.radians(candidate)
            fx  = -math.sin(rad)
            fy  =  math.cos(rad)
            test_x = police_x + fx * POLICE_SPEED
            test_y = police_y + fy * POLICE_SPEED
            if (abs(test_x) > limit or abs(test_y) > limit or
                    is_colliding(test_x, test_y, CAR_RADIUS)):
                continue
            # dot product: how much does this direction face the player?
            to_px = px - police_x
            to_py = py - police_y
            length = math.hypot(to_px, to_py)
            if length == 0:
                continue
            dot = (fx * to_px + fy * to_py) / length
            if dot > best_dot:
                best_dot   = dot
                best_angle = candidate
        police_angle = float(best_angle)

        # snap back onto the nearest road so it doesn't get stuck in a gap
        new_cur = police_angle % 360
        if new_cur in (0, 180):
            police_x = float(min(ROAD_COORDS, key=lambda r: abs(r - police_x)))
        else:
            police_y = float(min(ROAD_COORDS, key=lambda r: abs(r - police_y)))

    else:
        police_x = new_px
        police_y = new_py

        # at an intersection opportunistically steer toward the player
        on_x_road = any(abs(police_x - rx) < SNAP_THRESHOLD for rx in ROAD_COORDS)
        on_y_road = any(abs(police_y - ry) < SNAP_THRESHOLD for ry in ROAD_COORDS)

        if on_x_road and on_y_road:
            # decide preferred direction toward player
            dx = px - police_x
            dy = py - police_y

            if cur_angle in (0, 180):        # currently on Y road, can turn onto X
                if abs(dx) > abs(dy) * 0.5:  # player is more sideways than ahead
                    wanted = 90 if dx > 0 else 270
                    rad = math.radians(wanted)
                    tx  = police_x + (-math.sin(rad)) * POLICE_SPEED
                    ty  = police_y + ( math.cos(rad)) * POLICE_SPEED
                    if not is_colliding(tx, ty, CAR_RADIUS):
                        police_angle = float(wanted)
                        police_y = float(min(ROAD_COORDS,
                                             key=lambda r: abs(r - police_y)))
            else:                            # currently on X road, can turn onto Y
                if abs(dy) > abs(dx) * 0.5:
                    wanted = 0 if dy > 0 else 180
                    rad = math.radians(wanted)
                    tx  = police_x + (-math.sin(rad)) * POLICE_SPEED
                    ty  = police_y + ( math.cos(rad)) * POLICE_SPEED
                    if not is_colliding(tx, ty, CAR_RADIUS):
                        police_angle = float(wanted)
                        police_x = float(min(ROAD_COORDS,
                                             key=lambda r: abs(r - police_x)))

    #catch check — game over if police touches player / player car
    catch_radius = 40 if player_in_car else 22
    if math.hypot(px - police_x, py - police_y) < catch_radius:
        game_over = True
        _clear_heat()
        return

    #safe house escape
    sx, sy, _, _ = interactive_zones["safe_house"]
    if math.hypot(px - sx, py - sy) < SAFEHOUSE_ESCAPE:
        _clear_heat()
        

def _clear_heat():
    global suspicion_level, heat_level, police_active, k9_cooldown
    suspicion_level = 0
    heat_level      = 0
    police_active   = False
    k9_cooldown     = {}
    

def _player_world_pos():
    """Return the 2-D world position of the player (or car if driving)."""
    if player_in_car:
        return car_x, car_y
    return player_pos[0], player_pos[1]


def _near(ax, ay, bx, by, radius):
    return math.hypot(ax - bx, ay - by) < radius


def update_mission():
    global mission_state, current_mission_idx, missions_completed
    global drug_picked_up, mission_hint, player_money

    sx, sy, _, _ = interactive_zones["safe_house"]
    px, py = _player_world_pos()

    if mission_state == "idle":
        if _near(px, py, sx, sy, MISSION_TRIGGER_RADIUS):
            mission_hint = "Press M at the safe house to start a mission"
        else:
            mission_hint = ""
        return

    if mission_state == "at_safehouse":
        mission_hint = "Press M to start Mission {}/3".format(current_mission_idx + 1)
        return

    if missions_completed >= 3:
        mission_state = "done"
        mission_hint  = "All 3 missions complete!  Good work."
        return

    m = MISSION_DEFS[current_mission_idx]
    pick_x, pick_y = m["pickup"]
    drop_x, drop_y = m["dropoff"]

    if mission_state == "going_pickup":
        dist = math.hypot(px - pick_x, py - pick_y)
        mission_hint = (
            "Mission {}/3  |  Go pick up the package  "
            "({:.0f} units away)".format(current_mission_idx + 1, dist)
        )
        if _near(px, py, pick_x, pick_y, PICKUP_RADIUS):
            drug_picked_up  = True
            mission_state   = "carrying"

    elif mission_state == "carrying":
        dist = math.hypot(px - drop_x, py - drop_y)
        mission_hint = (
            "Mission {}/3  |  Deliver the package  "
            "({:.0f} units away)".format(current_mission_idx + 1, dist)
        )
        if _near(px, py, drop_x, drop_y, DROPOFF_RADIUS):
            drug_picked_up    = False
            missions_completed += 1
            player_money += 100
            _clear_heat()  
            if missions_completed >= 3:
                mission_state = "done"
                mission_hint  = "All 3 missions complete!  Good work."
            else:
                current_mission_idx += 1
                mission_state = "idle"
                mission_hint  = "Delivery done!  Return to safe house for next mission."

    elif mission_state == "done":
        mission_hint = "All 3 missions complete!  Good work."

def _road_nodes():
    """All road intersection coordinates on the grid."""
    coords = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    nodes = []
    for x in coords:
        for y in coords:
            nodes.append((x, y))
    return nodes


def _nearest_node(x, y):
    """Snap any world position to the closest road intersection."""
    nodes = _road_nodes()
    return min(nodes, key=lambda n: math.hypot(n[0] - x, n[1] - y))


def _bfs_path(start_node, end_node):
    """BFS on the road grid — returns list of (x,y) waypoints start→end."""
    if start_node == end_node:
        return [start_node]

    coords  = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    coord_set = set(coords)

    def neighbours(nx, ny):
        # four cardinal road directions
        result = []
        if nx + BLOCK_SPACING in coord_set or nx - BLOCK_SPACING in coord_set:
            pass  # x is on a road line — can go north/south along it
        for dx, dy in [(BLOCK_SPACING, 0), (-BLOCK_SPACING, 0),
                       (0, BLOCK_SPACING), (0, -BLOCK_SPACING)]:
            nb = (nx + dx, ny + dy)
            if nb[0] in coord_set and nb[1] in coord_set:
                result.append(nb)
        return result

    visited = {start_node}
    queue   = [(start_node, [start_node])]

    while queue:
        (cx, cy), path = queue.pop(0)
        for nb in neighbours(cx, cy):
            if nb == end_node:
                return path + [nb]
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, path + [nb]))

    return [start_node, end_node]   # fallback — straight line


def _plan_cheat_route(target_x, target_y):
    """Build waypoint list from car's current position to (target_x, target_y)."""
    start = _nearest_node(car_x, car_y)
    end   = _nearest_node(target_x, target_y)
    path  = _bfs_path(start, end)
    # add the exact target at the end so we arrive precisely
    path.append((target_x, target_y))
    return path

def update_cheat_drive():
    global cheat_mode, cheat_waypoints, cheat_target
    global car_x, car_y, car_angle, car_speed

    if not cheat_mode:
        return

    # cancel if conditions lost
    if not player_in_car or mission_state not in ("going_pickup", "carrying"):
        cheat_mode      = False
        cheat_waypoints = []
        car_speed       = 0
        return

    # keep target in sync with mission state
    new_target = "pickup" if mission_state == "going_pickup" else "dropoff"
    if new_target != cheat_target:
        cheat_target    = new_target
        m               = MISSION_DEFS[current_mission_idx]
        tx, ty          = m["pickup"] if cheat_target == "pickup" else m["dropoff"]
        cheat_waypoints = _plan_cheat_route(tx, ty)

    if not cheat_waypoints:
        m               = MISSION_DEFS[current_mission_idx]
        tx, ty          = m["pickup"] if cheat_target == "pickup" else m["dropoff"]
        cheat_waypoints = _plan_cheat_route(tx, ty)
        if not cheat_waypoints:
            cheat_mode = False
            return

    wx, wy = cheat_waypoints[0]

    dx   = wx - car_x
    dy   = wy - car_y
    dist = math.hypot(dx, dy)

    if dist < CHEAT_ARRIVE_DIST:
        # snap car exactly onto the waypoint before moving to next
        car_x = float(wx)
        car_y = float(wy)
        cheat_waypoints.pop(0)
        if not cheat_waypoints:
            car_speed  = 0
            cheat_mode = False
        return

    #determine axis of travel
    # look at where we came from vs where we're going to decide H or V travel
    if abs(dx) > abs(dy):
        # travelling horizontally — lock Y to current road line
        ROAD_COORDS = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
        car_y = float(min(ROAD_COORDS, key=lambda r: abs(r - car_y)))
        move_x = CHEAT_SPEED if dx > 0 else -CHEAT_SPEED
        move_y = 0.0
        car_angle = 90.0 if dx > 0 else 270.0
    else:
        # travelling vertically — lock X to current road line
        ROAD_COORDS = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
        car_x = float(min(ROAD_COORDS, key=lambda r: abs(r - car_x)))
        move_x = 0.0
        move_y = CHEAT_SPEED if dy > 0 else -CHEAT_SPEED
        car_angle = 0.0 if dy > 0 else 180.0

    # clamp inside map before applying movement
    new_cx = max(-MAP_SIZE + 50, min(car_x + move_x, MAP_SIZE - 50))
    new_cy = max(-MAP_SIZE + 50, min(car_y + move_y, MAP_SIZE - 50))

    car_x     = new_cx
    car_y     = new_cy
    car_speed = CHEAT_SPEED

    # keep player glued to car
    player_pos[0] = car_x
    player_pos[1] = car_y


def try_start_mission():
    """Called when player presses M."""
    global mission_state, current_mission_idx, missions_completed

    if missions_completed >= 3:
        return

    sx, sy, _, _ = interactive_zones["safe_house"]
    px, py = _player_world_pos()

    if not _near(px, py, sx, sy, MISSION_TRIGGER_RADIUS):
        return   # not close enough to safe house

    if mission_state in ("idle", "at_safehouse"):
        mission_state = "going_pickup"
        

def draw_mission_markers():
    """Draw a floating sphere at pickup and dropoff locations when active."""

    if mission_state in ("going_pickup", "carrying"):
        m = MISSION_DEFS[current_mission_idx]

        if mission_state == "going_pickup":
            px, py = m["pickup"]
            glPushMatrix()
            glColor3f(0.15, 0.55, 1.0)
            glTranslatef(px, py, 60)
            glutSolidSphere(14, 12, 8)
            glPopMatrix()
            glPushMatrix()
            glColor3f(0.15, 0.55, 1.0)
            glTranslatef(px, py, 2)
            gluCylinder(gluNewQuadric(), 2, 2, 58, 8, 2)
            glPopMatrix()

        dx, dy = m["dropoff"]
        glPushMatrix()
        glColor3f(0.15, 0.55, 1.0)
        glTranslatef(dx, dy, 60)
        glutSolidSphere(14, 12, 8)
        glPopMatrix()
        glPushMatrix()
        glColor3f(0.15, 0.55, 1.0)
        glTranslatef(dx, dy, 2)
        gluCylinder(gluNewQuadric(), 2, 2, 58, 8, 2)
        glPopMatrix()

    # final mission — bomb pickup, independent of the drug mission's state
    if final_mission_state == "get_bomb":
        glPushMatrix()
        glColor3f(0.9, 0.2, 0.9)
        glTranslatef(BOMB_PICKUP_POS[0], BOMB_PICKUP_POS[1], 60)
        glutSolidSphere(14, 12, 8)
        glPopMatrix()
        glPushMatrix()
        glColor3f(0.9, 0.2, 0.9)
        glTranslatef(BOMB_PICKUP_POS[0], BOMB_PICKUP_POS[1], 2)
        gluCylinder(gluNewQuadric(), 2, 2, 58, 8, 2)
        glPopMatrix()


def show_mission_hud():
    if mission_hint:
        # top center
        tx = screen_width // 2 - len(mission_hint) * 5
        draw_text(tx, screen_height - 36, mission_hint)

    # right side panel — mission progress
    rx = screen_width - 220
    draw_text(rx, screen_height - 30,  "=== MISSIONS ===")
    for i in range(3):
        if i < missions_completed:
            label = "Mission {}:  DONE".format(i + 1)
        elif i == current_mission_idx and mission_state not in ("idle", "done"):
            label = "Mission {}:  IN PROGRESS".format(i + 1)
        else:
            label = "Mission {}:  Pending".format(i + 1)
        draw_text(rx, screen_height - 55 - i * 25, label)

    if drug_picked_up:
        draw_text(screen_width // 2 - 60, screen_height - 65, "[CARRYING PACKAGE]")
        
    

def _random_npc_color():
    # pick hue from safe zones — anything except reds (0-30° and 330-360°)
    # green=90, cyan=180, blue=210, purple=270, yellow=60
    safe_hues = [50, 60, 90, 140, 170, 180, 200, 210, 240, 260, 270, 290, 310]
    h = random.choice(safe_hues) / 360.0
    s = random.uniform(0.55, 1.0)
    v = random.uniform(0.55, 1.0)

    # simple HSV -> RGB
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i = i % 6
    r, g, b = [
        (v, t, p), (q, v, p), (p, v, t),
        (p, q, v), (t, p, v), (v, p, q)
    ][i]

    dark = (r * 0.55, g * 0.55, b * 0.55)
    return (r, g, b), dark


def _make_npc_car():
    road_coords = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    if random.choice([True, False]):
        x = float(random.choice(road_coords))
        y = float(random.randint(-MAP_SIZE + 50, MAP_SIZE - 50))
    else:
        x = float(random.randint(-MAP_SIZE + 50, MAP_SIZE - 50))
        y = float(random.choice(road_coords))
    angle = float(random.choice([0, 90, 180, 270]))
    color, color_dark = _random_npc_color()
    return {
        "x": x, "y": y, "angle": angle,
        "speed": NPC_CAR_SPEED,
        "stuck_timer": 0.0,
        "turn_dir": random.choice([-1, 1]),
        "color": color,
        "color_dark": color_dark,
    }

npc_cars = [_make_npc_car() for _ in range(NPC_CAR_COUNT)]

def draw_npc_car(npc):
    """Draw one NPC car at its position using the same geometry as draw_car(),
    but coloured blue.  The steering-wheel / first-person cabin bits are skipped."""
    glPushMatrix()
    glTranslatef(npc["x"], npc["y"], 0)
    glRotatef(npc["angle"], 0, 0, 1)

    # --- body ---
    glColor3f(*npc["color"])
    draw_car_body()

    # hood
    glPushMatrix()
    glColor3f(*npc["color"])
    glTranslatef(0, 20, 10)
    glRotatef(-7, 1, 0, 0)
    glScalef(30, 25, 3)
    glutSolidCube(1)
    glPopMatrix()

    # cabin
    glPushMatrix()
    glColor3f(*npc["color_dark"])
    glTranslatef(0, -6, 16)
    glScalef(25, 27, 10)
    glutSolidCube(1)
    glPopMatrix()

    # windshield
    glPushMatrix()
    glColor3f(0.18, 0.55, 0.75)
    glTranslatef(0, 7.8, 20)
    glRotatef(28, 1, 0, 0)
    glScalef(22, 0.5, 7)
    glutSolidCube(1)
    glPopMatrix()

    # roof  (use darker accent colour)
    glPushMatrix()
    glColor3f(*npc["color_dark"])
    glTranslatef(0, -7, 23)
    glScalef(19, 14, 2)
    glutSolidCube(1)
    glPopMatrix()

    # rear glass
    glPushMatrix()
    glColor3f(*npc["color_dark"])
    glTranslatef(0, -18, 19)
    glRotatef(-28, 1, 0, 0)
    glScalef(20, 3, 8)
    glutSolidCube(1)
    glPopMatrix()

    # wheels and rims  (identical to player car)
    q = gluNewQuadric()
    for wx in (-18, 18):
        for wy in (-20, 20):
            glPushMatrix()
            glColor3f(0.03, 0.03, 0.03)
            glTranslatef(wx, wy, 6)
            glRotatef(90, 0, 1, 0)
            gluCylinder(q, 6, 6, 3, 16, 3)
            glPopMatrix()

            glPushMatrix()
            glColor3f(0.7, 0.7, 0.72)
            glTranslatef(wx * (18.2 / 18), wy, 6)
            glRotatef(90, 0, 1, 0)
            gluDisk(gluNewQuadric(), 0, 3.5, 12, 1)
            glPopMatrix()

    # headlights
    for lx in (-10, 10):
        glPushMatrix()
        glColor3f(1.0, 0.95, 0.75)
        glTranslatef(lx, 32, 8)
        glScalef(8, 2, 3)
        glutSolidCube(1)
        glPopMatrix()

    # tail lights
    for lx in (-10, 10):
        draw_cube(lx, -30.3, 8, 8 + 1.5, 2, 3 + 1.5, (0.03, 0.03, 0.03))
        draw_cube(lx, -30.6, 8, 8, 2, 3, (1.0, 0.02, 0.02))

    # side skirts
    for sx in (-20, 20):
        glPushMatrix()
        glColor3f(0.04, 0.04, 0.05)
        glTranslatef(sx, -1, 4)
        glScalef(2, 45, 3)
        glutSolidCube(1)
        glPopMatrix()

    # spoiler stands
    for sx in (-10, 10):
        glPushMatrix()
        glColor3f(*npc["color_dark"])
        glTranslatef(sx, -27, 15)
        glScalef(2, 2, 9)
        glutSolidCube(1)
        glPopMatrix()

    # spoiler wing
    glPushMatrix()
    glColor3f(*npc["color_dark"])
    glTranslatef(0, -28, 19)
    glScalef(28, 5, 2)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

def update_npc_cars(delta_time):
    ROAD_COORDS = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    SNAP_THRESHOLD = 8   # how close to a road center before we allow a turn

    for npc in npc_cars:
        angle_rad = math.radians(npc["angle"])
        fx = -math.sin(angle_rad)
        fy =  math.cos(angle_rad)

        new_x = npc["x"] + fx * npc["speed"]
        new_y = npc["y"] + fy * npc["speed"]

        limit = MAP_SIZE - 50
        blocked = (
            abs(new_x) > limit or
            abs(new_y) > limit or
            is_colliding(new_x, new_y, CAR_RADIUS)
        )

        if blocked:
            npc["stuck_timer"] += delta_time
            if npc["stuck_timer"] >= 0.5:
                npc["stuck_timer"] = 0.0
                # reverse or turn 90 degrees away
                npc["angle"] = (npc["angle"] + random.choice([90, 180, 270])) % 360
                # snap back to nearest road so it doesn't drift into a building
                nearest_rx = min(ROAD_COORDS, key=lambda r: abs(r - npc["x"]))
                nearest_ry = min(ROAD_COORDS, key=lambda r: abs(r - npc["y"]))
                a = npc["angle"] % 360
                if a in (0, 180):      # moving along Y axis — snap X to road
                    npc["x"] = float(nearest_rx)
                else:                  # moving along X axis — snap Y to road
                    npc["y"] = float(nearest_ry)
        else:
            npc["stuck_timer"] = 0.0
            npc["x"] = new_x
            npc["y"] = new_y

            # at an intersection, randomly decide to turn or go straight
            a = npc["angle"] % 360
            if a in (0, 180):          # travelling along Y — check if on an X road line
                on_x_road = any(abs(npc["x"] - rx) < SNAP_THRESHOLD for rx in ROAD_COORDS)
                on_y_road = any(abs(npc["y"] - ry) < SNAP_THRESHOLD for ry in ROAD_COORDS)
                if on_x_road and on_y_road and random.random() < 0.012:
                    npc["x"] = float(min(ROAD_COORDS, key=lambda r: abs(r - npc["x"])))
                    npc["angle"] = float(random.choice([90, 270]))
            else:                      # travelling along X — check if on a Y road line
                on_x_road = any(abs(npc["x"] - rx) < SNAP_THRESHOLD for rx in ROAD_COORDS)
                on_y_road = any(abs(npc["y"] - ry) < SNAP_THRESHOLD for ry in ROAD_COORDS)
                if on_x_road and on_y_road and random.random() < 0.012:
                    npc["y"] = float(min(ROAD_COORDS, key=lambda r: abs(r - npc["y"])))
                    npc["angle"] = float(random.choice([0, 180]))


def draw_npc_cars():
    for npc in npc_cars:
        draw_npc_car(npc)


def start_jump():
    global jumping
    global jump_velocity

    if player_in_car:
        return

    if game_over or game_paused:
        return

    if not jumping and player_pos[2] <= 0:
        jumping = True
        jump_velocity = JUMP_VELOCITY
        
def update_jump(delta_time):
    global jumping
    global jump_velocity

    if not jumping:
        return

    jump_velocity -= JUMP_GRAVITY * delta_time
    player_pos[2] += jump_velocity * delta_time

    if player_pos[2] <= 0:
        player_pos[2] = 0
        jump_velocity = 0
        jumping = False


def initialize():
    global screen_width, screen_height
    screen_width = glutGet(GLUT_SCREEN_WIDTH)
    screen_height = glutGet(GLUT_SCREEN_HEIGHT)
    if screen_width == 0:
        screen_width = 1280
    if screen_height == 0:
        screen_height = 720


def draw_car_body():
    glBegin(GL_QUADS)

    glVertex3f(-17, -30, 10); glVertex3f(17, -30, 10)
    glVertex3f(20, 25, 8); glVertex3f(-20, 25, 8)

    glVertex3f(-17, -30, 4); glVertex3f(-17, -30, 10)
    glVertex3f(-20, 25, 8); glVertex3f(-20, 25, 4)

    glVertex3f(17, -30, 4); glVertex3f(20, 25, 4)
    glVertex3f(20, 25, 8); glVertex3f(17, -30, 10)

    glVertex3f(-20, 25, 4); glVertex3f(20, 25, 4)
    glVertex3f(16, 34, 6); glVertex3f(-16, 34, 6)

    glVertex3f(-17, -30, 4); glVertex3f(17, -30, 4)
    glVertex3f(17, -30, 10); glVertex3f(-17, -30, 10)

    glEnd()


def draw_car():
    glPushMatrix()
    glTranslatef(car_x, car_y, car_z)
    glRotatef(car_angle, 0, 0, 1)

    glColor3f(0.82, 0.02, 0.07)
    draw_car_body()

    # hood
    glPushMatrix()
    glColor3f(0.95, 0.04, 0.08)
    glTranslatef(0, 20, 10)
    glRotatef(-7, 1, 0, 0)
    glScalef(30, 25, 3)
    glutSolidCube(1)
    glPopMatrix()
    
    if not (first_person and player_in_car):
        # cabin
        glPushMatrix()
        glColor3f(0.06, 0.08, 0.12)
        glTranslatef(0, -6, 16)
        glScalef(25, 27, 10)
        glutSolidCube(1)
        glPopMatrix()
        
        # windshield
        glPushMatrix()
        glColor3f(0.18, 0.55, 0.75)
        glTranslatef(0, 7.8, 20)
        glRotatef(28, 1, 0, 0)
        glScalef(22, 0.5, 7)
        glutSolidCube(1)
        glPopMatrix()


    # roof
    glPushMatrix()
    glColor3f(0.04, 0.05, 0.08)
    glTranslatef(0, -7, 23)
    glScalef(19, 14, 2)
    glutSolidCube(1)
    glPopMatrix()

    # rear glass
    glPushMatrix()
    glColor3f(0.15, 0.45, 0.65)
    glTranslatef(0, -18, 19)
    glRotatef(-28, 1, 0, 0)
    glScalef(20, 3, 8)
    glutSolidCube(1)
    glPopMatrix()

    # wheels and rims
    q = gluNewQuadric()
    for wx in (-18, 18):
        for wy in (-20, 20):
            glPushMatrix()
            glColor3f(0.03, 0.03, 0.03)
            glTranslatef(wx, wy, 6)
            glRotatef(90, 0, 1, 0)
            gluCylinder(q, 6, 6, 3, 16, 3)
            glPopMatrix()

            glPushMatrix()
            glColor3f(0.7, 0.7, 0.72)
            glTranslatef(wx * (18.2 / 18), wy, 6)
            glRotatef(90, 0, 1, 0)
            gluDisk(gluNewQuadric(), 0, 3.5, 12, 1)
            glPopMatrix()

    # headlights
    for lx in (-10, 10):
        glPushMatrix()
        glColor3f(1.0, 0.95, 0.75)
        glTranslatef(lx, 32, 8)
        glScalef(8, 2, 3)
        glutSolidCube(1)
        glPopMatrix()

    # tail lights
    
    for lx in (-10, 10):
        draw_cube(lx, -30.3, 8, 8 + 1.5, 2, 3 + 1.5, (0.03, 0.03, 0.03))
        draw_cube(lx, -30.6, 8, 8, 2, 3, (1.0, 0.02, 0.02))
    
    for lx in (-10, 10):
        glPushMatrix()
        glColor3f(1.0, 0.02, 0.02)
        glTranslatef(lx, -30.5, 8)
        glScalef(8, 2, 3)
        glutSolidCube(1)
        glPopMatrix()

    # side skirts
    for sx in (-20, 20):
        glPushMatrix()
        glColor3f(0.04, 0.04, 0.05)
        glTranslatef(sx, -1, 4)
        glScalef(2, 45, 3)
        glutSolidCube(1)
        glPopMatrix()

    # spoiler stands
    for sx in (-10, 10):
        glPushMatrix()
        glColor3f(0.04, 0.04, 0.05)
        glTranslatef(sx, -27, 15)
        glScalef(2, 2, 9)
        glutSolidCube(1)
        glPopMatrix()

    # spoiler wing
    glPushMatrix()
    glColor3f(0.04, 0.04, 0.05)
    glTranslatef(0, -28, 19)
    glScalef(28, 5, 2)
    glutSolidCube(1)
    glPopMatrix()
    
    if first_person and player_in_car:
        glDisable(GL_DEPTH_TEST)
        draw_steering_wheel(steering_wheel_angle)
        glEnable(GL_DEPTH_TEST)

    glPopMatrix()

def draw_steering_wheel(angle_deg):
    glPushMatrix()
    glTranslatef(0, 14, 13)          # wheel position, lower z = lower wheel
    glRotatef(angle_deg, 0, 1, 0)    # steering spin, about the forward axis

    glColor3f(0.05, 0.05, 0.05)
    radius = 6
    tube = 0.9
    segments = 20
    q = gluNewQuadric()

    # points around the rim, in the wheel's local xz plane
    points = []
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        points.append((math.sin(a) * radius, 0, math.cos(a) * radius))

    for i in range(segments):
        x1, y1, z1 = points[i]
        x2, y2, z2 = points[i + 1]
        dx, dz = x2 - x1, z2 - z1
        length = math.hypot(dx, dz)
        seg_angle = math.degrees(math.atan2(dx, dz))

        # short tube segment from point i to point i+1
        glPushMatrix()
        glTranslatef(x1, y1, z1)
        glRotatef(seg_angle, 0, 1, 0)
        gluCylinder(q, tube, tube, length, 10, 1)
        glPopMatrix()

        # sphere at the joint rounds the corner and hides the seam
        glPushMatrix()
        glTranslatef(x1, y1, z1)
        gluSphere(q, tube, 10, 10)
        glPopMatrix()

    # spokes
    for a_deg in (0, 120, 240):
        a = math.radians(a_deg)
        x = math.sin(a) * 3
        z = math.cos(a) * 3
        draw_cube(x, 0, z, 1, 1.5, 1, (0.05, 0.05, 0.05))

    # hub
    draw_cube(0, 0, 0, 3, 2, 3, (0.05, 0.05, 0.05))
    
    # hands gripping the rim, simple cylinders that spin with the wheel
    glColor3f(0.85, 0.65, 0.5)
    for side in (-1, 1):
        hx = side * radius * 0.85
        hz = -radius * 0.3
        glPushMatrix()
        glTranslatef(hx, -1, hz)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 1.8, 1.8, 5, 8, 2)
        glPopMatrix()
    
    glPopMatrix()

def update_car():
    global car_x, car_y, car_speed, car_angle,car_fuel
    global car_health, car_was_colliding_building

    if not player_in_car:
        return
    
    if cheat_mode:
        return 

    if b'w' in pressed_keys:
        car_speed = min(car_speed + car_acceleration, car_max_speed)
    elif b's' in pressed_keys:
        car_speed = max(car_speed - car_acceleration, -car_max_speed / 2)
    else:
        if car_speed > 0:
            car_speed = max(car_speed - car_friction, 0.0)
        elif car_speed < 0:
            car_speed = min(car_speed + car_friction, 0.0)

    if abs(car_speed) > 0.1:
        turn_dir = 1 if car_speed > 0 else -1
        if b'a' in pressed_keys:
            car_angle += car_turn_speed * turn_dir
        if b'd' in pressed_keys:
            car_angle -= car_turn_speed * turn_dir

    angle_rad = math.radians(car_angle)
    forward_x = -math.sin(angle_rad)
    forward_y = math.cos(angle_rad)

    new_cx = car_x + forward_x * car_speed
    new_cy = car_y + forward_y * car_speed

    limit = MAP_SIZE - 50

    # move on the x axis only if it stays in bounds and doesn't land inside a building
    test_cx = new_cx
    if abs(test_cx) > limit:
        test_cx = max(-limit, min(test_cx, limit))
        car_speed = 0
    if is_colliding(test_cx, car_y, CAR_RADIUS):
        car_speed = 0
    else:
        car_x = test_cx

    # move on the y axis the same way, so the car slides along a wall instead of clipping through it
    test_cy = new_cy
    if abs(test_cy) > limit:
        test_cy = max(-limit, min(test_cy, limit))
        car_speed = 0
    if is_colliding(car_x, test_cy, CAR_RADIUS):
        car_speed = 0
    else:
        car_y = test_cy

    # building collision damage -- only applied once per hit (on the frame the
    # car first touches a building), not continuously while pressed against it
    hit_building = (is_colliding_building(test_cx, car_y, CAR_RADIUS) or
                    is_colliding_building(car_x, test_cy, CAR_RADIUS))
    if hit_building and not car_was_colliding_building:
        car_health = max(0, car_health - CAR_HEALTH_DAMAGE)
    car_was_colliding_building = hit_building

    # fuel drain
    if abs(car_speed) > 0.5:
        car_fuel = max(0.0, car_fuel - CAR_FUEL_DRAIN)
    else:
        car_fuel = max(0.0, car_fuel - CAR_FUEL_IDLE)

    # out of fuel — car coasts to a stop
    if car_fuel <= 0:
        car_speed = max(car_speed - car_friction * 2, 0.0)

    # keep player glued to car
    if player_in_car:
        player_pos[0] = car_x
        player_pos[1] = car_y

def try_refuel():
    global car_fuel, player_money, fuel_hint

    if not player_in_car:
        fuel_hint = "Get in the car to refuel"
        return

    gx, gy, _, _ = interactive_zones["gas_station"]
    if math.hypot(car_x - gx, car_y - gy) > GAS_STATION_RADIUS:
        fuel_hint = "Drive closer to the pump"
        return

    if car_fuel >= CAR_FUEL_MAX:
        fuel_hint = "Tank is already full!"
        return

    if player_money < 10:
        fuel_hint = "Not enough money!  Need $10"
        return

    player_money -= 10
    car_fuel      = CAR_FUEL_MAX
    fuel_hint     = "Full tank!  Paid $10"
    

def update_fuel_hint():
    global fuel_hint
    if not player_in_car:
        fuel_hint = ""
        return
    gx, gy, _, _ = interactive_zones["gas_station"]
    if math.hypot(car_x - gx, car_y - gy) < GAS_STATION_RADIUS:
        if car_fuel < CAR_FUEL_MAX:
            needed = CAR_FUEL_MAX - car_fuel
            cost   = int(needed * FUEL_COST_PER_L)
            fuel_hint = "Press F to refuel  ($10 full tank)"
        else:
            fuel_hint = "Tank is full"
    else:
        if fuel_hint.startswith("Press F") or fuel_hint == "Tank is full":
            fuel_hint = ""

def shoot(is_cheat=False):
    angle = math.radians(player_angle)
    forward_x = -math.sin(angle)
    forward_y = math.cos(angle)

    gun_muzzle_distance = 15
    bullets.append({
        "x": player_pos[0] + forward_x * gun_muzzle_distance,
        "y": player_pos[1] + forward_y * gun_muzzle_distance,
        "z": 24,
        "dx": forward_x,
        "dy": forward_y,
        "cheat": is_cheat,
    })


def draw_bullets():
    glColor3f(1, 1, 0)
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet["x"], bullet["y"], bullet["z"])
        glScalef(bullet_size, bullet_size, bullet_size)
        glutSolidCube(1)
        glPopMatrix()


def update_bullets(delta_time):
    global bullets, enemies, game_over, game_score

    remaining = []
    for bullet in bullets:
        bullet["x"] += bullet["dx"] * bullet_speed * delta_time
        bullet["y"] += bullet["dy"] * bullet_speed * delta_time

        hit = False
        # iterate over a snapshot so removing during the loop is safe
        for enemy in list(enemies):
            dx = bullet["x"] - enemy["x"]
            dy = bullet["y"] - enemy["y"]
            if math.hypot(dx, dy) < enemy_body_radius + bullet_size:
                game_score += 1
                if enemy in enemies:
                    enemies.remove(enemy)
                hit = True
                break
            
        # check building cops
        if not hit:
            for cop in building_cops:
                if cop["dead"]:
                    continue
                if math.hypot(bullet["x"] - cop["x"],
                              bullet["y"] - cop["y"]) < 30 + bullet_size:
                    cop["hp"] -= bullet_damage
                    if cop["hp"] <= 0:
                        cop["dead"] = True
                        game_score += 1
                    hit = True
                    break

        if hit:
            continue

        # a bullet also stops if it hits a building instead of flying through it
        if is_colliding(bullet["x"], bullet["y"], bullet_size):
            continue

        

        remaining.append(bullet)
        
    bullets = remaining

    
def _draw_fuel_bar():
    """Draws a horizontal fuel bar in the bottom-right corner."""
    bar_w  = 160
    bar_h  = 16
    margin = 20
    bx     = screen_width - bar_w - margin
    by     = margin + 60   # sits just above the minimap bottom edge

    fill = (car_fuel / CAR_FUEL_MAX) * bar_w

    # choose colour: green → yellow → red as fuel drops
    if car_fuel > 50:
        rc, gc = 0.1, 0.85
    elif car_fuel > 25:
        rc, gc = 0.95, 0.75
    else:
        rc, gc = 0.95, 0.10

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # dark background
    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(bx,        by)
    glVertex2f(bx + bar_w, by)
    glVertex2f(bx + bar_w, by + bar_h)
    glVertex2f(bx,        by + bar_h)
    glEnd()

    # coloured fill
    glColor3f(rc, gc, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(bx,          by)
    glVertex2f(bx + fill,   by)
    glVertex2f(bx + fill,   by + bar_h)
    glVertex2f(bx,          by + bar_h)
    glEnd()

    # white border
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(bx,        by)
    glVertex2f(bx + bar_w, by)
    glVertex2f(bx + bar_w, by + bar_h)
    glVertex2f(bx,        by + bar_h)
    glEnd()
    glLineWidth(1)

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    # label drawn after matrix restore
    draw_text(bx, by + bar_h + 4, f"FUEL  {car_fuel:.0f}%")


def _draw_car_health_bar():
    """Draws a horizontal car-health bar just above the fuel bar."""
    bar_w  = 160
    bar_h  = 16
    margin = 20
    bx     = screen_width - bar_w - margin
    by     = margin + 60 + bar_h + 22   # stacked above the fuel bar

    fill = (car_health / CAR_HEALTH_MAX) * bar_w

    # choose colour: green -> yellow -> red as health drops
    if car_health > 50:
        rc, gc = 0.1, 0.85
    elif car_health > 25:
        rc, gc = 0.95, 0.75
    else:
        rc, gc = 0.95, 0.10

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # dark background
    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(bx,        by)
    glVertex2f(bx + bar_w, by)
    glVertex2f(bx + bar_w, by + bar_h)
    glVertex2f(bx,        by + bar_h)
    glEnd()

    # coloured fill
    glColor3f(rc, gc, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(bx,          by)
    glVertex2f(bx + fill,   by)
    glVertex2f(bx + fill,   by + bar_h)
    glVertex2f(bx,          by + bar_h)
    glEnd()

    # white border
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(bx,        by)
    glVertex2f(bx + bar_w, by)
    glVertex2f(bx + bar_w, by + bar_h)
    glVertex2f(bx,        by + bar_h)
    glEnd()
    glLineWidth(1)

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    # label drawn after matrix restore
    draw_text(bx, by + bar_h + 4, f"HEALTH  {car_health:.0f}%")

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    if screen_width == 0 or screen_height == 0:
        return
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_text_3d(x, y, z, text, font=GLUT_BITMAP_HELVETICA_18):
    # bitmap text anchored to a world position, e.g. signage on a building
    glColor3f(1, 1, 1)
    glRasterPos3f(x, y, z)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def show_status():
    px, py = _player_world_pos()
    draw_text(10, screen_height - 240, f"POS  x={px:.0f}  y={py:.0f}")
    draw_text(10, screen_height - 30,  f"Suspicion: {'|' * suspicion_level + '.' * (3 - suspicion_level)}  ({suspicion_level}/3)")
    draw_text(10, screen_height - 60,  f"Heat: {'WANTED' if heat_level else 'clean'}")
    draw_text(10, screen_height - 90,  f"Money: ${player_money}")

    if player_in_car:
        draw_text(10, screen_height - 120, f"IN CAR  speed={car_speed:.1f}")

        # fuel bar
        _draw_fuel_bar()
        # car health bar
        _draw_car_health_bar()

    if fuel_hint:
        draw_text(screen_width // 2 - len(fuel_hint) * 5,
                  screen_height - 65, fuel_hint)

    if cheat_mode:
        draw_text(screen_width // 2 - 55, screen_height - 90, "[CHEAT DRIVING]")
    if game_over:
        draw_text(screen_width // 2 - 80, screen_height // 2,
                  "GAME OVER - press R to restart")
    if game_paused:
        draw_text(screen_width // 2 - 40, screen_height // 2, "PAUSED")

    show_mission_hud()
    
    # BRAC University floating label (always visible near building)
    if final_mission_state != "locked":
        px2, py2 = _player_world_pos()
        if math.hypot(px2 - BRAC_POS[0], py2 - BRAC_POS[1]) < 400:
            draw_text(screen_width // 2 - 70, screen_height - 120,
                      "[ BRAC UNIVERSITY ]")
        if final_mission_state in ("drive_to_brac", "plant_bomb"):
            draw_text(screen_width // 2 - 100, screen_height - 145,
                      "Drive to the gate on the south side")

    # victory screen
    if final_mission_state == "victory":
        draw_text(screen_width // 2 - 140, screen_height // 2 + 40,
                  "MISSION COMPLETE!  You Win!")
        draw_text(screen_width // 2 - 120, screen_height // 2,
                  f"Final Score: {game_score}   Money: ${player_money}")
        draw_text(screen_width // 2 - 80, screen_height // 2 - 40,
                  "Press R to play again")


def draw_pause_menu():
    # semi-transparent full screen overlay with Restart / Resume / Exit buttons
    if screen_width == 0 or screen_height == 0:
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glDisable(GL_DEPTH_TEST)
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # dim the whole screen
    glColor4f(0, 0, 0, 0.65)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(screen_width, 0)
    glVertex2f(screen_width, screen_height)
    glVertex2f(0, screen_height)
    glEnd()

    # three stacked buttons, centered on screen
    btn_w, btn_h, gap = 220, 50, 20
    cx = screen_width / 2
    cy = screen_height / 2
    labels = ["Resume", "Start New Game", "Restart", "Shop", "Exit"]
    menu_buttons.clear()

    mid = (len(labels) - 1) / 2
    for i, label in enumerate(labels):
        top = cy + (mid - i) * (btn_h + gap)
        bottom = top - btn_h
        left = cx - btn_w / 2
        right = cx + btn_w / 2

        glColor4f(0.15, 0.15, 0.18, 0.9)
        glBegin(GL_QUADS)
        glVertex2f(left, bottom)
        glVertex2f(right, bottom)
        glVertex2f(right, top)
        glVertex2f(left, top)
        glEnd()

        menu_buttons[label] = (left, bottom, right, top)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    # labels drawn after popping, draw_text sets up its own ortho each call
    for label, (left, bottom, right, top) in menu_buttons.items():
        text_x = left + btn_w / 2 - len(label) * 5
        text_y = bottom + btn_h / 2 - 6
        draw_text(text_x, text_y, label)

def draw_shop_screen():
    # gray 800x600 panel, black border, centered -- one row per upgrade/action
    if screen_width == 0 or screen_height == 0:
        return

    cx = screen_width / 2
    cy = screen_height / 2
    half_w = SHOP_PANEL_W / 2
    half_h = SHOP_PANEL_H / 2

    row_w, row_h, row_gap = 700, 70, 14
    top_y = cy + half_h - 90
    left_x = cx - row_w / 2

    items = [
        ("refuel", "Refuel Car",
         "Tank is full" if car_fuel >= CAR_FUEL_MAX else f"{car_fuel:.0f}% fuel",
         "FULL" if car_fuel >= CAR_FUEL_MAX else f"${SHOP_REFUEL_PRICE}"),
        ("repair", "Repair Vehicle",
         "Car is undamaged" if car_health >= CAR_HEALTH_MAX else f"{car_health:.0f}% health",
         "FULL" if car_health >= CAR_HEALTH_MAX else f"${SHOP_REPAIR_PRICE}"),
        ("bullet", "Bullet Damage  (one-shot cops)",
         f"Level {bullet_damage_level}/{BULLET_DAMAGE_MAX_LEVEL}",
         "MAXED" if bullet_damage_level >= BULLET_DAMAGE_MAX_LEVEL
         else f"${BULLET_DAMAGE_PRICES[bullet_damage_level]}"),
        ("suspicion", "Reduce Suspicion",
         f"{suspicion_level}/3 stars  ({'WANTED' if heat_level else 'clean'})",
         f"${SUSPICION_CLEAR_PRICE}"),
        ("stamina", "Player Stamina  (run speed)",
         f"Level {stamina_level}/{STAMINA_MAX_LEVEL}",
         "MAXED" if stamina_level >= STAMINA_MAX_LEVEL
         else f"${STAMINA_PRICES[stamina_level]}"),
        ("carspeed", "Car Top Speed",
         f"Level {car_speed_level}/{CAR_SPEED_MAX_LEVEL}",
         "MAXED" if car_speed_level >= CAR_SPEED_MAX_LEVEL
         else f"${CAR_SPEED_PRICES[car_speed_level]}"),
    ]

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # dim the gameplay behind the shop
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.65)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(screen_width, 0)
    glVertex2f(screen_width, screen_height)
    glVertex2f(0, screen_height)
    glEnd()
    glDisable(GL_BLEND)

    # black border, slightly larger than the panel
    glColor3f(0, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(cx - half_w - SHOP_BORDER, cy - half_h - SHOP_BORDER)
    glVertex2f(cx + half_w + SHOP_BORDER, cy - half_h - SHOP_BORDER)
    glVertex2f(cx + half_w + SHOP_BORDER, cy + half_h + SHOP_BORDER)
    glVertex2f(cx - half_w - SHOP_BORDER, cy + half_h + SHOP_BORDER)
    glEnd()

    # gray 800x600 panel
    glColor3f(0.55, 0.55, 0.55)
    glBegin(GL_QUADS)
    glVertex2f(cx - half_w, cy - half_h)
    glVertex2f(cx + half_w, cy - half_h)
    glVertex2f(cx + half_w, cy + half_h)
    glVertex2f(cx - half_w, cy + half_h)
    glEnd()

    # one row per shop item
    shop_buttons.clear()
    for i, (item_id, _name, _status, _price) in enumerate(items):
        top = top_y - i * (row_h + row_gap)
        bottom = top - row_h

        glColor3f(0.33, 0.33, 0.37)
        glBegin(GL_QUADS)
        glVertex2f(left_x, bottom)
        glVertex2f(left_x + row_w, bottom)
        glVertex2f(left_x + row_w, top)
        glVertex2f(left_x, top)
        glEnd()

        glColor3f(0, 0, 0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(left_x, bottom)
        glVertex2f(left_x + row_w, bottom)
        glVertex2f(left_x + row_w, top)
        glVertex2f(left_x, top)
        glEnd()

        shop_buttons[item_id] = (left_x, bottom, left_x + row_w, top)

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    # text, drawn after popping -- draw_text sets up its own ortho each call
    draw_text(cx - 30, cy + half_h - 40, "SHOP")
    draw_text(cx + half_w - 150, cy + half_h - 40, f"Money: ${player_money}")

    for i, (item_id, name, status, price_text) in enumerate(items):
        top = top_y - i * (row_h + row_gap)
        bottom = top - row_h
        draw_text(left_x + 16, bottom + row_h - 22, name)
        draw_text(left_x + 16, bottom + 10, status)
        draw_text(left_x + row_w - 80, bottom + row_h / 2 - 6, price_text)

    if shop_message:
        draw_text(cx - len(shop_message) * 4, cy - half_h + 40, shop_message)
    draw_text(cx - 95, cy - half_h + 14, "Press ESC to go back")

def handle_shop_click(item_id):
    # runs when a shop row is clicked
    global player_money, shop_message, car_fuel
    global car_health
    global bullet_damage, bullet_damage_level
    global RUN_SPEED, stamina_level
    global car_max_speed, car_speed_level

    if item_id == "refuel":
        if car_fuel >= CAR_FUEL_MAX:
            shop_message = "Tank is already full!"
        elif player_money < SHOP_REFUEL_PRICE:
            shop_message = f"Not enough money! Need ${SHOP_REFUEL_PRICE}"
        else:
            player_money -= SHOP_REFUEL_PRICE
            car_fuel = CAR_FUEL_MAX
            shop_message = "Full tank!"

    elif item_id == "repair":
        if car_health >= CAR_HEALTH_MAX:
            shop_message = "Car is already undamaged!"
        elif player_money < SHOP_REPAIR_PRICE:
            shop_message = f"Not enough money! Need ${SHOP_REPAIR_PRICE}"
        else:
            player_money -= SHOP_REPAIR_PRICE
            car_health = CAR_HEALTH_MAX
            shop_message = "Vehicle repaired!"

    elif item_id == "bullet":
        if bullet_damage_level >= BULLET_DAMAGE_MAX_LEVEL:
            shop_message = "Bullet damage already maxed!"
        else:
            price = BULLET_DAMAGE_PRICES[bullet_damage_level]
            if player_money < price:
                shop_message = f"Not enough money! Need ${price}"
            else:
                player_money -= price
                bullet_damage_level += 1
                bullet_damage += 1
                shop_message = f"Bullet damage upgraded! (Lv {bullet_damage_level})"

    elif item_id == "suspicion":
        if suspicion_level <= 0 and heat_level <= 0:
            shop_message = "You're already clean!"
        elif player_money < SUSPICION_CLEAR_PRICE:
            shop_message = f"Not enough money! Need ${SUSPICION_CLEAR_PRICE}"
        else:
            player_money -= SUSPICION_CLEAR_PRICE
            _clear_heat()
            shop_message = "Suspicion cleared!"

    elif item_id == "stamina":
        if stamina_level >= STAMINA_MAX_LEVEL:
            shop_message = "Stamina already maxed!"
        else:
            price = STAMINA_PRICES[stamina_level]
            if player_money < price:
                shop_message = f"Not enough money! Need ${price}"
            else:
                player_money -= price
                stamina_level += 1
                RUN_SPEED += STAMINA_BOOST_PER_LEVEL
                shop_message = f"Stamina upgraded! (Lv {stamina_level})"

    elif item_id == "carspeed":
        if car_speed_level >= CAR_SPEED_MAX_LEVEL:
            shop_message = "Car speed already maxed!"
        else:
            price = CAR_SPEED_PRICES[car_speed_level]
            if player_money < price:
                shop_message = f"Not enough money! Need ${price}"
            else:
                player_money -= price
                car_speed_level += 1
                car_max_speed += CAR_SPEED_BOOST_PER_LEVEL
                shop_message = f"Car speed upgraded! (Lv {car_speed_level})"

def handle_menu_click(label):
    # runs when a pause-menu button is clicked
    global game_menu_open, shop_open
    if label == "Start New Game":
        RestartGame()
        game_menu_open = False
    elif label == "Restart":
        RestartGame()
        game_menu_open = False
    elif label == "Shop":
        shop_open = True
    elif label == "Resume":
        game_menu_open = False
    elif label == "Exit":
        glutLeaveMainLoop()

def _forward_from_angle(deg):
    rad = math.radians(deg)
    return -math.sin(rad), math.cos(rad)


def _camera_safe_distance(pivot_x, pivot_y, fx, fy, max_distance, radius=18):
    # walks backward from the pivot (player/car) along the camera's offset
    # direction and stops just before the camera would end up inside a
    # building, so the third-person camera never clips through walls
    step = 4
    distance = 0
    safe_distance = 0
    while distance < max_distance:
        distance += step
        test_x = pivot_x - fx * distance
        test_y = pivot_y - fy * distance
        if is_colliding(test_x, test_y, radius):
            break
        safe_distance = distance
    return safe_distance


def setupCamera():
    global camera_radius, camera_angle, camera_height

    if screen_height == 0:
        return

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, screen_width / screen_height, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        # first person works for both on-foot and in-car
        if player_in_car:
            cam_angle_rad = math.radians(car_angle)
            fx = -math.sin(cam_angle_rad)
            fy = math.cos(cam_angle_rad)

            eye_x = car_x + fx * 5
            eye_y = car_y + fy * 5
            eye_z = car_z + 22

            look_dir = car_angle
        else:
            fx, fy = _forward_from_angle(player_angle)
            eye_x = player_pos[0] + fx * 5
            eye_y = player_pos[1] + fy * 5
            eye_z = 32

            if cheat_mode and not gun_follow:
                look_dir = locked_camera_angle
            else:
                look_dir = player_angle

        lx, ly = _forward_from_angle(look_dir)
        gluLookAt(
            eye_x, eye_y, eye_z,
            eye_x + lx * 500, eye_y + ly * 500, eye_z,
            0, 0, 1,
        )

    else:
        # third person follows the car when in car, the player when on foot
        if player_in_car:
            pivot_x, pivot_y = car_x, car_y
            follow_angle = car_angle
        else:
            pivot_x, pivot_y = player_pos[0], player_pos[1]
            follow_angle = player_angle

        fx, fy = _forward_from_angle(follow_angle)

        tpp_distance = 80
        cam_radius = 20 if player_in_car else 16
        safe_distance = _camera_safe_distance(pivot_x, pivot_y, fx, fy, tpp_distance, radius=cam_radius)
        cam_x = pivot_x - fx * safe_distance
        cam_y = pivot_y - fy * safe_distance
        cam_z = 60

        gluLookAt(
            cam_x, cam_y, cam_z,
            pivot_x, pivot_y, 20,
            0, 0, 1,
        )

def draw_minimap():
    if screen_width==0 or screen_height==0:
        return

    if player_in_car:
        px,py=car_x,car_y
    else:
        px,py=player_pos[0],player_pos[1]

    map_size=220
    margin=20
    bottom_offset=60
    minimap_range=500

    glViewport(margin,margin+bottom_offset,map_size,map_size)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-minimap_range,minimap_range,-minimap_range,minimap_range,0.1,3000)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    gluLookAt(px,py,1200,px,py,0,0,1,0)

    # Background
    glDisable(GL_DEPTH_TEST)
    glColor3f(0.05,0.05,0.06)
    glBegin(GL_QUADS)
    glVertex3f(px-minimap_range,py-minimap_range,-5)
    glVertex3f(px+minimap_range,py-minimap_range,-5)
    glVertex3f(px+minimap_range,py+minimap_range,-5)
    glVertex3f(px-minimap_range,py+minimap_range,-5)
    glEnd()
    glEnable(GL_DEPTH_TEST)

    draw_ground()

    # Road lines
    glDisable(GL_DEPTH_TEST)
    glColor3f(1,0.9,0.1)
    for road in range(-MAP_SIZE,MAP_SIZE+1,BLOCK_SPACING):
        for p in range(-MAP_SIZE,MAP_SIZE,80):
            glBegin(GL_QUADS)
            glVertex3f(road-3,p,15);   glVertex3f(road+3,p,15)
            glVertex3f(road+3,p+38,15);glVertex3f(road-3,p+38,15)
            glVertex3f(p,road-3,15);   glVertex3f(p+38,road-3,15)
            glVertex3f(p+38,road+3,15);glVertex3f(p,road+3,15)
            glEnd()
    glEnable(GL_DEPTH_TEST)

    # Buildings
    for bx,by,bw,bh,r,g,b,h in buildings:
        glColor3f(r,g,b)
        glBegin(GL_QUADS)
        glVertex3f(bx-bw/2,by-bh/2,5);glVertex3f(bx+bw/2,by-bh/2,5)
        glVertex3f(bx+bw/2,by+bh/2,5);glVertex3f(bx-bw/2,by+bh/2,5)
        glEnd()

    # --- all blips drawn in world space, depth test off so they always show ---
    glDisable(GL_DEPTH_TEST)

    # collect every blip we want to draw: (wx, wy, r, g, b, size)
    blips = []

    gx,gy,gw,gh = interactive_zones["gas_station"]
    blips.append((gx, gy, 0.65, 0.10, 0.90, 22))   # purple — gas station

    sx,sy,sw,sh = interactive_zones["safe_house"]
    blips.append((sx, sy, 0.1, 1.0, 0.25, 22))     # green — safe house
    
    if police_active:
        blips.append((police_x, police_y, 0.9, 0.9, 1.0, 18))   # white-blue — police
    
    if mission_state == "going_pickup":
        pick_x,pick_y = MISSION_DEFS[current_mission_idx]["pickup"]
        blips.append((pick_x, pick_y, 0.15, 0.55, 1.0, 18))   # BLUE — pickup

    if mission_state == "carrying":
        drop_x,drop_y = MISSION_DEFS[current_mission_idx]["dropoff"]
        blips.append((drop_x, drop_y, 0.15, 0.55, 1.0, 18))    # blue — dropoff
        
    # bomb pickup blip — RED
    if final_mission_state == "get_bomb":
        blips.append((BOMB_PICKUP_POS[0], BOMB_PICKUP_POS[1], 1.0, 0.05, 0.05, 18))

    # BRAC university blip — RED
    if final_mission_state in ("drive_to_brac", "plant_bomb", "cops_incoming", "fight_out", "escape"):
        blips.append((BRAC_POS[0], BRAC_POS[1], 1.0, 0.05, 0.05, 22))

    # final police car blips
    for pc in final_police_cars:
        blips.append((pc["x"], pc["y"], 0.9, 0.9, 1.0, 16))

    for (wx, wy, r, g, b, size) in blips:
        rel_x = wx - px
        rel_y = wy - py

        # check if inside minimap view range
        if abs(rel_x) <= minimap_range and abs(rel_y) <= minimap_range:
            # draw square blip at world position
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            glVertex3f(wx-size, wy-size, 20)
            glVertex3f(wx+size, wy-size, 20)
            glVertex3f(wx+size, wy+size, 20)
            glVertex3f(wx-size, wy+size, 20)
            glEnd()
        else:
            # clamp to edge and draw a triangle arrow pointing inward
            edge = minimap_range * 0.88
            clamped_x = px + max(-edge, min(rel_x, edge))
            clamped_y = py + max(-edge, min(rel_y, edge))

            # direction from clamped edge pos toward the actual target
            dx = wx - clamped_x
            dy = wy - clamped_y
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            ndx = dx / length
            ndy = dy / length

            # perpendicular for triangle base
            px2 = -ndy
            py2 =  ndx

            tip_size  = size * 1.2
            base_size = size * 0.8

            glColor3f(r, g, b)
            glBegin(GL_TRIANGLES)
            glVertex3f(clamped_x + ndx * tip_size,
                       clamped_y + ndy * tip_size, 20)
            glVertex3f(clamped_x - ndx * base_size + px2 * base_size,
                       clamped_y - ndy * base_size + py2 * base_size, 20)
            glVertex3f(clamped_x - ndx * base_size - px2 * base_size,
                       clamped_y - ndy * base_size - py2 * base_size, 20)
            glEnd()

    glEnable(GL_DEPTH_TEST)

    # Car/player marker — drawn last so it's always on top
    if player_in_car:
        glPushMatrix()
        glTranslatef(px,py,20)
        glRotatef(car_angle,0,0,1)
        glColor3f(1,0,0)
        glBegin(GL_QUADS)
        glVertex3f(-10,-16,0);glVertex3f(10,-16,0)
        glVertex3f(10,16,0);  glVertex3f(-10,16,0)
        glEnd()
        glColor3f(0.1,0.1,0.1)
        glBegin(GL_QUADS)
        glVertex3f(-7,-5,1);glVertex3f(7,-5,1)
        glVertex3f(7,7,1);  glVertex3f(-7,7,1)
        glEnd()
        glPopMatrix()
    else:
        glPushMatrix()
        glTranslatef(px,py,20)
        glRotatef(player_angle,0,0,1)
        glColor3f(0,0.8,1)
        glBegin(GL_TRIANGLES)
        glVertex3f(0,25,0)
        glVertex3f(-17,-16,0)
        glVertex3f(17,-16,0)
        glEnd()
        glPopMatrix()

    # Restore
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glViewport(0,0,screen_width,screen_height)

    # Border
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0,screen_width,0,screen_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    x1=margin
    y1=margin+bottom_offset
    x2=margin+map_size
    y2=margin+bottom_offset+map_size

    glColor3f(0,0,0)
    glLineWidth(8)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x1-4,y1-4);glVertex2f(x2+4,y1-4)
    glVertex2f(x2+4,y2+4);glVertex2f(x1-4,y2+4)
    glEnd()

    glColor3f(1,1,1)
    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x1,y1);glVertex2f(x2,y1)
    glVertex2f(x2,y2);glVertex2f(x1,y2)
    glEnd()

    glLineWidth(1)
    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def showScreen():
    glClearColor(0.22,0.42,0.72,1.0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Main view
    if screen_width>0 and screen_height>0:
        glViewport(0,0,screen_width,screen_height)

    setupCamera()
    drawWORLD()
    
    draw_street_characters()

    if not player_in_car:
        draw_player(player_pos,player_angle,first_person,game_over)

    draw_car()
    draw_k9_zones()
    draw_police_car()
    draw_final_police_cars()
    draw_building_cops()
    draw_npc_cars()   
    draw_bullets()
    draw_mission_markers()
    
    if game_menu_open:
        if shop_open:
            draw_shop_screen()
        else:
            draw_pause_menu()

    # Minimap
    draw_minimap()

    # HUD
    glViewport(0,0,screen_width,screen_height)
    show_status()

    glutSwapBuffers()



def animate():
    global last_time, player_angle, cheat_shoot_timer, steering_wheel_angle

    current_time = time.perf_counter()
    delta_time = min(current_time - last_time, 0.1)
    last_time = current_time
    
    update_jump(delta_time)

    update_car()
    update_npc_cars(delta_time)
    update_heat(delta_time)
    update_mission() 
    update_final_mission(delta_time)
    update_fuel_hint() 
    if game_over or game_paused or game_menu_open:
        glutPostRedisplay()
        return
    
    update_street_characters(delta_time)

    # on-foot movement, uses pressed_keys so w+a, w+d etc. all work together
    if not player_in_car:
        moving = b'w' in pressed_keys or b's' in pressed_keys

        if b'a' in pressed_keys:
            player_angle = (player_angle + rotation_speed * delta_time * 60) % 360
        if b'd' in pressed_keys:
            player_angle = (player_angle - rotation_speed * delta_time * 60) % 360

        if moving:
            fx, fy = _forward_from_angle(player_angle)
            step = player_speed * delta_time * 60

            new_x = player_pos[0]
            new_y = player_pos[1]

            if b'w' in pressed_keys:
                new_x += fx * step
                new_y += fy * step
            if b's' in pressed_keys:
                new_x -= fx * step
                new_y -= fy * step

            # move on each axis separately so the player slides along a wall instead of clipping through it
            if abs(new_x) < PLAYER_LIMIT and not is_colliding(new_x, player_pos[1], PLAYER_RADIUS):
                player_pos[0] = new_x
            if abs(new_y) < PLAYER_LIMIT and not is_colliding(player_pos[0], new_y, PLAYER_RADIUS):
                player_pos[1] = new_y
                
    # steering wheel spins toward a/d, springs back to center when released
    if b'd' in pressed_keys:
        steering_wheel_angle = min(steering_wheel_angle + STEER_STEP, STEER_MAX)
    elif b'a' in pressed_keys:
        steering_wheel_angle = max(steering_wheel_angle - STEER_STEP, -STEER_MAX)
    else:
        steering_wheel_angle *= 0.85

    if cheat_mode:
        update_cheat_drive()

    update_bullets(delta_time)

    # automatic spray fire: while spray_mode is toggled on and the left
    # mouse button is held down, keep shooting at a fixed rate
    global spray_fire_timer
    if spray_mode and mouse_fire_held and not game_over and not game_paused:
        spray_fire_timer += delta_time
        fire_interval = 1.0 / spray_fire_rate
        while spray_fire_timer >= fire_interval:
            spray_fire_timer -= fire_interval
            shoot()

    glutPostRedisplay()
    
def _make_street_character():
    road_coords = list(range(-MAP_SIZE, MAP_SIZE + 1, BLOCK_SPACING))
    # ACTUAL SIDEWALK POSITION
    SIDEWALK_CENTER = ROAD_WIDTH / 2 + SIDEWALK_WIDTH / 2

    # Keep a small safety distance from road edges
    STREET_MARGIN = 8

    SIDEWALK_MIN = SIDEWALK_CENTER - SIDEWALK_WIDTH / 2 + STREET_MARGIN
    SIDEWALK_MAX = SIDEWALK_CENTER + SIDEWALK_WIDTH / 2 - STREET_MARGIN

    # Choose vertical or horizontal sidewalk

    vertical = random.choice([True, False])

    # Choose one road line
    road_index = random.randint(0, len(road_coords) - 1)
    road_value = float(road_coords[road_index])

    # Choose which side of the road
    side = random.choice([-1, 1])

    sidewalk_offset = random.uniform(
        SIDEWALK_MIN,
        SIDEWALK_MAX
    )

    if vertical:

        # Character walks along a vertical sidewalk
        x = road_value + side * sidewalk_offset

        # Need another road above/below to define the block
        if road_index == 0:
            block_low = road_coords[0]
            block_high = road_coords[1]
        elif road_index == len(road_coords) - 1:
            block_low = road_coords[-2]
            block_high = road_coords[-1]
        else:
            if random.choice([True, False]):
                block_low = road_coords[road_index - 1]
                block_high = road_coords[road_index]
            else:
                block_low = road_coords[road_index]
                block_high = road_coords[road_index + 1]

        # Walk only between the two road edges.
        y_min = block_low + ROAD_WIDTH / 2 + STREET_MARGIN
        y_max = block_high - ROAD_WIDTH / 2 - STREET_MARGIN

        y = random.uniform(y_min, y_max)

        # Vertical movement
        direction = random.choice([-1, 1])

    else:

        # Character walks along a horizontal sidewalk
        y = road_value + side * sidewalk_offset

        # Need another road left/right to define the block
        if road_index == 0:
            block_low = road_coords[0]
            block_high = road_coords[1]
        elif road_index == len(road_coords) - 1:
            block_low = road_coords[-2]
            block_high = road_coords[-1]
        else:
            if random.choice([True, False]):
                block_low = road_coords[road_index - 1]
                block_high = road_coords[road_index]
            else:
                block_low = road_coords[road_index]
                block_high = road_coords[road_index + 1]

        # Walk only between the two road edges.
        x_min = block_low + ROAD_WIDTH / 2 + STREET_MARGIN
        x_max = block_high - ROAD_WIDTH / 2 - STREET_MARGIN

        x = random.uniform(x_min, x_max)

        # Horizontal movement
        direction = random.choice([-1, 1])

    angle = 0

    if vertical:
        if direction == 1:
            angle = 0
        else:
            angle = 180
    else:
        if direction == 1:
            angle = 90
        else:
            angle = 270

    shirt_colors = [
        (0.10, 0.35, 0.75),
        (0.15, 0.55, 0.20),
        (0.65, 0.20, 0.15),
        (0.55, 0.20, 0.65),
        (0.80, 0.55, 0.10),
        (0.25, 0.25, 0.25)
    ]

    pants_colors = [
        (0.05, 0.05, 0.12),
        (0.10, 0.15, 0.30),
        (0.20, 0.20, 0.20),
        (0.35, 0.20, 0.10)
    ]

    skin_colors = [
        (1.0, 0.75, 0.55),
        (0.85, 0.60, 0.40),
        (0.65, 0.42, 0.25)
    ]

    return {
        "x": x,
        "y": y,
        "angle": angle,

        "shirt": random.choice(shirt_colors),
        "pants": random.choice(pants_colors),
        "skin": random.choice(skin_colors),

        # Movement information
        "vertical": vertical,
        "direction": direction,

        # Much slower than player's 8.0 walking speed
        "speed": 0.7,

        # Limits of the sidewalk segment
        "min_pos": (
            y_min if vertical else x_min
        ),

        "max_pos": (
            y_max if vertical else x_max
        )
    }
    
def draw_street_character(character):
    x = character["x"]
    y = character["y"]

    glPushMatrix()

    glTranslatef(x, y, 0)
    glRotatef(character["angle"], 0, 0, 1)
    glScalef(0.15, 0.15, 0.15)

    # BODY
    glColor3f(
        character["shirt"][0],
        character["shirt"][1],
        character["shirt"][2]
    )

    glPushMatrix()
    glTranslatef(0, 0, 140)
    glScalef(70, 40, 110)
    glutSolidCube(1)
    glPopMatrix()

    # HEAD
    glColor3f(
        character["skin"][0],
        character["skin"][1],
        character["skin"][2]
    )

    glPushMatrix()
    glTranslatef(0, 0, 225)
    glScalef(65, 65, 65)
    glutSolidCube(1)
    glPopMatrix()

    # LEFT LEG
    glColor3f(
        character["pants"][0],
        character["pants"][1],
        character["pants"][2]
    )

    glPushMatrix()
    glTranslatef(-22, 0, 45)
    glScalef(22, 32, 80)
    glutSolidCube(1)
    glPopMatrix()

    # RIGHT LEG
    glPushMatrix()
    glTranslatef(22, 0, 45)
    glScalef(22, 32, 80)
    glutSolidCube(1)
    glPopMatrix()

    # LEFT ARM
    glColor3f(
        character["skin"][0],
        character["skin"][1],
        character["skin"][2]
    )

    glPushMatrix()
    glTranslatef(-50, 0, 140)
    glScalef(20, 30, 75)
    glutSolidCube(1)
    glPopMatrix()

    # RIGHT ARM
    glPushMatrix()
    glTranslatef(50, 0, 140)
    glScalef(20, 30, 75)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()


def draw_street_characters():
    for character in street_characters:
        draw_street_character(character)
        
def update_street_characters(delta_time):
    for character in street_characters:
        # Move along the sidewalk

        step = character["speed"] * delta_time * 60

        if character["vertical"]:

            character["y"] += character["direction"] * step

            # Reached end of sidewalk segment
            if character["y"] >= character["max_pos"]:
                character["y"] = character["max_pos"]
                character["direction"] = -1
                character["angle"] = 180

            elif character["y"] <= character["min_pos"]:
                character["y"] = character["min_pos"]
                character["direction"] = 1
                character["angle"] = 0

        else:

            character["x"] += character["direction"] * step

            # Reached end of sidewalk segment
            if character["x"] >= character["max_pos"]:
                character["x"] = character["max_pos"]
                character["direction"] = -1
                character["angle"] = 270

            elif character["x"] <= character["min_pos"]:
                character["x"] = character["min_pos"]
                character["direction"] = 1
                character["angle"] = 90
               
street_characters = [
    _make_street_character()
    for _ in range(STREET_CHARACTER_COUNT)
]

def RestartGame():
    global player_pos, player_angle
    global game_over, game_score, bullets, enemies
    global first_person, camera_height, camera_angle
    global cheat_mode, game_paused, gun_follow, locked_camera_angle
    global player_life_remaining, player_in_car
    global car_x, car_y, car_z, car_speed, car_angle
    global cheat_shoot_timer
    global npc_cars
    global street_characters
    global mission_state, current_mission_idx, missions_completed, drug_picked_up, mission_hint, player_money
    global suspicion_level, heat_level, police_active, k9_cooldown
    global car_fuel, fuel_hint
    global car_health, car_was_colliding_building
    global final_mission_state, bomb_picked_up, bomb_planted, bomb_cooldown_timer
    global building_cops, building_cops_spawned, final_police_cars
    global shop_open, shop_message, bullet_damage, bullet_damage_level
    global RUN_SPEED, stamina_level, car_max_speed, car_speed_level

    npc_cars = [_make_npc_car() for _ in range(NPC_CAR_COUNT)]
    
    street_characters = [
        _make_street_character()
        for _ in range(STREET_CHARACTER_COUNT)
    ]

    player_pos = [200, 100, 0]
    player_angle = 0
    player_life_remaining = 5
    game_over = False
    game_score = 0
    bullets.clear()
    enemies.clear()
    pressed_keys.clear()
    first_person = False
    camera_angle = 0
    camera_height = 85
    
    #car fuel
    
    car_fuel  = CAR_FUEL_MAX
    fuel_hint = ""

    #car health
    car_health                 = CAR_HEALTH_MAX
    car_was_colliding_building = False

    #shop / upgrades
    shop_open           = False
    shop_message        = ""
    bullet_damage       = BULLET_DAMAGE_BASE
    bullet_damage_level = 0
    RUN_SPEED           = RUN_SPEED_BASE
    stamina_level       = 0
    car_max_speed       = CAR_MAX_SPEED_BASE
    car_speed_level     = 0
    
    #CHEAT
    cheat_mode      = False
    cheat_target    = None
    cheat_waypoints = []
    
    player_in_car = False
    car_x, car_y, car_z = 160, 150, 0
    car_angle = 0
    car_speed = 0
    
    #Mission Related
    mission_state       = "idle"
    current_mission_idx = 0
    missions_completed  = 0
    drug_picked_up      = False
    mission_hint        = ""
    player_money = 25
    suspicion_level = 0
    heat_level      = 0
    police_active   = False
    k9_cooldown     = {}
    
    #FINAL MISSION
    final_mission_state   = "locked"
    bomb_picked_up        = False
    bomb_planted          = False
    bomb_cooldown_timer   = 0.0
    building_cops         = []
    building_cops_spawned = False
    final_police_cars     = []


def keyboardListener(key, x, y):
    global player_pos, player_angle
    global player_speed
    global jumping, jump_velocity
    global game_over, game_score, bullets, enemies
    global first_person, camera_height, camera_angle
    global cheat_mode, game_paused, gun_follow, locked_camera_angle
    global player_life_remaining, player_in_car
    global car_x, car_y, car_z, car_speed, car_angle
    global cheat_shoot_timer, game_menu_open
    global final_mission_state
    global mission_state, current_mission_idx, missions_completed
    global drug_picked_up, player_money
   

    nk = key.lower() if isinstance(key, bytes) else key
    
    # esc toggles the pause menu
    # esc: shop -> pause menu -> resume game (and open pause menu from gameplay)
    if key == b'\x1b':
        global game_menu_open, shop_open
        if shop_open:
            shop_open = False
        elif game_menu_open:
            game_menu_open = False
        else:
            game_menu_open = True
        return

    # block all other input while the menu (or the shop) is open
    if game_menu_open:
        return

    # restart, always available
    if nk in (b'r',):
        player_pos = [200, 100, 0]
        jumping = False
        jump_velocity = 0.0
        player_angle = 0
        player_life_remaining = 5
        game_over = False
        game_score = 0
        bullets.clear()
        enemies.clear()
        pressed_keys.clear()
        first_person = False
        camera_angle = 0
        camera_height = 85
        cheat_mode = False
        gun_follow = True
        locked_camera_angle = 0
        cheat_shoot_timer = 0
        player_in_car = False
        car_x, car_y, car_z = 160, 150, 0
        car_angle = 0
        car_speed = 0
        RestartGame()
        return
    
    # cheat toggle
    if nk == b'c':
        if player_in_car and mission_state in ("going_pickup", "carrying"):
            cheat_mode = not cheat_mode
            if cheat_mode:
                cheat_target    = "pickup" if mission_state == "going_pickup" else "dropoff"
                m               = MISSION_DEFS[current_mission_idx]
                tx, ty          = m["pickup"] if cheat_target == "pickup" else m["dropoff"]
                cheat_waypoints = _plan_cheat_route(tx, ty)
            else:
                cheat_waypoints = []
                car_speed       = 0
        return

    # gun-follow toggle, cheat + first person only
    if nk == b'v':
        if cheat_mode and first_person:
            if gun_follow:
                locked_camera_angle = player_angle
                gun_follow = False
            else:
                gun_follow = True
        return

    # b toggles between single-shot and automatic spray firing
    if nk == b'b':
        global spray_mode, spray_fire_timer
        spray_mode = not spray_mode
        spray_fire_timer = 0.0
        return

    # car entry / exit
    if nk == b'e':
        dist = math.hypot(player_pos[0] - car_x, player_pos[1] - car_y)
        if dist < 80:
            player_in_car = not player_in_car
            if player_in_car:
                player_pos[0] = car_x
                player_pos[1] = car_y
                player_pos[2] = 0
                pressed_keys.discard(b'w')
                pressed_keys.discard(b's')
            else:
                car_speed = 0
                pressed_keys.clear()
                # step the player a little away from the car so they don't spawn stuck inside it
                angle_rad = math.radians(car_angle)
                player_pos[0] = car_x - math.sin(angle_rad) * 45
                player_pos[1] = car_y + math.cos(angle_rad) * 45
        return

    if game_over or game_paused:
        return
    
        # J = jump
    if nk == b' ':
        start_jump()
        return

    # K = run
    if nk == b'k':
        player_speed = RUN_SPEED
        return

    # wasd, added to pressed_keys so multiple keys combine
    if nk in (b'w', b'a', b's', b'd'):
        pressed_keys.add(nk)
        return

    # shoot
    if nk == b'm' or nk==b'M':
        try_start_mission()
        return
    
    # debug: instantly complete mission 1, 2 or 3
    if nk in (b'1', b'2', b'3'):
   
        idx = int(nk) - 1   # 0-based
        if idx >= missions_completed:
            missions_completed  = idx + 1
            current_mission_idx = missions_completed
            drug_picked_up      = False
            player_money       += 100
            _clear_heat()
            cheat_mode          = False
            cheat_waypoints     = []
            if missions_completed >= 3:
                mission_state = "done"
                mission_hint  = "All 3 missions complete!  Good work."
            else:
                mission_state = "idle"
                mission_hint  = f"Mission {idx+1} skipped. Return to safe house for next mission."
        return
    
    if nk == b'f':
        # plant the bomb at the marker just outside the BRAC gate
        if final_mission_state == "plant_bomb":
            px2, py2 = _player_world_pos()
            if math.hypot(px2 - BRAC_GATE_POS[0], py2 - BRAC_GATE_POS[1]) < BRAC_GATE_RADIUS:
                global bomb_planted, bomb_cooldown_timer
                bomb_planted        = True
                final_mission_state = "cops_incoming"
                bomb_cooldown_timer = POLICE_RESPONSE_DELAY
                mission_hint        = f"FINAL: BOMB PLANTED! Cops incoming in {POLICE_RESPONSE_DELAY:.0f}s..."
                return
        # refuel (original behaviour)
        try_refuel()
        return

def keyboardUpListener(key, x, y):
    nk = key.lower() if isinstance(key, bytes) else key
    
    if nk == b'k':
        global player_speed
        player_speed = 8
        return
    
    pressed_keys.discard(nk)


def specialKeyListener(key, x, y):
    global camera_height, camera_angle
    if first_person:
        return
    if key == GLUT_KEY_UP:
        camera_height += 20
    elif key == GLUT_KEY_DOWN:
        camera_height -= 20
    elif key == GLUT_KEY_LEFT:
        camera_angle += 3
    elif key == GLUT_KEY_RIGHT:
        camera_angle -= 3


def mouseListener(button, state, x, y):
    global first_person
    global mouse_fire_held, spray_fire_timer

    if game_menu_open:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            # glut gives y from the top, flip it to match our bottom-up button rects
            click_y = screen_height - y
            if shop_open:
                for item_id, (left, bottom, right, top) in shop_buttons.items():
                    if left <= x <= right and bottom <= click_y <= top:
                        handle_shop_click(item_id)
                        break
            else:
                for label, (left, bottom, right, top) in menu_buttons.items():
                    if left <= x <= right and bottom <= click_y <= top:
                        handle_menu_click(label)
                        break
        return

    if game_over:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not game_paused:
            shoot()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if not game_paused:
            first_person = not first_person

    # track left-button hold state so automatic spray fire can keep
    # shooting every frame in animate() while the button stays down
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_fire_held = True
            spray_fire_timer = 0.0
        elif state == GLUT_UP:
            mouse_fire_held = False
            


def main():
    glutInit()
    initialize()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(screen_width, screen_height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Mini Game")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(animate)
    glutMainLoop()


if __name__ == "__main__":
    main()