import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(layout="wide", page_title="BEN715 IFC Dashboard")
st.title("BEN715 IFC Dashboard")

projects = {
    "Office Block": "office",
    "Apartment Building": "apartment",
    "Town Hall": "town_hall"
}

selected_project = st.sidebar.selectbox("Select Project", list(projects.keys()))
project_folder = projects[selected_project]
data_path = os.path.join("data", project_folder)
st.sidebar.caption(f"Active folder: data/{project_folder}")

if not os.path.exists(data_path):
    st.error("Project data folder not found.")
    st.stop()

csv_files = sorted([f for f in os.listdir(data_path) if f.lower().endswith(".csv")])

if not csv_files:
    st.info("No schedules found for this project.")
    st.stop()

tab_labels = [os.path.splitext(f)[0].replace("_", " ").title() for f in csv_files]
tab_labels.append(" 3D Building Viewer")
tabs = st.tabs(tab_labels)

# =====================================================
# PDF DOCUMENTATION DROPDOWN
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### Documentation")

# Define your PDF files with descriptions
pdf_files = {
    "Handover Instructions": {
        "filename": "Handover_Instructions.pdf",
        "description": "Complete user guide for dashboard administrators. Includes setup, maintenance, and troubleshooting."
    },
    "Handover Instructions - IFC Cleaning": {
        "filename": "Handover_Instructions_Initial_IFC_Cleaning.pdf",
        "description": "Guide for initial cleaning of IFC files and creating CSV schedules directly from IFC data."
    },
    "Analysis Script": {
        "filename": "Analysis_Script.pdf",
        "description": "Python script for data analysis and BIM schedule processing."
    },
    "IFC Dashboard Full Code": {
        "filename": "IFC_Dashboard_Full_Code.pdf",
        "description": "Complete source code for the Streamlit dashboard (app.py)."
    },
    "IFC to Schedules Script": {
        "filename": "IFC_to_Schedules_Script.pdf",
        "description": "Script for extracting schedule data from IFC files."
    }
}

# Dropdown to select PDF
selected_pdf = st.sidebar.selectbox(
    "Select Document:",
    list(pdf_files.keys())
)

# Show description
st.sidebar.info(f" {pdf_files[selected_pdf]['description']}")

# Download button for selected PDF
pdf_path = pdf_files[selected_pdf]['filename']
if os.path.exists(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    st.sidebar.download_button(
        label=f" Download {selected_pdf} (PDF)",
        data=pdf_bytes,
        file_name=pdf_path,
        mime="application/pdf",
        use_container_width=True,
        key=selected_pdf
    )
else:
    st.sidebar.warning(f" File not found: {pdf_path}")
    st.sidebar.caption(f"Please place {pdf_path} in the dashboard folder")

# =====================================================
# ORIGINAL CSV TABS
# =====================================================
for tab, filename in zip(tabs[:-1], csv_files):
    with tab:
        schedule_name = os.path.splitext(filename)[0].replace("_", " ").title()
        csv_path = os.path.join(data_path, filename)
        
        st.subheader(schedule_name)
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            st.error("Failed to load schedule")
            st.exception(e)
            continue
        
        st.markdown("### Schedule Data")
        st.dataframe(df, use_container_width=True)
        
        # DOOR INSPECTION PANEL
        if "door" in schedule_name.lower():
            st.markdown("### Interactive Door Inspection")
            door_root = os.path.join("data", project_folder, "doors")
            
            if os.path.exists(door_root):
                door_ids = sorted([d for d in os.listdir(door_root) if os.path.isdir(os.path.join(door_root, d))])
                
                if door_ids:
                    selected_door = st.selectbox("Select a door", door_ids)
                    door_path = os.path.join(door_root, selected_door)
                    json_path = os.path.join(door_path, f"{selected_door}.json")
                    
                    if os.path.exists(json_path):
                        with open(json_path, "r") as f:
                            door_data = json.load(f)
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            image_path = os.path.join(door_path, door_data.get("image", ""))
                            if os.path.exists(image_path):
                                st.image(image_path, caption=f"Door {door_data['id']}", use_column_width=True)
                            else:
                                st.info("Door image not available.")
                        
                        with col2:
                            st.markdown(f"**Door ID:** {door_data.get('id', 'N/A')}")
                            st.markdown(f"**Type:** {door_data.get('type', 'N/A')}")
                            st.markdown(f"**Level:** {door_data.get('level', 'N/A')}")
                            st.markdown(f"**Fire Rating:** {door_data.get('fire_rating', 'N/A')}")
                            st.markdown(f"**Size:** {door_data.get('width_mm', 'N/A')} × {door_data.get('height_mm', 'N/A')} mm")
                            st.markdown(door_data.get('description', 'No description'))
                        
                        if door_data.get("video", {}).get("type") == "youtube":
                            st.markdown("### Area Walkthrough")
                            st.video(door_data["video"]["src"])
                        
                        # IFC Button
                        st.markdown(f"### IFC Model for {selected_project}")
                        viewer_url = f"http://localhost:8000/dashboard.html?building={project_folder}"
                        st.markdown(
                            f'<a href="{viewer_url}" target="_blank">'
                            '<button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">'
                            f' Open {selected_project} in 3D Viewer'
                            '</button></a>',
                            unsafe_allow_html=True
                        )

# =====================================================
# 3D VIEWER TAB
# =====================================================
with tabs[-1]:
    st.header(" Interactive 3D Building Viewer")

    server_running = False
    try:
        requests.get("http://localhost:8000", timeout=1)
        server_running = True
    except:
        pass

    if not server_running:
        st.warning(" HTTP Server not running!")
        st.markdown("""
        **To use the 3D viewer, start the server in a separate Anaconda Prompt:**
        """)
    else:
        st.success(" 3D Server is running!")
        xkt_base_url = "https://raw.githubusercontent.com/joelriley70-commits/ifc-dashboard/master/xeokit-simple-viewer-main/buildings/"
        iframe_url = f"/dashboard.html?building={project_folder}&xkt_base={xkt_base_url}"
        components.iframe(iframe_url, height=700, width=1200)
        st.caption(" Tip: Click on any door or element to highlight it!")

# =====================================================
# EXCEL GRAPHS AND IMAGES
# =====================================================
st.markdown("---")
st.subheader(" Excel-Based Analysis")

excel_dir = os.path.join("images", project_folder, "excel_graphs")

if os.path.exists(excel_dir):
    excel_images = [
        f for f in os.listdir(excel_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if excel_images:
        cols = st.columns(min(3, len(excel_images)))
        for col_img, img in zip(cols, excel_images):
            with col_img:
                st.image(
                    os.path.join(excel_dir, img),
                    caption=img.replace("_", " ").split(".")[0].title()
                )
    else:
        st.info("No Excel graph images found.")
else:
    st.info("Excel analysis not available for this project.")

# =====================================================
# BUILDING VISUALS
# =====================================================
st.subheader(" Building Visuals")

image_dir = os.path.join("images", project_folder)
image_map = {
    "Floor Plan": "floor_plan.png",
    "Render": "render.png",
    "Elevation": "elevation.png",
}

cols = st.columns(3)

for col, (label, file) in zip(cols, image_map.items()):
    path = os.path.join(image_dir, file)
    with col:
        if os.path.exists(path):
            st.image(path, caption=label)
        else:
            st.info(f"{label} not available")
