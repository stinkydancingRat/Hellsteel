import pygame
import math
import random
import time

pygame.init()
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font("pixelfont.ttf", 48)
level_font = pygame.font.Font("pixelfont.ttf", 24)
damage_font = pygame.font.Font("pixelfont.ttf", 16)
damage_font_stroke = pygame.font.Font("pixelfont.ttf", 18)


running = True
on_level_up_screen = False
second = 0
time_passed = time.time()
difficulty_start_time = time.time()
last_enemy_spawn = time.time()
enemy_spawn_speed = 1.4

# Player variables
plr_speed = 3
plr_x = WIDTH // 2
plr_y = HEIGHT // 2
plr_is_facing_right = True
plr_health = 100
last_hit_time = time.time()
knockback_velocity_x = 0
knockback_velocity_y = 0

attacking = False

last_weapon_switch = 0
weapon_switch_cooldown = 0.3

# Sword variables
swinging_time = 0.3
swing_time = time.time()
swinging = False
sword_cooldown = time.time()
sword_cooldown_time = 0.8
can_swing = True

# XP system
xp = 0
xp_orbs = []

# Fireball system
fireball_x = 0
fireball_y = 0
fireball_size = (32, 40)
fireball_level = 0
fireball_amount = 3
fireball_max_amount = 3
fireball_regen_time = 12
fireball_last_regen = None
fireball_cooldown = 0.5
last_fireball_time = 0
active_fireballs = []

abilities = ["fireball", "heart", "knife"]
inventory = ["sword"]
current_weapon = "sword"

# Level up cards
card1_ability = None
card2_ability = None
card3_ability = None
card1_pos = WIDTH // 2 - 180
card2_pos = WIDTH // 4 - 180
card3_pos = WIDTH // 2 + 270

# Sprites
knife_image = pygame.image.load("sprites/knife.png").convert_alpha()
knife_sprite = pygame.transform.scale(knife_image, (24, 44))
knife_mask = pygame.mask.from_surface(knife_sprite)
knife_icon = pygame.transform.scale(knife_image, (108, 198))

heart_image = pygame.image.load("sprites/heart.png").convert_alpha()
heart_icon = pygame.transform.scale(heart_image, (160,160))

sword_swing_image = pygame.image.load("sprites/swordSwing.png").convert_alpha()
sword_swing_sprite = pygame.transform.scale(sword_swing_image, (90, 96))

sword_image = pygame.image.load("sprites/sword.png").convert_alpha()
sword_sprite = pygame.transform.scale(sword_image, (20, 32))

level_up_card_image = pygame.image.load("sprites/levelUpCard.png").convert_alpha()
level_up_card = pygame.transform.scale(level_up_card_image, (320, 640))

xp_orb_image = pygame.image.load("sprites/xpOrb.png").convert_alpha()
xp_orb_sprite = pygame.transform.scale(xp_orb_image, (16, 16))

player_image = pygame.image.load("sprites/player.png").convert_alpha()
player_sprite = pygame.transform.scale(player_image, (32, 32))

enemy_image = pygame.image.load("sprites/enemy.png").convert_alpha()
enemy_sprite = pygame.transform.scale(enemy_image, (32, 32))
enemy_mask = pygame.mask.from_surface(enemy_sprite)

fireball_image = pygame.image.load("sprites/fireball.png").convert_alpha()
fireball_icon = pygame.transform.scale(fireball_image, (160, 200))


# Sounds

click_sfx = pygame.mixer.Sound("sounds/click.wav")
pickupXP_sfx = pygame.mixer.Sound("sounds/pickupXP.wav")
pickupXP_sfx.set_volume(0.3)
enemyHit_sfx = pygame.mixer.Sound("sounds/enemyHit.wav")
playerHit_sfx = pygame.mixer.Sound("sounds/playerHit.wav")

enemies = []
knives = []

knife_level = 0


last_sword_target_index = None
last_attack_time = 0
attack_delay = 0.1

