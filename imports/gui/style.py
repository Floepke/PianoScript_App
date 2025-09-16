from PySide6.QtGui import QColor, QPalette
import math

class Style():
    def __init__(self, io):
        
        self.io = io
        self.set_dynamic_theme(tint=.7)

    def calculate_luminance(self, rgb):
        """Calculate relative luminance of an RGB color"""
        def gamma_correct(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        return 0.2126 * gamma_correct(r) + 0.7152 * gamma_correct(g) + 0.0722 * gamma_correct(b)

    def calculate_contrast_ratio(self, rgb1, rgb2):
        """Calculate contrast ratio between two RGB colors"""
        lum1 = self.calculate_luminance(rgb1)
        lum2 = self.calculate_luminance(rgb2)
        
        # Ensure lighter color is numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)

    def ensure_min_contrast(self, color1, color2, min_ratio=4.5):
        """Ensure minimum contrast ratio between two colors"""
        current_ratio = self.calculate_contrast_ratio(color1, color2)
        
        if current_ratio >= min_ratio:
            return color1, color2
        
        # If contrast is too low, adjust the lighter color to be lighter
        # and the darker color to be darker
        lum1 = self.calculate_luminance(color1)
        lum2 = self.calculate_luminance(color2)
        
        if lum1 > lum2:
            # color1 is lighter, make it lighter and color2 darker
            lighter_color = self.adjust_brightness(color1, 1.2)  # Increase brightness
            darker_color = self.adjust_brightness(color2, 0.8)   # Decrease brightness
        else:
            # color2 is lighter, make it lighter and color1 darker
            lighter_color = self.adjust_brightness(color2, 1.2)
            darker_color = self.adjust_brightness(color1, 0.8)
            return darker_color, lighter_color
        
        return lighter_color, darker_color

    def adjust_brightness(self, rgb, factor):
        """Adjust brightness of RGB color by factor"""
        r, g, b = rgb
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        return (r, g, b)

    def smart_interpolate_color(self, light_rgb, dark_rgb, tint, maintain_contrast_with=None, min_contrast=4.5):
        """Smart interpolation that maintains contrast"""
        # Basic interpolation
        r = int(dark_rgb[0] + (light_rgb[0] - dark_rgb[0]) * tint)
        g = int(dark_rgb[1] + (light_rgb[1] - dark_rgb[1]) * tint)
        b = int(dark_rgb[2] + (light_rgb[2] - dark_rgb[2]) * tint)
        interpolated = (r, g, b)
        
        # If we need to maintain contrast with another color
        if maintain_contrast_with is not None:
            interpolated, _ = self.ensure_min_contrast(interpolated, maintain_contrast_with, min_contrast)
        
        return interpolated

    def set_dynamic_theme(self, tint=0.5):
        """
        Set a dynamic theme that interpolates between light and dark themes
        while maintaining proper contrast ratios
        """
        # Clear any custom stylesheet
        self.io['app'].setStyleSheet("")
        
        # Clamp tint between 0 and 1
        tint = max(0.0, min(1.0, tint))
        
        # Define light theme colors
        light_colors = {
            'window': (240, 240, 240),
            'window_text': (0, 0, 0),
            'base': (255, 255, 255),
            'alternate_base': (245, 245, 245),
            'tooltip_base': (255, 255, 220),
            'tooltip_text': (0, 0, 0),
            'text': (0, 0, 0),
            'button': (240, 240, 240),
            'button_text': (0, 0, 0),
            'bright_text': (255, 0, 0),
            'link': (0, 0, 255),
            'highlight': (0, 120, 215),
            'highlighted_text': (255, 255, 255)
        }
        
        # Define dark theme colors
        dark_colors = {
            'window': (53, 53, 53),
            'window_text': (255, 255, 255),
            'base': (25, 25, 25),
            'alternate_base': (53, 53, 53),
            'tooltip_base': (0, 0, 0),
            'tooltip_text': (255, 255, 255),
            'text': (255, 255, 255),
            'button': (53, 53, 53),
            'button_text': (255, 255, 255),
            'bright_text': (255, 0, 0),
            'link': (42, 130, 218),
            'highlight': (42, 130, 218),
            'highlighted_text': (0, 0, 0)
        }
        
        # Create dynamic palette
        dynamic_palette = QPalette()
        
        # Interpolate background colors first
        window_color = self.smart_interpolate_color(light_colors['window'], dark_colors['window'], tint)
        base_color = self.smart_interpolate_color(light_colors['base'], dark_colors['base'], tint)
        button_color = self.smart_interpolate_color(light_colors['button'], dark_colors['button'], tint)
        alternate_base_color = self.smart_interpolate_color(light_colors['alternate_base'], dark_colors['alternate_base'], tint)
        tooltip_base_color = self.smart_interpolate_color(light_colors['tooltip_base'], dark_colors['tooltip_base'], tint)
        highlight_color = self.smart_interpolate_color(light_colors['highlight'], dark_colors['highlight'], tint)
        
        # Interpolate text colors with contrast maintenance
        window_text_color = self.smart_interpolate_color(
            light_colors['window_text'], dark_colors['window_text'], tint, 
            maintain_contrast_with=window_color
        )
        text_color = self.smart_interpolate_color(
            light_colors['text'], dark_colors['text'], tint,
            maintain_contrast_with=base_color
        )
        button_text_color = self.smart_interpolate_color(
            light_colors['button_text'], dark_colors['button_text'], tint,
            maintain_contrast_with=button_color
        )
        tooltip_text_color = self.smart_interpolate_color(
            light_colors['tooltip_text'], dark_colors['tooltip_text'], tint,
            maintain_contrast_with=tooltip_base_color
        )
        highlighted_text_color = self.smart_interpolate_color(
            light_colors['highlighted_text'], dark_colors['highlighted_text'], tint,
            maintain_contrast_with=highlight_color
        )
        
        # Colors that don't need contrast checking
        bright_text_color = self.smart_interpolate_color(light_colors['bright_text'], dark_colors['bright_text'], tint)
        link_color = self.smart_interpolate_color(light_colors['link'], dark_colors['link'], tint)
        
        # Apply colors to palette
        dynamic_palette.setColor(QPalette.Window, QColor(*window_color))
        dynamic_palette.setColor(QPalette.WindowText, QColor(*window_text_color))
        dynamic_palette.setColor(QPalette.Base, QColor(*base_color))
        dynamic_palette.setColor(QPalette.AlternateBase, QColor(*alternate_base_color))
        dynamic_palette.setColor(QPalette.ToolTipBase, QColor(*tooltip_base_color))
        dynamic_palette.setColor(QPalette.ToolTipText, QColor(*tooltip_text_color))
        dynamic_palette.setColor(QPalette.Text, QColor(*text_color))
        dynamic_palette.setColor(QPalette.Button, QColor(*button_color))
        dynamic_palette.setColor(QPalette.ButtonText, QColor(*button_text_color))
        dynamic_palette.setColor(QPalette.BrightText, QColor(*bright_text_color))
        dynamic_palette.setColor(QPalette.Link, QColor(*link_color))
        dynamic_palette.setColor(QPalette.Highlight, QColor(*highlight_color))
        dynamic_palette.setColor(QPalette.HighlightedText, QColor(*highlighted_text_color))
        
        self.io['app'].setPalette(dynamic_palette)

    def set_grey_theme(self):
        """Set Qt's native grey theme using palette - calls dynamic theme with 0.5"""
        self.set_dynamic_theme(0.5)