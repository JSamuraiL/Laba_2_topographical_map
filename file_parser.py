import numpy as np
from PIL import Image


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
        self.is_image = False

    # Функция парсинга файлов
    def parse_file(self, filename):
        # Определение типа файла по расширению
        ext = self._get_file_extension(filename)

        # Проверка поддержки формата
        if ext in ['.fdf', '.txt']:
            self.is_image = False
            return self._parse_fdf(filename)
        else:
            self.is_image = True
            return self._parse_image(filename)

    # Получение расширения файла
    def _get_file_extension(self, filename):
        dot_pos = len(filename) - 1
        while dot_pos >= 0 and filename[dot_pos] != '.':
            dot_pos -= 1

        if dot_pos >= 0:
            return filename[dot_pos:].lower()
        return ''

    # Парсинг FDF файла
    def _parse_fdf(self, filename):
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

    # Парсинг изображения с сохранением распределения
    def _parse_image(self, filename):
        # Загрузка изображения
        try:
            img = Image.open(filename)

            # Конвертация различных форматов изображений
            if img.mode == 'P':
                # Для палитровых изображений конвертируем в RGBA
                img = img.convert('RGBA')
                img = img.convert('L')
            elif img.mode in ['RGBA', 'LA']:
                # Для изображений с альфа-каналом конвертируем в L
                img = img.convert('RGBA')
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(background, img)
                img = img.convert('L')
            elif img.mode != 'L':
                # Для RGB и других форматов конвертируем в оттенки серого
                img = img.convert('L')

            original_width, original_height = img.size

            # Конвертация в массив numpy
            img_array = np.array(img, dtype=np.float32)

            # Инвертирование значений (чтобы темные области были ниже)
            original_data = 255.0 - img_array

            # Расчет оптимального размера для дискретизации
            target_points = 5000  # Целевое количество точек

            # Вычисление коэффициента масштабирования
            total_pixels = original_width * original_height
            if total_pixels > target_points:
                scale_factor = np.sqrt(target_points / total_pixels)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)

                """
                Использование билинейной интерполяции для сохранения
                распределения
                """
                img_resized = img.resize((new_width, new_height),
                                         Image.BILINEAR)
                img_array_resized = np.array(img_resized, dtype=np.float32)
                self.data_array = 255.0 - img_array_resized
                self.width = new_width
                self.height = new_height
            else:
                self.data_array = original_data
                self.width = original_width
                self.height = original_height

            # Нормализация значений высоты
            self.min_z = np.min(self.data_array)
            self.max_z = np.max(self.data_array)

            print("Изображение оптимизировано: " +
                  f"{original_width}x{original_height} -> " +
                  f"{self.width}x{self.height}")
            print(f"Количество точек: {self.width * self.height}")
            print(f"Диапазон высот: {self.min_z:.1f} - {self.max_z:.1f}")

            # 3D точки
            self.create_points()

            # Линии каркаса (оптимизированные)
            self.create_lines_optimized_for_image()

            return self.normalize_points()

        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            return None, []

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

    # Создание линий каркаса (оптимизированная для изображений)
    def create_lines_optimized_for_image(self):
        # Ограничиваем максимальное количество линий для изображений
        max_lines = 20000

        if self.width * self.height * 2 > max_lines:
            # Если слишком много точек, прореживаем линии
            skip_factor = int(np.sqrt((self.width * self.height * 2) /
                                      max_lines))

            horizontal_lines = []
            y = 0
            while y < self.height:
                x = 0
                while x < self.width - 1:
                    idx1 = y * self.width + x
                    idx2 = y * self.width + (x + 1)
                    horizontal_lines.append([idx1, idx2])
                    x += skip_factor
                y += skip_factor

            vertical_lines = []
            x = 0
            while x < self.width:
                y = 0
                while y < self.height - 1:
                    idx1 = y * self.width + x
                    idx2 = (y + 1) * self.width + x
                    vertical_lines.append([idx1, idx2])
                    y += skip_factor
                x += skip_factor

            self.lines = np.array(horizontal_lines + vertical_lines,
                                  dtype=np.int32)
        else:
            # Для небольших изображений используем все линии
            horizontal_indices = np.arange(self.height * self.width). \
                reshape(self.height, self.width)
            horizontal_lines = np.stack([
                horizontal_indices[:, :-1].flatten(),
                horizontal_indices[:, 1:].flatten()
            ], axis=1)

            vertical_lines = np.stack([
                horizontal_indices[:-1, :].flatten(),
                horizontal_indices[1:, :].flatten()
            ], axis=1)

            self.lines = np.vstack([horizontal_lines, vertical_lines]). \
                astype(np.int32)

        print(f"Создано {len(self.lines)} линий")

    # Создание линий каркаса (для FDF)
    def create_lines(self):
        # Создание массива индексов для горизонтальных линий
        horizontal_indices = np.arange(self.height * self.width). \
            reshape(self.height, self.width)
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
        self.lines = np.vstack([horizontal_lines, vertical_lines]). \
            astype(np.int32)

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
                # Сохраняем исходные Z для цветовой градации
                original_z = normalized_points[:, 2].copy()

                # Усиливаем рельеф (сильнее для изображений)
                if self.is_image:
                    z_scale = 1.0 / z_range  # Усиление для изображений
                else:
                    z_scale = 0.5 / z_range  # Усиление для FDF

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
