import pytest
import runpy
from unittest.mock import patch, AsyncMock, MagicMock
from src.main import setup_logging, main

def test_setup_logging():
  with patch('src.main.dictConfig') as mock_config:
    setup_logging()
    mock_config.assert_called_once()

@pytest.mark.asyncio
async def test_main():
  with patch('src.main.setup_logging') as mock_setup:
    with patch('src.main.Bot') as mock_bot_cls:
      with patch('src.main.Dispatcher') as mock_dp_cls:
        mock_bot = AsyncMock()
        mock_bot_cls.return_value = mock_bot
        
        mock_dp = AsyncMock()
        mock_dp.include_router = MagicMock()
        mock_dp_cls.return_value = mock_dp
        
        await main()
        
        mock_setup.assert_called_once()
        mock_bot_cls.assert_called_once()
        mock_dp.include_router.assert_called_once()
        mock_dp.start_polling.assert_called_once_with(mock_bot)

def test_main_execution_via_runpy():
  with patch('asyncio.run') as mock_asyncio_run:
    def close_coroutine(coro):
      if hasattr(coro, 'close'):
        coro.close()
    mock_asyncio_run.side_effect = close_coroutine

    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
      try:
        runpy.run_module('src.main', run_name='__main__')
      except (ImportError, ValueError):
        pass
    
    mock_asyncio_run.assert_called_once()