"""Superhero Avatar Generator - Main Streamlit Application."""

import os
import time
from pathlib import Path

import streamlit as st
from PIL import Image
# Using built-in streamlit camera input
from dotenv import load_dotenv

from config import AppConfig
from image_generator import ImageGenerator
from database import db_manager
from utils import (
    validate_name,
    validate_email_address,
    validate_car_input,
    validate_color_input,
    save_image,
    generate_unique_filename,
    create_participant_record,
    show_error,
    show_success,
    show_info,
    reset_session_state,
    format_generation_time
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title=AppConfig.APP_TITLE,
    page_icon=AppConfig.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
def load_css():
    """Load custom CSS styling."""
    css_path = Path("assets/styles.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "photo" not in st.session_state:
        st.session_state.photo = None
    if "generated_avatar" not in st.session_state:
        st.session_state.generated_avatar = None
    if "generation_time" not in st.session_state:
        st.session_state.generation_time = None
    if "request_id" not in st.session_state:
        st.session_state.request_id = None

# Step indicator
def show_step_indicator(current_step: int):
    """Display step indicator."""
    steps = ["Info", "Preferences", "Photo", "Generate", "Result"]
    
    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps)):
        step_num = i + 1
        with col:
            if step_num < current_step:
                st.markdown(f"<div class='step completed'>{step_num}</div>", unsafe_allow_html=True)
            elif step_num == current_step:
                st.markdown(f"<div class='step active'>{step_num}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='step'>{step_num}</div>", unsafe_allow_html=True)
            st.caption(step_name)

# Step 1: Personal Information
def step_personal_info():
    """Collect personal information."""
    st.header("📝 Tell us about yourself")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input(
            "Your Name",
            value=st.session_state.form_data.get("name", ""),
            placeholder="John Doe"
        )
        
    with col2:
        email = st.text_input(
            "Email Address",
            value=st.session_state.form_data.get("email", ""),
            placeholder="john@example.com"
        )
    
    if st.button("Next →", key="next_1", use_container_width=True):
        # Validate inputs
        name_valid, name_error = validate_name(name)
        email_valid, email_error = validate_email_address(email)
        
        if not name_valid:
            show_error(name_error)
        elif not email_valid:
            show_error(email_error)
        else:
            st.session_state.form_data["name"] = name
            st.session_state.form_data["email"] = email
            st.session_state.step = 2
            st.rerun()

