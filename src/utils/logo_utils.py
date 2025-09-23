import os
import tkinter as tk
from PIL import Image, ImageTk
from functools import lru_cache

class TournamentLogoManager:
    def __init__(self, logo_directory="data/logos"):
        self.logo_directory = logo_directory
        self.default_size = (24, 24)  # Standard size for tournament logos
        self._logo_cache = {}
        
    @lru_cache(maxsize=100)
    def get_tournament_logo(self, tournament_id, size=None):
        """
        Get tournament logo for given tournament ID
        Returns PhotoImage object or None if logo doesn't exist
        """
        if size is None:
            size = self.default_size
            
        cache_key = f"{tournament_id}_{size[0]}x{size[1]}"
        
        if cache_key in self._logo_cache:
            return self._logo_cache[cache_key]
            
        logo_path = os.path.join(self.logo_directory, f"{tournament_id}.png")
        
        if os.path.exists(logo_path):
            try:
                # Load and resize image
                img = Image.open(logo_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Cache the PhotoImage
                self._logo_cache[cache_key] = photo
                return photo
            except Exception as e:
                print(f"Error loading logo for tournament {tournament_id}: {e}")
                return None
        else:
            return None
    
    def has_logo(self, tournament_id):
        """Check if a tournament has a logo file"""
        logo_path = os.path.join(self.logo_directory, f"{tournament_id}.png")
        return os.path.exists(logo_path)
    
    def create_tournament_label_with_logo(self, parent, tournament, font=None, bg="white", fg="black", size=None):
        """
        Create a frame containing tournament logo and name
        Returns a Frame widget
        """
        frame = tk.Frame(parent, bg=bg)
        
        # Try to get logo
        logo = self.get_tournament_logo(tournament.get('id'), size)
        
        if logo:
            # Create label with logo
            logo_label = tk.Label(frame, image=logo, bg=bg)
            logo_label.pack(side="left", padx=(0, 5))
            
            # Keep a reference to prevent garbage collection
            logo_label.image = logo
        else:
            # Fallback to emoji/icon based on category
            category = tournament.get('category', '')
            if 'Grand Slam' in category:
                icon = "👑"
            elif 'Masters' in category:
                icon = "🏆"
            elif 'ATP 500' in category:
                icon = "🥇"
            elif 'ATP 250' in category:
                icon = "🎾"
            elif 'Challenger' in category:
                icon = "🏟️"
            elif 'ITF' in category:
                icon = "🌍"
            elif 'Special' in category:
                icon = "⭐"
            else:
                icon = "🎯"
            
            icon_label = tk.Label(frame, text=icon, font=font, bg=bg, fg=fg)
            icon_label.pack(side="left", padx=(0, 2))
        
        # Tournament name
        name_label = tk.Label(frame, text=tournament.get('name', 'Unknown Tournament'), 
                            font=font, bg=bg, fg=fg)
        name_label.pack(side="left")
        
        return frame
        
    def get_tournament_display_text(self, tournament):
        """
        Get display text for tournament (without logo)
        For use in buttons and other text-only contexts
        """
        return tournament.get('name', 'Unknown Tournament')

# Global instance
tournament_logo_manager = TournamentLogoManager()