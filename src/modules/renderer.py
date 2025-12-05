import numpy as np
import pygame
from OpenGL.GL import glEnable, glClearColor, glViewport, glMatrixMode, \
    glLoadIdentity, glClear, glLineWidth, glBegin, glColor3f, glVertex3f, \
    glEnd, glPushMatrix, glDisable, glBlendFunc, glRasterPos2d, glDrawPixels, \
    glPopMatrix, GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW, \
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_LINES, GL_BLEND, \
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_RGBA, GL_UNSIGNED_BYTE
from OpenGL.GLU import gluPerspective, gluOrtho2D
from modules.graphics import SimpleRenderer


class Renderer:
    # Инициализация значений
    def __init__(self, width=1200, height=800):
        self.width = width
        self.height = height
        self.background_color = (0.1, 0.1, 0.1, 1.0)
        self.line_color = (0.8, 0.8, 0.8, 1.0)
        self.grid_color = (0.3, 0.3, 0.3, 0.5)

        # Настраиваемые параметры градиента
        self.gradient_colors = [
            (0.0, 0.0, 1.0),   # Синий (низкие точки)
            (0.0, 1.0, 1.0),   # Голубой
            (0.0, 1.0, 0.0),   # Зеленый
            (1.0, 1.0, 0.0),   # Желтый
            (1.0, 0.0, 0.0)    # Красный (высокие точки)
        ]
        self.gradient_positions = [0.0, 0.25, 0.5, 0.75, 1.0]

        # Renderer объекты
        self.renderer = SimpleRenderer()
        self.current_points = None
        self.current_lines = None
        self.current_min_z = 0
        self.current_max_z = 0
        self.current_width = 0
        self.current_height = 0

        # Инициализация Pygame и OpenGL
        pygame.init()

        # Получение информации
        info = pygame.display.Info()
        if width > info.current_w or height > info.current_h:
            # Если запрашиваемый размер больше экрана, уменьшаем
            self.width = min(width, info.current_w - 100)
            self.height = min(height, info.current_h - 100)
        else:
            self.width = width
            self.height = height

        self.screen = pygame.display.set_mode((self.width, self.height),
                                              pygame.OPENGL |
                                              pygame.DOUBLEBUF |
                                              pygame.RESIZABLE)
        pygame.display.set_caption("FDF Viewer")

        self.setup_opengl()

    # Настройка OpenGL
    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(*self.background_color)
        self.update_projection()

    # Обновление проекции при изменении размеров окна
    def update_projection(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.width / float(self.height)
        gluPerspective(45, aspect_ratio, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # Функция очистки экрана
    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Инициализация данных для модели
    def init_wireframe(self, points, lines, min_z, max_z, width, height):
        # Сохранение данных для пересчета при изменении градиента
        self.current_points = points
        self.current_lines = lines
        self.current_min_z = min_z
        self.current_max_z = max_z
        self.current_width = width
        self.current_height = height

        # Создание данных для проволочной модели
        self.renderer.build_wireframe(points, lines, min_z, max_z,
                                      self.get_color_by_height)

        # Создание данных для сетки
        self.renderer.build_grid(points, width, height, self.grid_color)

    # Функция получения цвета в зависимости от высоты
    def get_color_by_height(self, z, min_z, max_z):
        # Обработка скалярного значения
        if np.isscalar(z):
            return self._get_single_color_by_height(z, min_z, max_z)

        # Обработка массива значений
        return self._get_array_color_by_height(z, min_z, max_z)

    # Получение цвета для одного значения
    def _get_single_color_by_height(self, z, min_z, max_z):
        if max_z == min_z:
            return self.gradient_colors[0]  # Возвращение первый цвет градиента

        # Нормализация высоты
        normalized = (z - min_z) / (max_z - min_z)

        # Поиск между какими точками градиента находится нужная высота
        i = 0
        while i < len(self.gradient_positions) - 1:
            if self.gradient_positions[i] <= normalized <= \
                    self.gradient_positions[i + 1]:
                # Интерполяция между двумя цветами
                t = (normalized - self.gradient_positions[i]) / \
                    (self.gradient_positions[i + 1] -
                     self.gradient_positions[i])

                color1 = self.gradient_colors[i]
                color2 = self.gradient_colors[i + 1]

                r = color1[0] + t * (color2[0] - color1[0])
                g = color1[1] + t * (color2[1] - color1[1])
                b = color1[2] + t * (color2[2] - color1[2])

                return (r, g, b)
            i += 1

        # Если значение вне диапазона, крайний цвет
        return self.gradient_colors[-1]

    # Получение цвета для массива значений
    def _get_array_color_by_height(self, z_array, min_z, max_z):
        if max_z == min_z:
            # Возвращение массива с первым цветом градиента для всех значений
            base_color = self.gradient_colors[0]
            return np.tile(base_color, (len(z_array), 1))

        # Нормализация высот
        normalized = (z_array - min_z) / (max_z - min_z)

        # Инициализация массива цветов
        colors = np.zeros((len(z_array), 3))

        # Обработка каждого значения в массиве
        i = 0
        while i < len(z_array):
            norm_val = normalized[i]

            # Поиск интервала градиента
            grad_idx = 0
            while grad_idx < len(self.gradient_positions) - 1:
                if self.gradient_positions[grad_idx] <= norm_val <= \
                        self.gradient_positions[grad_idx + 1]:
                    # Интерполяция между двумя цветами
                    t = (norm_val - self.gradient_positions[grad_idx]) / \
                        (self.gradient_positions[grad_idx + 1] -
                         self.gradient_positions[grad_idx])

                    color1 = self.gradient_colors[grad_idx]
                    color2 = self.gradient_colors[grad_idx + 1]

                    colors[i, 0] = color1[0] + t * (color2[0] - color1[0])
                    colors[i, 1] = color1[1] + t * (color2[1] - color1[1])
                    colors[i, 2] = color1[2] + t * (color2[2] - color1[2])
                    break
                grad_idx += 1

            # Если значение вне диапазона, используем крайний цвет
            if grad_idx == len(self.gradient_positions) - 1:
                colors[i] = self.gradient_colors[-1]

            i += 1

        return colors

    # Функция для установки пользовательского градиента
    def set_gradient(self, colors, positions=None):
        """
        Установка пользовательского градиента.
        colors: список цветов в формате (r, g, b) от 0.0 до 1.0
        positions: список позиций от 0.0 до 1.0 (если None, то равномерно
        распределяем)
        """
        self.gradient_colors = colors

        if positions is None:
            # Равномерное распределение
            num_colors = len(colors)
            self.gradient_positions = []
            idx = 0
            while idx < num_colors:
                self.gradient_positions.append(idx / (num_colors - 1))
                idx += 1
        else:
            self.gradient_positions = positions

        # Перестройка данных с новым градиентом
        if (self.current_points is not None and
                self.current_lines is not None):
            self.renderer.build_wireframe(
                self.current_points, self.current_lines,
                self.current_min_z, self.current_max_z,
                self.get_color_by_height
            )

    # Отрисовка проволочной модели
    def render_wireframe(self):
        self.renderer.render_wireframe()

    # Отрисовка вторичной сетки
    def render_grid(self):
        self.renderer.render_grid()

    # Отрисовка осей координат
    def render_axes(self):
        glLineWidth(2.0)

        glBegin(GL_LINES)

        # Ось X (красная)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(2.0, 0.0, 0.0)

        # Ось Y (зеленая)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 2.0, 0.0)

        # Ось Z (синяя)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 2.0)

        glEnd()

    # Отображение информации на экране
    def display_info(self, font, filename, points_count, lines_count,
                     rotation_x, rotation_y, zoom):
        # Сохранение текущей матрицы проекции
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        # Установка ортографической проекцию для 2D
        gluOrtho2D(0, self.width, self.height, 0)

        # Сохранение текущей матрицы вида модели
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Отключение теста глубины для текста
        glDisable(GL_DEPTH_TEST)

        # Включение смешивания для прозрачности текста
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Отображение информации
        info_lines = [
            f"Файл: {filename}",
            f"Точек: {points_count}",
            f"Линий: {lines_count}",
            f"Вращение X: {rotation_x:.1f}°",
            f"Вращение Y: {rotation_y:.1f}°",
            f"Масштаб: {zoom:.2f}",
            "",
            "Управление:",
            "ЛКМ + движение - вращение",
            "Колесо мыши - масштаб",
            "ESC - выход",
            "",
            "Градиенты:",
            "1 - По умолчанию",
            "2 - Земля/Горы",
            "3 - Огонь",
            "4 - Лед/Снег",
            "",
            "Файлы:",
            "O - Открыть новый файл",
            "R - Сбросить вид"
        ]

        y_offset = 40
        idx = 0
        while idx < len(info_lines):
            line = info_lines[idx]
            text_surface = font.render(line, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)

            # Установка позиции с правильными координатами
            glRasterPos2d(10, y_offset)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                         GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            y_offset += 20
            idx += 1

        # Восстановление состояния
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

        # Восстанавление матрицы
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # Обработка изменения размера окна
    def handle_resize(self, width, height):
        self.width = width
        self.height = height
        self.update_projection()

    # Очистка ресурсов
    def cleanup(self):
        self.renderer.cleanup()
