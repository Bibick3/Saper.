import pygame
import random
import sys
import os
import json

# --- Настройки игры ---
TILE_SIZE = 30
GRID_WIDTH = {
    "легкий": 9,
    "средний": 16,
    "сложный": 16
}
GRID_HEIGHT = {
    "легкий": 9,
    "средний": 16,
    "сложный": 30
}
MINES_COUNT = {
    "легкий": 10,
    "средний": 40,
    "сложный": 99
}
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
FONT_SIZE = 20
LEADERBOARD_FILE = "leaderboard.json"
MENU_BAR_HEIGHT = 40  # высота полосы меню


class Tile:
    def __init__(self, x, y, is_mine=False, is_revealed=False, is_flagged=False, nearby_mines=0):
        self.x = x
        self.y = y
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.nearby_mines = nearby_mines
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + MENU_BAR_HEIGHT, TILE_SIZE, TILE_SIZE)

    def draw(self, screen):
        if self.is_revealed:
            if self.is_mine:
                pygame.draw.rect(screen, RED, self.rect)
                font = pygame.font.Font(None, 30)
                text = font.render("X", True, BLACK)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)
            elif self.nearby_mines > 0:
                pygame.draw.rect(screen, GRAY, self.rect)
                font = pygame.font.Font(None, 30)
                text = font.render(str(self.nearby_mines), True, BLUE)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)
            else:
                pygame.draw.rect(screen, GRAY, self.rect)

        else:
            pygame.draw.rect(screen, WHITE, self.rect)
            if self.is_flagged:
                font = pygame.font.Font(None, 30)
                text = font.render("F", True, BLACK)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)
        pygame.draw.rect(screen, BLACK, self.rect, 1)

    def reveal(self):
        self.is_revealed = True

    def toggle_flag(self):
        self.is_flagged = not self.is_flagged


