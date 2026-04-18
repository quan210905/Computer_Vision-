import cv2
import mediapipe as mp
import pygame
import random
import sys
import os

pygame.init()
pygame.mixer.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("🔥 BẮN MÁY BAY 🔥")
clock = pygame.time.Clock()

WHITE = (255,255,255)
RED = (255,50,50)
GREEN = (50,255,50)
YELLOW = (255,220,0)

font = pygame.font.SysFont("Arial", 28, True)
font_big = pygame.font.SysFont("Arial", 60, True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_img(name, size):
    path = os.path.join(BASE_DIR, "assets", name)
    if not os.path.exists(path):
        print("Thiếu:", path); pygame.quit(); sys.exit()
    return pygame.transform.scale(pygame.image.load(path), size)

def load_sound(name):
    return pygame.mixer.Sound(os.path.join(BASE_DIR, "assets", name))

def load_bg(name):
    path = os.path.join(BASE_DIR, "assets", name)
    if os.path.exists(path):
        return pygame.transform.scale(pygame.image.load(path), (WIDTH, HEIGHT))
    return None

player_img = load_img("player.png",(40,40))
enemy_img = load_img("enemy.png",(40,40))
boss_img = load_img("boss.png",(150,100))
heart_img = load_img("heart.png",(30,30))

bg1 = load_bg("bg1.jpg")
bg2 = load_bg("bg2.jpg")
bg3 = load_bg("bg3.jpg")
BACKGROUNDS = [bg1, bg2, bg3]

shoot_sound = load_sound("shoot.wav")
explosion_sound = load_sound("explosion.wav")

pygame.mixer.music.load(os.path.join(BASE_DIR,"assets","music.mp3"))
pygame.mixer.music.play(-1)

LEVELS = {
    1: {"target":50,"speed":3,"spawn":40,"boss_hp":20},
    2: {"target":100,"speed":4,"spawn":30,"boss_hp":30},
    3: {"target":150,"speed":5,"spawn":25,"boss_hp":222},
}

state = "MENU"

player_x, player_y = WIDTH//2, HEIGHT-100
smooth_x, smooth_y = player_x, player_y

SMOOTHING = 0.6
DEADZONE = 5
PLAYER_SPEED = 16

player_hp = 3

bullets=[]
chickens=[]

boss_active=False
boss_rect=None
boss_hp=0
boss_dir=1

score=0
level_score=0
current_level=1

shoot_delay=0
spawn_timer=0

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
cap = cv2.VideoCapture(0)

running=True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running=False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            if state=="MENU" and e.key==pygame.K_SPACE:
                state="PLAY"
            if e.key==pygame.K_p:
                state = "PAUSE" if state=="PLAY" else "PLAY"
            if e.key==pygame.K_r:
                state="MENU"
                score=0
                current_level=1
                player_hp=3
                level_score=0
                bullets.clear()
                chickens.clear()
                boss_active=False

    # 🔥 FIX BÓNG MỜ
    screen.fill((0,0,0))

    bg = BACKGROUNDS[current_level-1]
    if bg:
        screen.blit(bg,(0,0))

    if state=="MENU":
        screen.blit(font_big.render("PRESS SPACE",True,YELLOW),(WIDTH//2-200,HEIGHT//2))

    elif state=="PLAY":

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]: player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]: player_x += PLAYER_SPEED
        if keys[pygame.K_UP]: player_y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]: player_y += PLAYER_SPEED

        ret, frame = cap.read()
        if ret:
            frame=cv2.flip(frame,1)
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            res=hands.process(rgb)

            if res.multi_hand_landmarks and not any(keys):
                for h in res.multi_hand_landmarks:
                    tx = int(h.landmark[8].x * WIDTH)
                    ty = int(h.landmark[8].y * HEIGHT)

                    if abs(tx - smooth_x) < DEADZONE: tx = smooth_x
                    if abs(ty - smooth_y) < DEADZONE: ty = smooth_y

                    smooth_x += (tx - smooth_x) * SMOOTHING
                    smooth_y += (ty - smooth_y) * SMOOTHING

                    player_x = int(smooth_x)
                    player_y = int(smooth_y)

        player_x=max(0,min(WIDTH-40,player_x))
        player_y=max(0,min(HEIGHT-40,player_y))

        config=LEVELS[current_level]

        # ===== AUTO AIM =====
        shoot_delay += 1
        if shoot_delay > 3:

            target = None
            min_dist = 999999

            for c in chickens:
                dist = (c.x - player_x)**2 + (c.y - player_y)**2
                if dist < min_dist:
                    min_dist = dist
                    target = c

            if boss_active:
                target = boss_rect

            if target:
                dx = target.centerx - player_x
                dy = target.centery - player_y
                length = max(1, (dx**2 + dy**2)**0.5)

                speed = 10
                dx = dx/length * speed
                dy = dy/length * speed
            else:
                dx, dy = 0, -10

            bullets.append({
                "rect": pygame.Rect(player_x+18, player_y, 5, 15),
                "dx": dx,
                "dy": dy
            })

            shoot_sound.play()
            shoot_delay = 0

        # ===== MOVE BULLETS =====
        for b in bullets[:]:
            b["rect"].x += b["dx"]
            b["rect"].y += b["dy"]

            # 🔥 FIX DÍNH HÌNH
            if (b["rect"].y < 0 or b["rect"].y > HEIGHT or
                b["rect"].x < 0 or b["rect"].x > WIDTH):
                bullets.remove(b)

        # ===== SPAWN ENEMY =====
        spawn_timer+=1
        if spawn_timer>config["spawn"] and not boss_active:
            chickens.append(pygame.Rect(random.randint(0, WIDTH-40),-40,40,40))
            spawn_timer=0

        for c in chickens[:]:
            c.y+=config["speed"]
            if c.y>HEIGHT:
                chickens.remove(c)
                player_hp-=1

        # ===== COLLISION =====
        for b in bullets[:]:
            for c in chickens[:]:
                if b["rect"].colliderect(c):
                    explosion_sound.play()
                    chickens.remove(c)
                    bullets.remove(b)
                    score+=10
                    level_score+=10
                    break

        # ===== BOSS =====
        if level_score>=config["target"] and not boss_active:
            boss_active=True
            boss_hp=config["boss_hp"]
            boss_rect=pygame.Rect(WIDTH//2-75,50,150,100)
            chickens.clear()

        if boss_active:
            boss_rect.x+=5*boss_dir
            if boss_rect.left<0 or boss_rect.right>WIDTH:
                boss_dir*=-1

            for b in bullets[:]:
                if b["rect"].colliderect(boss_rect):
                    boss_hp-=1
                    bullets.remove(b)
                    if boss_hp <= 0:
                        boss_active = False
                        level_score = 0
                        if current_level == 3:
                            state = "WIN"
                        else:
                            current_level += 1

        # ===== DRAW =====
        screen.blit(player_img,(player_x,player_y))

        for c in chickens:
            screen.blit(enemy_img,(c.x,c.y))

        for b in bullets:
            pygame.draw.rect(screen,YELLOW,b["rect"])

        if boss_active:
            screen.blit(boss_img,(boss_rect.x,boss_rect.y))

        screen.blit(font.render(f"Score: {score}",True,WHITE),(20,20))

    pygame.display.flip()
    clock.tick(90)

cap.release()
pygame.quit()
sys.exit()