"""Tests for utility functions."""

import pytest
from pathlib import Path
from PIL import Image
import tempfile

from utils import (
    validate_name,
    validate_email_address,
    validate_car_input,
    process_uploaded_image,
    generate_unique_filename,
    save_image,
    format_generation_time,
    create_participant_record
)


class TestValidation:
    """Test validation functions."""
    
    def test_validate_name_valid(self):
        """Test valid names."""
        valid_names = [
            "John Doe",
            "Mary Jane",
            "Jean-Claude",
            "O'Brien",
            "Li"
        ]
        for name in valid_names:
            is_valid, error = validate_name(name)
            assert is_valid is True
            assert error is None
    
    def test_validate_name_invalid(self):
        """Test invalid names."""
        invalid_names = [
            "",  # Empty
            "J",  # Too short
            "a" * 101,  # Too long
            "John123",  # Contains numbers
            "John@Doe",  # Contains invalid characters
        ]
        for name in invalid_names:
            is_valid, error = validate_name(name)
            assert is_valid is False
            assert error is not None
    
    def test_validate_email_valid(self):
        """Test valid emails."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.org",
            "test+tag@gmail.com"
        ]
        for email in valid_emails:
            is_valid, error = validate_email_address(email)
            assert is_valid is True
            assert error is None
    
    def test_validate_email_invalid(self):
        """Test invalid emails."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@@example.com"
        ]
        for email in invalid_emails:
            is_valid, error = validate_email_address(email)
            assert is_valid is False
            assert error is not None
    
    def test_validate_car_input(self):
        """Test car input validation."""
        # Valid inputs
        valid_cars = ["Tesla Model S", "Ferrari 488", "My Custom Car", "BMW"]
        for car in valid_cars:
            is_valid, error = validate_car_input(car)
            assert is_valid is True
            assert error is None
        
        # Invalid inputs
        invalid_cars = ["", "A", "a" * 101]
        for car in invalid_cars:
            is_valid, error = validate_car_input(car)
            assert is_valid is False
            assert error is not None


class TestImageProcessing:
    """Test image processing functions."""
    
    def test_process_uploaded_image(self):
        """Test image processing."""
        # Create a test image
        test_image = Image.new('RGB', (2000, 1500), color='red')
        
        # Process it
        processed = process_uploaded_image(test_image)
        
        # Check it was resized
        assert processed.width <= 1024
        assert processed.height <= 1024
        assert processed.mode == 'RGB'
    
    def test_process_uploaded_image_small(self):
        """Test processing small image."""
        # Create a small test image
        test_image = Image.new('RGB', (500, 400), color='blue')
        
        # Process it
        processed = process_uploaded_image(test_image)
        
        # Check it wasn't resized
        assert processed.width == 500
        assert processed.height == 400
    
    def test_process_uploaded_image_rgba(self):
        """Test processing RGBA image."""
        # Create RGBA image
        test_image = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
        
        # Process it
        processed = process_uploaded_image(test_image)
        
        # Check it was converted to RGB
        assert processed.mode == 'RGB'


class TestFileOperations:
    """Test file operation functions."""
    
    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        filename1 = generate_unique_filename()
        filename2 = generate_unique_filename()
        
        assert filename1 != filename2
        assert filename1.startswith("avatar_")
        assert filename1.endswith(".png")
    
    def test_generate_unique_filename_custom(self):
        """Test custom filename generation."""
        filename = generate_unique_filename(prefix="test", extension="jpg")
        
        assert filename.startswith("test_")
        assert filename.endswith(".jpg")
    
    def test_save_image(self):
        """Test image saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            test_image = Image.new('RGB', (100, 100), color='green')
            
            # Save it
            save_path = Path(tmpdir)
            filename = "test_image.png"
            saved_path = save_image(test_image, save_path, filename)
            
            # Check it was saved
            assert saved_path.exists()
            assert saved_path.name == filename
            
            # Load and verify
            loaded = Image.open(saved_path)
            assert loaded.size == (100, 100)


class TestFormatting:
    """Test formatting functions."""
    
    def test_format_generation_time(self):
        """Test time formatting."""
        assert format_generation_time(30.5) == "30.5 seconds"
        assert format_generation_time(59.9) == "59.9 seconds"
        assert format_generation_time(60.0) == "1.0 minutes"
        assert format_generation_time(90.0) == "1.5 minutes"
        assert format_generation_time(120.0) == "2.0 minutes"


class TestDataRecords:
    """Test data record creation."""
    
    def test_create_participant_record(self):
        """Test participant record creation."""
        record = create_participant_record(
            name="John Doe",
            email="john@example.com",
            superhero="Superman",
            car="Tesla Model S",
            color="Blue",
            original_image_path=Path("/tmp/original.jpg"),
            generated_image_path=Path("/tmp/generated.png"),
            generation_time=45.5
        )
        
        assert record["name"] == "John Doe"
        assert record["email"] == "john@example.com"
        assert record["preferences"]["superhero"] == "Superman"
        assert record["preferences"]["car"] == "Tesla Model S"
        assert record["preferences"]["color"] == "Blue"
        assert record["metadata"]["generation_time"] == 45.5
        assert "id" in record
        assert "timestamp" in record