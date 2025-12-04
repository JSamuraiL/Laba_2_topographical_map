import numpy as np


class FDFParser:
    # Инициализация значений
    def __init__(self):
        self.points = None
        self.lines = []
        self.width = 0
        self.height = 0
        self.min_z = float('inf')
        self.max_z = float('-inf')
        self.norm_min_z = 0
        self.norm_max_z = 0
        self.data_array = None

    # Функция парсинга файла FDF
    def parse_file(self, filename):
        # Чтение файла
        with open(filename, 'r') as file:
            lines = file.readlines()

        self.height = len(lines)
        data_rows = []

        # Парсинг строк
        i = 0
        while i < len(lines):
            values = lines[i].strip().split()
            if values:
                # Преобразование строк в числа
                row = list(map(int, values))
                data_rows.append(row)
            i += 1

        if not data_rows:
            return None, []

        # Преобразование в массив
        self.data_array = np.array(data_rows, dtype=np.float32)
        self.width = self.data_array.shape[1]
        self.height = self.data_array.shape[0]

        # min и max значения Z с использованием NumPy
        self.min_z = np.min(self.data_array)
        self.max_z = np.max(self.data_array)

        # 3D точки
        self.create_points()

        # Линии каркаса
        self.create_lines()

        return self.normalize_points()

    # Создание точек
    def create_points(self):
        # Создание сетки координат XY
        y_coords, x_coords = np.meshgrid(
            np.arange(self.height),
            np.arange(self.width),
            indexing='ij'
        )

        # Центрирование координат
        x_coords_centered = x_coords - self.width / 2

        # Инвертирование оси Y, чтобы первая строка файла была верхом модели
        y_coords_centered = -(y_coords - self.height / 2)

        # Создание массива точек [x, y, z]
        self.points = np.stack([
            x_coords_centered.flatten(),
            y_coords_centered.flatten(),
            self.data_array.flatten()
        ], axis=1)

    # Создание линий каркаса
    def create_lines(self):
        # Создание массива индексов для горизонтальных линий
        horizontal_indices = np.arange(self.height * self.width).reshape(
            self.height, self.width)
        horizontal_lines = np.stack([
            horizontal_indices[:, :-1].flatten(),
            horizontal_indices[:, 1:].flatten()
        ], axis=1)

        # Создание массива индексов для вертикальных линий
        vertical_lines = np.stack([
            horizontal_indices[:-1, :].flatten(),
            horizontal_indices[1:, :].flatten()
        ], axis=1)

        # Объединение горизонтальных и вертикальных линий
        self.lines = np.vstack([horizontal_lines,
                                vertical_lines]).astype(np.int32)

    # Нормализация точек
    def normalize_points(self):
        if self.points is None or len(self.points) == 0:
            return np.array([]), np.array([])

        # Вычисление диапазонов по осям
        x_range = np.max(self.points[:, 0]) - np.min(self.points[:, 0])
        y_range = np.max(self.points[:, 1]) - np.min(self.points[:, 1])
        z_range = np.max(self.points[:, 2]) - np.min(self.points[:, 2])

        # Максимальный размер по всем осям
        max_range = max(x_range, y_range, z_range)

        # Коэффициент масштабирования
        if max_range > 0:
            scale_factor = 2.0 / max_range
        else:
            scale_factor = 1.0

        # Масштабирование всех точек
        normalized_points = self.points * scale_factor

        # Масштабирование по Z для лучшей визуализации
        if self.max_z != self.min_z:
            z_range = self.max_z - self.min_z
            if z_range > 0:
                # Сохранение исходных Z для цветовой градации
                original_z = normalized_points[:, 2].copy()
                # Усиление рельефа
                z_scale = 0.5 / z_range
                normalized_points[:, 2] = (self.data_array.flatten() -
                                           self.min_z) * z_scale
                # Сохранение нормализованных min/max Z для цветовой градации
                self.norm_min_z = np.min(original_z)
                self.norm_max_z = np.max(original_z)
            else:
                self.norm_min_z = self.min_z
                self.norm_max_z = self.max_z
        else:
            self.norm_min_z = self.min_z
            self.norm_max_z = self.max_z

        return normalized_points, self.lines
