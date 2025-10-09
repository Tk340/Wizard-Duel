import pygame, random, sys
from math import sqrt

pygame.init()
pygame.key.set_mods(0)  # prevent ⌘ or Ctrl interference

# Optional sounds — safe load
pygame.mixer.init()
try:
    fire_snd = pygame.mixer.Sound("wizard_duel/assets/sounds/fire.wav")
    hit_snd  = pygame.mixer.Sound("wizard_duel/assets/sounds/hit.wav")
    fire_snd.set_volume(0.5)
    hit_snd.set_volume(0.5)
except Exception:
    fire_snd = None
    hit_snd  = None

# Window
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard Duel ⚡")

# Colors
DARK_BLUE = (25, 25, 60)
RED = (255, 60, 60)
GREEN = (0, 255, 100)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# Assets
player_img = pygame.transform.scale(pygame.image.load("wizard_duel/assets/wizard_player.png").convert_alpha(), (100,140))
enemy_img  = pygame.transform.scale(pygame.image.load("wizard_duel/assets/wizard_enemy.png").convert_alpha(), (100,140))
enemy_img  = pygame.transform.flip(enemy_img, True, False)

font_big = pygame.font.Font(None, 72)
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

STATE = "MENU"
difficulty = "MEDIUM"

# Difficulty presets
DIFF = {
    "EASY":   {"enemy_speed":2, "enemy_cd":1500},
    "MEDIUM": {"enemy_speed":3, "enemy_cd":1000},
    "HARD":   {"enemy_speed":4, "enemy_cd":700},
}

