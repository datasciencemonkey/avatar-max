"""Tests for Claude quality checking functionality."""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
import base64

# Import the module to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from databricks_claude import DatabricksClaudeCommentator, get_claude_commentary


class TestDatabricksClaudeCommentator:
    """Unit tests for DatabricksClaudeCommentator class."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        img = Image.new('RGB', (512, 512), color='red')
        return img
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token-123")
        monkeypatch.setenv("DATABRICKS_CLAUDE_ENDPOINT", "https://test.databricks.com/claude")
    
    def test_initialization_with_token(self, mock_env):
        """Test that commentator initializes correctly with token."""
        commentator = DatabricksClaudeCommentator()
        assert commentator.token == "test-token-123"
        assert commentator.endpoint_url == "https://test.databricks.com/claude"
    
    def test_initialization_without_token(self, monkeypatch):
        """Test that commentator raises error without token."""
        monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
        with pytest.raises(ValueError, match="DATABRICKS_TOKEN is required"):
            DatabricksClaudeCommentator()
    
    def test_image_to_base64(self, mock_env, sample_image):
        """Test image to base64 conversion."""
        commentator = DatabricksClaudeCommentator()
        base64_str = commentator._image_to_base64(sample_image)
        
        # Verify it's a valid base64 string
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        
        # Verify we can decode it back
        decoded = base64.b64decode(base64_str)
        assert len(decoded) > 0
    
    def test_image_resize_for_large_images(self, mock_env):
        """Test that large images are resized."""
        commentator = DatabricksClaudeCommentator()
        
        # Create a large image
        large_image = Image.new('RGB', (2000, 2000), color='blue')
        base64_str = commentator._image_to_base64(large_image)
        
        # Decode and check size
        decoded = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(decoded))
        assert max(img.width, img.height) <= 1024
    
    @patch('requests.post')
    def test_call_claude_endpoint_success(self, mock_post, mock_env):
        """Test successful API call to Claude endpoint."""
        commentator = DatabricksClaudeCommentator()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "quality_score": 0.85,
                        "commentary": "Amazing avatar!",
                        "style_consistency": "excellent"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = commentator._call_claude_endpoint("test prompt", "base64data")
        
        assert result is not None
        assert "choices" in result
        mock_post.assert_called_once()
        
        # Verify request structure
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token-123"
        assert "messages" in call_args[1]["json"]
    
    @patch('requests.post')
    def test_call_claude_endpoint_failure(self, mock_post, mock_env):
        """Test handling of API call failure."""
        commentator = DatabricksClaudeCommentator()
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = commentator._call_claude_endpoint("test prompt", "base64data")
        
        assert result is None
    
    def test_parse_response_with_choices(self, mock_env):
        """Test parsing response with choices format."""
        commentator = DatabricksClaudeCommentator()
        
        response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "quality_score": 0.9,
                        "commentary": "Excellent work!",
                        "style_consistency": "excellent"
                    })
                }
            }]
        }
        
        score, commentary, analysis = commentator._parse_response(response)
        
        assert score == 0.9
        assert commentary == "Excellent work!"
        assert analysis["style_consistency"] == "excellent"
    
    def test_parse_response_with_markdown(self, mock_env):
        """Test parsing response with markdown code blocks."""
        commentator = DatabricksClaudeCommentator()
        
        response = {
            "content": """Here's my analysis:
            ```json
            {
                "quality_score": 0.8,
                "commentary": "Great superhero look!"
            }
            ```
            """
        }
        
        score, commentary, analysis = commentator._parse_response(response)
        
        assert score == 0.8
        assert commentary == "Great superhero look!"
    
    def test_parse_response_fallback(self, mock_env):
        """Test parsing response fallback on error."""
        commentator = DatabricksClaudeCommentator()
        
        response = {"invalid": "response"}
        
        score, commentary, analysis = commentator._parse_response(response)
        
        # Should return defaults
        assert score == 0.75
        assert "Fantastic superhero avatar!" in commentary
    
    @patch('requests.post')
    def test_analyze_avatar_full_flow(self, mock_post, mock_env, sample_image):
        """Test the complete analyze_avatar flow."""
        commentator = DatabricksClaudeCommentator()
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "quality_score": 0.92,
                        "commentary": "Incredible transformation!",
                        "style_consistency": "excellent",
                        "superhero_likeness": "strong",
                        "fun_factor": "high"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        score, commentary, analysis = commentator.analyze_avatar(
            sample_image, "Iron Man", "red", "Tesla"
        )
        
        assert score == 0.92
        assert commentary == "Incredible transformation!"
        assert analysis["superhero_likeness"] == "strong"
        
        # Verify the prompt contains the context
        call_args = mock_post.call_args[1]["json"]
        prompt_text = call_args["messages"][0]["content"][0]["text"]
        assert "Iron Man" in prompt_text
        assert "red" in prompt_text
        assert "Tesla" in prompt_text
    
    def test_analyze_avatar_error_handling(self, mock_env, sample_image):
        """Test error handling in analyze_avatar."""
        commentator = DatabricksClaudeCommentator()
        
        # Mock the _call_claude_endpoint to raise an exception
        with patch.object(commentator, '_call_claude_endpoint', side_effect=Exception("API Error")):
            score, commentary, analysis = commentator.analyze_avatar(
                sample_image, "Batman", "black", "Batmobile"
            )
            
            # Should return defaults
            assert score == 0.75
            assert "Awesome transformation!" in commentary
            assert analysis == {}


class TestGetClaudeCommentary:
    """Test the main entry point function."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        return Image.new('RGB', (512, 512), color='blue')
    
    @patch('databricks_claude.DatabricksClaudeCommentator')
    def test_get_claude_commentary_success(self, mock_commentator_class, sample_image):
        """Test successful get_claude_commentary call."""
        # Mock the commentator instance
        mock_instance = Mock()
        mock_instance.analyze_avatar.return_value = (0.88, "Super cool!", {"extra": "data"})
        mock_commentator_class.return_value = mock_instance
        
        score, commentary = get_claude_commentary(
            sample_image, "Spider-Man", "red", "Audi"
        )
        
        assert score == 0.88
        assert commentary == "Super cool!"
        mock_instance.analyze_avatar.assert_called_once_with(
            sample_image, "Spider-Man", "red", "Audi"
        )
    
    def test_get_claude_commentary_error(self, sample_image, monkeypatch):
        """Test error handling in get_claude_commentary."""
        # Remove the token to cause initialization error
        monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
        
        score, commentary = get_claude_commentary(
            sample_image, "Thor", "silver", "Volvo"
        )
        
        # Should return defaults
        assert score == 0.75
        assert "Your superhero avatar looks amazing!" in commentary


