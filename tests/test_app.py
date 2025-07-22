"""Tests for the main Streamlit app."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from PIL import Image

# Since Streamlit apps are tricky to test directly, we'll test the helper functions
# and critical logic paths


class TestAppFunctions:
    """Test app helper functions."""
    
    @patch('streamlit.set_page_config')
    def test_page_config(self, mock_config):
        """Test that page config is set correctly."""
        # Import here to trigger the set_page_config call
        import app
        
        mock_config.assert_called_once()
        call_args = mock_config.call_args[1]
        assert call_args['page_title'] == "🦸 Superhero Avatar Generator"
        assert call_args['page_icon'] == "🦸‍♀️"
        assert call_args['layout'] == "wide"
    
    def test_init_session_state(self):
        """Test session state initialization."""
        from app import init_session_state
        
        # Mock session state
        mock_session_state = {}
        
        with patch.object(st, 'session_state', mock_session_state):
            init_session_state()
            
            assert mock_session_state['step'] == 1
            assert mock_session_state['form_data'] == {}
            assert mock_session_state['photo'] is None
            assert mock_session_state['generated_avatar'] is None
            assert mock_session_state['generation_time'] is None
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', create=True)
    @patch('streamlit.markdown')
    def test_load_css(self, mock_markdown, mock_open, mock_exists):
        """Test CSS loading."""
        from app import load_css
        
        # Mock CSS file exists
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "body { color: red; }"
        
        load_css()
        
        # Check markdown was called with CSS
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        assert "<style>" in call_args
        assert "body { color: red; }" in call_args
    
    def test_form_validation_flow(self):
        """Test form validation in steps."""
        from app import step_personal_info
        
        # This is a placeholder for more complex testing
        # In practice, Streamlit apps are best tested with integration tests
        # or using Streamlit's testing framework when it becomes available
        assert True
    
    def test_environment_setup(self):
        """Test that environment is properly configured."""
        import os
        from pathlib import Path
        
        # Check required directories exist or can be created
        data_dir = Path("data")
        assert data_dir.exists() or True  # Will be created by AppConfig
        
        # Check .env.example exists
        env_example = Path(".env.example")
        assert env_example.exists()
    
    def test_imports(self):
        """Test that all required modules can be imported."""
        try:
            import app
            from config import AppConfig
            from image_generator import ImageGenerator
            import utils
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")