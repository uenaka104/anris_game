
import pygame
import sys
import random
import math
import os
import json # jsonモジュールを追加

# ベストスコアファイルパス
best_score_file = os.path.join(os.path.dirname(__file__), "assets", "data", "best_score.json")

def load_best_score():
    if os.path.exists(best_score_file):
        with open(best_score_file, "r") as f:
            return json.load(f)
    return 0

def save_best_score(score):
    # assets/data ディレクトリが存在しない場合は作成
    data_dir = os.path.dirname(best_score_file)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    with open(best_score_file, "w") as f:
        json.dump(score, f)

# ゲームの定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BOSS_SPAWN_COUNT = 10
BOSS_SPAWN_TIME = 20
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
        "background_imgs": ["background_stage1_a.png", "background_stage1_b.png"], # ステージ1の背景
    },
    2: {
        "max_enemies_on_screen": int(BASE_MAX_ENEMIES_ON_SCREEN * 0.4),
        "enemy_bullet_speed": int(BASE_ENEMY_BULLET_SPEED * 0.4),
        "enemy_shoot_delay_min": int(BASE_ENEMY_SHOOT_DELAY_MIN * 1.5),
        "enemy_shoot_delay_max": int(BASE_ENEMY_SHOOT_DELAY_MAX * 1.5),
        "boss_health": int(BASE_BOSS_HEALTH * 0.4),
        "boss_radial_attack_interval": int(BASE_BOSS_RADIAL_ATTACK_INTERVAL * 0.8),
        "background_imgs": ["background_stage2_a.png", "background_stage2_b.png"], # ステージ2の背景
    },
    3: {
        "max_enemies_on_screen": int(BASE_MAX_ENEMIES_ON_SCREEN * 0.6),
        "enemy_bullet_speed": int(BASE_ENEMY_BULLET_SPEED * 1.2),
        "enemy_shoot_delay_min": int(BASE_ENEMY_SHOOT_DELAY_MIN * 1.0),
        "enemy_shoot_delay_max": int(BASE_ENEMY_SHOOT_DELAY_MAX * 1.0),
        "boss_health": int(BASE_BOSS_HEALTH * 0.7),
        "boss_radial_attack_interval": int(BASE_BOSS_RADIAL_ATTACK_INTERVAL * 0.6),
        "background_imgs": ["background_stage3_a.png", "background_stage3_b.png"], # ステージ3の背景
    },
    4: {
        "max_enemies_on_screen": int(BASE_MAX_ENEMIES_ON_SCREEN * 1.0),
        "enemy_bullet_speed": int(BASE_ENEMY_BULLET_SPEED * 1.5),
        "enemy_shoot_delay_min": int(BASE_ENEMY_SHOOT_DELAY_MIN * 0.8),
        "enemy_shoot_delay_max": int(BASE_ENEMY_SHOOT_DELAY_MAX * 0.8),
        "boss_health": int(BASE_BOSS_HEALTH * 1.0),
        "boss_radial_attack_interval": int(BASE_BOSS_RADIAL_ATTACK_INTERVAL * 0.5),
        "background_imgs": ["background_stage4_a.png", "background_stage4_b.png"], # ステージ4の背景
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
        self.max_health = 6
        self.blinking = False
        self.blink_timer = 0
        self.blink_count = 0
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1500 # 1.5秒無敵
        self.blink_interval = 100 # 点滅間隔
        self.total_blinks = 6 # 3回点滅 (表示/非表示で2回1セット)
        self.shoot_delay = 250 # プレイヤーの初期連射間隔（ミリ秒）
        self.last_shot_time = pygame.time.get_ticks()
        self.rapid_fire_active = False
        self.rapid_fire_delay = 100 # 連射強化時の連射間隔
        self.spread_shot_active = False
        self.triple_shot_active = False # 三方向攻撃弾
        self.homing_missile_active = False # 追尾ミサイル
        self.shield_active = False
        self.shield_start_time = 0
        self.shield_duration = 10000 # 10秒間シールド

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

        # 連射強化時間処理
        # if self.rapid_fire_active:
        #     now = pygame.time.get_ticks()
        #     if now - self.rapid_fire_start_time > self.rapid_fire_duration:
        #         self.rapid_fire_active = False

        # 拡散ショット時間処理
        # if self.spread_shot_active:
        #     now = pygame.time.get_ticks()
        #     if now - self.spread_shot_start_time > self.spread_shot_duration:
        #         self.spread_shot_active = False

        # シールド時間処理
        if self.shield_active:
            now = pygame.time.get_ticks()
            if now - self.shield_start_time > self.shield_duration:
                self.shield_active = False

    def shoot(self):
        now = pygame.time.get_ticks()
        current_shoot_delay = self.rapid_fire_delay if self.rapid_fire_active else self.shoot_delay
        if now - self.last_shot_time > current_shoot_delay:
            bullets_to_add = []
            bullet_speed = 10 # プレイヤー弾の共通速度

            # 基本の弾（常に発射されるか、他のパワーアップで上書きされる）
            # 拡散ショットが有効な場合は、3発の直進弾
            if self.spread_shot_active:
                bullets_to_add.append(PlayerBullet(self.rect.centerx - 15, self.rect.top, speed_x=0, speed_y=-bullet_speed))
                bullets_to_add.append(PlayerBullet(self.rect.centerx, self.rect.top, speed_x=0, speed_y=-bullet_speed))
                bullets_to_add.append(PlayerBullet(self.rect.centerx + 15, self.rect.top, speed_x=0, speed_y=-bullet_speed))
            else: # 拡散ショットが有効でない場合、単発弾が基本
                bullets_to_add.append(PlayerBullet(self.rect.centerx, self.rect.top, speed_x=0, speed_y=-bullet_speed))

            # 三方向攻撃弾が有効な場合、斜め弾を追加
            if self.triple_shot_active:
                # 左斜め45度の弾
                angle_left = math.radians(-45) # -45度
                speed_x_left = bullet_speed * math.sin(angle_left)
                speed_y_left = -bullet_speed * math.cos(angle_left)
                bullets_to_add.append(PlayerBullet(self.rect.centerx - 15, self.rect.top, speed_x=speed_x_left, speed_y=speed_y_left))
                # 右斜め45度の弾
                angle_right = math.radians(45) # 45度
                speed_x_right = bullet_speed * math.sin(angle_right)
                speed_y_right = -bullet_speed * math.cos(angle_right)
                bullets_to_add.append(PlayerBullet(self.rect.centerx + 15, self.rect.top, speed_x=speed_x_right, speed_y=speed_y_right))

            # 収集した弾をスプライトグループに追加
            for bullet in bullets_to_add:
                all_sprites.add(bullet)
                player_bullets.add(bullet)

            # 追尾ミサイル（通常弾とは独立して発射）
            if self.homing_missile_active:
                missile = PlayerHomingMissile(self.rect.centerx, self.rect.top, enemies, bosses) # 敵グループとボスグループをターゲット
                all_sprites.add(missile)
                player_bullets.add(missile) # プレイヤーの弾グループに追加

            shoot_sound.play()
            self.last_shot_time = now

    def hit(self):
        if not self.invincible:
            self.health -= 1
            self.blinking = True
            self.blink_timer = pygame.time.get_ticks()
            self.blink_count = 0
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            self.rapid_fire_active = False # 被弾で連射強化解除
            self.spread_shot_active = False # 被弾で拡散ショット解除
            self.triple_shot_active = False # 被弾で三方向攻撃解除
            self.homing_missile_active = False # 被弾で追尾ミサイル解除

    def activate_shield(self):
        self.shield_active = True
        self.shield_start_time = pygame.time.get_ticks()
        shield_sprite = Shield(self)
        all_sprites.add(shield_sprite)
        shields.add(shield_sprite)

# プレイヤーの弾のクラス
class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_x=0, speed_y=-10):
        super().__init__()
        self.image = pygame.Surface([5, 10])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_x = speed_x
        self.speed_y = speed_y

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
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
        self.out_of_bounds_time = None # 画面外に出た時刻
        self.lifetime_after_out_of_bounds = 1000 # 画面外に出てから消えるまでの時間（ミリ秒）

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            if self.out_of_bounds_time is None:
                self.out_of_bounds_time = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - self.out_of_bounds_time > self.lifetime_after_out_of_bounds:
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
        self.out_of_bounds_time = None # 画面外に出た時刻
        self.lifetime_after_out_of_bounds = 1000 # 画面外に出てから消えるまでの時間（ミリ秒）

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
            if self.out_of_bounds_time is None:
                self.out_of_bounds_time = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - self.out_of_bounds_time > self.lifetime_after_out_of_bounds:
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

            if self.rect.left < 0:
                self.rect.left = 0
                self.speed_x = abs(self.speed_x) # 必ず右に動くようにする
            elif self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                self.speed_x = -abs(self.speed_x) # 必ず左に動くようにする

            if self.rect.top < self.active_y_pos:
                self.rect.top = self.active_y_pos
                self.speed_y = abs(self.speed_y) # 必ず下に動くようにする
            elif self.rect.bottom > self.active_y_pos + BOSS_ACTIVE_HEIGHT:
                self.rect.bottom = self.active_y_pos + BOSS_ACTIVE_HEIGHT
                self.speed_y = -abs(self.speed_y) # 必ず上に動くようにする

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

