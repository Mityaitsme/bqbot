import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.app.bot.handlers import handle_message

@pytest.mark.asyncio
async def test_handle_message():
  mock_tg_msg = AsyncMock()
  mock_tg_msg.bot = MagicMock()
  
  with patch('src.app.bot.handlers.MessageHandler.from_tg') as mock_from_tg:
    with patch('src.app.bot.handlers.Router.route') as mock_route:
      with patch('src.app.bot.handlers.send_message') as mock_send:
        mock_core_msg = MagicMock()
        mock_from_tg.return_value = mock_core_msg
        
        mock_response = MagicMock()
        mock_route.return_value = mock_response
        
        await handle_message(mock_tg_msg)
        
        mock_from_tg.assert_called_once_with(mock_tg_msg)
        mock_route.assert_called_once_with(mock_core_msg)
        mock_send.assert_called_once_with(mock_tg_msg.bot, mock_response)
