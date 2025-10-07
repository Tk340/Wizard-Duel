import pygame, random, sys
pygame.init()

# === Window ===
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard Duel - Main Menu")

# === Colors ===
DARK_BLUE = (25, 25, 60)
RED = (255, 60, 60)
GREEN = (0, 255, 100)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# === Assets ===
player_img = pygame.transform.scale(pygame.image.load("wizard_duel/assets/wizard_player.png").convert_alpha(), (100,140))
enemy_img  = pygame.transform.scale(pygame.image.load("wizard_duel/assets/wizard_enemy.png").convert_alpha(), (100,140))
enemy_img  = pygame.transform.flip(enemy_img, True, False)

font_big = pygame.font.Font(None, 72)
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

STATE = "MENU"
difficulty = "MEDIUM"
mode = "AI"

# === Difficulty presets ===
DIFF = {
    "EASY":   {"enemy_speed":2, "enemy_cd":1500},
    "MEDIUM": {"enemy_speed":3, "enemy_cd":1000},
    "HARD":   {"enemy_speed":4, "enemy_cd":700},
}

# === UI helpers ===
def draw_button(text,y,active=False):
    color = YELLOW if active else WHITE
    label = font.render(text,True,color)
    rect  = label.get_rect(center=(WIDTH//2,y))
    window.blit(label,rect)
    return rect

# === Menus ===
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

# === Game logic ===
def play_game(mode,difficulty):
    from math import sqrt
    player_x,player_y=150,400
    enemy_x,enemy_y=600,400
    p_hp,e_hp=100,100
    fireballs_p=[];fireballs_e=[]
    heal_orb=None; last_orb=0
    ORB_CD=7000
    last_p_shot=0; last_e_shot=0
    FIRE_CD=500
    e_cd=DIFF[difficulty]["enemy_cd"]; e_speed=DIFF[difficulty]["enemy_speed"]
    clock.tick(0)
    running=True
    while running:
        dt=clock.tick(60)
        t=pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                running=False; return
        keys=pygame.key.get_pressed()

        # === Player 1 (WASD) ===
        dx=dy=0
        if keys[pygame.K_a]: dx=-1
        if keys[pygame.K_d]: dx=1
        if keys[pygame.K_w]: dy=-1
        if keys[pygame.K_s]: dy=1
        mag=(dx**2+dy**2)**0.5
        if mag: dx/=mag; dy/=mag
        player_x+=dx*5; player_y+=dy*5
        player_x=max(0,min(player_x,WIDTH-100))
        player_y=max(0,min(player_y,HEIGHT-140))

        # === Player 2 / AI ===
        if mode=="2P":
            dx2=dy2=0
            if keys[pygame.K_LEFT]: dx2=-1
            if keys[pygame.K_RIGHT]: dx2=1
            if keys[pygame.K_UP]: dy2=-1
            if keys[pygame.K_DOWN]: dy2=1
            mag2=(dx2**2+dy2**2)**0.5
            if mag2: dx2/=mag2; dy2/=mag2
            enemy_x+=dx2*5; enemy_y+=dy2*5
            enemy_x=max(0,min(enemy_x,WIDTH-100))
            enemy_y=max(0,min(enemy_y,HEIGHT-140))
            # shoot
            if keys[pygame.K_RETURN] and t-last_e_shot>600:
                fireballs_e.append([enemy_x+30,enemy_y+60,-1,0])
                last_e_shot=t
        else:
            # simple chase AI
            dx=player_x-enemy_x; dy=player_y-enemy_y
            dist=max(1,sqrt(dx*dx+dy*dy))
            enemy_x+=dx/dist*e_speed; enemy_y+=dy/dist*e_speed
            if t-last_e_shot>e_cd:
                fireballs_e.append([enemy_x,enemy_y+60,dx/dist,dy/dist])
                last_e_shot=t

        # === Player1 shoot ===
        if keys[pygame.K_SPACE] and t-last_p_shot>FIRE_CD:
            fireballs_p.append([player_x+80,player_y+60,1,0])
            last_p_shot=t

        # === Move projectiles ===
        for f in fireballs_p: f[0]+=f[2]*8; f[1]+=f[3]*8
        for f in fireballs_e: f[0]+=f[2]*8; f[1]+=f[3]*8
        fireballs_p=[f for f in fireballs_p if 0<f[0]<WIDTH and 0<f[1]<HEIGHT]
        fireballs_e=[f for f in fireballs_e if 0<f[0]<WIDTH and 0<f[1]<HEIGHT]

        # === Spawn heal orb ===
        if heal_orb is None and t-last_orb>ORB_CD:
            heal_orb=[random.randint(100,WIDTH-150),random.randint(200,HEIGHT-120)]
            last_orb=t

        # === Collisions ===
        for f in fireballs_p[:]:
            if enemy_x<f[0]<enemy_x+80 and enemy_y<f[1]<enemy_y+140:
                e_hp-=10; fireballs_p.remove(f)
        for f in fireballs_e[:]:
            if player_x<f[0]<player_x+80 and player_y<f[1]<player_y+140:
                p_hp-=10; fireballs_e.remove(f)
        if heal_orb:
            x,y=heal_orb
            if player_x<x<player_x+100 and player_y<y<player_y+140:
                p_hp=min(100,p_hp+random.randint(20,30))
                heal_orb=None
            elif mode=="2P" and enemy_x<x<enemy_x+100 and enemy_y<y<enemy_y+140:
                e_hp=min(100,e_hp+random.randint(20,30))
                heal_orb=None

        # === Draw ===
        window.fill(DARK_BLUE)
        window.blit(player_img,(player_x,player_y))
        window.blit(enemy_img,(enemy_x,enemy_y))
        for f in fireballs_p: pygame.draw.circle(window,RED,(int(f[0]),int(f[1])),8)
        for f in fireballs_e: pygame.draw.circle(window,GREEN,(int(f[0]),int(f[1])),8)
        if heal_orb: pygame.draw.circle(window,(0,255,0),heal_orb,12)

        # hp bars
        pygame.draw.rect(window,RED,(100,50,200,25))
        pygame.draw.rect(window,GREEN,(100,50,2*max(0,p_hp),25))
        pygame.draw.rect(window,RED,(500,50,200,25))
        pygame.draw.rect(window,GREEN,(500,50,2*max(0,e_hp),25))
        window.blit(font.render(f"P1 HP:{p_hp}",True,WHITE),(100,20))
        window.blit(font.render(f"P2 HP:{e_hp}",True,WHITE),(500,20))

        if p_hp<=0 or e_hp<=0:
            res="P1 Wins!" if e_hp<=0 else "P2 Wins!" if mode=="2P" else ("You Win!" if e_hp<=0 else "You Lose!")
            txt=font.render(res+"  (ESC to return)",True,WHITE)
            window.blit(txt,(WIDTH//2-txt.get_width()//2,HEIGHT//2))
        pygame.display.flip()

# === State manager ===
while True:
    if STATE=="MENU": main_menu()
    elif STATE=="DIFFICULTY": diff_menu()
    elif STATE in ["AI","2P"]:
        play_game(STATE,difficulty)
        STATE="MENU"
