import numpy as np
from OpenGL.GL import glLineWidth, glBegin, glColor3f, glVertex3f, glEnd, \
    glColor4f, GL_LINES


class SimpleRenderer:
    # Инициализация данных
    def __init__(self):
        self.wireframe_data = None
        self.grid_data = None
        self.wireframe_initialized = False
        self.grid_initialized = False

    # Функция подготовки данных для проволочной модели
    def build_wireframe(self, points, lines, min_z, max_z, get_color_func):
        if not points or not lines:
            return False

        # Преобразование точек в массив NumPy для векторизации
        points_array = np.array(points, dtype=np.float32)
        lines_array = np.array(lines, dtype=np.int32)

        # Получение координат вершин линий
        idx1 = lines_array[:, 0]
        idx2 = lines_array[:, 1]

        points1 = points_array[idx1]
        points2 = points_array[idx2]

        # Получение цветов с использованием векторизации
        z1 = points1[:, 2]
        z2 = points2[:, 2]

        # Получение цветов для всех точек сразу
        colors1 = get_color_func(z1, min_z, max_z)
        colors2 = get_color_func(z2, min_z, max_z)

        # Объединение вершин и цветов
        self.wireframe_vertices = np.column_stack([points1, points2]).flatten()

        # Объединение цветов
        if colors1.ndim == 1 and colors2.ndim == 1:
            # Если возвращены одиночные цвета (не должно происходить)
            self.wireframe_colors = np.concatenate([colors1, colors2])
        else:
            # Если возвращены массивы цветов
            self.wireframe_colors = np.column_stack([
                colors1, colors2]).flatten()

        self.wireframe_num_lines = len(lines_array)
        self.wireframe_initialized = True
        return True

    # Подготовка данных для сетки
    def build_grid(self, points, width, height, grid_color):
        if not points or width == 0 or height == 0:
            return False

        self.grid_color = grid_color
        points_array = np.array(points, dtype=np.float32).reshape(height,
                                                                  width, 3)

        # Вычисление общего количества линий сетки
        total_horizontal = height * (width - 1)
        total_vertical = (height - 1) * width
        total_lines = total_horizontal + total_vertical

        # Создание массива для вершин сетки
        self.grid_vertices = np.zeros(total_lines * 6, dtype=np.float32)

        # Индекс для заполнения массива
        idx = 0

        # Горизонтальные линии сетки
        y = 0
        while y < height:
            x = 0
            while x < width - 1:
                point1 = points_array[y, x]
                point2 = points_array[y, x + 1]
                z_grid = min(point1[2], point2[2]) - 0.1

                # Присвоение координат первой точки
                self.grid_vertices[idx] = point1[0]
                self.grid_vertices[idx + 1] = point1[1]
                self.grid_vertices[idx + 2] = z_grid

                # Присвоение координат второй точки
                self.grid_vertices[idx + 3] = point2[0]
                self.grid_vertices[idx + 4] = point2[1]
                self.grid_vertices[idx + 5] = z_grid

                idx += 6
                x += 1
            y += 1

        # Вертикальные линии сетки
        x = 0
        while x < width:
            y = 0
            while y < height - 1:
                point1 = points_array[y, x]
                point2 = points_array[y + 1, x]
                z_grid = min(point1[2], point2[2]) - 0.1

                # Присвоение координат первой точки
                self.grid_vertices[idx] = point1[0]
                self.grid_vertices[idx + 1] = point1[1]
                self.grid_vertices[idx + 2] = z_grid

                # Присвоение координат второй точки
                self.grid_vertices[idx + 3] = point2[0]
                self.grid_vertices[idx + 4] = point2[1]
                self.grid_vertices[idx + 5] = z_grid

                idx += 6
                y += 1
            x += 1

        self.grid_num_lines = total_lines
        self.grid_initialized = True
        return True

    # Отрисовка проволочной модели
    def render_wireframe(self):
        if not self.wireframe_initialized or self.wireframe_vertices is None:
            return

        glLineWidth(2.0)
        glBegin(GL_LINES)

        vertices = self.wireframe_vertices
        colors = self.wireframe_colors

        # Отрисовка через предподготовленные данные
        i = 0
        num_vertices = len(vertices)
        while i < num_vertices:
            # Первая точка
            glColor3f(colors[i], colors[i+1], colors[i+2])
            glVertex3f(vertices[i], vertices[i+1], vertices[i+2])

            # Вторая точка
            glColor3f(colors[i+3], colors[i+4], colors[i+5])
            glVertex3f(vertices[i+3], vertices[i+4], vertices[i+5])

            i += 6

        glEnd()

    # Отрисовка сетки
    def render_grid(self):
        if not self.grid_initialized or self.grid_vertices is None:
            return

        glColor4f(*self.grid_color)
        glLineWidth(1.0)

        glBegin(GL_LINES)

        vertices = self.grid_vertices

        # Проход по всем линиям сетки
        i = 0
        num_vertices = len(vertices)
        while i < num_vertices:
            glVertex3f(vertices[i], vertices[i+1], vertices[i+2])
            glVertex3f(vertices[i+3], vertices[i+4], vertices[i+5])
            i += 6

        glEnd()

    # Очистка ресурсов
    def cleanup(self):
        self.wireframe_vertices = None
        self.wireframe_colors = None
        self.grid_vertices = None
        self.wireframe_initialized = False
        self.grid_initialized = False
