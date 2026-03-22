from collections.abc import Iterable

from dishka import Provider
from dishka.integrations.fastapi import FastapiProvider

from entrypoint.ioc import (
    ConfigProvider,
    DatabaseProvider,
    RepositoryProvider,
    ServiceProvider,
)


def get_providers() -> Iterable[Provider]:
    return (
        DatabaseProvider(),
        ServiceProvider(),
        RepositoryProvider(),
        FastapiProvider(),
        ConfigProvider(),
    )
