# World Crown Tournament System

## Overview
The World Crown is an international team tournament that runs throughout the tennis season. It features the top 5 players from each of the 8 fictional countries competing in a knockout format.

## Tournament Structure

### Countries
The tournament features 8 countries:
- Arcton
- Halcyon  
- Rin
- Hethrion
- Haran
- Loknig
- Jeonguk
- Bleak

### Team Selection
- At the start of each year (Week 1), the top 5 players from each country are automatically selected based on their ATP ranking
- Teams are locked for the entire year

### Tournament Format
- **Quarterfinals**: Best-of-5 individual matches between two countries
  - QF1: Arcton vs Halcyon (Week 11)
  - QF2: Rin vs Hethrion (Week 11) 
  - QF3: Haran vs Loknig (Week 13)
  - QF4: Jeonguk vs Bleak (Week 13)

- **Semifinals**: Winners advance to semifinals
  - SF1: QF1 winner vs QF2 winner (Week 18)
  - SF2: QF3 winner vs QF4 winner (Week 20)

- **Final**: Semifinal winners compete for the title (Week 47)

### Match Format
- Each tie consists of 5 individual matches
- Players are matched by ranking (best vs best, 2nd vs 2nd, etc.)
- First country to win 3 matches wins the tie
- All matches are simulated automatically when the week arrives

## Game Integration

### Menu Access
- Access via "World Crown" option in the main menu (located between Hall of Fame and History)

### Interface Tabs
1. **Current Bracket**: Shows the tournament structure and results
2. **Current Matches**: Shows matches available for the current week with team rosters
3. **Current Teams**: Displays all 8 national teams with their 5 selected players, rankings, and team statistics
4. **Winners History**: Historical list of World Crown champions

### Key Features
- **No ATP Points**: World Crown matches don't award ranking points
- **No Tournament History**: Results don't appear in player tournament records  
- **News Coverage**: 
  - World Crown weeks (11, 13, 18, 20, 47) announce current matches
  - Tournament winner announced in Week 48 news recap
- **Team Pride**: Represents pure national competition without ranking impact

## Technical Implementation

### Save File Integration
- World Crown data is stored in the main save file
- Use `utils/initialize_world_crown.py` to add World Crown support to existing saves
- Automatic backup creation during initialization

### Schedule Integration  
- World Crown matches are processed during the weekly advancement
- Automatic team selection occurs every January (Week 1)
- Results are stored for historical tracking

## Usage Tips

### For New Games
- World Crown system is automatically initialized
- First tournament begins in Week 11 of Year 1

### For Existing Saves
1. **Automatic Initialization**: If your save is before Week 11, World Crown will automatically initialize when you load the game
2. **Manual Initialization**: For saves that need the data structure, run: `python utils/initialize_world_crown.py`
3. **Mid-Season Support**: World Crown works even if you're past Week 1, as long as you haven't reached Week 11 yet
4. Check World Crown menu to see current status

### Viewing Results
- Use the "Current Matches" tab during tournament weeks to simulate ties
- Check "Current Bracket" for tournament progression
- Review "Winners History" for past champions

The World Crown adds a fun international dimension to the tennis simulation without interfering with the main ATP tour structure.
