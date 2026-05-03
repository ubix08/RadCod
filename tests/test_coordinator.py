"""Test RadcodeCoordinator core functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestRadcodeCoordinator:
    """Test RadcodeCoordinator class."""
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        with patch('src.coordinator.RadcodeCoordinator._initialize'):
            from src.coordinator import RadcodeCoordinator
            coord = RadcodeCoordinator()
            
            assert coord._workspace == Path("./workspace")
            assert coord._security_level == "medium"
            assert coord._key is None
    
    def test_init_with_params(self):
        """Test initialization with custom params."""
        with patch('src.coordinator.RadcodeCoordinator._initialize'):
            from src.coordinator import RadcodeCoordinator
            coord = RadcodeCoordinator(
                api_key="test-key",
                workspace="/custom/workspace",
                security_level="high"
            )
            
            assert coord._workspace == Path("/custom/workspace")
            assert coord._security_level == "high"
            assert coord._key == "test-key"
    
    @patch('src.coordinator.RadcodeCoordinator._initialize')
    def test_run_request(self, mock_init):
        """Test run method calls conversation."""
        from src.coordinator import RadcodeCoordinator
        
        with patch.object(RadcodeCoordinator, '_initialize') as mock_init:
            mock_conv = MagicMock()
            mock_conv.run.return_value = {"done": True}
            
            coord = RadcodeCoordinator()
            coord._conversation = mock_conv
            
            result = coord.run("test request")
            
            assert result["status"] == "success"
            mock_conv.run.assert_called_once()
    
    def test_build_security(self):
        """Test security configuration build."""
        with patch('src.coordinator.RadcodeCoordinator._initialize'):
            from src.coordinator import RadcodeCoordinator
            
            coord = RadcodeCoordinator(security_level="low")
            security = coord._build_security()
            
            assert security is not None
    
    def test_check_stuck_detection(self):
        """Test stuck detection logic."""
        with patch('src.coordinator.RadcodeCoordinator._initialize'):
            from src.coordinator import RadcodeCoordinator
            
            coord = RadcodeCoordinator()
            
            # Not stuck - different actions
            assert coord._check_stuck("action1", 1, "action0", 0) == False
            
            # Not stuck - first repeat
            assert coord._check_stuck("action1", 2, "action1", 0) == False
            
            # Stuck - 5th repeat
            assert coord._check_stuck("action1", 6, "action1", 4) == True
    
    def test_can_continue_no_context(self):
        """Test can_continue when not initialized."""
        from src.coordinator import RadcodeCoordinator
        
        coord = RadcodeCoordinator()
        coord._initialized = False
        
        # Should be True when not initialized (no context to manage)
        assert coord.can_continue() == True
    
    def test_get_metrics_not_initialized(self):
        """Test get_metrics when not initialized."""
        from src.coordinator import RadcodeCoordinator
        
        coord = RadcodeCoordinator()
        coord._initialized = False
        
        metrics = coord.get_metrics()
        
        assert metrics["status"] == "not_initialized"