# パワーアップアイテムのクラス
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, center, type):
        super().__init__()
        self.type = type
        if self.type == "rapid_fire":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_rapid.png")).convert()
        elif self.type == "spread_shot":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_spread.png")).convert()
        elif self.type == "shield":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_shield.png")).convert()
        elif self.type == "health":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_health.png")).convert()
        elif self.type == "triple_shot":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_triple.png")).convert()
        elif self.type == "homing_missile":
            self.image = pygame.image.load(os.path.join(img_dir, "powerup_homing.png")).convert()
        
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speed_y = 2 # アイテムの落下速度

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# プレイヤー追尾ミサイルのクラス
class PlayerHomingMissile(pygame.sprite.Sprite):
    def __init__(self, x, y, enemies_group, bosses_group, speed=7, turn_speed=0.1, homing_duration=1000):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join(img_dir, "player_homing_missile.png")).convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (5, 20)) # サイズ調整
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed
        self.turn_speed = turn_speed
        self.enemies_group = enemies_group # 敵グループ
        self.bosses_group = bosses_group # ボスグループ
        self.target = None
        self.velocity = pygame.math.Vector2(0, -self.speed) # 初期速度は上向き
        self.homing_duration = homing_duration # 追尾時間（ミリ秒）
        self.spawn_time = pygame.time.get_ticks() # 生成時刻

    def update(self):
        current_time = pygame.time.get_ticks()

        # 追尾時間内かつターゲットが存在する場合のみ追尾
        if current_time - self.spawn_time < self.homing_duration and (self.target is None or self.target.alive()):
            # 最も近いターゲット（ボス優先）を探す
            if self.target is None or not self.target.alive():
                self.target = None # ターゲットをリセット
                
                # ボスが存在すればボスをターゲットにする
                if self.bosses_group:
                    for boss in self.bosses_group:
                        self.target = boss
                        break # ボスは通常1体なので最初に見つけたボスをターゲット

                # ボスがいない場合、またはボスがターゲットにならなかった場合、通常の敵をターゲットにする
                if self.target is None:
                    min_dist = float('inf')
                    closest_enemy = None
                    for enemy in self.enemies_group:
                        dist = pygame.math.Vector2(self.rect.center).distance_to(enemy.rect.center)
                        if dist < min_dist:
                            min_dist = dist
                            closest_enemy = enemy
                    self.target = closest_enemy

            if self.target:
                target_vector = pygame.math.Vector2(self.target.rect.center)
                missile_vector = pygame.math.Vector2(self.rect.center)
                direction_to_target = (target_vector - missile_vector).normalize()

                self.velocity = self.velocity.lerp(direction_to_target * self.speed, self.turn_speed)
                self.velocity.normalize_ip()
                self.velocity *= self.speed
        else:
            # 追尾時間を過ぎたら直進
            if self.velocity.x == 0 and self.velocity.y == 0: # 初期状態の場合
                self.velocity = pygame.math.Vector2(0, -self.speed) # 上向きに直進

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # 画面外に出たら消滅
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

