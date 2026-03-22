"""
Консольная утилита для создания пользователей.

Позволяет создавать пользователей через командную строку или интерактивный режим.
Поддерживает различные роли пользователей (user, employee, admin).

Использование:
    python -m create_user --email user@example.com --username john --role admin
    python -m create_user  # Интерактивный режим

Аргументы командной строки:
    --email: Email пользователя
    --username: Имя пользователя
    --role: Роль (1/user, 2/employee, 3/admin)
    --password: Пароль

Note:
    Пароль хешируется перед сохранением в БД.
    При интерактивном режиме пароль запрашивается дважды для подтверждения.
"""

import argparse
import asyncio
import getpass
import os
import sys

from dishka import FromDishka

from entrypoint.ioc.integrations.console_integration import inject
from entrypoint.ioc.registry import get_providers
from entrypoint.setup import create_async_container
from models import RoleEnum
from schemas.user import UserCreateConsole
from services import UserService

# Настройка кодировки для корректного отображения Unicode
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")


@inject
async def create_user_from_args(
    args,
    dishka_container,
    user_service: FromDishka[UserService],
):
    """
    Создание пользователя из аргументов командной строки.
    
    Получает данные пользователя из аргументов или интерактивного ввода,
    создаёт DTO и вызывает сервис для создания пользователя.
    
    Args:
        args: Разобранные аргументы командной строки
        dishka_container: DI контейнер (для @inject декоратора)
        user_service: Сервис пользователей (внедряется через DI)
        
    Returns:
        User: Созданный пользователь
        
    Note:
        При ошибке создания пользователя завершает программу с кодом 1
    """
    # Получаем данные пользователя
    email = get_email(args)
    username = get_username(args)
    role = get_role(args)
    password = get_password(args)

    # Создаём DTO для консольного создания
    user_data = UserCreateConsole(
        email=email,
        username=username,
        role=role,
        password=password,
    )
    
    try:
        # Создаём пользователя через сервис
        result = await user_service.create_user_for_console(user_data)
        
        # Выводим информацию о созданном пользователе
        print("----------------------------------------")
        print("| User created successfully!           |")
        print("----------------------------------------")
        print(f"| ID:       {result.id:<27} |")
        print("----------------------------------------")
        print(f"| Email:    {result.email:<27} |")
        print("----------------------------------------")
        print(f"| Username: {result.username:<27} |")
        print("----------------------------------------")
        print(f"| Role:     {result.role:<27} |")
        print("----------------------------------------")
        return result
        
    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)


def parse_args():
    """
    Парсинг аргументов командной строки.
    
    Returns:
        argparse.Namespace: Разобранные аргументы
    """
    parser = argparse.ArgumentParser(
        description="Create a new user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--email",
        type=str,
        help="User email address",
    )
    parser.add_argument("--username", type=str, help="Username")
    parser.add_argument(
        "--role",
        type=str,
        help="User role: 1=user, 2=employee, 3=admin (default: 1)",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="User password",
    )
    return parser.parse_args()


def get_user_input(
    prompt: str,
    default: str = None,
    hide_input: bool = False,
) -> str:
    """
    Получение ввода от пользователя.
    
    Поддерживает скрытый ввод (для паролей) и значения по умолчанию.
    
    Args:
        prompt: Текст подсказки
        default: Значение по умолчанию (опционально)
        hide_input: Скрыть ввод (для паролей)
        
    Returns:
        str: Введённое значение или значение по умолчанию
    """
    if default:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "

    if hide_input:
        # Скрытый ввод для паролей
        value = getpass.getpass(prompt)
    else:
        try:
            # Прямой ввод с корректной кодировкой
            sys.stdout.write(prompt)
            sys.stdout.flush()
            raw = sys.stdin.buffer.readline()
            value = raw.decode("utf-8", errors="replace").strip()
        except Exception:
            value = input(prompt).strip()

    return value if value else (default or "")


def get_email(args):
    """
    Получение email из аргументов или интерактивного ввода.
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        str: Email адрес
        
    Raises:
        SystemExit: Если email не указан
    """
    if args.email:
        return args.email
    email = get_user_input("Email")
    if not email:
        print("Error: Email is required")
        sys.exit(1)
    return email


def get_username(args):
    """
    Получение имени пользователя из аргументов или интерактивного ввода.
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        str: Имя пользователя
        
    Raises:
        SystemExit: Если имя не указано
    """
    if args.username:
        return args.username
    username = get_user_input("Username")
    if not username:
        print("Error: Username is required")
        sys.exit(1)
    return username


def get_role(args):
    """
    Получение роли из аргументов или интерактивного выбора.
    
    Поддерживает числовые (1, 2, 3) и текстовые (user, employee, admin) значения.
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        str: Роль пользователя (значение из RoleEnum)
        
    Raises:
        SystemExit: Если роль невалидна
    """
    if args.role:
        role_input = args.role.lower()
        if role_input == "1" or role_input == "user":
            return RoleEnum.USER
        elif role_input == "2" or role_input == "employee":
            return RoleEnum.EMPLOYEE
        elif role_input == "3" or role_input == "admin":
            return RoleEnum.ADMIN
        else:
            print(
                f"Error: Invalid role '{args.role}'.",
                "Use 1, 2, 3 or user, employee, admin.",
            )
            sys.exit(1)

    # Интерактивный выбор роли
    print("\nAvailable roles:")
    print("1. user (8+ chars, 1 uppercase, 1 digit)")
    print("2. employee (12+ chars, 1 uppercase, 1 digit, 1 special char)")
    print("3. admin (12+ chars, 1 uppercase, 1 digit, 1 special char)")

    while True:
        role_input = get_user_input("Choose role (1-3)", "1")
        if not role_input:
            role_input = "1"

        if role_input == "1":
            return RoleEnum.USER
        elif role_input == "2":
            return RoleEnum.EMPLOYEE
        elif role_input == "3":
            return RoleEnum.ADMIN
        else:
            print("Error: Please enter 1, 2, or 3.")


def get_password(args):
    """
    Получение пароля из аргументов или интерактивного ввода.
    
    При интерактивном вводе запрашивает подтверждение пароля.
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        str: Пароль в открытом виде (будет захеширован сервисом)
        
    Raises:
        SystemExit: Если пароль не указан или не совпадает при подтверждении
    """
    if args.password:
        return args.password

    # Интерактивный ввод пароля с подтверждением
    while True:
        password = get_user_input("Password", hide_input=True)
        if not password:
            print("Error: Password is required")
            continue

        # Подтверждение пароля
        password_confirm = get_user_input("Password (again)", hide_input=True)
        if password != password_confirm:
            print("Error: Passwords don't match. Please try again.")
            continue

        break

    return password


async def main():
    """
    Основная функция создания пользователя.
    
    Создаёт DI контейнер и вызывает функцию создания пользователя.
    Обрабатывает прерывание пользователем (Ctrl+C).
    """
    try:
        args = parse_args()
        container = create_async_container(get_providers())
        await create_user_from_args(args, dishka_container=container)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
