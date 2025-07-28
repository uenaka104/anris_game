
import pygame
import sys
import random
import math
import os

# ゲームの定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BOSS_SPAWN_COUNT = 10
BOSS_SPAWN_TIME = 10
BOSS_ACTIVE_HEIGHT = SCREEN_HEIGHT // 3

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# ベースとなるゲーム設定値
BASE_MAX_ENEMIES_ON_SCREEN = 10
BASE_ENEMY_BULLET_SPEED = 5
BASE_ENEMY_SHOOT_DELAY_MIN = 300
BASE_ENEMY_SHOOT_DELAY_MAX = 1500
BASE_BOSS_HEALTH = 200
BASE_BOSS_RADIAL_ATTACK_INTERVAL = 5000

# ステージごとの設定
STAGE_SETTINGS = {
    1: {
        "max_enemies_on_screen": int(BASE_MAX_ENEMIES_ON_SCREEN * 0.2),
        "enemy_bullet_speed": int(BASE_ENEMY_BULLET_SPEED * 1.0),
        "enemy_shoot_delay_min": int(BASE_ENEMY_SHOOT_DELAY_MIN * 2.0),
        "enemy_shoot_delay_max": int(BASE_ENEMY_SHOOT_DELAY_MAX * 2.0),
        "boss_health": int(BASE_BOSS_HEALTH * 0.2),
        "boss_radial_attack_interval": int(BASE_BOSS_RADIAL_ATTACK_INTERVAL * 1.0),
    },
    2: {
        "max_enemies_on_screen": int(BASE_MAX_ENEMIES_ON_SCREEN * 0.4),
        "enemy_bullet_speed": int(BASE_ENEMY_BULLET_SPEED * 0.4),
        "enemy_shoot_delay_min": int(BASE_ENEMY_SHOOT_DELAY_MIN * 1.5),
        "enemy_shoot_delay_max": int(BASE_ENEMY_SHOOT_DELAY_MAX * 1.5),
        "boss_health": int(BASE_BOSS_HEALTH * 0.4),
        "boss_radial_attack_interval": int(BASE_BOSS_RADIAL_ATTACK_INTERVAL * 0.8),
    }
}

# アセットのパス設定
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
img_dir = os.path.join(assets_dir, "img")
sound_dir = os.path.join(assets_dir, "sound")

# プレイヤーのクラス
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join(img_dir, "player.png")).convert()
        self.original_image = pygame.transform.scale(self.original_image, (int(self.original_image.get_width() * 0.3), int(self.original_image.get_height() * 0.3)))
        self.original_image.set_colorkey(BLACK)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed_x = 0
        self.speed_y = 0
        self.health = 3
        self.max_health = 3
        self.blinking = False
        self.blink_timer = 0
        self.blink_count = 0
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1500 # 1.5秒無敵
        self.blink_interval = 100 # 点滅間隔
        self.total_blinks = 6 # 3回点滅 (表示/非表示で2回1セット)

    def update(self):
        self.speed_x = 0
        self.speed_y = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speed_x = -5
        if keystate[pygame.K_RIGHT]:
            self.speed_x = 5
        if keystate[pygame.K_UP]:
            self.speed_y = -5
        if keystate[pygame.K_DOWN]:
            self.speed_y = 5

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        # 点滅処理
        if self.blinking:
            now = pygame.time.get_ticks()
            if now - self.blink_timer > self.blink_interval:
                self.blink_timer = now
                self.blink_count += 1
                if self.blink_count % 2 == 0:
                    self.image = self.original_image.copy()
                else:
                    self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)

                if self.blink_count >= self.total_blinks:
                    self.blinking = False
                    self.blink_count = 0
                    self.image = self.original_image.copy()

        # 無敵時間処理
        if self.invincible:
            now = pygame.time.get_ticks()
            if now - self.invincible_timer > self.invincible_duration:
                self.invincible = False

    def shoot(self):
        bullet = PlayerBullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        player_bullets.add(bullet)
        shoot_sound.play()

    def hit(self):
        if not self.invincible:
            self.health -= 1
            self.blinking = True
            self.blink_timer = pygame.time.get_ticks()
            self.blink_count = 0
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()