class Minesweeper:
    def __init__(self, difficulty, screen_width, screen_height, player_name=""):
        self.difficulty = difficulty
        pygame.init()
        self.grid_width = GRID_WIDTH[self.difficulty]
        self.grid_height = GRID_HEIGHT[self.difficulty]
        self.mines_count = MINES_COUNT[self.difficulty]
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption(f"Minesweeper - {self.difficulty}")

        info = pygame.display.Info()
        screen_x = (info.current_w - self.screen_width) // 2
        screen_y = (info.current_h - self.screen_height) // 2

        # Устанавливаем позицию окна
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{screen_x},{screen_y}'

        self.font = pygame.font.Font(None, FONT_SIZE)
        self.grid = [[Tile(x, y) for x in range(self.grid_width)] for y in range(self.grid_height)]
        self.game_over = False
        self.game_won = False
        self.start_time = pygame.time.get_ticks()
        self.place_mines()
        self.calculate_nearby_mines()
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.player_name = player_name
        self.score = 0
        self.menu_button_rect = pygame.Rect(10, 10, 150, 30)

    def place_mines(self):
        mines_placed = 0
        while mines_placed < self.mines_count:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if not self.grid[y][x].is_mine:
                self.grid[y][x].is_mine = True
                mines_placed += 1

    def calculate_nearby_mines(self):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not self.grid[y][x].is_mine:
                    nearby_mines = 0
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height and self.grid[ny][nx].is_mine:
                                nearby_mines += 1
                    self.grid[y][x].nearby_mines = nearby_mines

    def reveal_tile(self, x, y):
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            tile = self.grid[y][x]
            if not tile.is_revealed and not tile.is_flagged:
                tile.reveal()
                if tile.is_mine:
                    self.game_over = True
                elif tile.nearby_mines == 0:
                    self.score += 5
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            self.reveal_tile(nx, ny)
                else:
                    self.score += 1

    def check_win(self):
        unrevealed_mines = 0
        for row in self.grid:
            for tile in row:
                if not tile.is_revealed and tile.is_mine:
                    unrevealed_mines += 1
        unrevealed_tiles = 0
        for row in self.grid:
            for tile in row:
                if not tile.is_revealed and not tile.is_mine:
                    unrevealed_tiles += 1
        if unrevealed_tiles == 0:
            self.game_won = True
            self.save_score()

    def save_score(self):
        time_elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        score_data = {"name": self.player_name, "score": self.score, "time": time_elapsed,
                      "difficulty": self.difficulty}
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            leaderboard = []

        leaderboard.append(score_data)
        leaderboard.sort(key=lambda x: (x["score"]), reverse=True)  # Сортируем по очкам

        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f)

    def draw_leaderboard(self, screen):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            leaderboard = []

        text = self.font.render("Таблица лидеров:", True, BLACK)
        screen.blit(text, (50, 50))

        y_offset = 80
        for entry in leaderboard:
            text = self.font.render(
                f"{entry['name']}: {entry['difficulty']}: Очки: {entry['score']}, Время: {entry['time']} сек",
                True, BLACK
            )
            screen.blit(text, (50, y_offset))
            y_offset += 30
            # Ограничиваем высоту таблицы лидеров
            if y_offset > self.screen_height - 150:  # Добавили отступ снизу
                break

    def draw(self):
        self.screen.fill(WHITE)
        # Vеню сверху
        pygame.draw.rect(self.screen, GRAY, (0, 0, self.screen_width, MENU_BAR_HEIGHT))

        # Отрисовка игрового поля
        for row in self.grid:
            for tile in row:
                tile.draw(self.screen)

        score_text = self.font.render(f"Очки: {self.score}", True, BLACK)
        self.screen.blit(score_text, (self.screen_width - 150, 10))
        pygame.draw.rect(self.screen, WHITE, self.menu_button_rect)
        menu_text = self.font.render("Выход в меню", True, BLACK)
        menu_text_rect = menu_text.get_rect(center=self.menu_button_rect.center)
        self.screen.blit(menu_text, menu_text_rect)

        if self.game_over:
            text = self.font.render("Game Over!", True, RED)
            text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text, text_rect)
        if self.game_won:
            text = self.font.render("You Win!", True, GREEN)
            text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text, text_rect)
        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if event.button == 1:
                # Проверка на захват окна мышью
                if self.screen.get_rect().collidepoint(mouse_x, mouse_y) and mouse_y <= MENU_BAR_HEIGHT:
                    self.dragging = True
                    self.offset_x = mouse_x - self.screen.get_rect().x
                    self.offset_y = mouse_y - self.screen.get_rect().y
                elif self.menu_button_rect.collidepoint(mouse_x, mouse_y):
                    self.save_score()
                    game = Minesweeper("легкий", 0, 0, self.player_name)
                    game.main_menu(self.screen_width, self.screen_height)
                else:
                    # Обработка клика по игровому полю
                    for row in self.grid:
                        for tile in row:
                            if tile.rect.collidepoint(mouse_x, mouse_y) and mouse_y > MENU_BAR_HEIGHT:
                                if event.button == 1 and not self.game_over and not self.game_won and not tile.is_flagged:  # Левая кнопка мыши
                                    self.reveal_tile(tile.x, tile.y)
                                    self.check_win()
                                elif event.button == 3 and not self.game_over and not self.game_won and not tile.is_revealed:  # Правая кнопка мыши
                                    tile.toggle_flag()
            elif event.button == 3:
                for row in self.grid:
                    for tile in row:
                        if tile.rect.collidepoint(mouse_x, mouse_y) and mouse_y > MENU_BAR_HEIGHT:
                            if not tile.is_revealed:
                                tile.toggle_flag()
                                break
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                self.screen.get_rect().x = mouse_x - self.offset_x
                self.screen.get_rect().y = mouse_y - self.offset_y
                pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.save_score()
                game = Minesweeper("легкий", 0, 0, self.player_name)
                game.main_menu(self.screen_width, self.screen_height)
            if event.key == pygame.K_r and (self.game_over or self.game_won):
                self.__init__(self.difficulty, self.screen_width, self.screen_height, self.player_name)

        elif event.type == pygame.VIDEORESIZE:
            self.screen_width, self.screen_height = event.size
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

    def run(self):
        running = True
        # Пересчет размера окна
        self.screen_width = TILE_SIZE * self.grid_width
        self.screen_height = TILE_SIZE * self.grid_height + MENU_BAR_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        info = pygame.display.Info()
        screen_x = (info.current_w - self.screen_width) // 2
        screen_y = (info.current_h - self.screen_height) // 2

        # Устанавливаем позицию окна
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{screen_x},{screen_y}'
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)
            self.draw()
        pygame.quit()

    def get_player_name(self, screen_width, screen_height):
        name = ""
        pygame.init()
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Enter your name")
        font = pygame.font.Font(None, FONT_SIZE)
        input_rect = pygame.Rect((screen_width - 200) // 2, (screen_height - 50) // 2, 200, 50)
        text_surface = font.render(name, True, BLACK)
        done = False

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                    return ""
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        name += event.unicode
                    text_surface = font.render(name, True, BLACK)

            screen.fill(WHITE)
            pygame.draw.rect(screen, GRAY, input_rect, 2)
            screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 10))
            pygame.display.flip()

        return name

    def edit_leaderboard(self, screen_width, screen_height):
        running = True
        pygame.init()
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Edit Leaderboard")
        font = pygame.font.Font(None, FONT_SIZE)

        try:
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            leaderboard = []

        finish_button_rect = pygame.Rect(screen_width - 150, screen_height - 50, 130, 30)

        while running:
            screen.fill(WHITE)
            text = font.render("Таблица лидеров:", True, BLACK)
            screen.blit(text, (50, 50))

            y_offset = 80
            for i, entry in enumerate(leaderboard):
                text = font.render(
                    f"{entry['name']}: {entry['difficulty']}: Очки: {entry['score']}, Время: {entry['time']} сек",
                    True, BLACK
                )
                screen.blit(text, (50, y_offset))

                delete_button_rect = pygame.Rect(screen_width - 100, y_offset, 80, 25)
                pygame.draw.rect(screen, RED, delete_button_rect)
                delete_text = font.render("Удалить", True, BLACK)
                delete_text_rect = delete_text.get_rect(center=delete_button_rect.center)
                screen.blit(delete_text, delete_text_rect)

                y_offset += 30
                # Ограничиваем высоту таблицы лидеров
                if y_offset > screen_height - 150:
                    break
            pygame.draw.rect(screen, GREEN, finish_button_rect)
            finish_text = font.render("Закончить", True, BLACK)
            finish_text_rect = finish_text.get_rect(center=finish_button_rect.center)
            screen.blit(finish_text, finish_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    for i, entry in enumerate(leaderboard):
                        delete_button_rect = pygame.Rect(screen_width - 100, 80 + i * 30, 80, 25)
                        if delete_button_rect.collidepoint(mouse_x, mouse_y):
                            del leaderboard[i]
                            with open(LEADERBOARD_FILE, "w") as f:
                                json.dump(leaderboard, f)
                            break
                    if finish_button_rect.collidepoint(mouse_x, mouse_y):
                        running = False
            pygame.display.flip()
        pygame.quit()

    def main_menu(self, screen_width, screen_height):
        running = True
        self.screen_width = screen_width
        self.screen_height = screen_height
        pygame.init()

        info = pygame.display.Info()
        screen_x = (info.current_w - self.screen_width) // 2
        screen_y = (info.current_h - self.screen_height) // 2

        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{screen_x},{screen_y}'

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Minesweeper")
        self.font = pygame.font.Font(None, FONT_SIZE)

        button_width = 150
        button_height = 50
        button_x_offset = 50
        button_y_offset = 100
        easy_button_rect = pygame.Rect(self.screen_width - button_width - button_x_offset, button_y_offset,
                                       button_width, button_height)
        medium_button_rect = pygame.Rect(self.screen_width - button_width - button_x_offset, button_y_offset + 70,
                                         button_width, button_height)
        hard_button_rect = pygame.Rect(self.screen_width - button_width - button_x_offset, button_y_offset + 140,
                                       button_width, button_height)

        edit_button_rect = pygame.Rect(self.screen_width - button_width - button_x_offset, button_y_offset + 210,
                                       button_width, button_height)

        # отрисовка таблицы лидеров
        self.draw_leaderboard(self.screen)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    if event.button == 1:
                        if easy_button_rect.collidepoint(mouse_x, mouse_y):
                            player_name = self.get_player_name(self.screen_width, self.screen_height)
                            game = Minesweeper("легкий", TILE_SIZE * GRID_WIDTH["легкий"],
                                               TILE_SIZE * GRID_HEIGHT["легкий"] + MENU_BAR_HEIGHT, player_name)
                            game.run()
                            return
                        elif medium_button_rect.collidepoint(mouse_x, mouse_y):
                            player_name = self.get_player_name(self.screen_width, self.screen_height)
                            game = Minesweeper("средний", TILE_SIZE * GRID_WIDTH["средний"],
                                               TILE_SIZE * GRID_HEIGHT["средний"] + MENU_BAR_HEIGHT, player_name)
                            game.run()
                            return
                        elif hard_button_rect.collidepoint(mouse_x, mouse_y):
                            player_name = self.get_player_name(self.screen_width, self.screen_height)
                            game = Minesweeper("сложный", TILE_SIZE * GRID_WIDTH["сложный"],
                                               TILE_SIZE * GRID_HEIGHT["сложный"] + MENU_BAR_HEIGHT, player_name)
                            game.run()
                            return
                        elif edit_button_rect.collidepoint(mouse_x, mouse_y):
                            self.edit_leaderboard(self.screen_width, self.screen_height)

                            # Получаем информацию о мониторе
                            info = pygame.display.Info()
                            screen_x = (info.current_w - self.screen_width) // 2
                            screen_y = (info.current_h - self.screen_height) // 2

                            # Устанавливаем позицию окна
                            os.environ['SDL_VIDEO_WINDOW_POS'] = f'{screen_x},{screen_y}'

                            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height),
                                                                  pygame.RESIZABLE)
                            self.draw_leaderboard(self.screen)
            self.screen.fill(WHITE)
            self.draw_leaderboard(self.screen)
            # Рисование кнопок
            pygame.draw.rect(self.screen, GRAY, easy_button_rect)
            pygame.draw.rect(self.screen, GRAY, medium_button_rect)
            pygame.draw.rect(self.screen, GRAY, hard_button_rect)
            pygame.draw.rect(self.screen, BLUE, edit_button_rect)

            # Рисование текста на кнопках
            text_easy = self.font.render("Легкий", True, BLACK)
            text_medium = self.font.render("Средний", True, BLACK)
            text_hard = self.font.render("Сложный", True, BLACK)
            text_edit = self.font.render("Редактировать", True, BLACK)

            text_easy_rect = text_easy.get_rect(center=easy_button_rect.center)
            text_medium_rect = text_medium.get_rect(center=medium_button_rect.center)
            text_hard_rect = text_hard.get_rect(center=hard_button_rect.center)
            text_edit_rect = text_edit.get_rect(center=edit_button_rect.center)

            self.screen.blit(text_easy, text_easy_rect)
            self.screen.blit(text_medium, text_medium_rect)
            self.screen.blit(text_hard, text_hard_rect)
            self.screen.blit(text_edit, text_edit_rect)

            pygame.display.flip()


if __name__ == "__main__":
    menu_width = TILE_SIZE * 20
    menu_height = TILE_SIZE * 10
    game = Minesweeper("легкий", 0, 0)
    game.main_menu(menu_width, menu_height)