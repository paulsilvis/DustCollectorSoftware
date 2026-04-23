# 🚀 Quick Start Guide - Viewing Your Diagrams

## The Problem
You tried to open `diagrams_viewer.html` directly in your browser, but the images don't load. This is because browsers block local HTML files from loading other local files for security reasons.

## ✅ Easy Solutions

### Option 1: Use the Launcher Script (EASIEST!)

**On Linux/Mac:**
```bash
chmod +x VIEW_DIAGRAMS.sh
./VIEW_DIAGRAMS.sh
```

**On Windows:**
```
Double-click VIEW_DIAGRAMS.bat
```

This starts a simple web server and opens the viewer automatically!

---

### Option 2: Start a Web Server Manually

Open a terminal/command prompt in this folder and run:

**On Linux/Mac/Windows:**
```bash
python3 -m http.server 8000
```

Then open your browser to: **http://localhost:8000/diagrams_viewer_simple.html**

(Or use diagrams_viewer.html - both work, but the "simple" version is more reliable)

Press Ctrl+C in the terminal to stop the server when you're done.

---

### Option 3: Just View the Images Directly (SIMPLEST!)

Skip the HTML viewer entirely! Just open these files in any image viewer or browser:

📊 **Main Diagrams:**
- **system_diagram_enhanced.png** - Beautiful full system architecture ⭐
- **system_diagram_poster.png** - High-resolution version for printing (300 DPI)
- **dataflow_diagram.png** - How data flows through the system
- **state_machine.png** - Gate control state machine

📊 **Auto-Generated Diagrams:**
- **event_flow.png** - Event publish/subscribe relationships
- **component_architecture.png** - Layered architecture view
- **module_dependencies.png** - Python module structure

You can also use the SVG versions (same names with .svg extension) for infinite zoom!

---

### Option 4: Use an Online Viewer

If you want to see the interactive HTML without setting up a server:

1. Go to: https://htmlpreview.github.io/
2. Upload or paste the `diagrams_viewer.html` file
3. View it there!

---

## 🖨️ For Printing

Use **system_diagram_poster.png** - it's 300 DPI and will look amazing printed at:
- 24" × 36" (poster size)
- 18" × 24" (medium)
- Even larger if you want!

Most print shops (FedEx Office, Staples, local print shops) can print this easily.

---

## ❓ Troubleshooting

**"Python is not recognized"**
- Install Python from https://www.python.org/downloads/
- Or just use Option 3 and open the PNG files directly!

**"Port 8000 is already in use"**
- Change the port: `python3 -m http.server 8080`
- Then use: http://localhost:8080/diagrams_viewer.html

**Images still not loading**
- Make sure all the .png and .svg files are in the same folder as diagrams_viewer.html
- Or just open the image files directly!

---

## 📚 More Info

See these files for complete documentation:
- **VISUALIZATION_GUIDE.md** - Complete usage guide
- **DIAGRAMS_README.md** - Technical details about each diagram

---

## 🎨 What Each Diagram Shows

- **System Diagram Enhanced** - Complete architecture, event bus, hardware, controllers
- **Data Flow** - Sensor input → processing → gate control → outputs
- **State Machine** - How gates transition between open/closed states
- **Event Flow** - Which components publish/subscribe to which events
- **Component Architecture** - Software layers and dependencies
- **Module Dependencies** - Python code structure

---

**TIP:** If you just want to see the diagrams quickly, open the PNG files directly in any image viewer. The HTML viewer is nice but not required!
