import PyInstaller.__main__
import shutil
import os

def build_app():
    print("🚀 Starting Build Process for AiXiaoliang...")
    
    # 1. Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    # 2. Run PyInstaller
    print("📦 Running PyInstaller...")
    PyInstaller.__main__.run([
        'aixiaoliang_agent/app.py',
        '--name=AiXiaoliang',
        '--onedir',
        '--clean',
        '--noconfirm',
        '--hidden-import=gradio',
        '--hidden-import=pandas',
        '--hidden-import=tushare',
        '--hidden-import=matplotlib',
        '--collect-all=safehttpx',
        '--collect-all=gradio',
        '--collect-all=gradio_client',
        '--collect-all=groovy',
        # Add root to python path implicitly by running from root
    ])
    
    # 3. Post-Build: Copy Assets
    dist_path = os.path.join("dist", "AiXiaoliang")
    print(f"📂 Copying assets to {dist_path}...")
    
    # Copy Knowledge Base
    src_knowledge = "knowledge"
    dst_knowledge = os.path.join(dist_path, "knowledge")
    if os.path.exists(src_knowledge):
        shutil.copytree(src_knowledge, dst_knowledge)
        print("   ✅ Copied knowledge/")
    else:
        print("   ⚠️ Warning: knowledge/ folder not found!")
        
    # Copy .env.template (as .env or template)
    # Let's simple copy .env.template
    if os.path.exists(".env.template"):
        shutil.copy(".env.template", os.path.join(dist_path, ".env.template"))
        # Also copy .env if exists for convenience? No, unsafe for distribution.
        # But for "Colleague" usage, user might want to copy their own .env manually.
        print("   ✅ Copied .env.template")
        
    # Create logs directory
    os.makedirs(os.path.join(dist_path, "logs"), exist_ok=True)
    print("   ✅ Created logs/ directory")
    
    # Create Debug Script
    bat_content = """@echo off
echo [*] Starting AiXiaoliang in Debug Mode...
cd /d "%~dp0"
AiXiaoliang.exe
echo.
echo [!] Application exited.
pause
"""
    with open(os.path.join(dist_path, "run_debug.bat"), "w") as f:
        f.write(bat_content)
    print("   ✅ Created run_debug.bat")
    
    print("\n🎉 Build Complete! Artifact is in: dist/AiXiaoliang")
    print("👉 To run: Go to dist/AiXiaoliang and run AiXiaoliang.exe (Internal Console will open)")
    
if __name__ == "__main__":
    build_app()