def spawn_knife(plr_x, plr_y, angle):
    knives.append([plr_x + 16, plr_y + 16, angle, 0, pygame.time.get_ticks(), knife_sprite.copy(), True, 0, 0, 'orbiting', None, time.time()])

def rotate_knife(plr_x, plr_y):
    for knife in knives:
        if knife[9] == 'orbiting':
            knife[2] = (knife[2] + 2) % 360
            x_offset = math.cos(math.radians(knife[2])) * 60
            y_offset = math.sin(math.radians(knife[2])) * 60
            knife[0] = plr_x + 16 + x_offset - 6
            knife[1] = plr_y + 16 + y_offset - 12
            knife[7] = 0
            knife[8] = 0

def knife_attack(enemies):
    global last_attack_time
    now = time.time()
    if now - last_attack_time < attack_delay:
        return
    for knife in knives:
        if knife[9] == 'orbiting' and now > knife[11] + 0.2:
            closest_enemy = None
            closest_dist = 300
            for i, (ex, ey, *_) in enumerate(enemies):
                dist = math.hypot(ex - knife[0], ey - knife[1])
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = (i, ex, ey)
            if closest_enemy:
                i, ex, ey = closest_enemy
                angle = math.atan2(ey - knife[1], ex - knife[0])
                deg_angle = math.degrees(angle)
                knife[5] = pygame.transform.rotate(knife_sprite.copy(), -deg_angle + 90)
                speed = 15
                knife[7] = math.cos(angle) * speed
                knife[8] = math.sin(angle) * speed
                knife[9] = 'attacking'
                knife[10] = i
                last_attack_time = now

def update_knives(enemies, plr_x, plr_y):
    return_speed = 10
    attack_speed = 15
    for knife in knives:
        state = knife[9]
        if state == 'attacking':
            target_index = knife[10]
            if target_index is None or target_index >= len(enemies):
                knife[9] = 'returning'
                knife[10] = None
                knife[7] = 0
                knife[8] = 0
                continue
            ex, ey = enemies[target_index][0], enemies[target_index][1]
            dx, dy = ex - knife[0], ey - knife[1]
            dist = math.hypot(dx, dy)
            if dist < 5:
                knife[9] = 'returning'
                knife[10] = None
                knife[7] = 0
                knife[8] = 0
                continue
            angle = math.atan2(dy, dx)
            deg_angle = math.degrees(angle)
            knife[5] = pygame.transform.rotate(knife_sprite.copy(), -deg_angle + 90)
            knife[7] = math.cos(angle) * attack_speed
            knife[8] = math.sin(angle) * attack_speed
            knife[0] += knife[7]
            knife[1] += knife[8]
        elif state == 'returning':
            dx, dy = (plr_x + 16) - knife[0], (plr_y + 16) - knife[1]
            dist = math.hypot(dx, dy)
            if dist < 5:
                knife[9] = 'orbiting'
                knife[11] = time.time()
                knife[7] = 0
                knife[8] = 0
                knife[5] = knife_sprite.copy()
                continue
            angle = math.atan2(dy, dx)
            knife[7] = math.cos(angle) * return_speed
            knife[8] = math.sin(angle) * return_speed
            knife[0] += knife[7]
            knife[1] += knife[8]

def draw_knives():
    rotate_knife(plr_x, plr_y)
    for knife in knives:
        elapsed_time = pygame.time.get_ticks() - knife[4]
        if knife[3] < 255:
            alpha = int((elapsed_time / 1000) * 255)
            knife[5].set_alpha(alpha)
        window.blit(knife[5], (knife[0], knife[1]))



def cheats():
    global xp
    keys = pygame.key.get_pressed()
    if keys[pygame.K_o]:
        xp += 100

def reset_level_up_cards():
    global card1_ability, card2_ability, card3_ability
    card1_ability = None
    card2_ability = None
    card3_ability = None


