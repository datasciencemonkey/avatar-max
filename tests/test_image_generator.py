"""Tests for image generator module."""

import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image
import io

from image_generator import ImageGenerator


class TestImageGenerator:
    """Test ImageGenerator class."""
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment with API token."""
        with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "test_token"}):
            yield
    
    @pytest.fixture
    def generator(self, mock_env):
        """Create ImageGenerator instance with mocked client."""
        with patch('image_generator.AppConfig.REPLICATE_API_TOKEN', 'test_token'):
            with patch('replicate.Client'):
                gen = ImageGenerator()
                gen.client = Mock()
                return gen
    
    @pytest.fixture
    def test_image(self):
        """Create a test image."""
        return Image.new('RGB', (512, 512), color='red')
    
    def test_init_without_token(self):
        """Test initialization fails without API token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="REPLICATE_API_TOKEN"):
                ImageGenerator()
    
    def test_init_with_token(self, mock_env):
        """Test successful initialization with token."""
        with patch('image_generator.AppConfig.REPLICATE_API_TOKEN', 'test_token'):
            with patch('replicate.Client') as mock_client:
                gen = ImageGenerator()
                mock_client.assert_called_once_with(api_token="test_token")
                assert gen.model_name == "black-forest-labs/flux-kontext-pro"
    
    def test_image_to_base64(self, generator, test_image):
        """Test image to base64 conversion."""
        base64_str = generator._image_to_base64(test_image)
        
        assert base64_str.startswith("data:image/png;base64,")
        assert len(base64_str) > 100
    
    @patch('requests.get')
    def test_download_image(self, mock_get, generator):
        """Test image download."""
        # Create a mock response with image data
        test_image_bytes = io.BytesIO()
        test_img = Image.new('RGB', (100, 100), color='blue')
        test_img.save(test_image_bytes, format='PNG')
        test_image_bytes.seek(0)
        
        mock_response = Mock()
        mock_response.content = test_image_bytes.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Download image
        result = generator._download_image("http://example.com/image.png")
        
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
    
    def test_run_model_with_url_output(self, generator):
        """Test model run with URL output."""
        generator.client.run = Mock(return_value="http://example.com/generated.png")
        
        result = generator._run_model("base64_data", "test prompt")
        
        assert result == "http://example.com/generated.png"
        generator.client.run.assert_called_once()
    
    def test_run_model_with_list_output(self, generator):
        """Test model run with list output."""
        generator.client.run = Mock(return_value=["http://example.com/generated.png"])
        
        result = generator._run_model("base64_data", "test prompt")
        
        assert result == "http://example.com/generated.png"
    
    def test_run_model_with_empty_output(self, generator):
        """Test model run with empty output."""
        generator.client.run = Mock(return_value=[])
        
        result = generator._run_model("base64_data", "test prompt")
        
        assert result is None
    
    @patch('requests.get')
    def test_generate_avatar_success(self, mock_get, generator, test_image):
        """Test successful avatar generation."""
        # Mock the model output
        generator.client.run = Mock(return_value="http://example.com/avatar.png")
        
        # Mock the download
        avatar_bytes = io.BytesIO()
        avatar_img = Image.new('RGB', (1024, 1024), color='green')
        avatar_img.save(avatar_bytes, format='PNG')
        avatar_bytes.seek(0)
        
        mock_response = Mock()
        mock_response.content = avatar_bytes.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Generate avatar
        result_img, gen_time, error = generator.generate_avatar(
            test_image,
            "Superman",
            "Blue",
            "Tesla Model S"
        )
        
        assert result_img is not None
        assert isinstance(result_img, Image.Image)
        assert gen_time > 0
        assert error is None
    
    def test_generate_avatar_failure(self, generator, test_image):
        """Test avatar generation failure."""
        # Mock the model to raise an exception
        generator.client.run = Mock(side_effect=Exception("API Error"))
        
        # Generate avatar
        result_img, gen_time, error = generator.generate_avatar(
            test_image,
            "Superman",
            "Blue",
            "Tesla Model S"
        )
        
        assert result_img is None
        assert gen_time > 0
        assert "Generation failed: API Error" in error
    
    def test_generate_avatar_with_retries(self, generator, test_image):
        """Test avatar generation with retries."""
        # Mock the model to fail twice then succeed
        generator.client.run = Mock(side_effect=[
            Exception("Temporary error"),
            Exception("Another temporary error"),
            "http://example.com/avatar.png"
        ])
        
        # Mock successful download
        with patch.object(generator, '_download_image') as mock_download:
            mock_download.return_value = Image.new('RGB', (100, 100))
            
            # Generate avatar
            result_img, gen_time, error = generator.generate_avatar(
                test_image,
                "Superman",
                "Blue",
                "Tesla Model S",
                max_retries=3
            )
            
            assert result_img is not None
            assert error is None
            assert generator.client.run.call_count == 3