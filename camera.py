from OpenGL.GL import glTranslatef, glRotatef
import pygame


class Camera:
    # Инициализация данных
    def __init__(self):
        self.rotation_x = 30.0
        self.rotation_y = -45.0
        self.zoom = 1.0
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.last_mouse_pos = None
        self.is_dragging = False

    # Обработка событий мыши
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                self.is_dragging = True
                self.last_mouse_pos = pygame.mouse.get_pos()
            elif event.button == 4:  # Колесико вверх - ПРИБЛИЖЕНИЕ
                self.zoom /= 1.1  # Деление для приближения
            elif event.button == 5:  # Колесико вниз - ОТДАЛЕНИЕ
                self.zoom *= 1.1  # Умножение для отдаления

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
                self.last_mouse_pos = None

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging and self.last_mouse_pos:
                x, y = pygame.mouse.get_pos()
                dx = x - self.last_mouse_pos[0]
                dy = y - self.last_mouse_pos[1]

                self.rotation_y += dx * 0.5
                self.rotation_x += dy * 0.5

                # Ограничение вращения по X для более естественного поведения
                self.rotation_x = max(-90, min(90, self.rotation_x))

                self.last_mouse_pos = (x, y)

    # Применение трансформаций камеры
    def apply_transformations(self):
        glTranslatef(self.translation_x, self.translation_y, -5.0 * self.zoom)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)

    # Сброс камеры к начальным значениям
    def reset(self):
        self.rotation_x = 30.0
        self.rotation_y = -45.0
        self.zoom = 1.0
        self.translation_x = 0.0
        self.translation_y = 0.0