def spawn_enemy():
    side = random.choice(['bottom', 'left', 'right', 'left', 'right', 'left', 'right'])

    if side == 'bottom':
        enemy_x = random.randint(0, WIDTH)
        enemy_y = HEIGHT + 50
    elif side == 'left':
        enemy_x = -50
        enemy_y = random.randint(0, HEIGHT)
    elif side == 'right':
        enemy_x = WIDTH + 50
        enemy_y = random.randint(0, HEIGHT)

    enemy_is_facing_right = enemy_x < plr_x
    enemies.append([enemy_x, enemy_y, enemy_is_facing_right, 20, 0, 0])  


def spawn_first_enemies():
    initial_enemy_count = random.randint(5, 10)
    for _ in range(initial_enemy_count):
        spawn_enemy()

def spawn_xp(enemy_x, enemy_y):
    xp_orbs.append([enemy_x, enemy_y])


def draw_health_bar(health, x, y):
    bar_width = 60
    bar_height = 10
    fill = (health / 100) * bar_width
    outline_rect = pygame.Rect(x - 15, y, bar_width, bar_height)
    fill_rect = pygame.Rect(x - 15, y, fill, bar_height)
    blank_rect = pygame.Rect(x - 15, y, bar_width, bar_height)
    pygame.draw.rect(window, (150, 0, 0), blank_rect)
    pygame.draw.rect(window, (255, 0, 0), fill_rect)
    pygame.draw.rect(window, (0, 0, 0), outline_rect, 2)


def draw_xp_bar():
    bar_width = WIDTH
    bar_height = 50
    fill = (xp / 100) * bar_width
    outline_rect = pygame.Rect(0, 0, bar_width, bar_height)
    fill_rect = pygame.Rect(0, 0, fill, bar_height)
    blank_rect = pygame.Rect(0, 0, bar_width, bar_height)
    pygame.draw.rect(window, (0, 50, 0), blank_rect)
    pygame.draw.rect(window, (0, 255, 0), fill_rect)
    pygame.draw.rect(window, (0, 0, 0), outline_rect, 5)


