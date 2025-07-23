# Superhero Avatar Generator

Transform your photos into personalized superhero avatars using AI! This Streamlit application uses Replicate's FLUX Kontext Pro model to create stunning superhero transformations.

## Features

- **5-Step Wizard Interface**: Easy-to-use multi-step form
- **Photo Capture**: Use camera or upload files
- **AI-Powered Generation**: Leverages FLUX Kontext Pro for high-quality avatars
- **Personalization**: Choose superhero style, colors, and favorite car
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
   - Add your Replicate API token to `.env`:
   ```
   REPLICATE_API_TOKEN=your_token_here
   ```
   
   - (Optional) For Databricks volume storage:
   ```
   DATABRICKS_HOST=https://your-workspace.databricks.com
   DATABRICKS_TOKEN=your_databricks_token
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

- **Frontend**: Streamlit
- **AI Model**: Replicate (FLUX Kontext Pro)
- **Image Processing**: Pillow
- **Package Management**: uv

## Development

```bash
# Run tests
uv run pytest

# Install new dependencies
uv add package_name

# Sync dependencies
uv sync
```

## License

MIT License - Built for event engagement and fun!