# 背景スクロールのクラス
class Background:
    def __init__(self, image_paths, scroll_speed=1):
        self.images = [pygame.image.load(os.path.join(img_dir, path)).convert() for path in image_paths]
        self.images = [pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in self.images]
        
        self.rect1 = self.images[0].get_rect()
        self.rect2 = self.images[1].get_rect()
        
        self.rect1.top = 0
        self.rect2.top = -SCREEN_HEIGHT
        
        self.scroll_speed = scroll_speed

    def update(self):
        self.rect1.y += self.scroll_speed
        self.rect2.y += self.scroll_speed
        
        if self.rect1.top >= SCREEN_HEIGHT:
            self.rect1.top = self.rect2.top - SCREEN_HEIGHT
        if self.rect2.top >= SCREEN_HEIGHT:
            self.rect2.top = self.rect1.top - SCREEN_HEIGHT

    def draw(self, surface):
        surface.blit(self.images[0], self.rect1)
        surface.blit(self.images[1], self.rect2)

# シールドのクラス
class Shield(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.image = shield_effect_img
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self):
        # プレイヤーが存在し、シールドが有効な場合のみ追従
        if self.player.alive() and self.player.shield_active:
            self.rect.center = self.player.rect.center
        else:
            self.kill() # プレイヤーがいない、またはシールドが切れたら消滅

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

