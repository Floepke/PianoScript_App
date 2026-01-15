#!/usr/bin/env python3
# coding: utf8

""" Simple test script to verify font loading without GUI """

import sys
import os

# Add the project root to Python path (go up two levels from imports/fonts/)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_basic_imports():
    """Test basic imports without Qt"""
    print("Basic Import Test")
    print("=" * 50)
    
    try:
        from fonts_data import font_dict
        print("✓ Successfully imported font_dict")
        print(f"  Available keys: {list(font_dict.keys())}")
        
        # Check if data exists
        if 'edwin_roman' in font_dict:
            data_length = len(font_dict['edwin_roman'])
            print(f"  Edwin Roman data length: {data_length} characters")
        
    except Exception as e:
        print(f"✗ Error importing font_dict: {e}")
        return False
    
    try:
        import fonts
        print("✓ Successfully imported font utility functions")
        
        # Test decoding
        if 'edwin_roman' in font_dict:
            decoded_bytes = fonts.b64_decode(font_dict['edwin_roman'])
            print(f"  Decoded font size: {len(decoded_bytes)} bytes")
            
            # Check if it looks like a font file (OTF files start with specific bytes)
            if decoded_bytes[:4] == b'OTTO':
                print("  ✓ Data appears to be a valid OTF font file")
            else:
                print(f"  ? Data doesn't start with OTF header (starts with: {decoded_bytes[:8]})")
        
    except Exception as e:
        print(f"✗ Error testing font decoding: {e}")
        return False
    
    return True


def test_qt_initialization():
    """Test Qt initialization separately"""
    print("\nQt Initialization Test")
    print("=" * 50)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtCore import QByteArray
        print("✓ Successfully imported Qt modules")
        
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✓ QApplication created/retrieved")
        
        # Test QFontDatabase
        db = QFontDatabase()
        system_families = db.families()
        print(f"✓ System has {len(system_families)} font families")
        
        return app
        
    except Exception as e:
        print(f"✗ Error with Qt initialization: {e}")
        return None


def test_font_loading_with_qt(app):
    """Test actual font loading with Qt"""
    print("\nFont Loading with Qt Test")
    print("=" * 50)
    
    if not app:
        print("✗ No Qt application available")
        return
    
    try:
        from fonts_data import font_dict
        import fonts
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtCore import QByteArray
        
        if 'edwin_roman' not in font_dict:
            print("✗ edwin_roman not found in font_dict")
            return
        
        # Decode font data
        font_bytes = fonts.b64_decode(font_dict['edwin_roman'])
        font_data = QByteArray(font_bytes)
        print(f"✓ Font data prepared: {len(font_bytes)} bytes")
        
        # Load into QFontDatabase
        font_id = QFontDatabase.addApplicationFontFromData(font_data)
        if font_id == -1:
            print("✗ Failed to load font into QFontDatabase")
        else:
            print(f"✓ Font loaded successfully with ID: {font_id}")
            
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"✓ Available font families: {families}")
        
    except Exception as e:
        print(f"✗ Error during font loading: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    print("Font System Test")
    print("=" * 80)
    
    # Test 1: Basic imports and data integrity
    if not test_basic_imports():
        print("\n✗ Basic tests failed, stopping")
        return
    
    # Test 2: Qt initialization
    app = test_qt_initialization()
    
    # Test 3: Font loading with Qt
    if app:
        test_font_loading_with_qt(app)
    
    print("\n" + "=" * 80)
    print("Test completed")


if __name__ == "__main__":
    main()