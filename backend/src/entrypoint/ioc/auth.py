"""
Провайдер аутентификации для dependency injection.

Отвечает за извлечение и валидацию пользователя из JWT токена.
Поддерживает аутентификацию через заголовок Authorization и cookie.
"""

from dishka import Provider, Scope, provide
from fastapi import HTTPException, Request, status
from jwt import InvalidTokenError

from schemas.user import UserResponse
from services.user import UserService
from utils.jwt_utils import decode_jwt


class AuthProvider(Provider):
    """
    Провайдер аутентификации пользователей.
    
    Извлекает пользователя из JWT токена в каждом запросе.
    Поддерживает два способа передачи токена:
    1. Заголовок Authorization: Bearer <token>
    2. Cookie: access_token=<token>
    
    Scope: REQUEST - аутентификация выполняется для каждого запроса
    
    Raises:
        HTTPException: 401 UNAUTHORIZED если токен невалиден или пользователь не найден
    """
    scope = Scope.REQUEST

    @provide
    async def get_current_user(
        self,
        user_service: UserService,
        request: Request,
    ) -> UserResponse:
        """
        Получение текущего пользователя из запроса.
        
        Извлекает JWT токен из заголовка Authorization или cookie,
        декодирует его и возвращает данные пользователя.
        
        Args:
            user_service: Сервис для работы с пользователями
            request: Объект HTTP запроса FastAPI
            
        Returns:
            UserResponse: Данные аутентифицированного пользователя
            
        Raises:
            HTTPException: 401 если:
                - Неверная схема авторизации (не Bearer)
                - Невалидный заголовок Authorization
                - Токен не предоставлен
                - Токен невалиден или просрочен
                - Пользователь не найден в БД
        """
        # Пытаемся получить токен из заголовка Authorization
        authorization = request.headers.get("Authorization")

        if authorization:
            try:
                scheme, token = authorization.split()
                # Проверяем схему авторизации (должна быть Bearer)
                if scheme.lower() != "bearer":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication scheme",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header",
                )
        else:
            # Если заголовка нет, пробуем получить токен из cookie
            token = request.cookies.get("access_token")

        # Проверяем наличие токена
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
            )

        # Декодируем JWT токен
        try:
            decoded_token = decode_jwt(token)
        except InvalidTokenError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from err

        # Извлекаем ID пользователя из subject токена
        user_id = int(decoded_token.get("sub"))

        if user_id:
            # Получаем пользователя из БД
            user = await user_service.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            # Возвращаем DTO с данными пользователя
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
            )
