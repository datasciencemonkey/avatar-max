# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management (uses uv, not pip)
```bash
# Install all dependencies
uv sync

# Add new dependency
uv add package-name

# Add dev dependency  
uv add --dev package-name

# Install specific packages
uv add google-cloud-storage "qrcode[pil]"
```

### Running the Application
```bash
# Run the Streamlit app
streamlit run app.py

# Run with specific port
streamlit run app.py --server.port 8502
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_image_generator.py

# Run with verbose output
python -m pytest -v

# Test specific AI model (requires API keys)
python tests/test_fal_model.py
python tests/test_prunaai_model.py
```

### Manual Testing
```bash
# Test email functionality
python manual_tests/test_email.py

# Test Databricks integration
python manual_tests/test_databricks.py

# Test logo overlay functionality
python manual_tests/test_logo_overlay.py
```

## Architecture Overview

### Core Application Flow
The application follows a 5-step wizard pattern:
1. **Personal Info**: Name/email collection with validation
2. **Preferences**: Superhero, car, color selection  
3. **Photo Capture**: Camera or file upload
4. **Generation**: AI model processing with progress tracking
5. **Results**: Display with download/QR options

### AI Provider Architecture
The app implements a **provider abstraction layer** supporting multiple AI services:

- **Primary**: Fal AI with FLUX Kontext Pro model
- **Fallback**: Replicate with FLUX Kontext Pro model  
- **Configuration**: Environment-driven provider selection via `AppConfig.AI_PROVIDER`

Key architectural pattern: Each provider implements the same interface but handles image input differently (Fal uses PIL objects, Replicate uses base64 strings).

### Storage Architecture
**Hybrid storage system** with automatic environment detection:

- **Databricks Environment**: Uses Unity Catalog volumes (`/Volumes/...`)
- **Local Development**: Uses local filesystem (`./outputs/...`)
- **Detection Logic**: Checks for `/Volumes` directory existence

### Database Integration
- **Primary**: PostgreSQL with SQLAlchemy ORM
- **Graceful Degradation**: Application continues if database unavailable
- **Connection**: Uses `DB_CONNECTION_STRING` environment variable
- **Management**: Custom `db_manager` handles request lifecycle tracking

### Quality Assessment Pipeline
**Databricks-hosted Claude integration**:
- Model: `databricks-meta-llama-3-1-405b-instruct` 
- Endpoint: `/serving-endpoints/databricks-meta-llama-3-1-405b-instruct`
- Function: Provides style scores (0-1) and commentary for generated avatars
- Architecture: Score/commentary attached as attributes to PIL Image objects

### Email Service Architecture
**Queue-based email delivery system**:
- **Templates**: Jinja2-based HTML/text email templates in `email_templates/`
- **SMTP**: Brevo (Sendinblue) service integration
- **Processing**: Databricks scheduled jobs for batch email delivery
- **Queue**: Database-stored email requests with retry logic

### Logo Overlay System
**Multi-brand asset management**:
- **Assets**: CarMax, Databricks, Innovation Garage logos in `assets/`
- **Positioning**: Configurable corner placement with opacity control
- **Format**: PNG with transparency support, automatic resizing

### QR Code Integration
**Google Cloud Storage workflow**:
- **Upload**: Generated avatars to `innovation_garage01` bucket
- **Access**: Public URLs with unique UUIDs
- **QR Generation**: High error correction QR codes linking to GCS URLs
- **Display**: In-app QR code display with direct link sharing

## Key Configuration

### Environment Variables Required
```bash
# AI Service Configuration
FAL_API_KEY=your_fal_key
REPLICATE_API_TOKEN=your_replicate_token

# Database (optional)
DB_CONNECTION_STRING=postgresql://user:pass@host:port/db

# Email Service (optional)
BREVO_API_KEY=your_brevo_key
BREVO_SENDER_EMAIL=sender@domain.com
BREVO_SENDER_NAME="Event Team"

# Databricks (for enterprise features)
DATABRICKS_HOST=your_workspace_url
DATABRICKS_TOKEN=your_pat_token
```

### Configuration Patterns
- **Central Config**: `config.py` with `AppConfig` class manages all settings
- **Environment Detection**: Automatic Databricks vs local environment detection
- **Feature Flags**: Email capture, download functionality can be toggled
- **Provider Selection**: AI service provider configurable via environment

## Project Structure Patterns

### Modular Service Architecture
- `image_generator.py`: Core AI provider abstraction and image processing
- `database.py`: Database operations with graceful fallback
- `email_service/`: Complete email delivery system with templates and queue
- `qr_service/`: GCS upload and QR code generation
- `utils.py`: Validation, file operations, session management

### Testing Strategy
- **Unit Tests**: Individual component testing in `tests/`
- **Integration Tests**: Full workflow testing with mock services
- **Manual Tests**: Real API testing utilities in `manual_tests/`
- **Model-Specific Tests**: Separate test files for each AI provider

### Asset Management
- **Static Assets**: Logos, CSS, images in `assets/`
- **Templates**: Email templates with Jinja2 inheritance
- **Output Directories**: Auto-created `outputs/` structure for local development

## Development Notes

### Session State Management
Streamlit session state is extensively used for wizard flow management. Key session variables:
- `step`: Current wizard step (1-5)
- `form_data`: User input across all steps
- `generated_avatar`: PIL Image with attached quality metrics
- `request_id`: Database tracking ID

### Image Processing Pipeline
1. **Input Standardization**: PIL Image conversion and validation
2. **AI Generation**: Provider-specific API calls with retry logic
3. **Quality Assessment**: Databricks Claude scoring
4. **Logo Overlay**: Multi-brand asset composition
5. **Format Optimization**: PNG output with metadata preservation

### Error Handling Patterns
- **Graceful Degradation**: App continues with reduced functionality if services unavailable
- **User-Friendly Messages**: Technical errors translated to user-friendly feedback
- **Logging**: Comprehensive error logging without exposing sensitive information
- **Retry Logic**: Built-in retry mechanisms for transient failures

## Development Workflow

### Git Workflow
- **Always commit as me**: Ensure proper commit attribution