# Superhero Avatar Generator

Transform your photos into personalized superhero avatars using AI! This Streamlit application uses advanced AI models (Fal AI or Replicate's FLUX Kontext Pro) to create stunning superhero transformations.

## Features

- **5-Step Wizard Interface**: Easy-to-use multi-step form
- **Photo Capture**: Use camera or upload files
- **AI-Powered Generation**: Leverages FLUX Kontext Pro for high-quality avatars
- **Dual AI Provider Support**: Choose between Fal AI (preferred) or Replicate
- **Personalization**: Choose superhero style, colors, and favorite car
- **Quality Scoring**: AI-powered quality assessment using Claude
- **Database Integration**: PostgreSQL for tracking generation requests
- **Enterprise Storage**: Support for Databricks Unity Catalog volumes
- **Branded Output**: Avatars include Databricks and CarMax logos
- **Download Ready**: Get your avatar as a PNG file

## Quick Start

1. **Set up environment**:
   ```bash
   # Install dependencies
   uv sync
   
   # Copy environment template
   cp .env.example .env
   ```

2. **Configure API**:
   - For Fal AI (recommended):
   ```
   FAL_KEY=your_fal_api_key
   AI_PROVIDER=fal
   ```
   
   - For Replicate:
   ```
   REPLICATE_API_TOKEN=your_token_here
   AI_PROVIDER=replicate
   ```
   
   - (Optional) For PostgreSQL database:
   ```
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=superhero_db
   ```
   
   - (Optional) For Databricks integration:
   ```
   USE_DATABRICKS_VOLUME=true
   DATABRICKS_HOST=https://your-workspace.databricks.com
   DATABRICKS_TOKEN=your_databricks_token
   DATABRICKS_CATALOG=your_catalog
   DATABRICKS_SCHEMA=your_schema
   DATABRICKS_VOLUME=your_volume
   ```

3. **Run the app**:
   ```bash
   uv run streamlit run app.py
   ```

4. **Open browser** to http://localhost:8501

## How It Works

1. **Personal Info**: Enter your name and email
2. **Preferences**: Choose superhero, car, and color
3. **Photo**: Take or upload your photo
4. **Generate**: AI creates your superhero avatar
5. **Result**: Download your personalized avatar

## Technology Stack

- **Frontend**: Streamlit with custom CSS theming
- **AI Models**: 
  - Fal AI (FLUX Kontext Pro) - Primary provider
  - Replicate (FLUX Kontext Pro) - Alternative provider
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Storage**: Local filesystem or Databricks Unity Catalog volumes
- **Image Processing**: Pillow, OpenCV
- **Quality Assessment**: Databricks-hosted Claude integration
- **Package Management**: uv (modern Python package manager)
- **Python**: 3.12+

## Project Structure

```
superhero-max/
├── app.py                  # Main Streamlit application
├── config.py              # Centralized configuration
├── image_generator.py     # AI image generation orchestration
├── fal_service.py         # Fal AI integration
├── database.py            # PostgreSQL database models
├── utils.py               # Utility functions
├── databricks_claude.py   # Claude quality scoring
├── logo_overlay.py        # Logo branding functionality
├── quality_check.py       # Style consistency checker
├── assets/               
│   ├── styles.css         # Custom CSS styling
│   ├── Databricks-Logo.png
│   └── carmax_logo.png
├── data/                  # Generated content storage
│   ├── avatars/          # Generated superhero avatars
│   └── originals/        # User uploaded photos
└── tests/                # Test suite

```

## Development

```bash
# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_utils.py

# Install new dependencies
uv add package_name

# Install dev dependencies
uv add --group dev package_name

# Sync dependencies
uv sync
```

## Configuration

The application can be configured through environment variables. See `.env.example` for all available options.

### Key Configurations:
- **AI Provider**: Switch between Fal AI and Replicate
- **Storage**: Choose between local filesystem and Databricks volumes
- **Database**: Optional PostgreSQL integration for tracking
- **Branding**: Logos are automatically added to generated avatars

## Planned Features

- Batch inference for on-demand story/joke generation
- Email delivery of generated avatars via Databricks jobs

## License

MIT License - Built for event engagement and lead generation!