# UI helpers
def draw_button(text,y,active=False):
    color = YELLOW if active else WHITE
    label = font.render(text,True,color)
    rect  = label.get_rect(center=(WIDTH//2,y))
    window.blit(label,rect)
    return rect

# Menus
def main_menu():
    global STATE
    opts=["Play vs AI","2 Player Battle","Quit"]
    sel=0
    while True:
        window.fill(DARK_BLUE)
        t=font_big.render("Wizard Duel ⚡",True,WHITE)
        window.blit(t,(WIDTH//2-t.get_width()//2,100))
        for i,opt in enumerate(opts):
            draw_button(opt,250+i*80,active=(i==sel))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_UP:   sel=(sel-1)%len(opts)
                if e.key==pygame.K_DOWN: sel=(sel+1)%len(opts)
                if e.key==pygame.K_RETURN:
                    if sel==0: STATE="DIFFICULTY";return
                    if sel==1: STATE="2P";return
                    if sel==2: pygame.quit();sys.exit()

def diff_menu():
    global STATE,difficulty
    diffs=["EASY","MEDIUM","HARD"]
    sel=1
    while True:
        window.fill(DARK_BLUE)
        t=font_big.render("Select Difficulty",True,WHITE)
        window.blit(t,(WIDTH//2-t.get_width()//2,120))
        for i,d in enumerate(diffs): draw_button(d,250+i*80,active=(i==sel))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_UP: sel=(sel-1)%3
                if e.key==pygame.K_DOWN: sel=(sel+1)%3
                if e.key==pygame.K_RETURN:
                    difficulty=diffs[sel]; STATE="AI"; return
                if e.key==pygame.K_ESCAPE: STATE="MENU"; return

def show_controls(mode):
    window.fill(DARK_BLUE)
    title = font_big.render("Controls 🪄", True, WHITE)
    window.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    # Player 1 controls
    y = 150
    lines_p1 = [
        "Player 1:",
        "Move: W A S D",
        "Fireball: SPACE",
        "Lightning: F",
        "Ice Spell: G",
    ]
    for line in lines_p1:
        text = font.render(line, True, WHITE)
        window.blit(text, (WIDTH // 4 - text.get_width() // 2, y))
        y += 35

    # Player 2 or AI controls
    y = 150
    if mode == "AI":
        lines_p2 = [
            "Enemy (AI):",
            "Automatically moves and attacks!",
        ]
    else:
        lines_p2 = [
            "Player 2:",
            "Move: Arrow Keys",
            "Fireball: ENTER",
            "Lightning: . (Period)",
            "Ice Spell: / (Slash)",
        ]
    for line in lines_p2:
        text = font.render(line, True, WHITE)
        window.blit(text, (3 * WIDTH // 4 - text.get_width() // 2, y))
        y += 35

    # Footer
    hint = font.render("Press ENTER to start!", True, YELLOW)
    window.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

    pygame.display.flip()

    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                waiting = False

# Game logic
def play_game(mode,difficulty):
    # Cooldowns
    FIRE_CD = 500
    LIGHTNING_CD = 3000
    ICE_CD = 5000

    last_p_fire = last_p_lightning = last_p_ice = 0
    last_e_fire = last_e_lightning = last_e_ice = 0

    # Status effects
    enemy_slowed_until = 0
    player_slowed_until = 0
    player_damage_over_time = 0
    enemy_damage_over_time = 0
    player_damaged_until = 0
    enemy_damaged_until = 0
    ult_start = 0
    ult_start_e = 0

    # Rounds
    round_num = 1
    p1_wins = p2_wins = 0
    max_rounds = 3
    round_active = False
    round_start_time = pygame.time.get_ticks()

    player_x,player_y=150,400
    enemy_x,enemy_y=600,400
    p_hp,e_hp=100,100
    fireballs_p, fireballs_e = [], []
    heal_orb=None; last_orb=0; ORB_CD=7000
    ult_orb = None
    ult_orb_e = None

    p_mana = 0
    e_mana = 0

    e_cd=DIFF[difficulty]["enemy_cd"]
    e_speed=DIFF[difficulty]["enemy_speed"]

    running=True
    while running:
        dt=clock.tick(60)
        t=pygame.time.get_ticks()

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                running=False; return

        if round_active:
            keys=pygame.key.get_pressed()

            # Player 1 (WASD)
            dx=dy=0
            if keys[pygame.K_a]: dx=-1
            if keys[pygame.K_d]: dx=1
            if keys[pygame.K_w]: dy=-1
            if keys[pygame.K_s]: dy=1
            mag=(dx**2+dy**2)**0.5
            if mag: dx/=mag; dy/=mag
            speed_p1 = 5 * (0.5 if t < player_slowed_until else 1)
            player_x += dx * speed_p1
            player_y += dy * speed_p1
            player_x=max(0,min(player_x,WIDTH-100))
            player_y=max(0,min(player_y,HEIGHT-140))

            # Player 2 / AI
            if mode=="2P":
                dx2=dy2=0
                if keys[pygame.K_LEFT]: dx2=-1
                if keys[pygame.K_RIGHT]: dx2=1
                if keys[pygame.K_UP]: dy2=-1
                if keys[pygame.K_DOWN]: dy2=1
                mag2=(dx2**2+dy2**2)**0.5
                if mag2: dx2/=mag2; dy2/=mag2
                speed_p2 = 5 * (0.5 if t < enemy_slowed_until else 1)
                enemy_x += dx2 * speed_p2
                enemy_y += dy2 * speed_p2
                enemy_x=max(0,min(enemy_x,WIDTH-100))
                enemy_y=max(0,min(enemy_y,HEIGHT-140))

                # Player 2 Fire
                if keys[pygame.K_RETURN] and t-last_e_fire>FIRE_CD:
                    fireballs_e.append([enemy_x,enemy_y+60,-1,0])
                    last_e_fire=t
                    if fire_snd: fire_snd.play()

                # Player 2 Lightning
                if keys[pygame.K_PERIOD] and t - last_e_lightning > LIGHTNING_CD and e_mana >= 20:
                    e_mana -= 20
                    last_e_lightning = t
                    if fire_snd: fire_snd.play()

                    pygame.draw.line(window, YELLOW,
                                    (enemy_x + 50, enemy_y + 70),
                                    (player_x + 50, player_y + 70), 5)
                    pygame.display.flip()
                    pygame.time.delay(150)

                    p_hp -= 20
                    if hit_snd: hit_snd.play()
                        
                # Player 2 Ice, same as Player 1
                if keys[pygame.K_SLASH] and t-last_e_ice>ICE_CD:
                    if e_mana >= 40:
                        e_mana -= 40
                        last_e_ice=t
                        if fire_snd: fire_snd.play()
                        x1 = player_x + 50
                        y1 = player_y + 70
                        pygame.draw.circle(window, (150, 200, 255), (x1, y1), 50)
                        pygame.display.flip()
                        pygame.time.delay(300)
                        player_slowed_until = t + 3000
                        if hit_snd: hit_snd.play()
                # Player 2 ult
                if keys[pygame.K_RSHIFT] and e_mana >= 100:
                    e_mana -= 100
                    enemy_damage_over_time = 15
                    player_damaged_until = t + 4000
                    ult_orb_e = (player_x + 50, player_y + 70)

            else:
                # Simple chase AI
                # slow down if frozen
                dist_x = player_x - enemy_x
                dist_y = player_y - enemy_y
                distance = sqrt(dist_x**2 + dist_y**2)

                # AI priorities
                want_heal = heal_orb and e_hp < 60
                want_attack = distance < 450
                stop_getting_closer = distance < 200
                too_close = distance < 150
                can_lightning = e_mana >= 20 and t - last_e_lightning > LIGHTNING_CD
                can_ice = e_mana >= 40 and t - last_e_ice > ICE_CD
                can_fire = t - last_e_fire > e_cd

                target_x, target_y = player_x, player_y

                # Healing behavior
                if want_heal:
                    hx, hy = heal_orb
                    target_x, target_y = hx - 50, hy - 70
                    # if abs(enemy_x - hx) < 40 and abs(enemy_y - hy) < 40:
                    #     want_attack = False

                # Maintain distance 
                if stop_getting_closer and not want_heal:
                    target_x = enemy_x
                    target_y = enemy_y
                elif too_close and not want_heal:
                    target_x = enemy_x
                    target_y = enemy_y
                elif distance > 450 and not want_heal:
                    target_x = player_x  # move in
                    target_y = player_y
                # else:
                #     # random strafe
                #     if random.random() < 0.03:
                #         strafe = random.choice([-1, 1])
                #         target_x += 100 * strafe

                # Move toward target
                dx = target_x - enemy_x if abs(target_x - enemy_x) > 20 else 0
                dy = target_y - enemy_y if abs(target_y - enemy_y) > 20 else 0
                mag = max(1, sqrt(dx**2 + dy**2))
                enemy_x += (dx / mag) * e_speed
                enemy_y += (dy / mag) * e_speed
                enemy_x = max(0, min(enemy_x, WIDTH - 100))
                enemy_y = max(0, min(enemy_y, HEIGHT - 140))

                # Attacks
                if want_attack and can_fire and not want_heal:
                    fireballs_e.append([enemy_x, enemy_y + 60, dist_x / distance, dist_y / distance])
                    last_e_fire = t
                    if fire_snd: fire_snd.play()

                # queue special moves (handled later safely)
                ai_lightning = can_lightning and random.random() < 0.02 and distance < 300
                ai_ice = can_ice and random.random() < 0.015 and distance < 300

                if ai_lightning:
                    e_mana -= 20
                    last_e_lightning = t
                    e_mana -= 20
                    last_e_lightning = t
                    if fire_snd: fire_snd.play()

                    pygame.draw.line(window, YELLOW,
                                    (enemy_x + 50, enemy_y + 70),
                                    (player_x + 50, player_y + 70), 5)
                    pygame.display.flip()
                    pygame.time.delay(150)

                    p_hp -= 20
                    if hit_snd: hit_snd.play()

                if ai_ice:
                    e_mana -= 40
                    last_e_ice = t
                    e_mana -= 40
                    last_e_ice=t
                    if fire_snd: fire_snd.play()
                    x1 = player_x + 50
                    y1 = player_y + 70
                    pygame.draw.circle(window, (150, 200, 255), (x1, y1), 50)
                    pygame.display.flip()
                    pygame.time.delay(300)
                    player_slowed_until = t + 3000
                    if hit_snd: hit_snd.play()


            # Player 1 Fire
            if keys[pygame.K_SPACE] and t-last_p_fire>FIRE_CD:
                fireballs_p.append([player_x+80,player_y+60,1,0])
                last_p_fire=t
                if fire_snd: fire_snd.play()

            # Player 1 Lightning
            if keys[pygame.K_f] and t - last_p_lightning > LIGHTNING_CD and p_mana >= 20:
                p_mana -= 20
                last_p_lightning = t
                if fire_snd: fire_snd.play()

                # Draw lightning briefly
                pygame.draw.line(window, YELLOW,
                                (player_x + 50, player_y + 70),
                                (enemy_x + 50, enemy_y + 70), 5)
                pygame.display.flip()
                pygame.time.delay(150)

                # Damage check (AFTER delay)
            #    if abs(player_y - enemy_y) < 80 and abs(player_x - enemy_x) < 400:
                e_hp -= 20
                if hit_snd: hit_snd.play()

            # Player 1 Ice
            if keys[pygame.K_g] and t-last_p_ice>ICE_CD:
                if p_mana >= 40:
                    p_mana -= 40
                    last_p_ice=t
                    if fire_snd: fire_snd.play()
                    # freeze the enemy for 3 seconds, no damage
                    # draw ice puddle on enemy's position
                    x1 = enemy_x + 50
                    y1 = enemy_y + 70
                    pygame.draw.circle(window, (150, 200, 255), (x1, y1), 50)
                    pygame.display.flip()
                    pygame.time.delay(300)
                    enemy_slowed_until = t + 3000
                    e_speed = DIFF[difficulty]["enemy_speed"] / 2.5
                    if hit_snd: hit_snd.play()
            
            # Player 1 ult
            # 15 damage per second for 4 seconds
            # keep main loop running to allow movement
            if keys[pygame.K_r] and p_mana >= 100:
                p_mana -= 100
                # use damage over time variables
                player_damage_over_time = 15
                enemy_damaged_until = t + 4000
                # do not use while loop, just set the variables and let main loop handle it
                # draw a big red circle around enemy to indicate ult
                ult_orb = (enemy_x + 50, enemy_y + 70)
            # Move projectiles
            for f in fireballs_p: f[0]+=f[2]*8; f[1]+=f[3]*8
            for f in fireballs_e: f[0]+=f[2]*8; f[1]+=f[3]*8
            fireballs_p=[f for f in fireballs_p if 0<f[0]<WIDTH]
            fireballs_e=[f for f in fireballs_e if 0<f[0]<WIDTH]

            # Heal orb spawn
            if heal_orb is None and t-last_orb>7000:
                heal_orb=[random.randint(100,WIDTH-150),random.randint(200,HEIGHT-120)]
                last_orb=t

            # Collisions
            for f in fireballs_p[:]:
                if enemy_x < f[0] < enemy_x + 80 and enemy_y < f[1] < enemy_y + 140:
                    e_hp -= 10
                    p_mana = min(100, p_mana + 10)
                    e_mana = min(100, e_mana + 5)
                    fireballs_p.remove(f)
            for f in fireballs_e[:]:
                if player_x < f[0] < player_x + 80 and player_y < f[1] < player_y + 140:
                    p_hp -= 10
                    e_mana = min(100, e_mana + 10)
                    p_mana = min(100, p_mana + 5)
                    fireballs_e.remove(f)
            if heal_orb:
                x,y=heal_orb
                if player_x<x<player_x+100 and player_y<y<player_y+140:
                    p_hp=min(100,p_hp+random.randint(20,30))
                    heal_orb=None
                elif enemy_x<x<enemy_x+100 and enemy_y<y<enemy_y+140:
                    e_hp=min(100,e_hp+random.randint(20,30))
                    heal_orb=None
            
            #apply damage over time
            if t < player_damaged_until:
                #enemy_damage_over_time per second
                p_hp -= (enemy_damage_over_time * dt / 1000)
            if t < enemy_damaged_until:
                e_hp -= (player_damage_over_time * dt / 1000)

            # if player or enemy damage over time ended, reset variables
            if t >= player_damaged_until:
                enemy_damage_over_time = 0
                ult_orb = None
            if t >= enemy_damaged_until:
                player_damage_over_time = 0
                ult_orb_e = None

        # Drawing
        window.fill(DARK_BLUE)
        if p_hp<=0 or e_hp<=0:
            flash=pygame.Surface((WIDTH,HEIGHT)); flash.fill(RED); flash.set_alpha(80)
            window.blit(flash,(0,0))

        if t - round_start_time < 2000:
            label=font.render(f"Round {round_num}!",True,WHITE)
            window.blit(label,(WIDTH//2-label.get_width()//2,HEIGHT//2-50))
            sub=font.render("FIGHT!",True,WHITE)
            window.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//2+10))
        else:
            round_active=True

        for f in fireballs_p: pygame.draw.circle(window,RED,(int(f[0]),int(f[1])),8)
        for f in fireballs_e: pygame.draw.circle(window,GREEN,(int(f[0]),int(f[1])),8)
        if heal_orb: pygame.draw.circle(window,(0,255,0),heal_orb,12)
        if t < player_damaged_until:
            ult_orb = (player_x + 50, player_y + 70)
            pygame.draw.circle(window, (255, 0, 255), ult_orb, 70)
        if t < enemy_damaged_until:
            ult_orb_e = (enemy_x + 50, enemy_y + 70)
            pygame.draw.circle(window, (255, 0, 255), ult_orb_e, 70)
        
        window.blit(player_img,(player_x,player_y))
        window.blit(enemy_img,(enemy_x,enemy_y))

        # HP bars
        pygame.draw.rect(window,RED,(100,50,200,25))
        pygame.draw.rect(window,GREEN,(100,50,2*max(0,p_hp),25))
        pygame.draw.rect(window,RED,(500,50,200,25))
        pygame.draw.rect(window,GREEN,(500,50,2*max(0,e_hp),25))
        window.blit(font.render(f"P1 HP:{int(p_hp)}",True,WHITE),(100,20))
        window.blit(font.render(f"P2 HP:{int(e_hp)}",True,WHITE),(500,20))

        # mana bars (below health)
        pygame.draw.rect(window,(0,0,60),(100,80,200,10))
        pygame.draw.rect(window,(0,100,255),(100,80,2*p_mana,10))
        pygame.draw.rect(window,(0,0,60),(500,80,200,10))
        pygame.draw.rect(window,(0,100,255),(500,80,2*e_mana,10))

        # text when ult ready
        if p_mana >= 100:
            ready = font.render("ULT READY (R)", True, YELLOW)
            window.blit(ready, (100, 95))
        if e_mana >= 100 and mode == "2P":
            ready2 = font.render("ULT READY (R-Shift)", True, YELLOW)
            window.blit(ready2, (500, 95))

        if p_hp<=0 or e_hp<=0:
            result = ("Draw!" if p_hp<=0 and e_hp<=0 else
                      "Player 1 Wins!" if e_hp<=0 else
                      "Player 2 Wins!" if mode=="2P" else "Enemy Wins!")
            STATE = "MENU"
            txt=font.render(result,True,WHITE)
            window.blit(txt,(WIDTH//2-txt.get_width()//2,HEIGHT//2))
            pygame.display.flip()
            pygame.time.delay(2000)
            running=False; return

        pygame.display.flip()

# State manager
while True:
    if STATE == "MENU":
        main_menu()
    elif STATE == "DIFFICULTY":
        diff_menu()
    elif STATE in ["AI", "2P"]:
        show_controls(STATE)  # 👈 this runs the controls screen
        play_game(STATE, difficulty)
        STATE = "MENU"

