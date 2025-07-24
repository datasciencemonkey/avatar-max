# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package_name

# Run application
uv run streamlit run app.py

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_app.py

# Run specific test
uv run pytest tests/test_utils.py::test_validate_name
```

### Environment Setup
```bash
# Copy environment template (if .env.example exists)
cp .env.example .env

# Required environment variable
REPLICATE_API_TOKEN=your_token_here
```

## Code Architecture

### Core Application Structure
This is a **Streamlit-based AI avatar generator** with a modular architecture:

- **app.py**: Main Streamlit application with 5-step wizard interface using session state management
- **config.py**: Centralized configuration class (AppConfig) containing all app settings, AI model parameters, and feature flags
- **image_generator.py**: AI image generation service using Replicate's FLUX Kontext Pro model
- **utils.py**: Validation functions, image processing utilities, and Streamlit UI helpers

### Key Architectural Patterns

**Multi-Step Form Flow**: The app uses Streamlit's session state to manage a 5-step wizard:
1. Personal information collection
2. Preference selection (superhero, car, color)
3. Photo capture/upload
4. AI generation processing
5. Result display and download

**Configuration Management**: All settings are centralized in `AppConfig` class including:
- AI model parameters (guidance_scale, num_inference_steps, etc.)
- UI theming and branding
- Feature flags for email capture, downloads, analytics
- Superhero/color/car option lists

**Image Processing Pipeline**: 
- Input validation and preprocessing in `utils.py`
- AI generation with retry logic in `image_generator.py`
- Base64 encoding/decoding for Streamlit integration
- Automatic image resizing and format conversion

**Data Storage Structure**:
- `data/originals/`: User uploaded photos
- `data/avatars/`: AI-generated superhero avatars
- Unique filename generation with timestamp and hash

### Session State Management
Critical session state variables:
- `step`: Current wizard step (1-5)
- `name`, `email`: User information
- `superhero`, `car`, `color`: User preferences
- `photo`: Uploaded/captured image
- `generated_avatar`: AI result

### AI Integration Architecture
Uses Replicate API with sophisticated prompt engineering:
- Template-based prompt construction in `config.py`
- Context injection combining user photo and preferences
- Exponential backoff retry logic for reliability
- Generation time tracking and user feedback

### Testing Structure
Comprehensive test coverage with mocked external dependencies:
- `tests/test_app.py`: Streamlit app logic testing
- `tests/test_config.py`: Configuration validation
- `tests/test_image_generator.py`: AI generation mocking
- `tests/test_utils.py`: Utility function validation

### Custom Styling
`assets/styles.css` provides superhero-themed dark UI with:
- Gradient backgrounds and animations
- Step indicator progress styling
- Mobile responsive design
- Custom button and form styling

## Important Implementation Notes

### Replicate API Integration
The application specifically uses `black-forest-labs/flux-kontext-pro` model. When modifying AI generation:
- Prompts are constructed in `config.py` using the `PROMPT_TEMPLATE`
- Image inputs must be base64 encoded
- Generation parameters are configurable via `AppConfig`

### File Management
- All file operations use `pathlib.Path` for cross-platform compatibility
- Unique filenames include timestamp and content hash
- Images are automatically resized to optimize AI processing

### Session State Persistence
When adding new form steps or data:
- Initialize new variables in `init_session_state()` in app.py
- Use helper functions from `utils.py` for consistent UI messaging
- Maintain the step-based navigation pattern

### Environment Configuration
The app supports feature flags via environment variables:
- `ENABLE_EMAIL_CAPTURE`: Toggle email collection
- `ENABLE_DOWNLOADS`: Control download functionality
- `ENABLE_ANALYTICS`: Toggle analytics tracking


## Bug Handling Workflow
- When a bug is reported, always start by creating an issue on GitHub, then fix it and push code to remote git and close the issue