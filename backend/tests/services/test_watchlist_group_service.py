"""Unit tests for WatchlistGroupService."""

import pytest
from unittest.mock import patch
from app.services.watchlist_group_service import WatchlistGroupService


class TestWatchlistGroupService:
    """Test cases for WatchlistGroupService."""

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_get_user_groups_success(self, mock_db):
        """Test getting user groups successfully."""
        # Arrange
        user_id = 'test-user-123'
        mock_results = [
            {
                'id': 1,
                'name': '未分类',
                'color': '#999999',
                'sort_order': 0,
                'created_at': '2025-11-19',
                'updated_at': '2025-11-19'
            },
            {
                'id': 2,
                'name': '银行板块',
                'color': '#1890ff',
                'sort_order': 1,
                'created_at': '2025-11-19',
                'updated_at': '2025-11-19'
            }
        ]
        mock_db.execute_query.return_value = mock_results

        # Act
        result = WatchlistGroupService.get_user_groups(user_id)

        # Assert
        assert len(result) == 2
        assert result[0]['name'] == '未分类'
        assert result[1]['name'] == '银行板块'
        mock_db.execute_query.assert_called_once()

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_get_user_groups_with_counts(self, mock_db):
        """Test getting groups with stock counts."""
        # Arrange
        user_id = 'test-user-123'
        mock_results = [
            {
                'id': 1,
                'name': '未分类',
                'color': '#999999',
                'sort_order': 0,
                'created_at': '2025-11-19',
                'updated_at': '2025-11-19',
                'stock_count': 5
            }
        ]
        mock_db.execute_query.return_value = mock_results

        # Act
        result = WatchlistGroupService.get_user_groups(user_id, include_counts=True)

        # Assert
        assert len(result) == 1
        assert result[0]['stock_count'] == 5
        # Verify query includes COUNT
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert 'COUNT(ws.id)' in query

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_create_group_success(self, mock_db):
        """Test creating group successfully."""
        # Arrange
        user_id = 'test-user-123'
        name = '科技板块'
        color = '#52c41a'

        # Mock: check_query (no duplicate), max_query (next order), insert
        mock_db.execute_query.side_effect = [
            [],  # no duplicate
            [{'next_order': 2}],  # max order
            [{'id': 10, 'name': name, 'color': color, 'sort_order': 2,
              'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistGroupService.create_group(user_id, name, color)

        # Assert
        assert result['name'] == name
        assert result['color'] == color
        assert result['sort_order'] == 2
        assert mock_db.execute_query.call_count == 3

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_create_group_duplicate_name(self, mock_db):
        """Test creating group with duplicate name raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        name = '银行板块'

        # Mock: check_query returns existing group
        mock_db.execute_query.return_value = [{'id': 1}]

        # Act & Assert
        with pytest.raises(ValueError, match='分组名称已存在'):
            WatchlistGroupService.create_group(user_id, name)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_create_group_empty_name(self, mock_db):
        """Test creating group with empty name raises ValueError."""
        # Arrange
        user_id = 'test-user-123'

        # Act & Assert
        with pytest.raises(ValueError, match='分组名称不能为空'):
            WatchlistGroupService.create_group(user_id, '')

        with pytest.raises(ValueError, match='分组名称不能为空'):
            WatchlistGroupService.create_group(user_id, '   ')

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_create_group_name_too_long(self, mock_db):
        """Test creating group with name too long raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        long_name = 'A' * 51  # 51 characters

        # Act & Assert
        with pytest.raises(ValueError, match='分组名称最长50个字符'):
            WatchlistGroupService.create_group(user_id, long_name)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_update_group_success(self, mock_db):
        """Test updating group successfully."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 5
        updates = {'name': '新名称', 'color': '#ff0000'}

        # Mock: check_query (group exists), dup_query (no duplicate), update
        mock_db.execute_query.side_effect = [
            [{'id': 5, 'name': '旧名称'}],  # group exists
            [],  # no duplicate name
            [{'id': 5, 'name': '新名称', 'color': '#ff0000', 'sort_order': 1,
              'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistGroupService.update_group(user_id, group_id, updates)

        # Assert
        assert result['name'] == '新名称'
        assert result['color'] == '#ff0000'
        assert mock_db.execute_query.call_count == 3

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_update_group_not_found(self, mock_db):
        """Test updating non-existent group raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 999
        updates = {'name': '新名称'}

        # Mock: check_query returns empty
        mock_db.execute_query.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match='分组不存在或不属于当前用户'):
            WatchlistGroupService.update_group(user_id, group_id, updates)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_update_default_group_name_forbidden(self, mock_db):
        """Test updating default group name is forbidden."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 1
        updates = {'name': '新名称'}

        # Mock: check_query returns default group
        mock_db.execute_query.return_value = [{'id': 1, 'name': '未分类'}]

        # Act & Assert
        with pytest.raises(ValueError, match='不能修改默认分组的名称'):
            WatchlistGroupService.update_group(user_id, group_id, updates)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_update_group_duplicate_name(self, mock_db):
        """Test updating to duplicate name raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 5
        updates = {'name': '银行板块'}

        # Mock: check_query (group exists), dup_query (name taken)
        mock_db.execute_query.side_effect = [
            [{'id': 5, 'name': '旧名称'}],  # group exists
            [{'id': 6}]  # duplicate name found
        ]

        # Act & Assert
        with pytest.raises(ValueError, match='分组名称已存在'):
            WatchlistGroupService.update_group(user_id, group_id, updates)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_update_group_empty_updates(self, mock_db):
        """Test updating with no valid fields raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 5
        updates = {'invalid_field': 'value'}

        # Mock: check_query (group exists)
        mock_db.execute_query.return_value = [{'id': 5, 'name': '分组'}]

        # Act & Assert
        with pytest.raises(ValueError, match='没有可更新的字段'):
            WatchlistGroupService.update_group(user_id, group_id, updates)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_delete_group_success(self, mock_db):
        """Test deleting group successfully."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 5

        # Mock: check_query (group exists), delete
        mock_db.execute_query.side_effect = [
            [{'name': '银行板块'}],  # group exists and not default
            None  # delete
        ]

        # Act
        result = WatchlistGroupService.delete_group(user_id, group_id)

        # Assert
        assert result is True
        assert mock_db.execute_query.call_count == 2

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_delete_group_not_found(self, mock_db):
        """Test deleting non-existent group raises ValueError."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 999

        # Mock: check_query returns empty
        mock_db.execute_query.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match='分组不存在或不属于当前用户'):
            WatchlistGroupService.delete_group(user_id, group_id)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_delete_default_group_forbidden(self, mock_db):
        """Test deleting default group is forbidden."""
        # Arrange
        user_id = 'test-user-123'
        group_id = 1

        # Mock: check_query returns default group
        mock_db.execute_query.return_value = [{'name': '未分类'}]

        # Act & Assert
        with pytest.raises(ValueError, match='不能删除默认分组'):
            WatchlistGroupService.delete_group(user_id, group_id)

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_ensure_default_group_exists(self, mock_db):
        """Test ensuring default group when it exists."""
        # Arrange
        user_id = 'test-user-123'
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': '未分类', 'color': '#999999', 'sort_order': 0,
             'created_at': '2025-11-19', 'updated_at': '2025-11-19'}
        ]

        # Act
        result = WatchlistGroupService.ensure_default_group(user_id)

        # Assert
        assert result['name'] == '未分类'
        assert mock_db.execute_query.call_count == 1

    @patch('app.services.watchlist_group_service.DatabaseManager')
    def test_ensure_default_group_creates_when_missing(self, mock_db):
        """Test ensuring default group creates it when missing."""
        # Arrange
        user_id = 'test-user-123'

        # Mock: check_query (not exists), insert
        mock_db.execute_query.side_effect = [
            [],  # not exists
            [{'id': 1, 'name': '未分类', 'color': '#999999', 'sort_order': 0,
              'created_at': '2025-11-19', 'updated_at': '2025-11-19'}]
        ]

        # Act
        result = WatchlistGroupService.ensure_default_group(user_id)

        # Assert
        assert result['name'] == '未分类'
        assert mock_db.execute_query.call_count == 2
