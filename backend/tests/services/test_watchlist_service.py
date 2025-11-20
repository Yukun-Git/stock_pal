"""Unit tests for WatchlistService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.watchlist_service import WatchlistService


class TestWatchlistService:
    """Test cases for WatchlistService."""

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_get_user_watchlist_success(self, mock_db):
        """Test getting user watchlist successfully."""
        # Arrange
        user_id = 'test-user-123'
        mock_results = [
            {
                'id': 1,
                'stock_code': '600000',
                'stock_name': '浦发银行',
                'note': '测试备注',
                'group_id': 1,
                'created_at': '2025-11-19',
                'updated_at': '2025-11-19',
                'group_name': '银行板块',
                'group_color': '#1890ff'
            }
        ]
        mock_db.execute_query.return_value = mock_results

        # Act
        result = WatchlistService.get_user_watchlist(user_id)

        # Assert
        assert len(result) == 1
        assert result[0]['stock_code'] == '600000'
        assert result[0]['stock_name'] == '浦发银行'
        mock_db.execute_query.assert_called_once()

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_get_user_watchlist_with_group_filter(self, mock_db):
        """Test getting watchlist with group filter."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 1
        mock_db.execute_query.return_value = []

        # Act
        WatchlistService.get_user_watchlist(user_id, group_id=group_id)

        # Assert
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'ws.group_id = %s' in query
        assert user_id in params
        assert group_id in params

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_success(self, mock_db):
        """Test adding stock successfully."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'
        stock_name = '浦发银行'

        # Mock: check_query returns empty (stock doesn't exist)
        # Mock: insert_query returns created record
        mock_db.execute_query.side_effect = [
            [],  # check_query: stock doesn't exist
            [{'id': 1, 'stock_code': stock_code, 'stock_name': stock_name,
              'group_id': None, 'note': None, 'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistService.add_stock(user_id, stock_code, stock_name)

        # Assert
        assert result['stock_code'] == stock_code
        assert result['stock_name'] == stock_name
        assert mock_db.execute_query.call_count == 2

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_duplicate(self, mock_db):
        """Test adding duplicate stock raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'
        stock_name = '浦发银行'

        # Mock: check_query returns existing record
        mock_db.execute_query.return_value = [{'id': 1}]

        # Act & Assert
        with pytest.raises(ValueError, match='该股票已在自选股中'):
            WatchlistService.add_stock(user_id, stock_code, stock_name)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_invalid_code(self, mock_db):
        """Test adding stock with invalid code raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        invalid_codes = ['12345', '1234567', 'ABCDEF', '']

        # Act & Assert
        for code in invalid_codes:
            with pytest.raises(ValueError, match='股票代码必须为6位数字'):
                WatchlistService.add_stock(user_id, code, '测试股票')

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_empty_name(self, mock_db):
        """Test adding stock with empty name raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'

        # Act & Assert
        with pytest.raises(ValueError, match='股票名称不能为空'):
            WatchlistService.add_stock(user_id, stock_code, '')

        with pytest.raises(ValueError, match='股票名称不能为空'):
            WatchlistService.add_stock(user_id, stock_code, '   ')

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_with_group(self, mock_db):
        """Test adding stock with group_id."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'
        stock_name = '浦发银行'
        group_id = 5

        # Mock: check_query (stock doesn't exist), group_check (group exists), insert
        mock_db.execute_query.side_effect = [
            [],  # stock doesn't exist
            [{'id': 5}],  # group exists
            [{'id': 1, 'stock_code': stock_code, 'stock_name': stock_name,
              'group_id': group_id, 'note': None, 'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistService.add_stock(user_id, stock_code, stock_name, group_id=group_id)

        # Assert
        assert result['group_id'] == group_id
        assert mock_db.execute_query.call_count == 3

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_add_stock_invalid_group(self, mock_db):
        """Test adding stock with non-existent group raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'
        stock_name = '浦发银行'
        group_id = 999

        # Mock: check_query (stock doesn't exist), group_check (group doesn't exist)
        mock_db.execute_query.side_effect = [
            [],  # stock doesn't exist
            []   # group doesn't exist
        ]

        # Act & Assert
        with pytest.raises(ValueError, match='指定的分组不存在或不属于当前用户'):
            WatchlistService.add_stock(user_id, stock_code, stock_name, group_id=group_id)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_delete_stock_success(self, mock_db):
        """Test deleting stock successfully."""
        # Arrange
        user_id = 'test-user-123'
        stock_id = 1

        # Mock: delete returns None, check returns empty (deleted)
        mock_db.execute_query.side_effect = [
            None,  # delete
            []     # check: no remaining rows
        ]

        # Act
        result = WatchlistService.delete_stock(user_id, stock_id)

        # Assert
        assert result is True
        assert mock_db.execute_query.call_count == 2

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_update_stock_success(self, mock_db):
        """Test updating stock successfully."""
        # Arrange
        user_id = 'test-user-123'
        stock_id = 1
        updates = {'note': '新备注', 'group_id': 5}

        # Mock: check_query (stock exists), group_check (group exists), update
        mock_db.execute_query.side_effect = [
            [{'id': 1}],  # stock exists
            [{'id': 5}],  # group exists
            [{'id': 1, 'stock_code': '600000', 'stock_name': '浦发银行',
              'group_id': 5, 'note': '新备注', 'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistService.update_stock(user_id, stock_id, updates)

        # Assert
        assert result['note'] == '新备注'
        assert result['group_id'] == 5
        assert mock_db.execute_query.call_count == 3

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_update_stock_not_found(self, mock_db):
        """Test updating non-existent stock raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_id = 999
        updates = {'note': '新备注'}

        # Mock: check_query returns empty
        mock_db.execute_query.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match='记录不存在或不属于当前用户'):
            WatchlistService.update_stock(user_id, stock_id, updates)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_update_stock_empty_updates(self, mock_db):
        """Test updating with no valid fields raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_id = 1
        updates = {'invalid_field': 'value'}

        # Mock: check_query (stock exists)
        mock_db.execute_query.return_value = [{'id': 1}]

        # Act & Assert
        with pytest.raises(ValueError, match='没有可更新的字段'):
            WatchlistService.update_stock(user_id, stock_id, updates)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_batch_delete_stocks_success(self, mock_db):
        """Test batch deleting stocks successfully."""
        # Arrange
        user_id = 'test-user-123'
        stock_ids = [1, 2, 3]

        # Mock: delete returns None, check returns 0 remaining
        mock_db.execute_query.side_effect = [
            None,  # delete
            [{'count': 0}]  # check: all deleted
        ]

        # Act
        result = WatchlistService.batch_delete_stocks(user_id, stock_ids)

        # Assert
        assert result == 3
        assert mock_db.execute_query.call_count == 2

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_batch_delete_stocks_empty_list(self, mock_db):
        """Test batch deleting with empty list raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_ids = []

        # Act & Assert
        with pytest.raises(ValueError, match='股票ID列表不能为空'):
            WatchlistService.batch_delete_stocks(user_id, stock_ids)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_batch_delete_stocks_too_many(self, mock_db):
        """Test batch deleting with too many IDs raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        stock_ids = list(range(51))  # 51 IDs

        # Act & Assert
        with pytest.raises(ValueError, match='批量删除最多支持50只股票'):
            WatchlistService.batch_delete_stocks(user_id, stock_ids)

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_check_stock_in_watchlist_exists(self, mock_db):
        """Test checking stock that exists in watchlist."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'

        mock_db.execute_query.return_value = [
            {'watchlist_id': 1, 'group_id': 5, 'group_name': '银行板块'}
        ]

        # Act
        result = WatchlistService.check_stock_in_watchlist(user_id, stock_code)

        # Assert
        assert result['in_watchlist'] is True
        assert result['watchlist_id'] == 1
        assert result['group_name'] == '银行板块'

    @patch('app.services.watchlist_service.DatabaseManager')
    def test_check_stock_in_watchlist_not_exists(self, mock_db):
        """Test checking stock that doesn't exist in watchlist."""
        # Arrange
        user_id = 'test-user-123'
        stock_code = '600000'

        mock_db.execute_query.return_value = []

        # Act
        result = WatchlistService.check_stock_in_watchlist(user_id, stock_code)

        # Assert
        assert result['in_watchlist'] is False
        assert 'watchlist_id' not in result
