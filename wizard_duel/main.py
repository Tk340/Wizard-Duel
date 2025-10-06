import pygame
import random
import sys

pygame.init()

# --- Window setup ---
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard Duel - Real Time")

# --- Colors ---
DARK_BLUE = (30, 30, 60)
RED = (255, 60, 60)
GREEN = (0, 255, 100)
WHITE = (255, 255, 255)

# --- Load sprites ---
player_img = pygame.image.load("wizard_duel/assets/wizard_player.png").convert_alpha()
enemy_img = pygame.image.load("wizard_duel/assets/wizard_enemy.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (100, 140))
enemy_img = pygame.transform.scale(enemy_img, (100, 140))
enemy_img = pygame.transform.flip(enemy_img, True, False)

# --- Stats ---
player_health = 100
enemy_health = 100
player_speed = 5
FIREBALL_SPEED = 8

# --- Cooldowns ---
FIREBALL_COOLDOWN = 500     # ms
DODGE_COOLDOWN = 1500       # ms
DODGE_DURATION = 150        # ms
ENEMY_SHOOT_COOLDOWN = 1200
ENEMY_MOVE_CHANGE = 1000
POWERUP_SPAWN= 8000 #new heal orb every 8 seconds

# --- Timers ---
last_shot_time = 0
last_dodge_time = 0
dodging = False
dodge_start = 0
last_enemy_shot = 0
last_enemy_move = 0
enemy_dx, enemy_dy = 0, 0
last_powerup_spawn = 0
powerup = None

# --- Fireballs ---
fireballs = []
lightnings = []     
enemy_fireballs = []

# --- Positions ---
player_x, player_y = 150, 400
enemy_x, enemy_y = 600, 400

# --- Font & Clock ---
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

# --- Game loop ---
while True:
    dt = clock.tick(60)
    t = pygame.time.get_ticks()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    # --- Player input ---
    keys = pygame.key.get_pressed()

    # Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:  player_x -= player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player_x += player_speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:    player_y -= player_speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:  player_y += player_speed

    # Dodge (Shift)
    if keys[pygame.K_LSHIFT] and t - last_dodge_time > DODGE_COOLDOWN:
        dodging = True
        dodge_start = t
        last_dodge_time = t

    # If dodging, move faster briefly
    if dodging:
        player_speed = 15
        if t - dodge_start > DODGE_DURATION:
            player_speed = 5; dodging = False

    # fireball (spacebar) with cooldown
    if keys[pygame.K_SPACE] and t - last_shot_time > FIREBALL_COOLDOWN:
        fireballs.append([player_x + 80, player_y + 40])
        last_shot_time = t
    
    # Lighning (L) 
    if keys[pygame.K_l] and t - last_shot_time > FIREBALL_COOLDOWN:
        lightnings.append([player_x + 80, player_y + 40])
        last_shot_time = t

    # --- Enemy random movement ---
    if t - last_enemy_move > ENEMY_MOVE_CHANGE:
        enemy_dx = random.choice([-3, -2, -1, 0, 1, 2, 3])
        enemy_dy = random.choice([-2, -1, 0, 1, 2])
        last_enemy_move = t 

    enemy_x += enemy_dx; enemy_y += enemy_dy
    enemy_x = max(400, min(enemy_x, WIDTH - 100))
    enemy_y = max(200, min(enemy_y, HEIGHT - 140))

    # --- Enemy shooting cooldown ---
    if t - last_enemy_shot > ENEMY_SHOOT_COOLDOWN:
        enemy_fireballs.append([enemy_x, enemy_y + 40])
        last_enemy_shot = t

    # Power-up spawn
    if (powerup is None) and (t - last_powerup_spawn > POWERUP_SPAWN):
        px = random.randint(100, WIDTH - 150)
        py = random.randint(250, HEIGHT - 100)
        powerup = [px, py]
        last_powerup_spawn = t

    # --- Move projectiles ---
    for f in fireballs:   f[0] += 8
    for l in lightnings:   l[0] += 5
    for ef in enemy_fireballs:   ef[0] -= 6

    # --- Collision detection ---
    fireballs = [f for f in fireballs if f[0] < WIDTH]
    lightnings = [l for l in lightnings if l[0] < WIDTH]
    enemy_fireballs = [ef for ef in enemy_fireballs if ef[0] > 0]


    # Player projectile vs enemy
    for f in fireballs[:]:
        if enemy_x < f[0] < enemy_x + 80 and enemy_y < f[1] < enemy_y + 140:
            enemy_health -= 10
            fireballs.remove(f)

    for l in lightnings[:]:
        if enemy_x < l[0] < enemy_x + 80 and enemy_y < l[1] < enemy_y + 140:
            enemy_health -= 15
            lightnings.remove(l)

    # Enemy Projectile vs player
    for ef in enemy_fireballs[:]:
        if player_x < ef[0] < player_x + 80 and player_y < ef[1] < player_y + 140:
            # If not dodging, take damage
            if not dodging:
                player_health -= 10
            enemy_fireballs.remove(ef)
    
    # PLayer vs heal orb
    if powerup:
        px, py = powerup
        if player_x < px < player_x + 100 and player_y < py < player_y + 140:
            heal = random.randint(20, 30)
            player_health = min(100, player_health + heal)
            powerup = None

    # --- Draw scene ---
    window.fill(DARK_BLUE)
    window.blit(player_img, (player_x, player_y))
    window.blit(enemy_img, (enemy_x, enemy_y))

# Fireballs
    for f in fireballs:
        pygame.draw.circle(window, RED, (int(f[0]), int(f[1])), 8)
# Lightnings
    for l in lightnings:
        pygame.draw.circle(window, WHITE, (int(l[0]), int(l[1])), 12)
# Heal orb
    if powerup:
        pygame.draw.circle(window, (0, 255, 0), (powerup[0], powerup[1]), 12)
# Enemy fireballs
    for ef in enemy_fireballs:
        pygame.draw.circle(window, GREEN, (int(ef[0]), int(ef[1])), 8)

    # Health bars
    pygame.draw.rect(window, RED, (100, 50, 200, 25))
    pygame.draw.rect(window, GREEN, (100, 50, 2 * max(0, player_health), 25))
    pygame.draw.rect(window, RED, (500, 50, 200, 25))
    pygame.draw.rect(window, GREEN, (500, 50, 2 * max(0, enemy_health), 25))

    # Text
    player_text = font.render(f"Player HP: {max(0, player_health)}", True, WHITE)
    enemy_text = font.render(f"Enemy HP: {max(0, enemy_health)}", True, WHITE)
    dodge_text = font.render("Shift = Dodge  |  Space = Fire", True, WHITE)
    window.blit(player_text, (100, 20))
    window.blit(enemy_text, (500, 20))
    window.blit(dodge_text, (220, 560))

    # --- Endgame ---
    if player_health <= 0 or enemy_health <= 0:
        result = "You Win!" if enemy_health <= 0 else "You Lose!"
        result_text = font.render(result, True, WHITE)
        window.blit(result_text, (WIDTH // 2 - 80, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.delay(3000)
        pygame.quit()
        sys.exit()

    pygame.display.flip()
