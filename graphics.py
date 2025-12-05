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
        self.is_image_mode = False

    # Функция подготовки данных для проволочной модели
    def build_wireframe(self, points, lines, min_z, max_z, get_color_func):
        if not points or not lines or len(lines) == 0:
            print("Нет данных для построения проволочной модели")
            return False

        # Преобразование точек в массив NumPy для векторизации
        points_array = np.array(points, dtype=np.float32)
        lines_array = np.array(lines, dtype=np.int32)

        # Ограничение количества линий для рендеринга
        max_render_lines = 10000
        if len(lines_array) > max_render_lines:
            # Прореживание линий для отображения
            skip_factor = len(lines_array) // max_render_lines + 1
            lines_array = lines_array[::skip_factor]
            print(f"Линии прорежены для отображения: {len(lines_array)}")

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
            self.wireframe_colors = \
                np.column_stack([colors1, colors2]).flatten()

        self.wireframe_num_lines = len(lines_array)
        self.wireframe_initialized = True
        return True

    # Подготовка данных для сетки
    def build_grid(self, points, width, height, grid_color):
        if not points or width == 0 or height == 0:
            return False

        self.grid_color = grid_color

        # Нужно ли рисовать сетку
        if width * height > 10000:  # Для больших - не рисуем сетку
            print("Сетка отключена для оптимизации производительности")
            self.grid_vertices = np.array([], dtype=np.float32)
            self.grid_num_lines = 0
            self.grid_initialized = True
            return True

        points_array = np.array(points, dtype=np.float32). \
            reshape(height, width, 3)

        # Ограничение детализации сетки
        grid_step_x = max(1, width // 20)
        grid_step_y = max(1, height // 20)

        # Создание массива для вершин сетки
        grid_vertices_list = []

        # Рисование только основных линий сетки
        y = 0
        while y < height:
            x = 0
            while x < width:
                point1 = points_array[y, x]
                z_grid = point1[2] - 0.1

                # Горизонтальная линия
                if x + grid_step_x < width:
                    point2 = points_array[y, x + grid_step_x]
                    grid_vertices_list.extend([point1[0], point1[1], z_grid])
                    grid_vertices_list.extend([point2[0], point2[1], z_grid])

                # Вертикальная линия
                if y + grid_step_y < height:
                    point2 = points_array[y + grid_step_y, x]
                    grid_vertices_list.extend([point1[0], point1[1], z_grid])
                    grid_vertices_list.extend([point2[0], point2[1], z_grid])

                x += grid_step_x
            y += grid_step_y

        # Преобразование в numpy array
        self.grid_vertices = np.array(grid_vertices_list, dtype=np.float32)
        self.grid_num_lines = len(self.grid_vertices) // 6
        self.grid_initialized = True
        return True

    # Отрисовка проволочной модели
    def render_wireframe(self):
        if not self.wireframe_initialized or self.wireframe_vertices is None:
            return

        if self.is_image_mode:
            glLineWidth(0.8)
        else:
            glLineWidth(1.5)

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
        if not self.grid_initialized or self.grid_vertices is None or len(
                self.grid_vertices) == 0:
            return

        glColor4f(*self.grid_color)
        glLineWidth(0.5)

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

    # Установка режима для изображений
    def set_image_mode(self, is_image):
        self.is_image_mode = is_image

    # Очистка ресурсов
    def cleanup(self):
        self.wireframe_vertices = None
        self.wireframe_colors = None
        self.grid_vertices = None
        self.wireframe_initialized = False
        self.grid_initialized = False