def fireball_level_up(card_pos):
    level_text = font.render(f"LVL:{fireball_level}→{fireball_level + 1}", True, (255, 255, 255))
    level_rect = level_text.get_rect(center=(card_pos - 24 + 180, HEIGHT // 2))

    info_text1 = level_font.render("   Increase size and", True, (255, 255, 255))
    info_text2 = level_font.render("lower cooldown", True, (255, 255, 255))

    info_rect1 = info_text1.get_rect(center=(card_pos - 50 + 180, HEIGHT // 2 + 50))
    info_rect2 = info_text2.get_rect(center=(card_pos - 50 + 180, HEIGHT // 2 + 80))

    window.blit(info_text1, info_rect1)
    window.blit(info_text2, info_rect2)

    window.blit(fireball_icon, (card_pos - 100 + 180, HEIGHT // 2 - 260))
    window.blit(level_text, level_rect)

def health_card(card_pos):
    level_text = font.render(f"Health", True, (255, 255, 255))
    level_rect = level_text.get_rect(center=(card_pos - 24 + 180, HEIGHT // 2))


    info_text1 = level_font.render("    Heals +40 health", True, (255, 255, 255))

    info_rect1 = info_text1.get_rect(center=(card_pos - 50 + 180, HEIGHT // 2 + 50))

    window.blit(info_text1, info_rect1)

    window.blit(heart_icon, (card_pos - 100 + 180, HEIGHT // 2 - 260))
    window.blit(level_text, level_rect)

def knife_card(card_pos):
    level_text = font.render(f"LVL:{knife_level}→{knife_level + 1}", True, (255, 255, 255))
    level_rect = level_text.get_rect(center=(card_pos - 24 + 180, HEIGHT // 2))


    info_text1 = level_font.render("    +1 knife" if knife_level > 0 else "     It protects you", True, (255, 255, 255))

    info_rect1 = info_text1.get_rect(center=(card_pos - 50 + 180, HEIGHT // 2 + 50))

    window.blit(info_text1, info_rect1)

    window.blit(knife_icon, (card_pos - 75 + 180, HEIGHT // 2 - 260))
    window.blit(level_text, level_rect)




def check_ability(card_pos, ability):
    if ability == "fireball":
        fireball_level_up(card_pos)
    if ability == "heart":
        health_card(card_pos)
    if ability == "knife":
        knife_card(card_pos)


def draw_card1():
    global card1_ability
    if card1_ability is None:
        available_abilities = [a for a in abilities if a not in [card2_ability, card3_ability]]
        if available_abilities:
            card1_ability = random.choice(available_abilities)

    window.blit(level_up_card, (card1_pos, HEIGHT // 2 - 320))
    if card1_ability:
        check_ability(card1_pos, card1_ability)


def draw_card2():
    global card2_ability
    if card2_ability is None:
        available_abilities = [a for a in abilities if a not in [card1_ability, card3_ability]]
        if available_abilities:
            card2_ability = random.choice(available_abilities)

    window.blit(level_up_card, (card2_pos, HEIGHT // 2 - 320))
    if card2_ability:
        check_ability(card2_pos, card2_ability)


def draw_card3():
    global card3_ability
    if card3_ability is None:
        available_abilities = [a for a in abilities if a not in [card1_ability, card2_ability]]
        if available_abilities:
            card3_ability = random.choice(available_abilities)

    window.blit(level_up_card, (card3_pos, HEIGHT // 2 - 320))
    if card3_ability:
        check_ability(card3_pos, card3_ability)


def level_up_ability_check(selected_card):
    global plr_health, fireball_level, fireball_regen_time, fireball_size, fireball_cooldown, inventory, knife_level

    if selected_card == card1_pos and card1_ability == "fireball" or \
        selected_card == card2_pos and card2_ability == "fireball" or \
        selected_card == card3_pos and card3_ability == "fireball":

        if "fireball" not in inventory:
            inventory.append("fireball")

        fireball_level += 1
        if fireball_regen_time > 3:
            fireball_regen_time -= 0.5
        fireball_size = (fireball_size[0] + 8, fireball_size[1] + 10)
        fireball_cooldown = max(0.1, fireball_cooldown - 0.05)


    if selected_card == card1_pos and card1_ability == "heart" or \
        selected_card == card2_pos and card2_ability == "heart" or \
        selected_card == card3_pos and card3_ability == "heart":
        

        plr_health += 40

    if selected_card == card1_pos and card1_ability == "knife" or \
        selected_card == card2_pos and card2_ability == "knife" or \
        selected_card == card3_pos and card3_ability == "knife":
            knife_level += 1
            spawn_knife(plr_x, plr_y, knife_level * 22)
        


def normalize(enemy_x, enemy_y):
    distance = math.sqrt((plr_x - enemy_x) ** 2 + (plr_y - enemy_y) ** 2)
    if distance == 0:
        return 0, 0
    dx = (plr_x - enemy_x) / distance
    dy = (plr_y - enemy_y) / distance
    return dx, dy



def separation(enemy_index):
    separation_force_x = 0
    separation_force_y = 0

    for i, enemy in enumerate(enemies):
        if i != enemy_index:
            other_enemy_x = enemy[0]
            other_enemy_y = enemy[1]
            dx = enemies[enemy_index][0] - other_enemy_x
            dy = enemies[enemy_index][1] - other_enemy_y
            distance = math.hypot(dx, dy)
            if distance < 32 and distance > 0:
                separation_force_x += dx / distance
                separation_force_y += dy / distance

    return separation_force_x, separation_force_y


def player_apply_knockback(enemy_x, enemy_y):
    global knockback_velocity_x, knockback_velocity_y
    knockback_distance = 10
    dx = plr_x - enemy_x
    dy = plr_y - enemy_y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    if distance != 0:
        dx /= distance
        dy /= distance
    knockback_velocity_x = dx * knockback_distance
    knockback_velocity_y = dy * knockback_distance


def enemy_hit_knockback(enemy_x, enemy_y):
    dx = enemy_x - plr_x
    dy = enemy_y - plr_y
    distance = math.hypot(dx, dy)
    if distance == 0:
        return 0, 0
    dx /= distance
    dy /= distance
    knockback_distance = 6
    return dx * knockback_distance, dy * knockback_distance

def player_check_collision(obj_x, obj_y, obj_width, obj_height):
    return (
            plr_x + 30 >= obj_x and
            plr_x + 2 <= obj_x + obj_width and
            plr_y + 32 >= obj_y and
            plr_y <= obj_y + obj_height
    )


def sword_check_collision(enemy_x, enemy_y, enemy_width, enemy_height):
    if not swinging:
        return False

    if plr_is_facing_right:
        return (
                plr_x + 90 >= enemy_x and
                plr_x + 2 <= enemy_x + enemy_width and
                plr_y + 48 >= enemy_y and
                plr_y - 48 <= enemy_y + enemy_height
        )
    else:
        return (
                plr_x >= enemy_x and
                plr_x - 52 <= enemy_x + enemy_width and
                plr_y + 48 >= enemy_y and
                plr_y - 48 <= enemy_y + enemy_height
        )


def draw_sword_idle():
    if plr_is_facing_right:
        window.blit(sword_sprite, (plr_x + 24, plr_y + 5))
    else:
        window.blit(sword_sprite, (plr_x - 8, plr_y + 5))


def draw_sword_swing():
    if plr_is_facing_right:
        window.blit(sword_swing_sprite, (plr_x, plr_y - 32))
    else:
        window.blit(pygame.transform.flip(sword_swing_sprite, True, False), (plr_x - 54, plr_y - 32))


sword_hit_enemies = set()


def start_sword_swing():
    global swinging, can_swing, sword_cooldown, sword_hit_enemies
    swinging = True
    can_swing = False
    sword_hit_enemies.clear()
    sword_cooldown = time.time()


def spawn_fireball(player_x, player_y, mouse_x, mouse_y):
    global fireball_amount, fireball_last_regen

    current_time = time.time()
    if fireball_amount <= 0 or current_time - last_fireball_time < fireball_cooldown:
        return

    fireball_amount -= 1

    if fireball_last_regen is None and fireball_amount < fireball_max_amount:
        fireball_last_regen = current_time

    angle = math.atan2(mouse_y - player_y, mouse_x - player_x)
    angle_degrees = math.degrees(angle)

    fireball_x = player_x + 16 - fireball_size[0] // 2
    fireball_y = player_y + 16 - fireball_size[1] // 2

    fireball_dx = math.cos(angle) * 15
    fireball_dy = math.sin(angle) * 15

    active_fireballs.append({
        'x': fireball_x,
        'y': fireball_y,
        'dx': fireball_dx,
        'dy': fireball_dy,
        'angle': angle_degrees,
        'enemies_hit': 0,
        'hit_enemies' : set()
    })


def update_fireballs():
    global active_fireballs, last_fireball_time

    for i in range(len(active_fireballs) - 1, -1, -1):
        fireball = active_fireballs[i]
        fireball['x'] += fireball['dx']
        fireball['y'] += fireball['dy']

        rotated_fireball = pygame.transform.rotate(
            pygame.transform.scale(fireball_image, fireball_size),
            -fireball['angle'] - 90
        )
        window.blit(rotated_fireball, (fireball['x'], fireball['y']))

        if (fireball['x'] < -200 or fireball['x'] > WIDTH + 200 or
                fireball['y'] < -200 or fireball['y'] > HEIGHT + 200):
            active_fireballs.pop(i)


def fireball_check_collision(fireball, enemy_x, enemy_y, enemy_width, enemy_height):
    return (
            fireball['x'] + fireball_size[0] >= enemy_x and
            fireball['x'] <= enemy_x + enemy_width and
            fireball['y'] + fireball_size[1] >= enemy_y and
            fireball['y'] <= enemy_y + enemy_height
    )


def fireball_hit_enemy(fireball_index):
    active_fireballs[fireball_index]['enemies_hit'] += 1
    max_enemies = 1000
    return active_fireballs[fireball_index]['enemies_hit'] >= max_enemies


def attack():
    global attacking, swinging, fireball_amount, last_fireball_time

    if current_weapon == "fireball" and fireball_amount > 0:
        mouse_pos = pygame.mouse.get_pos()
        spawn_fireball(plr_x, plr_y, mouse_pos[0], mouse_pos[1])
        last_fireball_time = time.time()
    elif current_weapon == "sword" and not swinging and can_swing:
        start_sword_swing()

    attacking = False


def update_fireball_regeneration():
    global fireball_amount, fireball_last_regen

    if fireball_amount < fireball_max_amount:
        if fireball_last_regen is None:
            fireball_last_regen = time.time()
        elif time.time() - fireball_last_regen > fireball_regen_time:
            fireball_amount += 1
            fireball_last_regen = time.time()
            if fireball_amount >= fireball_max_amount:
                fireball_last_regen = None


def switch_weapons(key):
    global current_weapon, last_weapon_switch

    current_time = time.time()
    if current_time - last_weapon_switch < weapon_switch_cooldown:
        return

    if key == pygame.K_1 and "sword" in inventory:
        current_weapon = "sword"
        last_weapon_switch = current_time
    elif key == pygame.K_2 and "fireball" in inventory:
        current_weapon = "fireball"
        last_weapon_switch = current_time


def draw_current_weapon():
    if current_weapon == "sword":
        if swinging:
            draw_sword_swing()
        else:
            draw_sword_idle()


def draw_weapon_ui():
    weapons_text = level_font.render("Weapons:", True, (0, 0, 0))
    window.blit(weapons_text, (10, 60))

    for i, weapon in enumerate(inventory):
        if weapon == current_weapon:
            color = (255, 255, 0)
        else:
            color = (255, 255, 255)

        weapon_text = level_font.render(f"{i + 1}: {weapon.capitalize()}", True, color)
        window.blit(weapon_text, (10, 90 + i * 30))

        if weapon == "fireball" and weapon == current_weapon:
            ammo_text = level_font.render(
                f"Ammo: {fireball_amount}/{fireball_max_amount}", True, color)
            window.blit(ammo_text, (200, 90 + i * 30))


def update_player():
    global plr_x, plr_y, plr_is_facing_right, knockback_velocity_x, knockback_velocity_y

    keys = pygame.key.get_pressed()
    move_x, move_y = 0, 0

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and plr_x + 2 > 0:
        move_x = -1
        plr_is_facing_right = False

    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and plr_x + 30 < WIDTH:
        move_x = 1
        plr_is_facing_right = True

    if (keys[pygame.K_UP] or keys[pygame.K_w]) and plr_y > 0:
        move_y = -1

    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and plr_y + 32 < HEIGHT:
        move_y = 1

    if move_x != 0 and move_y != 0:
        move_x *= math.sqrt(0.5)
        move_y *= math.sqrt(0.5)

    plr_x += move_x * plr_speed
    plr_y += move_y * plr_speed

    plr_x += knockback_velocity_x
    plr_y += knockback_velocity_y

    knockback_velocity_x *= 0.9
    knockback_velocity_y *= 0.9

    if plr_x < 0:
        plr_x = 0
    elif plr_x + 30 > WIDTH:
        plr_x = WIDTH - 30

    if plr_y < 50:
        plr_y = 50
    elif plr_y + 32 > HEIGHT:
        plr_y = HEIGHT - 32


def update_xp_orbs():
    global xp, xp_orbs

    for i in range(len(xp_orbs) - 1, -1, -1):
        xp_x, xp_y = xp_orbs[i]

        distance = math.sqrt((plr_x - xp_x) ** 2 + (plr_y - xp_y) ** 2)

        if distance < 120:
            if distance > 1:
                xp_orb_dx = (plr_x - xp_x) / distance * 3.5
                xp_orb_dy = (plr_y - xp_y) / distance * 3.5
                xp_x += xp_orb_dx
                xp_y += xp_orb_dy

        window.blit(xp_orb_sprite, (xp_x, xp_y))

        if player_check_collision(xp_x, xp_y, 16, 16):
            pickupXP_sfx.play()
            xp += 2
            xp_orbs.pop(i)
        else:
            xp_orbs[i] = [xp_x, xp_y]


damage_texts = []

def damage_text(damage, x, y):
    global damage_texts

    text = damage_font.render(str(damage), True, (255, 255, 255))
    stroke = damage_font_stroke.render(str(damage), True, (0, 0, 0))
    damage_texts.append([text, stroke, x , y, time.time()])
    

def render_damage_text():
    global damage_texts
    for text in damage_texts[:]:
        #Stroke
        window.blit(text[1], (text[2] - 1, text[3] - 1))

        #Text
        window.blit(text[0], (text[2], text[3]))
        text[3] -= 1
        if time.time() - text[4] > 0.45:
            damage_texts.remove(text)



enemy_hit_timers = {}

def update_enemies():
    global enemies, plr_health, last_hit_time, sword_hit

    for i in range(len(enemies) - 1, -1, -1):
        enemy_x, enemy_y, enemy_is_facing_right, enemy_health, enemy_vx, enemy_vy = enemies[i]

        dx, dy = normalize(enemy_x, enemy_y)
        sep_force_x, sep_force_y = separation(i)
        dx += sep_force_x
        dy += sep_force_y

        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance != 0:
            dx /= distance
            dy /= distance

        enemy_x += dx * 1
        enemy_y += dy * 1

        window.blit(
            pygame.transform.flip(enemy_sprite, True, False)
            if not enemy_is_facing_right else enemy_sprite,
            (enemy_x, enemy_y)
        )

        for j in range(len(active_fireballs) - 1, -1, -1):
            fireball = active_fireballs[j]
            if fireball_check_collision(fireball, enemy_x, enemy_y, 30, 32) and i not in fireball["hit_enemies"]:
                damage_text(15, enemy_x, enemy_y)
                enemyHit_sfx.play()
                fireball["hit_enemies"].add(i)
                enemy_vx, enemy_vy = enemy_hit_knockback(enemy_x, enemy_y)
                enemy_health -= 15
                fireball["enemies_hit"] += 1
                if fireball["enemies_hit"] >= 20:
                    active_fireballs.pop(j)
                break

        if sword_check_collision(enemy_x, enemy_y, 30, 32) and i not in sword_hit_enemies:
            enemyHit_sfx.play()
            sword_hit_enemies.add(i)
            enemy_vx, enemy_vy = enemy_hit_knockback(enemy_x, enemy_y)
            enemy_health -= 10

        
        for knife in knives:
            if knife_mask.overlap(enemy_mask, (knife[0] - enemy_x, knife[1] - enemy_y)):
                
                now = time.time()
                if i not in enemy_hit_timers or now - enemy_hit_timers[i] > 0.2:
                    enemyHit_sfx.play()
                    enemy_health -= 2.5
                    enemy_vx, enemy_vy = enemy_hit_knockback(enemy_x, enemy_y)
                    enemy_hit_timers[i] = now

        if enemy_health <= 0:
            enemies.pop(i)
            spawn_xp(enemy_x, enemy_y)
            continue

        if player_check_collision(enemy_x, enemy_y, 30, 32):
            if time.time() - last_hit_time > 1:
                playerHit_sfx.play()
                plr_health -= 10
                player_apply_knockback(enemy_x, enemy_y)
                last_hit_time = time.time()
                return last_hit_time

        enemy_vx *= 0.9
        enemy_vy *= 0.9

        enemy_x += enemy_vx
        enemy_y += enemy_vy
        enemies[i] = [enemy_x, enemy_y, enemy_is_facing_right, enemy_health, enemy_vx, enemy_vy]

def update_difficulty():
    global enemy_spawn_speed

    elapsed_time = time.time() - difficulty_start_time

    if elapsed_time > 20:
        enemy_spawn_speed = 1.2
    elif elapsed_time > 50:
        enemy_spawn_speed = 1
    elif elapsed_time > 100:
        enemy_spawn_speed = 0.5
    elif elapsed_time > 150:
        enemy_spawn_speed = 0.1
    elif elapsed_time > 400:
        enemy_spawn_speed = 0.08
    elif elapsed_time > 500:
        enemy_spawn_speed = 0.06
    elif elapsed_time > 600:
        enemy_spawn_speed = 0.04
    elif elapsed_time > 800:
        enemy_spawn_speed = 0.02


def handle_input():
    global running, on_level_up_screen, attacking, xp, plr_health

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not on_level_up_screen:
            if event.button == 1:
                attacking = True
        if event.type == pygame.KEYDOWN:
            switch_weapons(event.key)

    if xp >= 100:
        on_level_up_screen = True
        reset_level_up_cards()


def handle_level_up_screen():
    global on_level_up_screen, xp, plr_health, running

    mouse_x, mouse_y = pygame.mouse.get_pos()

    draw_card1()
    draw_card2()
    draw_card3()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if card1_pos <= mouse_x <= card1_pos + 320 and \
                        HEIGHT // 2 - 320 <= mouse_y <= HEIGHT // 2 + 320:
                    xp = 0
                    level_up_ability_check(card1_pos)
                    click_sfx.play()
                    time.sleep(0.1)
                    on_level_up_screen = False

                if card2_pos <= mouse_x <= card2_pos + 320 and \
                        HEIGHT // 2 - 320 <= mouse_y <= HEIGHT // 2 + 320:
                    xp = 0
                    level_up_ability_check(card2_pos)
                    click_sfx.play()
                    time.sleep(0.1)
                    on_level_up_screen = False

                if card3_pos <= mouse_x <= card3_pos + 320 and \
                        HEIGHT // 2 - 320 <= mouse_y <= HEIGHT // 2 + 320:
                    xp = 0
                    level_up_ability_check(card3_pos)
                    click_sfx.play()
                    time.sleep(0.1)
                    on_level_up_screen = False


def draw_game():
    window.fill((85, 170, 0))

    draw_xp_bar()
    draw_health_bar(plr_health, plr_x, plr_y + 40)

    window.blit(pygame.transform.flip(player_sprite, True, False)
                if not plr_is_facing_right else player_sprite, (plr_x, plr_y))

    draw_current_weapon()

    minutes = second // 60
    seconds = second % 60
    time_text = font.render(f"{minutes}:{seconds:02}", True, (0, 0, 0))
    time_rect = time_text.get_rect(center=(WIDTH // 2, 100))
    window.blit(time_text, time_rect)

    draw_weapon_ui()


def update_game_state():
    global plr_health, second, time_passed, last_enemy_spawn, sword_hit

    if plr_health >= 100:
        plr_health = 100

    if time.time() - time_passed >= 1:
        second += 1
        time_passed = time.time()

    update_difficulty()

    if time.time() - last_enemy_spawn > enemy_spawn_speed:
        spawn_enemy()
        last_enemy_spawn = time.time()

    update_player()

    global swinging, swing_time, can_swing, sword_cooldown
    if swinging and time.time() - swing_time > swinging_time:
        sword_hit = False
        swinging = False

    if time.time() - sword_cooldown > sword_cooldown_time:
        can_swing = True
        sword_cooldown = time.time()

    update_fireball_regeneration()

    if attacking:
        attack()


spawn_first_enemies()

while running:
    fireball = pygame.transform.scale(fireball_image, fireball_size)

    if on_level_up_screen:
        handle_level_up_screen()
    else:
        handle_input()
        update_game_state()
        draw_game()
        update_xp_orbs()
        update_enemies()
        update_fireballs()
        knife_attack(enemies)
        update_knives(enemies, plr_x, plr_y)
        rotate_knife(plr_x, plr_y)
        draw_knives()
        render_damage_text()
        cheats()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
