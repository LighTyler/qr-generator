"""
Провайдер конфигурации для dependency injection.

Предоставляет конфигурацию приложения через DI контейнер Dishka.
Конфигурация создаётся один раз при старте приложения (Scope.APP).
"""

from dishka import Provider, Scope, provide

from entrypoint.config import Config, create_config


class ConfigProvider(Provider):
    """
    Провайдер конфигурации приложения.
    
    Предоставляет объект Config для всех компонентов приложения.
    Конфигурация создаётся один раз и используется всё время жизни приложения.
    
    Scope: APP - один экземпляр на всё приложение
    """
    scope = Scope.APP

    @provide
    def get_config(self) -> Config:
        """
        Получение конфигурации приложения.
        
        Returns:
            Config: Объект конфигурации со всеми настройками
        """
        config = create_config()
        return config