# シールドエフェクト画像
shield_effect_img = pygame.image.load(os.path.join(img_dir, "shield_effect.png")).convert_alpha() # 透明度を保持
shield_effect_img = pygame.transform.scale(shield_effect_img, (int(player_img.get_width() * 1.0), int(player_img.get_height() * 1.0))) # プレイヤーと同じサイズに調整

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
score_count_sound = pygame.mixer.Sound(os.path.join(sound_dir, "score_count.wav")) # スコアカウントアップサウンドを追加
score_count_sound.set_volume(0.5) # スコアカウントアップ音の音量
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
powerups = pygame.sprite.Group() # パワーアップアイテムグループを追加
shields = pygame.sprite.Group() # シールドグループを追加

# 敵が倒されたときの共通処理
def handle_enemy_defeat(enemy):
    global enemies_defeated, score
    enemies_defeated += 1
    score += 10
    expl_sounds[0].play() # 敵撃破時にexpl3.wavを再生
    # 敵の数が最大出現数未満の場合のみ新しい敵を生成
    if len(enemies) < current_stage_settings["max_enemies_on_screen"]:
        new_enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
        all_sprites.add(new_enemy)
        enemies.add(new_enemy)
    
    # パワーアップアイテムのドロップ判定
    if random.random() < 1.0: # 100%の確率でドロップ
        powerup_type = random.choice(["rapid_fire", "spread_shot", "shield", "health", "triple_shot", "homing_missile"])
        powerup = PowerUp(enemy.rect.center, powerup_type)
        all_sprites.add(powerup)
        powerups.add(powerup)

# ゲーム変数
enemies_defeated = 0
current_boss = None
score = 0
boss_spawn_timer = pygame.time.get_ticks()
game_state = "playing"
current_stage = 1
current_stage_settings = STAGE_SETTINGS[current_stage]
game_over_sound_played = False # ゲームオーバーサウンド再生フラグ
best_score = load_best_score() # ベストスコアを読み込み
is_new_best_score = False
score_to_add = 0
current_score_display = 0
score_counting_start_time = 0
score_counting_duration = 0
score_count_interval = 0
last_score_count_sound_time = 0

