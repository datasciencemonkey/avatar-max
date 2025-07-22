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
            if st.button("← Try Again", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        else:
            # Save images
            status_text.text("Saving your avatar...")
            
            # Save original
            original_filename = generate_unique_filename("original", "jpg")
            original_path = save_image(
                st.session_state.photo,
                AppConfig.ORIGINALS_DIR,
                original_filename
            )
            
            # Save avatar
            avatar_filename = generate_unique_filename("avatar", "png")
            avatar_path = save_image(
                avatar,
                AppConfig.AVATARS_DIR,
                avatar_filename
            )
            
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
    st.info(f"✨ Generated in {format_generation_time(st.session_state.generation_time)}")
    
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
        f"<p style='text-align: center; color: #888;'>Built for {AppConfig.EVENT_NAME}</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()