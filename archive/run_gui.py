#!/usr/bin/env python3
"""
Launcher script for the Steel-Coal I-O Analysis Streamlit GUI
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit application."""
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit not found. Installing GUI requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_gui.txt"])
        print("✅ GUI requirements installed!")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "libs", "gui", "streamlit_app.py")
    
    print("🚀 Launching Steel-Coal I-O Analysis Dashboard...")
    print("📊 The GUI will open in your web browser automatically.")
    print("🔗 If it doesn't open, go to: http://localhost:8502")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Launch Streamlit
    try:
        # Check if file exists before launching
        if not os.path.exists(app_path):
            print(f"❌ Error: Streamlit app not found at {app_path}")
            print(f"📁 Current directory: {script_dir}")
            print("📋 Available files:")
            for root, dirs, files in os.walk(script_dir):
                level = root.replace(script_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # Show first 5 files
                    print(f"{subindent}{file}")
                if len(files) > 5:
                    print(f"{subindent}... and {len(files)-5} more files")
                if level > 2:  # Limit depth
                    break
            return
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", "8502",  # Changed port to avoid conflicts
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 GUI application stopped.")
    except Exception as e:
        print(f"❌ Error launching GUI: {str(e)}")
        print("\n💡 Try running manually:")
        print(f"   streamlit run {app_path}")

if __name__ == "__main__":
    main()