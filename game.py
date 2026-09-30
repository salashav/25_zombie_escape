import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30, 35, 25)


class Zombie:
    SPEED = 1.5

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.color = (60, 140, 60)
        self.hp = 3
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px - cx, py - cy
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist:
            self.rect.x += int(dx / dist * self.SPEED)
            self.rect.y += int(dy / dist * self.SPEED)

        self.frame += 1

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame * 0.2) * 3)
        draw_rect = self.rect.move(0, wobble_y)

        pygame.draw.rect(
            screen,
            self.color,
            draw_rect,
            border_radius=5
        )

        for ex in [draw_rect.x + 6, draw_rect.x + 18]:
            pygame.draw.circle(
                screen,
                (200, 40, 40),
                (ex, draw_rect.y + 10),
                4
            )


def spawn_zombie(width, height, player_rect, margin=120):
    while True:
        x = random.randint(0, width - 30)
        y = random.randint(0, height - 30)

        rect = pygame.Rect(x, y, 30, 30)

        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return Zombie(x, y)


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60, 160, 220)

        # Each bullet is stored as:
        # [x, y, velocity_x, velocity_y]
        self.bullets = []

        self.shoot_cooldown = 0

    def move(self, keys, width, height):
        dx = dy = 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -SPEED

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = SPEED

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -SPEED

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = SPEED

        self.rect.x = max(
            0,
            min(width - self.rect.width, self.rect.x + dx)
        )

        self.rect.y = max(
            0,
            min(height - self.rect.height, self.rect.y + dy)
        )

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self, target_pos):
        if self.shoot_cooldown > 0:
            return

        cx, cy = self.rect.center
        tx, ty = target_pos

        dx = tx - cx
        dy = ty - cy

        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist == 0:
            return

        vx = dx / dist * 10
        vy = dy / dist * 10

        self.bullets.append([
            cx,
            cy,
            vx,
            vy
        ])

        self.shoot_cooldown = 15

    def update_bullets(self, width, height):
        live = []

        for bullet in self.bullets:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]

            if (
                0 <= bullet[0] <= width
                and 0 <= bullet[1] <= height
            ):
                live.append(bullet)

        self.bullets = live

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=6
        )

        for bullet in self.bullets:
            pygame.draw.circle(
                screen,
                (255, 220, 60),
                (int(bullet[0]), int(bullet[1])),
                5
            )


class GameEngine:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption("Zombie Escape")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            24
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            44,
            bold=True
        )

        self.reset()

    def reset(self):
        self.player = Player(
            WIDTH // 2,
            HEIGHT // 2
        )

        self.zombies = [
            spawn_zombie(
                WIDTH,
                HEIGHT,
                self.player.rect
            )
            for _ in range(4)
        ]

        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False
        self.start_time = time.time()

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
            ):
                self.reset()

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and not self.game_over
            ):
                self.player.shoot(event.pos)

        return True

    def update(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            WIDTH,
            HEIGHT
        )

        self.player.update_bullets(
            WIDTH,
            HEIGHT
        )

        self.score = int(
            time.time() - self.start_time
        )

        for zombie in self.zombies:
            zombie.update(
                self.player.rect.center
            )

            if zombie.rect.colliderect(
                self.player.rect
            ):
                self.game_over = True

        dead = []

        for zombie in self.zombies:

            for bullet in self.player.bullets[:]:

                bx = int(bullet[0])
                by = int(bullet[1])

                if zombie.rect.collidepoint(
                    bx,
                    by
                ):

                    if zombie.hit():
                        dead.append(zombie)

                    if bullet in self.player.bullets:
                        self.player.bullets.remove(
                            bullet
                        )

        for zombie in dead:

            if zombie in self.zombies:
                self.zombies.remove(zombie)

                self.kills += 1
                self.score += 10

        if self.kills >= self.kills_to_next:

            self.kills = 0
            self.wave += 1

            self.kills_to_next = (
                8 + self.wave * 2
            )

            for _ in range(self.wave + 3):

                self.zombies.append(
                    spawn_zombie(
                        WIDTH,
                        HEIGHT,
                        self.player.rect
                    )
                )

    def draw(self):
        self.screen.fill(BG)

        for x in range(0, WIDTH, 60):
            pygame.draw.line(
                self.screen,
                (40, 45, 35),
                (x, 0),
                (x, HEIGHT),
                1
            )

        for y in range(0, HEIGHT, 60):
            pygame.draw.line(
                self.screen,
                (40, 45, 35),
                (0, y),
                (WIDTH, y),
                1
            )

        for zombie in self.zombies:
            zombie.draw(self.screen)

        self.player.draw(self.screen)

        hud_bg = pygame.Rect(
            0,
            0,
            WIDTH,
            40
        )

        pygame.draw.rect(
            self.screen,
            (15, 20, 15),
            hud_bg
        )

        hud = self.font.render(
            f"Wave: {self.wave}  "
            f"Score: {self.score}  "
            f"Kills: {self.kills}/{self.kills_to_next}  |  "
            f"WASD Move, Click Shoot, R Restart",
            True,
            (160, 220, 120)
        )

        self.screen.blit(
            hud,
            (8, 8)
        )

        if self.game_over:

            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 160)
            )

            self.screen.blit(
                overlay,
                (0, 0)
            )

            message = self.big_font.render(
                "DEVOURED!",
                True,
                (180, 40, 40)
            )

            score_message = self.font.render(
                f"Wave {self.wave} | "
                f"Score {self.score} | "
                f"Press R",
                True,
                (200, 200, 200)
            )

            self.screen.blit(
                message,
                (
                    WIDTH // 2
                    - message.get_width() // 2,
                    HEIGHT // 2 - 40
                )
            )

            self.screen.blit(
                score_message,
                (
                    WIDTH // 2
                    - score_message.get_width() // 2,
                    HEIGHT // 2 + 20
                )
            )

        pygame.display.flip()

    def run(self):
        running = True

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()