# 背景の作成
background = Background(current_stage_settings["background_imgs"])

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
                    if current_stage + 1 in STAGE_SETTINGS:
                        current_stage += 1
                        current_stage_settings = STAGE_SETTINGS[current_stage]

                        # 背景を新しいステージ用に再作成
                        background = Background(current_stage_settings["background_imgs"])

                        # パワーアップ状態を保存
                        was_rapid_fire_active = player.rapid_fire_active
                        was_spread_shot_active = player.spread_shot_active
                        was_triple_shot_active = player.triple_shot_active
                        was_homing_missile_active = player.homing_missile_active

                        all_sprites.empty()
                        enemies.empty()
                        player_bullets.empty()
                        enemy_bullets.empty()
                        bosses.empty()
                        
                        player = Player()
                        # 保存したパワーアップ状態を復元
                        player.rapid_fire_active = was_rapid_fire_active
                        player.spread_shot_active = was_spread_shot_active
                        player.triple_shot_active = was_triple_shot_active
                        player.homing_missile_active = was_homing_missile_active

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
                        is_new_best_score = False # 次のステージではリセット
                    else:
                        game_state = "game_cleared" # 全ステージクリア

            elif game_state == "game_over" or game_state == "game_cleared":
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
                    is_new_best_score = False # リスタート時にリセット

                    # 背景をステージ1用に再作成
                    background = Background(current_stage_settings["background_imgs"])

                    # 初期敵の再生成
                    for i in range(current_stage_settings["max_enemies_on_screen"]):
                        enemy = Enemy(random.randrange(1, 4), random.choice([-1, 1]) * random.randrange(1, 3), current_stage_settings["enemy_bullet_speed"], current_stage_settings["enemy_shoot_delay_min"], current_stage_settings["enemy_shoot_delay_max"])
                        all_sprites.add(enemy)
                        enemies.add(enemy)

                    pygame.mixer.music.play(loops=-1) # BGMを再開
                    game_over_sound_played = False # フラグをリセット
                    player.rapid_fire_active = False # リスタート時に連射強化をリセット
                    player.spread_shot_active = False # リスタート時に拡散ショットをリセット
                    player.triple_shot_active = False # リスタート時に三方向攻撃をリセット
                    player.homing_missile_active = False # リスタート時に追尾ミサイルをリセット

    # 更新
    if game_state == "playing" or game_state == "exploding" or game_state == "score_counting":
        background.update()
        all_sprites.update()
        if game_state == "exploding" and not explosions:
            game_state = "game_over"

    if game_state == "score_counting":
        current_time = pygame.time.get_ticks()
        if current_time - score_counting_start_time < score_counting_duration:
            # スコアを徐々に増やす
            progress = (current_time - score_counting_start_time) / score_counting_duration
            score = current_score_display + int(score_to_add * progress)

            # 効果音を鳴らす
            if current_time - last_score_count_sound_time > score_count_interval:
                score_count_sound.play()
                last_score_count_sound_time = current_time
        else:
            score = current_score_display + score_to_add # 最終的なスコアを設定
            # ベストスコアの更新チェック
            if score > best_score:
                best_score = score
                save_best_score(best_score)
                is_new_best_score = True
            else:
                is_new_best_score = False
            game_state = "stage_cleared" # カウントアップ完了後、ステージクリア状態へ

    if game_state == "playing":
        current_time = pygame.time.get_ticks()
        if current_time - boss_spawn_timer >= BOSS_SPAWN_TIME * 1000 and current_boss is None:
            for enemy in enemies:
                enemy.kill()
            current_boss = Boss(current_stage_settings["boss_health"], current_stage_settings["boss_radial_attack_interval"])
            all_sprites.add(current_boss)
            bosses.add(current_boss)

        # プレイヤーの弾と敵の衝突判定
        hits = pygame.sprite.groupcollide(enemies, player_bullets, True, True)
        for hit_enemy in hits:
            handle_enemy_defeat(hit_enemy)

        if current_boss:
            boss_hits = pygame.sprite.spritecollide(current_boss, player_bullets, True)
            if boss_hits:
                current_boss.health -= len(boss_hits)
                if current_boss.health <= 0:
                    score += 1000
                    current_boss.kill()
                    current_boss = None
                    expl_sounds[1].play() # ボス撃破時にexpl6.wavを再生
                    game_state = "score_counting" # スコアカウントアップ状態へ遷移
                    score_to_add = 1000 # ボス撃破ボーナス
                    current_score_display = score - score_to_add # カウントアップ開始時のスコア
                    score_counting_start_time = pygame.time.get_ticks()
                    score_counting_duration = 4000 # 4秒でカウントアップ完了
                    score_count_interval = 50 # 50msごとにカウントアップ音を鳴らす
                    last_score_count_sound_time = pygame.time.get_ticks()

        # シールドと敵弾の衝突判定 (弾のみ消滅)
        pygame.sprite.groupcollide(shields, enemy_bullets, False, True)

        # シールドと敵本体の衝突判定 (敵のみ消滅)
        shield_enemy_hits = pygame.sprite.groupcollide(enemies, shields, True, False)
        for hit_enemy in shield_enemy_hits:
            handle_enemy_defeat(hit_enemy)

        # プレイヤーと敵弾の衝突判定
        hits = pygame.sprite.groupcollide(players, enemy_bullets, False, True)
        if hits:
            for p in hits:
                p.hit()
                if p.health <= 0 and p.alive():
                    expl = Explosion(p.rect.center)
                    all_sprites.add(expl)
                    explosions.add(expl)
                    p.kill()
                    pygame.mixer.music.stop()
                    expl_sounds[0].play()
                    game_state = "exploding"

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

        # プレイヤーとパワーアップアイテムの衝突判定
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for hit in hits:
            if hit.type == "rapid_fire":
                player.rapid_fire_active = True
                player.rapid_fire_start_time = pygame.time.get_ticks()
            elif hit.type == "spread_shot":
                player.spread_shot_active = True
                player.spread_shot_start_time = pygame.time.get_ticks()
            elif hit.type == "shield":
                player.activate_shield()
            elif hit.type == "health":
                player.health = min(player.health + 1, player.max_health) # 体力を1回復（最大体力まで）
            elif hit.type == "triple_shot":
                player.triple_shot_active = True
            elif hit.type == "homing_missile":
                player.homing_missile_active = True

    # 描画
    background.draw(screen)
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

        # シールドの描画
        if player.shield_active:
            # pygame.draw.circle(screen, BLUE, player.rect.center, player.rect.width // 2 + 10, 3) # プレイヤーの周りに青い円を描画
            shield_rect = shield_effect_img.get_rect(center=player.rect.center)
            screen.blit(shield_effect_img, shield_rect)

    elif game_state == "stage_cleared":
        clear_text = font.render("STAGE CLEAR!", True, GREEN)
        clear_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(clear_text, clear_rect)

        final_score_text = score_font.render(f"FINAL SCORE: {score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(final_score_text, final_score_rect)

        if is_new_best_score:
            best_score_text = score_font.render("NEW BEST SCORE!", True, YELLOW)
            best_score_rect = best_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            screen.blit(best_score_text, best_score_rect)

        next_stage_text = score_font.render("Press SPACE for Next Stage", True, WHITE)
        next_stage_rect = next_stage_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(next_stage_text, next_stage_rect)

    elif game_state == "game_cleared":
        clear_text = font.render("GAME CLEARED!", True, GREEN)
        clear_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(clear_text, clear_rect)

        final_score_text = score_font.render(f"FINAL SCORE: {score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(final_score_text, final_score_rect)

        if is_new_best_score:
            best_score_text = score_font.render("NEW BEST SCORE!", True, YELLOW)
            best_score_rect = best_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            screen.blit(best_score_text, best_score_rect)

        retry_text = score_font.render("PRESS SPACE TO RETRY", True, WHITE)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(retry_text, retry_rect)

    elif game_state == "score_counting":
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(score_text, text_rect)

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
