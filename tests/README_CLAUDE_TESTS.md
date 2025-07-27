# Claude Quality Checking Tests

This directory contains tests for verifying the Claude AI quality checking functionality.

## Test Files

### 1. `test_claude_quality.py` - Comprehensive Test Suite
Full pytest suite with unit tests and integration tests for the Claude quality checking module.

**Features:**
- Unit tests with mocked API calls
- Integration tests that make real API calls
- Tests for error handling and edge cases
- Comprehensive coverage of all module functions

### 2. `test_claude_manual.py` - Command-Line Test Tool
Simple manual test script for quick verification of Claude integration.

**Features:**
- Easy command-line execution
- Creates test images automatically
- Provides clear success/failure feedback
- Can test with custom images

## Running the Tests

### Prerequisites
Make sure you have your Databricks token set:
```bash
export DATABRICKS_TOKEN="your-databricks-token-here"
```

### Running All Unit Tests
```bash
# Run all tests in the file
uv run pytest tests/test_claude_quality.py -v

# Run only unit tests (skip integration)
uv run pytest tests/test_claude_quality.py -v -k "not integration"
```

### Running Integration Tests
```bash
# Run only integration tests that call the real API
uv run pytest tests/test_claude_quality.py::TestClaudeIntegration -v

# Or use the marker
uv run pytest tests/test_claude_quality.py -v -k "integration"
```

### Running Manual Command-Line Test
```bash
# Run with auto-generated test image
uv run python tests/test_claude_manual.py

# Run with your own image
uv run python tests/test_claude_manual.py path/to/your/image.png
```

## What the Tests Verify

### Unit Tests Check:
- ✅ Proper initialization with/without tokens
- ✅ Image to base64 conversion
- ✅ Large image resizing
- ✅ API request formatting
- ✅ Response parsing (multiple formats)
- ✅ Error handling and fallbacks

### Integration Tests Check:
- ✅ Real API connectivity
- ✅ Valid responses from Claude
- ✅ Quality score generation
- ✅ Commentary generation
- ✅ Full analysis data structure

### Manual Test Shows:
- ✅ Token availability
- ✅ Endpoint configuration
- ✅ Test image creation
- ✅ API call success/failure
- ✅ Response data details

## Expected Output

### Successful Manual Test:
```
======================================================================
CLAUDE QUALITY CHECKING - MANUAL TEST
======================================================================

✅ DATABRICKS_TOKEN found
📍 Endpoint: https://dbc-xxx.cloud.databricks.com/serving-endpoints/...

🎨 Creating test superhero image...
💾 Test image saved as: test_superhero.png

🦸 Test Parameters:
   Superhero: Iron Man
   Color: red and gold
   Car: Audi R8

🔄 Calling Claude API...

--- Test 1: get_claude_commentary() ---
✅ Success!
📊 Quality Score: 0.85/1.00
💬 Commentary: Amazing transformation! Your Iron Man suit looks incredible!

✅ ALL TESTS PASSED! Claude integration is working correctly.
======================================================================
```

### Failed Test (No Token):
```
❌ ERROR: DATABRICKS_TOKEN environment variable not set!
Please set your Databricks token to run this test.
Example: export DATABRICKS_TOKEN='your-token-here'
```

## Troubleshooting

1. **No DATABRICKS_TOKEN**: Set the environment variable
2. **API Connection Failed**: Check network and endpoint URL
3. **Invalid Token**: Verify your Databricks token is current
4. **Timeout Errors**: Claude endpoint might be slow, tests have 30s timeout
5. **INVALID_PARAMETER_VALUE Error**: Check that your endpoint URL is correct and the model is properly deployed

### API Format Notes

The Claude integration uses the Databricks-specific format for vision models:
- Images are passed as `image_url` with a data URL containing base64-encoded image data
- Format: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,{base64_data}"}}`
- This follows the Databricks Model Serving documentation for vision models

Reference: https://docs.databricks.com/aws/en/machine-learning/model-serving/score-vision-models

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:
- Unit tests run without API tokens
- Integration tests skip gracefully if no token
- Exit codes: 0 for success, 1 for failure