# Step 2: Preferences
def step_preferences():
    """Collect user preferences."""
    st.header("🎨 Choose your superhero style")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        superhero = st.selectbox(
            "Favorite Superhero",
            options=AppConfig.SUPERHERO_OPTIONS,
            index=None,
            placeholder="Select a superhero"
        )
    
    with col2:
        car = st.text_input(
            "Favorite Car",
            value=st.session_state.form_data.get("car", ""),
            placeholder="e.g., Tesla Model S, Ferrari 488"
        )
    
    with col3:
        color = st.text_input(
            "Favorite Color",
            value=st.session_state.form_data.get("color", ""),
            placeholder="e.g., Red, Blue, Gold"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back", key="back_2", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("Next →", key="next_2", use_container_width=True):
            # Validate inputs
            if not superhero:
                show_error("Please select a superhero")
            elif not car:
                show_error("Please enter your favorite car")
            else:
                car_valid, car_error = validate_car_input(car)
                color_valid, color_error = validate_color_input(color)
                if not car_valid:
                    show_error(car_error)
                elif not color_valid:
                    show_error(color_error)
                else:
                    st.session_state.form_data["superhero"] = superhero
                    st.session_state.form_data["car"] = car
                    st.session_state.form_data["color"] = color
                    st.session_state.step = 3
                    st.rerun()

# Step 3: Photo Capture
def step_photo_capture():
    """Capture or upload photo."""
    st.header("📸 Take your photo")
    
    tab1, tab2 = st.tabs(["📷 Camera", "📁 Upload"])
    
    with tab1:
        st.info("Click the camera button below to take your photo")
        
        # Camera input
        photo = st.camera_input("Take a photo")
        
        if photo is not None:
            st.session_state.photo = Image.open(photo)
            st.image(st.session_state.photo, caption="Your photo", use_container_width=True)
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Choose a photo",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear photo of yourself"
        )
        
        if uploaded_file is not None:
            st.session_state.photo = Image.open(uploaded_file)
            st.image(st.session_state.photo, caption="Your photo", use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back", key="back_3", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    
    with col2:
        if st.button("Generate Avatar →", key="next_3", use_container_width=True):
            if st.session_state.photo is None:
                show_error("Please take or upload a photo first")
            else:
                st.session_state.step = 4
                st.rerun()

# Step 4: Generate Avatar
def step_generate_avatar():
    """Generate the superhero avatar."""
    st.header("🎨 Creating your superhero avatar...")
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Validate configuration
        AppConfig.validate()
        
        # Create database request if not already created
        if not st.session_state.request_id:
            try:
                st.session_state.request_id = db_manager.create_avatar_request(
                    name=st.session_state.form_data["name"],
                    email=st.session_state.form_data["email"],
                    superhero=st.session_state.form_data["superhero"],
                    car=st.session_state.form_data["car"],
                    color=st.session_state.form_data["color"]
                )
                status_text.text("Request saved to database...")
                progress_bar.progress(10)
            except Exception as e:
                print(f"Database error: {e}")
                # Continue even if database fails
        
        # Update status to processing
        if st.session_state.request_id:
            try:
                db_manager.update_request_processing(st.session_state.request_id)
            except Exception as e:
                print(f"Database update error: {e}")
        
        # Initialize generator
        status_text.text("Initializing AI model...")
        progress_bar.progress(20)
        generator = ImageGenerator()
        
        # Generate avatar
        status_text.text("Transforming you into a superhero...")
        progress_bar.progress(50)
        
        avatar, generation_time, error = generator.generate_avatar(
            st.session_state.photo,
            st.session_state.form_data["superhero"],
            st.session_state.form_data["color"],
            st.session_state.form_data["car"]
        )
        
        progress_bar.progress(80)
        
        if error:
            show_error(f"Generation failed: {error}")
            # Update database with failure
            if st.session_state.request_id:
                try:
                    db_manager.update_request_failed(st.session_state.request_id, error)
                except Exception as e:
                    print(f"Database update error: {e}")
            if st.button("← Try Again", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        else:
            # Save images
            status_text.text("Saving your avatar...")
            progress_bar.progress(85)
            
            try:
                # Save original
                original_filename = generate_unique_filename("original", "jpg")
                original_path = save_image(
                    st.session_state.photo,
                    AppConfig.ORIGINALS_DIR,
                    original_filename
                )
                
                progress_bar.progress(90)
                
                # Save avatar
                avatar_filename = generate_unique_filename("avatar", "png")
                avatar_path = save_image(
                    avatar,
                    AppConfig.AVATARS_DIR,
                    avatar_filename
                )
                
                progress_bar.progress(95)
            except Exception as e:
                print(f"Error saving images: {e}")
                # Continue anyway - we have the generated avatar in memory
                original_path = f"temp_{original_filename}"
                avatar_path = f"temp_{avatar_filename}"
            
            # Create participant record
            if AppConfig.ENABLE_EMAIL_CAPTURE:
                record = create_participant_record(
                    st.session_state.form_data["name"],
                    st.session_state.form_data["email"],
                    st.session_state.form_data["superhero"],
                    st.session_state.form_data["car"],
                    st.session_state.form_data["color"],
                    original_path,
                    avatar_path,
                    generation_time
                )
            
            # Update database with success
            if st.session_state.request_id:
                try:
                    db_manager.update_request_completed(
                        st.session_state.request_id,
                        generation_time,
                        original_path,
                        avatar_path
                    )
                except Exception as e:
                    print(f"Database update error: {e}")
            
            progress_bar.progress(100)
            status_text.text("Complete!")
            
            # Store results
            st.session_state.generated_avatar = avatar
            st.session_state.generation_time = generation_time
            st.session_state.step = 5
            
            time.sleep(1)
            st.rerun()
            
    except Exception as e:
        show_error(f"An error occurred: {str(e)}")
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# Step 5: Display Result
def step_display_result():
    """Display the generated avatar."""
    st.header("🦸 Your Superhero Avatar is Ready!")
    
    # Display side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Photo")
        st.image(st.session_state.photo, use_container_width=True)
    
    with col2:
        st.subheader("Superhero Avatar")
        st.image(st.session_state.generated_avatar, use_container_width=True)
    
    # Show generation details and Claude's commentary
    style_score = getattr(st.session_state.generated_avatar, 'style_score', None)
    commentary = getattr(st.session_state.generated_avatar, 'commentary', None)
    
    # Display Claude's fun commentary if available
    if commentary:
        st.success(f"🎭 {commentary}")
    
    # Show generation time and quality score
    if style_score is not None:
        quality_emoji = "🌟" if style_score >= 0.8 else "✨" if style_score >= 0.7 else "⭐"
        st.info(f"{quality_emoji} Generated in {format_generation_time(st.session_state.generation_time)} | Quality score: {style_score:.1%}")
    else:
        st.info(f"✨ Generated in {format_generation_time(st.session_state.generation_time)}")
    
    # Regeneration tip
    st.caption("💡 Try regenerating for different variations!")
    
    # Download and Email buttons
    if AppConfig.ENABLE_DOWNLOAD:
        avatar_bytes = save_image(
            st.session_state.generated_avatar,
            Path("/tmp"),
            "temp_avatar.png"
        )
        
        # Add custom CSS for button alignment and styling
        st.markdown(
            """<style>
            /* Ensure buttons are properly aligned */
            div[data-testid="column"] > div > div > div > div {
                height: 100%;
                display: flex;
                align-items: stretch;
            }
            
            /* Style both buttons with rounded corners */
            div[data-testid="column"] button {
                border-radius: 25px !important;
                padding: 0.75rem 2rem !important;
                font-size: 1rem !important;
                height: 100%;
                transition: all 0.3s ease !important;
            }
            
            /* Style the download button - keep original appearance but with rounded shape */
            div[data-testid="column"]:first-child .stDownloadButton > button {
                background-color: #FAFAFA !important;
                color: #262730 !important;
                border: 1px solid rgba(49, 51, 63, 0.2) !important;
                font-weight: 400 !important;
            }
            
            div[data-testid="column"]:first-child .stDownloadButton > button:hover {
                background-color: #F0F2F6 !important;
                border-color: rgba(49, 51, 63, 0.4) !important;
            }
            
            /* Style the email button - make it prominent with gradient */
            div[data-testid="column"]:last-child button {
                background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%) !important;
                color: white !important;
                border: none !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3) !important;
                letter-spacing: 0.5px !important;
            }
            
            div[data-testid="column"]:last-child button:hover {
                background: linear-gradient(90deg, #FF4500 0%, #FF6B35 100%) !important;
                box-shadow: 0 6px 20px rgba(255, 69, 0, 0.4) !important;
                transform: translateY(-1px) !important;
            }
            
            /* Ensure equal height for both buttons */
            div[data-testid="column"] .stDownloadButton {
                height: 100%;
            }
            
            div[data-testid="column"] .stDownloadButton > button,
            div[data-testid="column"] > div > div > div > button {
                min-height: 3rem !important;
            }
            </style>""",
            unsafe_allow_html=True
        )
        
        # Create two columns for buttons
        col1, col2 = st.columns(2, gap="small")
        
        with col1:
            with open(avatar_bytes, "rb") as f:
                st.download_button(
                    label="⬇️ Download Your Avatar",
                    data=f.read(),
                    file_name=f"{st.session_state.form_data['name'].replace(' ', '_')}_superhero_avatar.png",
                    mime="image/png",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📧 Email My Avatar", key="email_avatar", use_container_width=True):
                try:
                    # Import email service components
                    from email_service.db_manager import email_db_manager
                    
                    # Create email request
                    email = st.session_state.form_data["email"]
                    name = st.session_state.form_data["name"]
                    
                    email_request_id = email_db_manager.create_email_request(
                        avatar_request_id=st.session_state.request_id,
                        recipient_email=email,
                        recipient_name=name
                    )
                    
                    # Mark avatar request as email requested
                    email_db_manager.mark_email_requested(st.session_state.request_id)
                    
                    # Show success message
                    st.success(f"✅ We'll email your avatar to **{email}** within 5 minutes!")
                    st.info("💡 Check your inbox (and spam folder just in case)")
                    
                except Exception as e:
                    st.error("😔 Sorry, we couldn't queue your email request. Please try again later.")
                    print(f"Email request error: {e}")
    
    # Regenerate button with special styling
    st.markdown("---")
    if st.button("🎲 Regenerate Avatar", key="regenerate", use_container_width=True, type="primary"):
        # Keep all data but go back to generation step
        st.session_state.step = 4
        st.rerun()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Create Another", use_container_width=True):
            reset_session_state()
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            reset_session_state()
            st.session_state.step = 1
            st.rerun()

# Main app
def main():
    """Main application entry point."""
    # Load CSS
    load_css()
    
    # Add Databricks logo in top right
    # Read and encode the logo image
    try:
        with open("assets/Databricks-Logo.png", "rb") as f:
            logo_data = f.read()
        import base64
        logo_base64 = base64.b64encode(logo_data).decode()
        
        st.markdown(
            f"""<a href="https://www.databricks.com" target="_blank" class="databricks-logo-link">
                <img src="data:image/png;base64,{logo_base64}" class="databricks-logo" alt="Databricks">
            </a>""",
            unsafe_allow_html=True
        )
    except:
        # Fallback to text if logo not found
        st.markdown(
            """<a href="https://www.databricks.com" target="_blank" class="databricks-text">
                Databricks
            </a>""",
            unsafe_allow_html=True
        )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown(
        f"<h1 class='stTitle'>{AppConfig.APP_TITLE}</h1>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"<p style='text-align: center; font-size: 1.2rem; margin-bottom: 2rem;'>{AppConfig.APP_DESCRIPTION}</p>",
        unsafe_allow_html=True
    )
    
    # Show step indicator
    show_step_indicator(st.session_state.step)
    
    # Display current step
    if st.session_state.step == 1:
        step_personal_info()
    elif st.session_state.step == 2:
        step_preferences()
    elif st.session_state.step == 3:
        step_photo_capture()
    elif st.session_state.step == 4:
        step_generate_avatar()
    elif st.session_state.step == 5:
        step_display_result()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: #888;'>{AppConfig.EVENT_NAME}</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()