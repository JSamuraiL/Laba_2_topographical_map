import pygame
from OpenGL.GL import glLoadIdentity
import sys
import os
import tkinter as tk
from tkinter import filedialog

from file_parser import FDFParser
from camera import Camera
from renderer import Renderer


# Загрузка файла
def load_file(filename):
    parser = FDFParser()
    points, lines = parser.parse_file(filename)

    if points is None or lines is None:
        print(f"Ошибка загрузки файла: {filename}")
        return None, None, None

    # Преобразование точек в список для совместимости
    if hasattr(points, 'tolist'):
        points_list = points.tolist()
    else:
        points_list = points

    if hasattr(lines, 'tolist'):
        lines_list = lines.tolist()
    else:
        lines_list = lines

    return parser, points_list, lines_list


# Открытие диалога выбора файла
def select_file_dialog():
    # Скрытое окно tkinter
    root = tk.Tk()
    root.withdraw()

    # Настройка диалога выбора файла
    file_path = filedialog.askopenfilename(
        title="Выберите файл",
        filetypes=[
            ("FDF файлы", "*.fdf"),
            ("Изображения", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.tif;*.gif;" +
             "*.psd"),
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*")
        ]
    )

    # Уничтожение окна tkinter
    root.destroy()

    return file_path


# Поиск тестового файла
def find_test_file():
    test_files = ["test.fdf", "sample.fdf", "example.fdf",
                  "test.png", "sample.jpg", "example.bmp"]
    i = 0
    while i < len(test_files):
        if os.path.exists(test_files[i]):
            print(f"Найден тестовый файл: {test_files[i]}")
            return test_files[i]
        i += 1
    return None