# Integration test that can be run from command line
@pytest.mark.integration
class TestClaudeIntegration:
    """Integration tests that actually call the Claude API."""
    
    def test_real_claude_api_call(self):
        """
        Integration test that makes a real API call to Claude.
        
        This test is skipped if DATABRICKS_TOKEN is not set.
        Run with: uv run pytest tests/test_claude_quality.py::TestClaudeIntegration -v
        """
        token = os.getenv("DATABRICKS_TOKEN")
        if not token:
            pytest.skip("DATABRICKS_TOKEN not set - skipping integration test")
        
        # Create a test image
        test_image = Image.new('RGB', (512, 512))
        draw = Image.new('RGB', (512, 512), color=(70, 130, 180))  # Steel blue
        test_image.paste(draw, (0, 0))
        
        print("\n" + "="*60)
        print("CLAUDE QUALITY CHECK INTEGRATION TEST")
        print("="*60)
        
        try:
            # Test the main function
            score, commentary = get_claude_commentary(
                test_image, 
                "Captain America", 
                "blue", 
                "Ford Mustang"
            )
            
            print(f"\n✅ API Call Successful!")
            print(f"Quality Score: {score:.2f}")
            print(f"Commentary: {commentary}")
            
            # Verify the response
            assert isinstance(score, float)
            assert 0 <= score <= 1
            assert isinstance(commentary, str)
            assert len(commentary) > 0
            
            # Test with the class directly for more details
            commentator = DatabricksClaudeCommentator()
            score2, commentary2, analysis = commentator.analyze_avatar(
                test_image,
                "Wonder Woman",
                "gold",
                "Lamborghini"
            )
            
            print(f"\n🔍 Detailed Analysis:")
            print(f"Quality Score: {score2:.2f}")
            print(f"Commentary: {commentary2}")
            if analysis:
                print(f"Full Analysis: {json.dumps(analysis, indent=2)}")
            
            print("\n✅ All integration tests passed!")
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            pytest.fail(f"Integration test failed: {e}")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    """Allow running specific tests from command line."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "integration":
        # Run only integration tests
        pytest.main([__file__, "-v", "-k", "integration"])
    else:
        # Run all tests
        pytest.main([__file__, "-v"])