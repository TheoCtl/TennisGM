# Tournament Logo System Documentation

## Overview
The TennisGM game now includes a comprehensive tournament logo system that enhances the visual experience by displaying custom logos for tournaments throughout the game interface.

## Features

### Tournament Logo Manager
- **File**: `src/utils/logo_utils.py`
- **Class**: `TournamentLogoManager`
- **Key Features**:
  - Automatic logo loading from PNG files
  - Image resizing to 32x32 pixels for consistency
  - LRU caching for performance optimization
  - Fallback emoji system when logos aren't available

### Logo File Structure
```
data/
  logos/
    1.png          # Tournament ID 1 logo
    2.png          # Tournament ID 2 logo
    32.png         # Tournament ID 32 logo
    ...
```

### Supported Formats
- **File Format**: PNG (recommended for transparency support)
- **Naming Convention**: `{tournament_id}.png`
- **Recommended Size**: 32x32 pixels (automatically resized if different)

## Integration Points

### 1. Tournament List Display (`show_tournaments`)
- **Location**: Main tournaments view
- **Behavior**: 
  - Shows tournament logo if available
  - Falls back to category-based emojis (👑 for Grand Slams, 🏆 for Masters, etc.)
  - Maintains color-coded backgrounds based on tournament prestige

### 2. Tournament Bracket Header (`show_tournament_bracket`)
- **Location**: Tournament bracket view header
- **Behavior**:
  - Displays logo next to tournament name in header
  - Maintains professional appearance with logo placement

### 3. Tournament History (`show_history`)
- **Location**: Tournament history cards
- **Behavior**:
  - Shows logos in tournament cards
  - Consistent with main tournament display

### 4. Tournament History Details (`show_tournament_history_details`)
- **Location**: Individual tournament history page
- **Behavior**:
  - Logo display in header for tournament-specific pages

### 5. Player Tournament Wins (`show_tournament_wins`)
- **Location**: Player profile tournament achievements
- **Behavior**:
  - Attempts to match tournament names to current tournaments
  - Shows logo if tournament is found and has logo
  - Falls back to trophy emoji for historical consistency

## Fallback System

### Category-Based Emoji Fallbacks
When no logo is available, the system uses tournament category-based emojis:

- **Grand Slam**: 👑 (Crown)
- **Masters 1000**: 🏆 (Trophy) 
- **ATP 500**: 🥇 (Gold Medal)
- **ATP 250**: 🎾 (Tennis Ball)
- **Other**: 🏟️ (Stadium)

### Special Cases
- **Favorite Tournaments**: ⭐ (Star) overrides category icons in some contexts
- **Recent Wins**: Tournament wins maintain logo display with special "RECENT" badges

## Performance Optimizations

### Caching Strategy
- **LRU Cache**: `@lru_cache(maxsize=128)` on logo loading
- **Image Reference Preservation**: Tkinter image references preserved to prevent garbage collection
- **Lazy Loading**: Logos only loaded when needed

### Error Handling
- **File Not Found**: Graceful fallback to emoji system
- **Invalid Images**: Exception handling with emoji fallback
- **Missing PIL**: System continues functioning with emoji-only display

## Usage for Developers

### Adding New Tournament Logos
1. Create a 32x32 PNG image for the tournament
2. Name it with the tournament ID: `{tournament_id}.png`
3. Place in `data/logos/` directory
4. Logo will automatically appear in all tournament displays

### Getting Tournament Logo in Code
```python
from utils.logo_utils import TournamentLogoManager

tournament_logo_manager = TournamentLogoManager()
logo = tournament_logo_manager.get_tournament_logo(tournament_id)

if logo:
    # Display logo
    logo_label = tk.Label(parent, image=logo)
    logo_label.image = logo  # Important: Keep reference
else:
    # Use fallback emoji
    icon_label = tk.Label(parent, text="🎾")
```

### Creating Tournament Labels with Logos
```python
# Use the utility method for consistent logo + text display
label_with_logo = tournament_logo_manager.create_tournament_label(
    parent_frame, 
    tournament_id, 
    tournament_name,
    bg_color="#3498db"
)
```

## Test Logo Creation

A utility script is provided to create test logos:
- **File**: `utils/create_test_logos.py`
- **Purpose**: Generate sample tournament logos for demonstration
- **Output**: Creates numbered logos with different colors and designs

## Future Enhancements

### Planned Features
- **Logo Editor**: In-game logo customization tool
- **Logo Import**: Import logos from web or file system
- **Logo Categories**: Different logo styles based on tournament prestige
- **Animated Logos**: Support for subtle animations in logos
- **High-DPI Support**: Multiple resolution logo variants

### Tournament Branding Extensions
- **Custom Colors**: Tournament-specific color schemes
- **Typography**: Tournament-specific fonts
- **Sponsors**: Sponsor logo integration
- **Seasonal Themes**: Special logos for different seasons

## Technical Implementation

### Core Components
1. **Logo Loading**: PIL-based image loading and processing
2. **Tkinter Integration**: PhotoImage conversion for Tkinter compatibility  
3. **Cache Management**: Memory-efficient logo storage
4. **Fallback Logic**: Robust error handling and emoji alternatives

### Dependencies
- **PIL (Pillow)**: Image processing and format support
- **Tkinter**: GUI integration and PhotoImage support
- **functools**: LRU cache implementation

## Installation and Setup

### Requirements
```bash
pip install Pillow  # For image processing
```

### Directory Structure Setup
```bash
mkdir -p data/logos  # Create logos directory
```

### Verification
The system is fully backward compatible - if no logos exist, the game continues to function with the emoji-based tournament icons as before.

## Troubleshooting

### Common Issues
1. **Logos Not Appearing**: Check file naming (must match tournament ID)
2. **Performance Issues**: Verify LRU cache is functioning
3. **Image Quality**: Ensure logos are 32x32 for best appearance
4. **File Format**: Use PNG for transparency support

### Debug Information
The logo manager includes error handling that logs issues while maintaining game functionality. Check console output for logo loading messages.

---

*This tournament logo system significantly enhances the visual appeal and professional appearance of TennisGM while maintaining full backward compatibility and robust fallback mechanisms.*