# プレイヤーの弾のクラス
class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 10])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_y = -10

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()

# 敵の弾のクラス
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_x=0, speed_y=5):
        super().__init__()
        self.image = pygame.Surface([4, 8])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed_x = speed_x
        self.speed_y = speed_y

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()

# 誘導弾のクラス
class HomingBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_sprite, speed=5, turn_speed=0.05, homing_duration=1000):
        super().__init__()
        self.image = pygame.Surface([6, 12]) # 少し大きめの誘導弾
        self.image.fill(PURPLE) # 誘導弾の色
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = speed
        self.turn_speed = turn_speed
        self.target_sprite = target_sprite
        self.velocity = pygame.math.Vector2(0, self.speed) # 初期速度は下向き
        self.homing_duration = homing_duration # 誘導時間（ミリ秒）
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time < self.homing_duration and self.target_sprite.alive(): # 誘導時間内かつターゲットが存在する場合のみ追尾
            target_vector = pygame.math.Vector2(self.target_sprite.rect.center)
            bullet_vector = pygame.math.Vector2(self.rect.center)
            direction_to_target = (target_vector - bullet_vector).normalize()

            # 緩やかに方向転換
            self.velocity = self.velocity.lerp(direction_to_target * self.speed, self.turn_speed)
            self.velocity.normalize_ip() # 速度を一定に保つ
            self.velocity *= self.speed

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()

# 敵のクラス
class Enemy(pygame.sprite.Sprite):
    def __init__(self, initial_speed_y, initial_speed_x, bullet_speed, shoot_delay_min, shoot_delay_max):
        super().__init__()
        original_image = pygame.image.load(os.path.join(img_dir, "enemy.png")).convert()
        self.image = pygame.transform.scale(original_image, (original_image.get_width() // 2, original_image.get_height() // 2))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.initial_speed_y = initial_speed_y
        self.initial_speed_x = initial_speed_x
        self.bullet_speed = bullet_speed
        self.shoot_delay_min = shoot_delay_min
        self.shoot_delay_max = shoot_delay_max
        self.reset()
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = random.randrange(self.shoot_delay_min, self.shoot_delay_max + 1)

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.speed_x *= -1

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.shoot_delay:
            self.shoot()
            self.last_shot_time = current_time
            self.shoot_delay = random.randrange(self.shoot_delay_min, self.shoot_delay_max + 1)

        if self.rect.top > SCREEN_HEIGHT + 10:
            self.reset()

    def reset(self):
        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-200, -100)
        self.speed_y = self.initial_speed_y
        self.speed_x = self.initial_speed_x
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_delay = random.randrange(self.shoot_delay_min, self.shoot_delay_max + 1)

    def shoot(self):
        enemy_bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, speed_y=self.bullet_speed)
        all_sprites.add(enemy_bullet)
        enemy_bullets.add(enemy_bullet)

