import os
import pytest
import winreg  # Модуль только для Windows


def compare_files_byte_by_byte(file1, file2):
    """Сравнивает два файла побайтово."""
    try:
        with open(file1, "rb") as f1, open(file2, "rb") as f2:
            while True:
                byte1 = f1.read(1)
                byte2 = f2.read(1)
                if byte1 != byte2:
                    return False
                if not byte1:  # Если дошли до конца первого файла
                    break # Выходим из цикла, если дошли до конца
                if not byte2: # Проверка, что второй файл тоже закончился
                    return False #  Второй файл короче

            # Если первый файл закончился, а второй - нет, то файлы различаются
            if f2.read(1):
                return False
        return True
    except FileNotFoundError:
        return False


def compare_applications(app1_dir, app2_dir):
    """Сравнивает два приложения побайтово, сравнивая файлы в каталогах."""
    differences = []

    for root, _, files in os.walk(app1_dir):
        for file in files:
            app1_file = os.path.join(root, file)
            relative_path = os.path.relpath(app1_file, app1_dir)
            app2_file = os.path.join(app2_dir, relative_path)

            if not os.path.exists(app2_file):
                differences.append(f"Файл {relative_path} отсутствует во втором приложении.")
                continue

            if not compare_files_byte_by_byte(app1_file, app2_file):
                differences.append(f"Файл {relative_path} различается побайтово.")

    # Проверяем файлы, которые есть только во втором приложении
    for root, _, files in os.walk(app2_dir):
        for file in files:
            app2_file = os.path.join(root, file)
            relative_path = os.path.relpath(app2_file, app2_dir)
            app1_file = os.path.join(app1_dir, relative_path)
            if not os.path.exists(app1_file):
                differences.append(f"Файл {relative_path} отсутствует в первом приложении.")

    if differences:
        return 'Не корректно скачано'
    else:
        return 'Корректно скачано'


def get_app_install_path(app_name):
    """Ищет путь к установке приложения в реестре Windows."""
    sub_keys = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]

    for sub_key in sub_keys:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(key, i)
                    app_key = winreg.OpenKey(key, name)
                    try:
                        display_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                        if app_name.lower() in display_name.lower():
                            try:
                                install_location, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                return install_location.replace("\\", "\\\\")  # Заменяем обратные слеши на двойные
                            except FileNotFoundError:
                                pass

                            try:
                                display_icon, _ = winreg.QueryValueEx(app_key, "DisplayIcon")
                                if "," in display_icon:
                                    display_icon = display_icon.split(",")[0]
                                return display_icon.replace("\\", "\\\\") # Заменяем обратные слеши на двойные
                            except FileNotFoundError:
                                pass

                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(app_key)

                except OSError:
                    break

                i += 1

        except FileNotFoundError:
            pass

        finally:
            if key:
                winreg.CloseKey(key)

    return None


def is_app_installed(app_name):
    """Проверяет, установлено ли приложение в Windows, ища записи в реестре."""
    sub_keys = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]  # Для 32-битных приложений на 64-битной системе

    for sub_key in sub_keys:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(key, i)
                    app_key = winreg.OpenKey(key, name)
                    try:
                        display_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                        if app_name.lower() in display_name.lower():
                            return 'Установлено'
                    except FileNotFoundError:
                        pass # У некоторых ключей нет "DisplayName"
                    finally:
                        winreg.CloseKey(app_key)

                except OSError:
                    break # Больше нет подключей

                i += 1

        except FileNotFoundError:
            pass # Подключ не существует

        finally:
            if key:
                winreg.CloseKey(key)

    return 'Не установлено'


global app
app = get_app_install_path('VK Teams') + 'vkteams.exe' # это путь к приложению
@pytest.mark.parametrize("app, expected_result", [
    ("VK Teams", 'Установлено')
])
def test_is_app_installed(app, expected_result):
    assert is_app_installed(app) == expected_result

'''
Если приложение установлено, тест должен пройти.
Тем самым мы проверим, установилось автоматически приложение или нет.
'''


@pytest.mark.parametrize("file, expected_result", [
    (app, 'Корректно скачано')
])
def test_compare_applications(file, expected_result):
    assert compare_applications(app, "VK Teams.lnk") == expected_result

'''
Мы побайтово сравниваем оригинальное приложение (то есть 100% корректное),
с тем, что установилось. Если они совпадают, значит, что установка корректна.
'''

