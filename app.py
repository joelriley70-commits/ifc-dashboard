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
tab_labels.append("🏗️ 3D Building Viewer")
tabs = st.tabs(tab_labels)

# =====================================================
# PDF DOCUMENTATION DROPDOWN
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Documentation")

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
st.sidebar.info(f"📄 {pdf_files[selected_pdf]['description']}")

# Download button for selected PDF
pdf_path = pdf_files[selected_pdf]['filename']
if os.path.exists(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    st.sidebar.download_button(
        label=f"📥 Download {selected_pdf} (PDF)",
        data=pdf_bytes,
        file_name=pdf_path,
        mime="application/pdf",
        use_container_width=True,
        key=selected_pdf
    )
else:
    st.sidebar.warning(f"⚠️ File not found: {pdf_path}")
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
            # Try both "doors" and "Doors" for compatibility
            door_root = os.path.join("data", project_folder, "doors")
            if not os.path.exists(door_root):
                door_root = os.path.join("data", project_folder, "Doors")
            
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
                                st.image(image_path, caption=f"Door {door_data.get('id', selected_door)}", use_column_width=True)
                            else:
                                st.info("Door image not available.")
                        
                        with col2:
                            st.markdown(f"**Door ID:** {door_data.get('id', selected_door)}")
                            st.markdown(f"**Type:** {door_data.get('type', 'N/A')}")
                            st.markdown(f"**Level:** {door_data.get('level', 'N/A')}")
                            st.markdown(f"**Fire Rating:** {door_data.get('fire_rating', 'N/A')}")
                            st.markdown(f"**Size:** {door_data.get('width_mm', 'N/A')} × {door_data.get('height_mm', 'N/A')} mm")
                            st.markdown(door_data.get('description', 'No description'))
                        
                        if door_data.get("video", {}).get("type") == "youtube":
                            st.markdown("### Area Walkthrough")
                            video_url = door_data["video"]["src"]
                            # Convert youtu.be links to youtube.com/embed
                            if "youtu.be" in video_url:
                                video_id = video_url.split("/")[-1]
                                video_url = f"https://www.youtube.com/embed/{video_id}"
                            st.video(video_url)
                        
                        # IFC Button - Link to 3D viewer tab
                        st.markdown(f"### IFC Model for {selected_project}")
                        st.info(f"📐 View the complete **{selected_project}** building in the **🏗️ 3D Building Viewer** tab above")

# =====================================================
# 3D VIEWER TAB - DIRECT EMBED (NO IFRAME)
# =====================================================
with tabs[-1]:
    st.header("🏗️ Interactive 3D Building Viewer")
    
    st.info(f"📍 Currently viewing: **{selected_project}** building")
    
    # Read the dashboard.html file and modify it for direct embedding
    import base64
    
    # Google Drive direct download URLs
    xkt_urls = {
        "town_hall": "https://drive.google.com/uc?export=download&id=1V43mltb7NMKHNx0NRIRXEN2YscvEW8MP",
        "apartment": "https://drive.google.com/uc?export=download&id=12gsJ8o4Puzx-6OGFeUnm83dROMS4a0R3",
        "office": "https://drive.google.com/uc?export=download&id=1hnlM1HQXkRxLpwbGKEEYyqb86MawqBKK"
    }
    
    # Create the viewer HTML with the correct XKT URL
    viewer_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; font-family: Arial; }}
            #info {{
                position: absolute;
                top: 20px;
                left: 20px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 10px;
                border-radius: 5px;
                z-index: 100;
                font-size: 12px;
                pointer-events: none;
            }}
            canvas {{ width: 100%; height: 100%; display: block; }}
        </style>
    </head>
    <body>
        <div id="info">
            <strong>🏗️ Loading {selected_project}...</strong><br>
            Please wait, this may take 30-60 seconds
        </div>
        <canvas id="myCanvas"></canvas>
        
        <script type="importmap">
            {{
                "imports": {{
                    "@xeokit/xeokit-sdk": "https://unpkg.com/@xeokit/xeokit-sdk/dist/xeokit-sdk.es.js"
                }}
            }}
        </script>
        
        <script type="module">
            import {{Viewer, XKTLoaderPlugin}} from "@xeokit/xeokit-sdk";
            
            const viewer = new Viewer({{
                canvasId: "myCanvas",
                transparent: false,
                backgroundColor: [0.15, 0.15, 0.2]
            }});
            
            viewer.camera.eye = [-10, 5, 10];
            viewer.camera.look = [0, 0, 0];
            
            const xktLoader = new XKTLoaderPlugin(viewer);
            
            const infoDiv = document.getElementById("info");
            const xktUrl = "{xkt_urls[project_folder]}";
            
            infoDiv.innerHTML = `<strong>🏗️ Loading {selected_project}...</strong><br>Downloading model...`;
            
            const model = xktLoader.load({{
                id: "{project_folder}",
                src: xktUrl,
                edges: true
            }});
            
            model.on("loaded", () => {{
                infoDiv.innerHTML = `<strong>✅ {selected_project} loaded!</strong><br>Click any element to highlight it`;
                setTimeout(() => {{
                    infoDiv.style.opacity = "0.5";
                }}, 3000);
            }});
            
            model.on("error", (error) => {{
                infoDiv.innerHTML = `<strong>❌ Error loading model</strong><br>Check console for details`;
                console.error("Load error:", error);
            }});
            
            // Click to highlight
            viewer.cameraControl.on("click", (e) => {{
                const canvasRect = document.getElementById('myCanvas').getBoundingClientRect();
                const pickResult = viewer.scene.pick({{
                    canvasPos: [e.clientX - canvasRect.left, e.clientY - canvasRect.top]
                }});
                
                if (pickResult && pickResult.object) {{
                    viewer.scene.objects.forEach(obj => obj.highlighted = false);
                    pickResult.object.highlighted = true;
                    infoDiv.innerHTML = `<strong>✅ Selected:</strong> ${{pickResult.object.id}}`;
                    infoDiv.style.opacity = "1";
                    setTimeout(() => {{
                        infoDiv.style.opacity = "0.5";
                    }}, 2000);
                }}
            }});
        </script>
    </body>
    </html>
    '''
    
    # Display the viewer directly in Streamlit
    components.html(viewer_html, height=700, width=1200)
    
    with st.expander("📖 Instructions", expanded=False):
        st.markdown("""
        **🎮 Controls:**
        - **Left click + drag**: Rotate the view
        - **Right click + drag**: Pan around  
        - **Scroll**: Zoom in/out
        - **Click on any object**: Highlight it
        
        **💡 Note:** The first load may take 30-60 seconds as the model downloads from Google Drive.
        """)
# =====================================================
# EXCEL GRAPHS AND IMAGES
# =====================================================
st.markdown("---")
st.subheader("📊 Excel-Based Analysis")

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
st.subheader("🏛️ Building Visuals")

image_dir = os.path.join("images", project_folder)
image_map = {
    "Floor Plan": "floor_plan.png",
    "Render": "render.png",
    "Elevation": "elevation.png"
}

cols = st.columns(3)

for col, (label, file) in zip(cols, image_map.items()):
    path = os.path.join(image_dir, file)
    with col:
        if os.path.exists(path):
            st.image(path, caption=label)
        else:
            st.info(f"{label} not available")