# Основная функция
def main():
    # Проверка аргументов командной строки
    if len(sys.argv) < 2:
        print("Использование: python main.py [расположение файла]")
        print("Пример: python main.py test.fdf")

        # Попытка найти тестовый файл
        filename = find_test_file()

        if filename is None:
            # Если файл не указан и нет тестового, открываем диалог
            filename = select_file_dialog()
            if not filename:
                print("Файл не выбран. Выход.")
                sys.exit(1)
    else:
        filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"Файл {filename} не найден!")

        # Попытка открыть диалог выбора
        filename = select_file_dialog()
        if not filename:
            print("Файл не выбран. Выход.")
            sys.exit(1)

    # Проверка расширения файла
    ext = os.path.splitext(filename)[1].lower()
    supported_extensions = ['.fdf', '.txt', '.png', '.jpg', '.jpeg',
                            '.bmp', '.tiff', '.tif', '.gif', '.psd']

    ext_found = False
    i = 0
    while i < len(supported_extensions):
        if ext == supported_extensions[i]:
            ext_found = True
            break
        i += 1

    if not ext_found:
        print(f"Неподдерживаемый формат файла: {ext}")
        print("Поддерживаемые форматы: .fdf, .txt, .png, .jpg, .jpeg, .bmp, " +
              ".tiff, .tif, .gif, .psd")

        # Попытка открыть диалог выбора
        filename = select_file_dialog()
        if not filename:
            print("Файл не выбран. Выход.")
            sys.exit(1)

    # Загрузка файла
    parser, points_list, lines_list = load_file(filename)

    if parser is None:
        print("Не удалось загрузить файл.")
        sys.exit(1)

    # Инициализация рендерера и камеры
    renderer = Renderer()
    camera = Camera()

    # Инициализация данных для модели
    renderer.init_wireframe(points_list, lines_list,
                            parser.norm_min_z, parser.norm_max_z,
                            parser.width, parser.height)

    # Загрузка шрифта для отображения информации
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 16)

    clock = pygame.time.Clock()

    print(f"Загружено {len(points_list)} точек и {len(lines_list)} линий")
    print(f"Размер: {parser.width}x{parser.height}")
    print("Управление:")
    print("  ЛКМ + движение - вращение модели")
    print("  Колесо мыши - масштабирование" +
          "(вверх - приближение, вниз - отдаление)")
    print("  ESC - выход")
    print("  Градиенты: 1-по умолчанию, 2-земля/горы, 3-огонь, 4-лед/снег")
    print("  O - Открыть новый файл")
    print("  R - Сбросить вид камеры")

    # Главный цикл
    running = True
    current_filename = os.path.basename(filename)

    while running:
        # Обработка событий
        events = pygame.event.get()
        i = 0
        while i < len(events):
            event = events[i]

            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_o:
                    # Открытие нового файла
                    new_filename = select_file_dialog()
                    if new_filename and os.path.exists(new_filename):
                        # Загрузка нового файла
                        new_parser, new_points, new_lines = load_file(
                            new_filename)
                        if new_parser is not None:
                            parser = new_parser
                            points_list = new_points
                            lines_list = new_lines
                            current_filename = os.path.basename(new_filename)

                            # Инициализация данных для новой модели
                            renderer.init_wireframe(points_list, lines_list,
                                                    parser.norm_min_z,
                                                    parser.norm_max_z,
                                                    parser.width,
                                                    parser.height)

                            print(f"Загружен файл: {current_filename}")
                            print(f"  Точек: {len(points_list)}," +
                                  f" Линий: {len(lines_list)}")
                            print(f"  Размер: {parser.width}x{parser.height}")
                elif event.key == pygame.K_r:
                    # Сброс камеры
                    camera.reset()
                    print("Вид камеры сброшен")
                elif event.key == pygame.K_1:
                    # Градиент по умолчанию
                    renderer.set_gradient([
                        (0.0, 0.0, 1.0),   # Синий
                        (0.0, 1.0, 1.0),   # Голубой
                        (0.0, 1.0, 0.0),   # Зеленый
                        (1.0, 1.0, 0.0),   # Желтый
                        (1.0, 0.0, 0.0)    # Красный
                    ])
                elif event.key == pygame.K_2:
                    # Градиент "Земля/Горы"
                    renderer.set_gradient([
                        (0.2, 0.6, 0.2),   # Темно-зеленый (низины)
                        (0.5, 0.8, 0.3),   # Светло-зеленый
                        (0.7, 0.6, 0.4),   # Коричневый
                        (0.8, 0.7, 0.6),   # Светло-коричневый
                        (1.0, 1.0, 1.0)    # Белый (снежные вершины)
                    ])
                elif event.key == pygame.K_3:
                    # Градиент "Огонь"
                    renderer.set_gradient([
                        (0.0, 0.0, 0.0),   # Черный
                        (0.5, 0.0, 0.0),   # Темно-красный
                        (1.0, 0.5, 0.0),   # Оранжевый
                        (1.0, 1.0, 0.0),   # Желтый
                        (1.0, 1.0, 1.0)    # Белый
                    ])
                elif event.key == pygame.K_4:
                    # Градиент "Лед/Снег"
                    renderer.set_gradient([
                        (0.0, 0.2, 0.8),   # Темно-синий
                        (0.3, 0.5, 1.0),   # Голубой
                        (0.6, 0.8, 1.0),   # Светло-голубой
                        (0.8, 0.9, 1.0),   # Очень светлый голубой
                        (1.0, 1.0, 1.0)    # Белый
                    ])
            elif event.type == pygame.VIDEORESIZE:
                # Обработка изменения размера окна
                renderer.handle_resize(event.w, event.h)
            elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                pygame.MOUSEMOTION]:
                camera.handle_event(event)
            i += 1

        # Очистка экрана
        renderer.clear()

        # Применение трансформаций камеры
        glLoadIdentity()
        camera.apply_transformations()

        # Отрисовка
        renderer.render_grid()
        renderer.render_wireframe()
        renderer.render_axes()

        # Отображение информации
        renderer.display_info(font, current_filename, len(points_list),
                              len(lines_list),
                              camera.rotation_x, camera.rotation_y,
                              camera.zoom)

        # Обновление экрана
        pygame.display.flip()
        clock.tick(60)

    # Очистка ресурсов
    renderer.cleanup()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
