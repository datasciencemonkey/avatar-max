"""Tests for Prunaai model integration and scoring."""

import os
import io
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image
import requests
import replicate

from image_generator import ImageGenerator, ReplicateImageGenerator


class MockPrunaaiOutput:
    """Mock Prunaai output that behaves like the real API response."""
    def __init__(self, url):
        self._url = url
        self._content = None
        
    def url(self):
        """Return the URL of the generated image."""
        return self._url
    
    def read(self):
        """Read the image content from the URL."""
        if self._content is None:
            # Simulate downloading the image
            response = requests.get(self._url)
            response.raise_for_status()
            self._content = response.content
        return self._content


class TestPrunaaiModel:
    """Test Prunaai model specific functionality."""
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment with API token and Prunaai model."""
        with patch.dict(os.environ, {
            "REPLICATE_API_TOKEN": "test_token",
            "AI_PROVIDER": "replicate",
            "AI_MODEL": "prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b"
        }):
            yield
    
    @pytest.fixture
    def prunaai_generator(self, mock_env):
        """Create ImageGenerator instance configured for Prunaai."""
        with patch('image_generator.AppConfig.REPLICATE_API_TOKEN', 'test_token'):
            with patch('image_generator.AppConfig.REPLICATE_MODEL', 
                      'prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b'):
                with patch('replicate.Client'):
                    gen = ImageGenerator()
                    gen.generator = ReplicateImageGenerator()
                    gen.generator.client = Mock()
                    gen.generator.model_name = 'prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b'
                    return gen
    
    def test_prunaai_model_parameters(self, prunaai_generator):
        """Test that Prunaai model uses correct parameters."""
        # Create mock output
        mock_output = MockPrunaaiOutput("http://example.com/prunaai-image.jpg")
        prunaai_generator.generator.client.run = Mock(return_value=mock_output)
        
        # Mock that we have an image URL (simulating upload)
        with patch.object(prunaai_generator.generator, '_upload_image_to_url', 
                         return_value="https://example.com/uploaded-image.png"):
            # Run the model
            result = prunaai_generator.generator._run_model("base64_data", "test prompt", seed=42)
        
        # Check that the correct parameters were used
        prunaai_generator.generator.client.run.assert_called_once()
        call_args = prunaai_generator.generator.client.run.call_args
        
        # Verify model name
        assert "prunaai" in call_args[0][0].lower()
        
        # Verify input parameters specific to Prunaai
        input_params = call_args[1]['input']
        assert input_params['prompt'] == "test prompt"
        assert input_params['seed'] == 42
        assert input_params['aspect_ratio'] == "match_input_image"
        assert input_params['output_format'] == "png"
        assert input_params['img_cond_path'] == "https://example.com/uploaded-image.png"
        
        # Verify Prunaai doesn't use base64 image input
        assert 'input_image' not in input_params
    
    def test_prunaai_output_url_access(self, prunaai_generator):
        """Test accessing URL from Prunaai output."""
        # Create mock output
        test_url = "http://example.com/prunaai-generated.jpg"
        mock_output = MockPrunaaiOutput(test_url)
        prunaai_generator.generator.client.run = Mock(return_value=mock_output)
        
        # Run the model
        result = prunaai_generator.generator._run_model("base64_data", "superhero prompt")
        
        # Test URL access
        assert result == test_url
        assert mock_output.url() == test_url
    
    @patch('requests.get')
    def test_prunaai_output_read(self, mock_get, prunaai_generator):
        """Test reading image content from Prunaai output."""
        # Create test image data
        test_image = Image.new('RGB', (1024, 1024), color='blue')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.content = img_bytes.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create mock output
        test_url = "http://example.com/prunaai-image.jpg"
        mock_output = MockPrunaaiOutput(test_url)
        
        # Test reading the content
        content = mock_output.read()
        
        assert content == img_bytes.getvalue()
        mock_get.assert_called_once_with(test_url)
    
    @patch('requests.get')
    def test_prunaai_scoring_integration(self, mock_get, prunaai_generator):
        """Test that Prunaai-generated images can be scored correctly."""
        # Create test image for scoring
        test_image = Image.new('RGB', (1024, 1024), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Mock HTTP response for image download
        mock_response = Mock()
        mock_response.content = img_bytes.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock Prunaai output
        mock_output = MockPrunaaiOutput("http://example.com/avatar.png")
        prunaai_generator.generator.client.run = Mock(return_value=mock_output)
        
        # Mock quality check
        with patch('image_generator.check_avatar_quality') as mock_quality:
            mock_quality.return_value = (0.85, "Great superhero transformation!")
            
            # Generate avatar
            original_image = Image.new('RGB', (512, 512), color='green')
            result_img, gen_time, error = prunaai_generator.generate_avatar(
                original_image,
                "Iron Man",
                "Red",
                "Audi R8"
            )
            
            # Verify the image was generated successfully
            assert result_img is not None
            assert error is None
            
            # Verify scoring was applied
            assert hasattr(result_img, 'style_score')
            assert result_img.style_score == 0.85
            assert hasattr(result_img, 'commentary')
            assert result_img.commentary == "Great superhero transformation!"
    
    def test_prunaai_error_handling(self, prunaai_generator):
        """Test error handling specific to Prunaai models."""
        # Test with "Invalid input" error
        prunaai_generator.generator.client.run = Mock(
            side_effect=Exception("Invalid input: Prunaai validation failed")
        )
        
        # Mock successful retry with modified prompt
        with patch.object(prunaai_generator.generator, '_run_model') as mock_run:
            # First call fails, second succeeds
            mock_run.side_effect = [
                Exception("Invalid input: Prunaai validation failed"),
                "http://example.com/success.png"
            ]
            
            # Generate avatar with retries
            with patch.object(prunaai_generator, '_download_image') as mock_download:
                mock_download.return_value = Image.new('RGB', (100, 100))
                
                result_img, gen_time, error = prunaai_generator.generate_avatar(
                    Image.new('RGB', (100, 100)),
                    "Spider-Man",
                    "Red and Blue",
                    "Motorcycle",
                    max_retries=2
                )
                
                # Should retry with modified prompt
                assert mock_run.call_count == 2


class TestPrunaaiModelReal:
    """Test Prunaai model with real API calls."""
    
    @pytest.fixture
    def real_api_token(self):
        """Get real API token from environment."""
        token = os.getenv("REPLICATE_API_TOKEN")
        if not token:
            pytest.skip("REPLICATE_API_TOKEN not set for real API tests")
        return token
    
    @pytest.fixture
    def test_image_path(self):
        """Path to a test image file."""
        # Use the actual test image from test_images folder
        import os
        test_path = os.path.join(os.path.dirname(__file__), "test_images", "test-img.png")
        if not os.path.exists(test_path):
            # Fallback: Create a simple test image if the file doesn't exist
            test_path = "/tmp/test_superhero_input.png"
            img = Image.new('RGB', (512, 512), color='blue')
            # Add some variation to make it more interesting
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 100, 400, 400], fill='white')
            draw.ellipse([200, 200, 300, 300], fill='red')
            img.save(test_path)
        yield test_path
    
    @pytest.mark.skipif(not os.getenv("REPLICATE_API_TOKEN"), 
                        reason="Requires REPLICATE_API_TOKEN for real API test")
    def test_prunaai_real_api_basic(self, real_api_token):
        """Test basic Prunaai API call with minimal parameters."""
        client = replicate.Client(api_token=real_api_token)
        
        # Run the model with basic parameters using a test image URL
        output = client.run(
            "prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b",
            input={
                "seed": -1,
                "prompt": "Transform this person into a superhero with red and blue costume",
                "guidance": 2.5,
                "image_size": 1024,
                "speed_mode": "Real Time",
                "aspect_ratio": "match_input_image",
                "img_cond_path": "https://replicate.delivery/pbxt/NFoiYQ8DdIEQFepICB7SpZB6mI2HC4xZjiHl9mXFqMhZS9sY/flux_schnell.png",
                "output_format": "jpg",
                "output_quality": 80,
                "num_inference_steps": 30
            }
        )
        
        # Test URL access
        assert hasattr(output, 'url'), "Output should have url() method"
        url = output.url()
        assert url.startswith("http"), f"URL should be valid HTTP URL, got: {url}"
        print(f"Generated image URL: {url}")
        
        # Test reading the image
        image_content = output.read()
        assert len(image_content) > 1000, "Image content should be substantial"
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(image_content))
        assert img.size[0] > 0 and img.size[1] > 0, "Image should have valid dimensions"
        print(f"Image dimensions: {img.size}")
    
    @pytest.mark.skipif(not os.getenv("REPLICATE_API_TOKEN"), 
                        reason="Requires REPLICATE_API_TOKEN for real API test")
    def test_prunaai_real_with_scoring(self, real_api_token, test_image_path):
        """Test Prunaai with real API and quality scoring."""
        # Configure for Prunaai
        with patch('image_generator.AppConfig.REPLICATE_API_TOKEN', real_api_token):
            with patch('image_generator.AppConfig.REPLICATE_MODEL', 
                      'prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b'):
                generator = ImageGenerator()
                
                # Load test image
                test_image = Image.open(test_image_path)
                
                # Generate avatar
                result_img, gen_time, error = generator.generate_avatar(
                    test_image,
                    "Iron Man",
                    "Red and Gold",
                    "Lamborghini",
                    max_retries=1  # Limit retries for test
                )
                
                # Check results
                assert error is None, f"Generation should succeed, got error: {error}"
                assert result_img is not None, "Should return an image"
                assert gen_time > 0, "Generation time should be tracked"
                
                # Check scoring attributes
                assert hasattr(result_img, 'style_score'), "Image should have style_score"
                assert hasattr(result_img, 'commentary'), "Image should have commentary"
                
                print(f"Generation time: {gen_time:.2f}s")
                print(f"Style score: {result_img.style_score}")
                print(f"Commentary: {result_img.commentary}")
                
                # Save the result for manual inspection
                output_path = "/tmp/prunaai_test_output.png"
                result_img.save(output_path)
                print(f"Saved result to: {output_path}")
    
    @pytest.mark.skipif(not os.getenv("REPLICATE_API_TOKEN"), 
                        reason="Requires REPLICATE_API_TOKEN for real API test")
    def test_prunaai_real_error_handling(self, real_api_token):
        """Test Prunaai error handling with real API."""
        client = replicate.Client(api_token=real_api_token)
        
        # Try with invalid parameters to trigger an error
        with pytest.raises(Exception) as exc_info:
            output = client.run(
                "prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b",
                input={
                    "prompt": "",  # Empty prompt might cause error
                    "seed": -999999,  # Invalid seed
                    "invalid_param": "test"  # Unknown parameter
                }
            )
        
        print(f"Error message: {str(exc_info.value)}")


    @pytest.mark.skipif(not os.getenv("REPLICATE_API_TOKEN"), 
                        reason="Requires REPLICATE_API_TOKEN for real API test")
    def test_prunaai_real_with_local_image_upload(self, real_api_token, test_image_path):
        """Test Prunaai with local image that needs to be uploaded."""
        import replicate
        from replicate import file
        
        client = replicate.Client(api_token=real_api_token)
        
        # Check if test image exists
        if not os.path.exists(test_image_path):
            pytest.skip(f"Test image not found at {test_image_path}")
        
        # Upload the local image using Replicate's file API
        print(f"Uploading test image from: {test_image_path}")
        with open(test_image_path, "rb") as f:
            uploaded_file = file.put(f, client=client)
        
        print(f"Uploaded image URL: {uploaded_file}")
        
        # Run the model with the uploaded image
        output = client.run(
            "prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b",
            input={
                "seed": 42,
                "prompt": "Transform person into Iron Man superhero with metallic red and gold armor, standing next to a luxury sports car",
                "guidance": 3.5,
                "image_size": 1024,
                "speed_mode": "Juiced 🔥 (default)",
                "aspect_ratio": "match_input_image",
                "img_cond_path": uploaded_file,
                "output_format": "jpg",
                "output_quality": 90,
                "num_inference_steps": 30
            }
        )
        
        # Verify the output
        url = output.url()
        print(f"Generated Iron Man transformation: {url}")
        
        # Download and verify
        image_content = output.read()
        img = Image.open(io.BytesIO(image_content))
        
        # Save for inspection
        output_path = "/tmp/prunaai_ironman_test.jpg"
        with open(output_path, "wb") as f:
            f.write(image_content)
        print(f"Saved Iron Man transformation to: {output_path}")
        
        # Verify dimensions
        assert img.size[0] > 0 and img.size[1] > 0, "Image should have valid dimensions"
        print(f"Output image dimensions: {img.size}")


if __name__ == "__main__":
    # Allow running specific real API tests from command line
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        pytest.main([__file__, "-k", "real", "-v", "-s"])
    else:
        print("Run with --real to test against real Prunaai API")
        print("Make sure REPLICATE_API_TOKEN is set in environment")