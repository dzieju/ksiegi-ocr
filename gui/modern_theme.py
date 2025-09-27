"""
Modern theme configuration for the application using CustomTkinter
Provides consistent colors, fonts, and styling throughout the application
"""

import customtkinter as ctk
from typing import Dict, Tuple

class ModernTheme:
    """Modern theme configuration for CustomTkinter application"""
    
    # Color scheme - Professional blue/gray theme
    COLORS = {
        'primary': '#2B579A',      # Professional blue
        'primary_hover': '#1E3A8A',  # Darker blue for hover
        'secondary': '#64748B',    # Slate gray
        'success': '#059669',      # Green for success states
        'warning': '#D97706',      # Orange for warnings
        'error': '#DC2626',        # Red for errors
        'background': '#F8FAFC',   # Light gray background
        'surface': '#FFFFFF',      # White surface
        'text_primary': '#1E293B', # Dark gray text
        'text_secondary': '#64748B', # Lighter gray text
        'border': '#E2E8F0',       # Light border
        'hover': '#F1F5F9',        # Light hover state
    }
    
    # Font configuration
    FONTS = {
        'heading': ('Segoe UI', 16, 'bold'),
        'subheading': ('Segoe UI', 14, 'bold'),
        'body': ('Segoe UI', 11),
        'button': ('Segoe UI', 11, 'bold'),
        'small': ('Segoe UI', 9),
        'monospace': ('Consolas', 10),
    }
    
    # Spacing and sizing
    SPACING = {
        'small': 8,
        'medium': 16,
        'large': 24,
        'xlarge': 32,
    }
    
    # Button dimensions
    BUTTON_SIZE = {
        'small': (100, 28),
        'medium': (140, 32),
        'large': (180, 36),
    }
    
    @classmethod
    def setup_theme(cls):
        """Initialize the CustomTkinter theme"""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("light")  # or "system"
        ctk.set_default_color_theme("blue")
        
        # Configure CustomTkinter colors
        ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = [cls.COLORS['surface'], cls.COLORS['surface']]
        ctk.ThemeManager.theme["CTkFrame"]["border_color"] = [cls.COLORS['border'], cls.COLORS['border']]
        
    @classmethod
    def get_button_style(cls, style_type: str = 'primary') -> Dict:
        """Get button style configuration"""
        styles = {
            'primary': {
                'fg_color': cls.COLORS['primary'],
                'hover_color': cls.COLORS['primary_hover'],
                'text_color': 'white',
                'font': cls.FONTS['button'],
                'corner_radius': 6,
            },
            'secondary': {
                'fg_color': cls.COLORS['secondary'],
                'hover_color': '#475569',
                'text_color': 'white',
                'font': cls.FONTS['button'],
                'corner_radius': 6,
            },
            'success': {
                'fg_color': cls.COLORS['success'],
                'hover_color': '#047857',
                'text_color': 'white',
                'font': cls.FONTS['button'],
                'corner_radius': 6,
            },
            'danger': {
                'fg_color': cls.COLORS['error'],
                'hover_color': '#B91C1C',
                'text_color': 'white',
                'font': cls.FONTS['button'],
                'corner_radius': 6,
            },
        }
        return styles.get(style_type, styles['primary'])
    
    @classmethod
    def get_frame_style(cls, style_type: str = 'default') -> Dict:
        """Get frame style configuration"""
        styles = {
            'default': {
                'fg_color': cls.COLORS['surface'],
                'corner_radius': 8,
                'border_width': 1,
                'border_color': cls.COLORS['border'],
            },
            'card': {
                'fg_color': cls.COLORS['surface'],
                'corner_radius': 12,
                'border_width': 0,
            },
            'section': {
                'fg_color': 'transparent',
                'corner_radius': 0,
                'border_width': 0,
            },
        }
        return styles.get(style_type, styles['default'])
    
    @classmethod
    def get_label_style(cls, style_type: str = 'body') -> Dict:
        """Get label style configuration"""
        styles = {
            'heading': {
                'font': cls.FONTS['heading'],
                'text_color': cls.COLORS['text_primary'],
            },
            'subheading': {
                'font': cls.FONTS['subheading'],
                'text_color': cls.COLORS['text_primary'],
            },
            'body': {
                'font': cls.FONTS['body'],
                'text_color': cls.COLORS['text_primary'],
            },
            'secondary': {
                'font': cls.FONTS['body'],
                'text_color': cls.COLORS['text_secondary'],
            },
            'success': {
                'font': cls.FONTS['body'],
                'text_color': cls.COLORS['success'],
            },
            'warning': {
                'font': cls.FONTS['body'],
                'text_color': cls.COLORS['warning'],
            },
            'error': {
                'font': cls.FONTS['body'],
                'text_color': cls.COLORS['error'],
            },
        }
        return styles.get(style_type, styles['body'])
    
    @classmethod
    def get_entry_style(cls) -> Dict:
        """Get entry field style configuration"""
        return {
            'font': cls.FONTS['body'],
            'corner_radius': 6,
            'border_width': 1,
            'border_color': cls.COLORS['border'],
        }
    
    @classmethod
    def get_textbox_style(cls) -> Dict:
        """Get textbox style configuration"""
        return {
            'font': cls.FONTS['monospace'],
            'corner_radius': 6,
            'border_width': 1,
            'border_color': cls.COLORS['border'],
        }