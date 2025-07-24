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
    
    # Show generation details
    style_score = getattr(st.session_state.generated_avatar, 'style_score', None)
    if style_score:
        quality_emoji = "🌟" if style_score >= 0.8 else "✨" if style_score >= 0.7 else "⭐"
        st.info(f"{quality_emoji} Generated in {format_generation_time(st.session_state.generation_time)} | Style consistency: {style_score:.1%} | Try regenerating for different variations!")
    
    # Download button
    if AppConfig.ENABLE_DOWNLOAD:
        avatar_bytes = save_image(
            st.session_state.generated_avatar,
            Path("/tmp"),
            "temp_avatar.png"
        )
        
        with open(avatar_bytes, "rb") as f:
            st.download_button(
                label="⬇️ Download Your Avatar",
                data=f.read(),
                file_name=f"{st.session_state.form_data['name'].replace(' ', '_')}_superhero_avatar.png",
                mime="image/png",
                use_container_width=True
            )
    
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
    st.markdown(
        """<a href="https://www.databricks.com" target="_blank">
            <svg class="databricks-logo" viewBox="0 0 216 48" style="height: 40px; width: auto;">
                <g fill="none" fill-rule="evenodd">
                    <path fill="#FF3621" d="M10.5 24l10.5 6v12L10.5 36V24zM0 18l10.5 6v12L0 30V18zm21 0l10.5 6v12L21 30V18z"/>
                    <path fill="#00A972" d="M10.5 0L21 6v12l-10.5-6V0z"/>
                    <path fill="#FF3621" d="M21 6l10.5 6v12L21 18V6z"/>
                    <path fill="#00A972" d="M0 6l10.5 6v12L0 18V6z"/>
                    <path fill="#1B1B1B" d="M50.4 36h5.1v-8.7c0-3.6 2.4-5.7 5.4-5.7 1.2 0 2.1.3 2.7.6v-4.8c-.6-.2-1.2-.3-1.8-.3-2.4 0-4.5 1.2-5.7 3.3h-.3v-3h-5.4V36zm-18.3-8.4c0 2.4 1.5 4.2 3.9 4.2s3.9-1.8 3.9-4.2-1.5-4.2-3.9-4.2-3.9 1.8-3.9 4.2m-5.4 0c0-5.1 3.6-9 8.7-9 2.7 0 4.8.9 6.3 2.7h.3v-2.4H47V36h-5.1v-2.4h-.3c-1.5 1.8-3.6 2.7-6.3 2.7-5.1 0-8.7-3.9-8.7-9m40.5 0c0 2.4 1.5 4.2 3.9 4.2s3.9-1.8 3.9-4.2-1.5-4.2-3.9-4.2-3.9 1.8-3.9 4.2m-5.4 0c0-5.1 3.6-9 8.7-9 2.7 0 4.8.9 6.3 2.7h.3v-2.4h5.1V36h-5.1v-2.4h-.3c-1.5 1.8-3.6 2.7-6.3 2.7-5.1 0-8.7-3.9-8.7-9m31.8 5.7c2.1 0 3.3-1.5 3.3-3.6s-1.2-3.6-3.3-3.6-3.3 1.5-3.3 3.6 1.2 3.6 3.3 3.6m-.6-12c1.8 0 3.3-1.5 3.3-3.3s-1.5-3.3-3.3-3.3-3.3 1.5-3.3 3.3 1.5 3.3 3.3 3.3M108 27.6c0 5.1-3.6 8.7-8.1 8.7-2.4 0-4.5-.9-5.7-2.7h-.3V36h-5.1V10.8h5.4v9.5h.3c1.2-1.5 3-2.4 5.4-2.4 4.5 0 8.1 3.6 8.1 8.7m5.7 8.4V10.8h5.4V36h-5.4zm22.2-18.6c-2.7 0-4.2 1.8-4.5 3.9h8.7c-.3-2.1-1.8-3.9-4.2-3.9m9.6 6.9h-14.1c.3 2.4 2.1 3.9 4.8 3.9 1.8 0 3.3-.6 4.2-1.8l3.6 3c-1.8 2.4-4.8 3.6-8.1 3.6-5.7 0-9.6-3.9-9.6-9s3.9-9 9.3-9 9.3 3.6 9.3 9c0 .6 0 .9-.3 1.2m11.1-6c-2.1 0-3.6 1.5-3.6 3.6s1.5 3.6 3.6 3.6 3.6-1.5 3.6-3.6-1.5-3.6-3.6-3.6m3.9 14.1c-1.2 1.8-3.6 2.7-6.3 2.7-5.1 0-8.7-3.9-8.7-9s3.6-9 8.7-9c2.7 0 4.8.9 6.3 2.7h.3v-7.2h5.4V36h-5.1v-2.4h-.3zm11.7-11.1h2.7v-3.9h-2.7v3.9zM193 27.6c0-5.1 3.9-9 9.3-9 3.3 0 6.3 1.5 7.8 4.2l-4.5 2.4c-.6-1.2-1.8-1.8-3.3-1.8-2.4 0-3.9 1.8-3.9 4.2s1.5 4.2 3.9 4.2c1.5 0 2.7-.6 3.3-1.8l4.5 2.4c-1.5 2.7-4.5 4.2-7.8 4.2-5.4 0-9.3-3.9-9.3-9m30-4.5l-5.7 6.3V36H212V10.8h5.4v11.4l5.1-5.1h6.6l-6.6 6.9 7.2 11.1H223l-4.5-7.8-.6.6zm-36.6.3c-1.8 0-3 .6-3.6 1.5l3.9 2.7c0-.3.3-.6.9-.6.9 0 1.8.3 1.8 1.2v.3c-.6-.3-1.8-.6-2.7-.6-3 0-5.1 1.5-5.1 4.2 0 2.4 2.1 3.9 4.5 3.9 1.5 0 2.7-.6 3.3-1.5h.3V36h5.1v-9.9c0-3.9-3-6-6.6-6m-1.8 10.2c-.9 0-1.5-.3-1.5-.9 0-.9.9-1.2 1.8-1.2.9 0 1.5.3 1.8.3 0 1.2-.9 1.8-2.1 1.8"/>
                </g>
            </svg>
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