# ボスのクラス
class Boss(pygame.sprite.Sprite):
    def __init__(self, initial_health, radial_attack_interval):
        super().__init__()
        self.image = pygame.image.load(os.path.join(img_dir, "boss.png")).convert()
        self.image.set_colorkey(BLACK)
        temp_rect = self.image.get_rect() # まず画像と同じサイズのrectを取得
        
        # 当たり判定のサイズを画像より小さくする (例: 幅を80%、高さを80%に)
        new_width = int(temp_rect.width * 0.8)
        new_height = int(temp_rect.height * 0.8)
        
        # 新しいサイズのrectを作成し、元のrectの中心を維持
        self.rect = pygame.Rect(0, 0, new_width, new_height)
        self.rect.center = temp_rect.center # ここで中心を合わせる
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = -150
        self.speed_y = 1
        self.speed_x = 0
        self.health = initial_health
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_interval = 500
        self.active_y_pos = 50
        self.radial_attack_interval = radial_attack_interval
        self.last_radial_attack_time = pygame.time.get_ticks()
        self.homing_attack_active = False
        self.homing_attack_start_time = 0
        self.homing_attack_duration = 2000 # 2秒間誘導弾を発射
        self.homing_bullet_interval = 3000 # 3秒ごとに誘導弾を発射
        self.last_homing_bullet_time = 0

    def update(self):
        if self.rect.y < self.active_y_pos:
            self.rect.y += self.speed_y
        else:
            # ボスの体力が半分以下になったら誘導弾モードをアクティブにする
            if self.health <= BASE_BOSS_HEALTH // 2 and not self.homing_attack_active:
                self.homing_attack_active = True
                self.homing_attack_start_time = pygame.time.get_ticks()

            # 誘導弾モード中の処理
            if self.homing_attack_active:
                current_time = pygame.time.get_ticks()
                if current_time - self.homing_attack_start_time < self.homing_attack_duration:
                    if current_time - self.last_homing_bullet_time > self.homing_bullet_interval:
                        self.shoot_homing_bullet()
                        self.last_homing_bullet_time = current_time
                else:
                    self.homing_attack_active = False # 誘導弾モード終了

            self.rect.x += self.speed_x
            self.rect.y += self.speed_y

            if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.speed_x *= -1
            if self.rect.top < self.active_y_pos or self.rect.bottom > self.active_y_pos + BOSS_ACTIVE_HEIGHT:
                self.speed_y *= -1

            if random.random() < 0.005:
                self.speed_x = random.choice([-1, 1]) * random.randrange(1, 3)
                self.speed_y = random.choice([-1, 1]) * random.randrange(1, 3)

            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time > self.shoot_interval:
                self.shoot()
                self.last_shot_time = current_time
                self.shoot_interval = random.randrange(250, 1000)

            if current_time - self.last_radial_attack_time > self.radial_attack_interval:
                self.shoot_radial()
                self.last_radial_attack_time = current_time

    def shoot(self):
        enemy_bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
        all_sprites.add(enemy_bullet)
        enemy_bullets.add(enemy_bullet)

    def shoot_radial(self):
        num_bullets = 12
        bullet_speed = 5
        for i in range(num_bullets):
            angle = 2 * math.pi * i / num_bullets
            speed_x = bullet_speed * math.cos(angle)
            speed_y = bullet_speed * math.sin(angle)
            bullet = EnemyBullet(self.rect.centerx + int(speed_x * 10), self.rect.centery + int(speed_y * 10), speed_x, speed_y)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

    def shoot_homing_bullet(self):
        homing_bullet = HomingBullet(self.rect.centerx, self.rect.bottom, player) # プレイヤーをターゲット
        all_sprites.add(homing_bullet)
        enemy_bullets.add(homing_bullet)

