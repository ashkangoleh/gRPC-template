import pytest
import grpc
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_get_user_not_found():
    context = AsyncMock()
    context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
