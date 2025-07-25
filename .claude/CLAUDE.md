# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Practices
- Always start feature requests by creating a Github issue as datasciencemonkey@gmail.com.

## Project Overview

Superhero Avatar Generator - A Streamlit web application that transforms user photos into personalized superhero avatars using AI image generation services (Fal AI or Replicate).

## Development Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run streamlit run app.py

# Run tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_utils.py

# Add new dependencies
uv add package_name

# Add development dependencies
uv add --group dev package_name
```

## High-Level Architecture

### Core Application Flow
1. **app.py** - Main Streamlit application implementing a 5-step wizard:
   - Step 1: Personal info collection (name, email)
   - Step 2: Preferences (superhero, car, color)
   - Step 3: Photo capture/upload
   - Step 4: AI generation
   - Step 5: Result display and download

### Key Modules
- **config.py** - Central configuration for AI providers, superhero options, storage settings
- **image_generator.py** - Orchestrates AI image generation (supports Fal and Replicate)
- **database.py** - PostgreSQL integration via SQLAlchemy for tracking generation requests
- **utils.py** - Validation, image processing, session management utilities
- **fal_service.py** - Fal AI integration (FLUX Kontext Pro model)
- **databricks_claude.py** - Quality scoring using Databricks-hosted Claude

### AI Provider Architecture
The application supports two AI providers with a unified interface:
- **Fal AI** (preferred): Direct integration via fal-client
- **Replicate**: Fallback option via replicate API

Provider selection is controlled by `AI_PROVIDER` environment variable.

### Storage Architecture
Dual storage support:
- **Local**: Files stored in `data/originals/` and `data/avatars/`
- **Databricks Volumes**: When `USE_DATABRICKS_VOLUME=true`, stores in Unity Catalog volumes

### Database Schema
PostgreSQL database tracks:
- Avatar generation requests
- User information
- Generated image paths
- Quality scores
- Timestamps

## Environment Variables

Key environment variables to configure:
- `REPLICATE_API_TOKEN` - For Replicate API access
- `FAL_KEY` - For Fal AI access
- `AI_PROVIDER` - Choose 'fal' or 'replicate'
- `USE_DATABRICKS_VOLUME` - Enable Databricks storage
- `DATABRICKS_HOST` / `DATABRICKS_TOKEN` - For Databricks integration
- `POSTGRES_*` - Database connection settings

## Testing Approach

Tests are located in the `tests/` directory and use pytest. Key test files:
- `test_utils.py` - Validation and utility function tests
- `test_image_generator.py` - AI generation logic tests
- `test_app.py` - Streamlit application flow tests
- `test_fal_integration.py` - Fal AI integration tests

## Important Considerations

1. **AI Model**: Uses FLUX Kontext Pro model for high-quality superhero transformations
2. **Image Processing**: All uploaded images are preprocessed to ensure compatibility
3. **Session State**: Streamlit session state manages multi-step wizard flow
4. **Error Handling**: Comprehensive validation at each step with user-friendly error messages
5. **Production Features**: Includes database persistence, quality scoring, and enterprise storage options