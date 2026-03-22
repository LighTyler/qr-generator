from schemas.user import UserResponse
from repositories.user import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int) -> UserResponse | None:
        user = await self.user_repository.get(user_id)
        if not user:
            return None
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
        )