# 爆発のクラス
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = explosion_anim[0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosion_anim[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

# ゲームの初期化
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("シューティングゲーム")
clock = pygame.time.Clock()

# フォントの準備
font = pygame.font.Font(None, 74)
score_font = pygame.font.Font(None, 36)

# 画像の読み込み
player_img = pygame.image.load(os.path.join(img_dir, "player.png")).convert()
enemy_img = pygame.image.load(os.path.join(img_dir, "enemy.png")).convert()
boss_img = pygame.image.load(os.path.join(img_dir, "boss.png")).convert()

# プレイヤー体力ゲージ用アイコン
player_health_icon = pygame.transform.scale(player_img, (player_img.get_width() // 4, player_img.get_height() // 4))
explosion_anim = []
for i in range(9):
    filename = 'regularExplosion0{}.png'.format(i)
    img = pygame.image.load(os.path.join(img_dir, filename)).convert()
    img = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
    img.set_colorkey(BLACK)
    explosion_anim.append(img)

# サウンドの読み込み
shoot_sound = pygame.mixer.Sound(os.path.join(sound_dir, "shoot.wav"))
shoot_sound.set_volume(1.0) # 最大音量に設定
expl_sound_enemy_defeat = pygame.mixer.Sound(os.path.join(sound_dir, "expl3.wav"))
expl_sound_enemy_defeat.set_volume(0.25) # 敵撃破音の音量をさらに50%下げる
expl_sound_boss_defeat = pygame.mixer.Sound(os.path.join(sound_dir, "expl6.wav"))
expl_sound_boss_defeat.set_volume(1.0) # ボス撃破音の音量は最大に維持
expl_sounds = [expl_sound_enemy_defeat, expl_sound_boss_defeat]
game_over_sound = pygame.mixer.Sound(os.path.join(sound_dir, "game_over.wav")) # ゲームオーバーサウンドを追加
game_over_sound.set_volume(1.0) # 最大音量に設定
pygame.mixer.music.load(os.path.join(sound_dir, "tgfcoder-FrozenJam-SeamlessLoop.ogg"))
pygame.mixer.music.set_volume(0.4)

# スプライトグループ
all_sprites = pygame.sprite.Group()
players = pygame.sprite.Group()
enemies = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
bosses = pygame.sprite.Group()
explosions = pygame.sprite.Group()

# ゲーム変数
enemies_defeated = 0
current_boss = None
score = 0
boss_spawn_timer = pygame.time.get_ticks()
game_state = "playing"
current_stage = 1
current_stage_settings = STAGE_SETTINGS[current_stage]
game_over_sound_played = False # ゲームオーバーサウンド再生フラグ

# 初期敵の生成
for i in range(current_stage_settings["max_enemies_on_screen"]):
    enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
    all_sprites.add(enemy)
    enemies.add(enemy)

# プレイヤーの作成
player = Player()
all_sprites.add(player)
players.add(player)

# BGMの再生
pygame.mixer.music.play(loops=-1)

# ゲームループ
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "playing":
                if event.key == pygame.K_SPACE:
                    player.shoot()
            elif game_state == "stage_cleared":
                if event.key == pygame.K_SPACE:
                    current_stage += 1
                    current_stage_settings = STAGE_SETTINGS[current_stage]
                    all_sprites.empty()
                    enemies.empty()
                    player_bullets.empty()
                    enemy_bullets.empty()
                    bosses.empty()
                    player = Player()
                    all_sprites.add(player)
                    players.add(player)
                    for i in range(current_stage_settings["max_enemies_on_screen"]):
                        enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                    enemies_defeated = 0
                    current_boss = None
                    boss_spawn_timer = pygame.time.get_ticks()
                    game_state = "playing"
            elif game_state == "game_over":
                if event.key == pygame.K_SPACE:
                    # ゲームをステージ1からリスタート
                    all_sprites.empty()
                    enemies.empty()
                    player_bullets.empty()
                    enemy_bullets.empty()
                    bosses.empty()
                    explosions.empty() # 爆発スプライトもクリア

                    player = Player()
                    all_sprites.add(player)
                    players.add(player)

                    enemies_defeated = 0
                    current_boss = None
                    score = 0
                    boss_spawn_timer = pygame.time.get_ticks()
                    game_state = "playing"
                    current_stage = 1 # ステージを1にリセット
                    current_stage_settings = STAGE_SETTINGS[current_stage]

                    # 初期敵の再生成
                    for i in range(current_stage_settings["max_enemies_on_screen"]):
                        enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
                        all_sprites.add(enemy)
                        enemies.add(enemy)

                    pygame.mixer.music.play(loops=-1) # BGMを再開
                    game_over_sound_played = False # フラグをリセット

    # 更新
    if game_state == "playing" or game_state == "exploding":
        all_sprites.update()
        if game_state == "exploding" and not explosions:
            game_state = "game_over"

    if game_state == "playing":
        current_time = pygame.time.get_ticks()
        if current_time - boss_spawn_timer >= BOSS_SPAWN_TIME * 1000 and current_boss is None:
            for enemy in enemies:
                enemy.kill()
            current_boss = Boss(current_stage_settings["boss_health"], current_stage_settings["boss_radial_attack_interval"])
            all_sprites.add(current_boss)
            bosses.add(current_boss)

        hits = pygame.sprite.groupcollide(enemies, player_bullets, True, True)
        for hit in hits:
            enemies_defeated += 1
            score += 10
            expl_sounds[0].play() # 敵撃破時にexpl3.wavを再生
            # 敵の数が最大出現数未満の場合のみ新しい敵を生成
            if len(enemies) < current_stage_settings["max_enemies_on_screen"]:
                enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
                all_sprites.add(enemy)
                enemies.add(enemy)

        if current_boss:
            boss_hits = pygame.sprite.spritecollide(current_boss, player_bullets, True)
            for hit_bullet in boss_hits:
                current_boss.health -= 1
                if current_boss.health <= 0:
                    score += 1000
                    current_boss.kill()
                    current_boss = None
                    game_state = "stage_cleared"
                    expl_sounds[1].play() # ボス撃破時にexpl6.wavを再生

        hits = pygame.sprite.groupcollide(players, enemies, False, True)
        if hits:
            for p in players:
                p.hit()
                if p.health <= 0:
                    expl = Explosion(p.rect.center)
                    all_sprites.add(expl)
                    explosions.add(expl)
                    p.kill()
                    pygame.mixer.music.stop()
                    expl_sounds[0].play() # プレイヤー撃破時にexpl3.wavを再生
                    game_state = "exploding"

        hits = pygame.sprite.groupcollide(players, enemy_bullets, False, True)
        if hits:
            for p in players:
                p.hit()
                if p.health <= 0:
                    expl = Explosion(p.rect.center)
                    all_sprites.add(expl)
                    explosions.add(expl)
                    p.kill()
                    pygame.mixer.music.stop()
                    expl_sounds[0].play() # プレイヤー撃破時にexpl3.wavを再生
                    game_state = "exploding"

        if current_boss and pygame.sprite.spritecollideany(player, bosses):
            for p in players:
                p.hit()
                if p.health <= 0:
                    expl = Explosion(p.rect.center)
                    all_sprites.add(expl)
                    explosions.add(expl)
                    p.kill()
                    pygame.mixer.music.stop()
                    expl_sounds[0].play() # プレイヤー撃破時にexpl3.wavを再生
                    game_state = "exploding"

    # 描画
    screen.fill(BLACK)
    all_sprites.draw(screen)

    if game_state == "playing":
        score_text = score_font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        if current_boss:
            # ボスの体力表示は削除済み
            pass

        # プレイヤー体力ゲージの描画
        health_icon_x_start = SCREEN_WIDTH - (player.max_health * (player_health_icon.get_width() + 5)) - 10 # 右端からアイコンの幅+間隔で配置
        health_icon_y = SCREEN_HEIGHT - player_health_icon.get_height() - 10 # 下端からアイコンの高さ+間隔で配置

        for i in range(player.max_health):
            if i < player.health:
                screen.blit(player_health_icon, (health_icon_x_start + i * (player_health_icon.get_width() + 5), health_icon_y))

    elif game_state == "stage_cleared":
        clear_text = font.render("STAGE CLEAR!", True, GREEN)
        clear_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(clear_text, clear_rect)
        next_stage_text = score_font.render("Press SPACE for Next Stage", True, WHITE)
        next_stage_rect = next_stage_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(next_stage_text, next_stage_rect)

    elif game_state == "game_over":
        game_over_text = font.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(game_over_text, text_rect)

        retry_text = score_font.render("PRESS SPACE TO RETRY", True, WHITE)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(retry_text, retry_rect)

        if not game_over_sound_played:
            game_over_sound.play()
            game_over_sound_played = True

    pygame.display.flip()

    

pygame.quit()
sys.exit()
