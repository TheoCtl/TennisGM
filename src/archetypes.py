"""
Central archetype definitions and helper for determining archetype from a player's skills.

Provides get_archetype_for_player(player) -> (name, description, key_tuple)
"""
from typing import Tuple

# Mapping of archetype keys (sorted tuples of the top-3 skill names) to
# (archetype name, short multi-sentence description). Keys use lowercase skill names.
ARCTYPE_MAP = {
    ('backhand', 'forehand', 'serve'): (
        'Complete Server',
        "This player builds points off the serve and finishes them with reliable weapons on both wings. "
        "Their serve frequently gives them the initiative, but it’s their balanced ground game — a heavy, penetrating forehand paired with a compact, dependable backhand — that allows them to convert openings from any side of the court. "
        "They read opponent positioning well and vary depth and direction to keep pressure on, winning both with power and placement. "
        "Comfortable on all surfaces, they mix serve-powered winners and patient baseline construction to control matches."
    ),

    ('forehand', 'serve', 'speed'): (
        'Serve & Rush Specialist',
        "This player uses a potent serve to seize early control of points, then follows up with a forceful forehand and rapid court coverage to press the advantage. "
        "Their speed allows them to take the ball early, close angles, and rush the net or step into the court to finish points before opponents recover. "
        "Matches show them converting short points and punishing short replies, and their footwork makes their aggressive transitions consistently effective. "
        "They thrive when they can keep tempo high and use movement and timing to dominate rallies."
    ),

    ('forehand', 'serve', 'stamina'): (
        'Relentless Server-Attacker',
        "Combining a strong serve with a heavy forehand and outstanding endurance, this player relentlessly applies pressure across long matches and days. "
        "They can sustain a high-intensity game plan for prolonged periods, repeatedly serving well to free up short, decisive forehand opportunities while still outlasting opponents in extended baseline exchanges. "
        "Their physical resilience complements tactical patience: they’ll repeatedly go after openings while maintaining consistency when points get tight. "
        "This archetype is particularly dangerous late in long matches, where fitness and repeated aggression produce breaks of momentum."
    ),

    ('forehand', 'serve', 'straight'): (
        'Down-the-Line Server',
        "This player prioritizes linear aggression: a penetrating serve followed by a brutally effective down-the-line forehand. "
        "Their preferred tactic is to open the court with the serve and then attack the opponent’s sideline or run them off the court with a straight, finishing forehand. "
        "Precision and timing are central — they aim for narrow windows and use pace and depth rather than excessive angles to finish points. "
        "When their timing is right they produce sudden, match-clinching winners; when it’s not, they revert to disciplined baseline exchanges to rebuild the point."
    ),

    ('backhand', 'forehand', 'speed'): (
        'Swift Groundstroke Artist',
        "A balanced baseline player with exceptional movement, this player relies on quick positioning to strike clean shots off both wings. "
        "Their rapid footwork allows them to take the ball early and redirect pace effectively, while their sound technique on both sides gives them tactical flexibility. "
        "They excel at using their speed to turn defense into offense, often wrong-footing opponents with unexpected changes of direction. "
        "Most comfortable in dynamic baseline exchanges, they wear opponents down with their ability to extend points and create openings through movement."
    ),

    ('backhand', 'forehand', 'stamina'): (
        'Enduring Baseline Master',
        "This player combines solid groundstrokes on both wings with exceptional physical endurance to dominate long matches. "
        "Their balanced baseline game allows them to maintain consistent pressure, while their stamina lets them sustain high-quality shots even in extended rallies. "
        "They excel at wearing down opponents through steady, purposeful play from both sides, rarely giving away free points. "
        "Particularly effective in long matches, they maintain technical precision even as opponents begin to fatigue."
    ),

    ('backhand', 'forehand', 'straight'): (
        'Linear Striker',
        "A specialist in down-the-line shots from both wings, this player excels at creating acute angles and changing direction of play. "
        "Their ability to hit penetrating shots up both lines puts constant pressure on opponents' court positioning and movement. "
        "They're particularly effective at breaking up cross-court exchanges by suddenly redirecting pace down the line. "
        "Most dangerous when allowed to step into the court, they can quickly take control of points with precise linear hitting."
    ),

    ('backhand', 'forehand', 'cross'): (
        'Cross-Court Controller',
        "This player excels at controlling points through consistent cross-court exchanges from both wings. "
        "Their balanced ground game and strong cross-court shots allow them to pin opponents wide while maintaining court position. "
        "They're especially effective at using angles to open up the court and create opportunities for winners. "
        "Most comfortable in baseline rallies, they gradually work points to create openings through tactical cross-court play."
    ),

    ('forehand', 'speed', 'stamina'): (
        'Athletic Forehand Specialist',
        "Combining explosive movement with outstanding endurance and a powerful forehand, this player covers court exceptionally well. "
        "Their speed allows them to defend effectively while their stamina ensures they can maintain aggressive forehand patterns throughout long matches. "
        "They excel at turning defensive positions into attacking opportunities through their movement and forehand power. "
        "Particularly dangerous in long matches where their physicality allows them to maintain aggressive patterns longer than opponents."
    ),

    ('forehand', 'speed', 'straight'): (
        'Aggressive Line Runner',
        "This player uses their speed to enable aggressive down-the-line forehand patterns. "
        "Their quick movement allows them to take early positions for line drives while maintaining defensive coverage. "
        "They excel at surprising opponents with sudden line drives after establishing cross-court patterns. "
        "Most effective when able to use their speed to create angles for down-the-line winners."
    ),

    ('forehand', 'speed', 'cross'): (
        'Dynamic Cross-Court Specialist',
        "This player combines quick movement with effective cross-court forehand patterns. "
        "Their speed allows them to maintain aggressive court positioning while executing consistent cross-court patterns. "
        "They excel at using movement and angles to gradually work points towards forehand opportunities. "
        "Particularly effective at using their speed to enhance cross-court patterns and create openings."
    ),

    ('forehand', 'stamina', 'straight'): (
        'Enduring Line Driver',
        "This player combines physical endurance with powerful down-the-line forehand shots. "
        "Their stamina allows them to maintain aggressive line-drive patterns throughout long matches. "
        "They excel at wearing down opponents through consistent pressure up the line, particularly off the forehand wing. "
        "Most dangerous in long matches where their endurance allows them to maintain line-drive accuracy."
    ),

    ('cross', 'forehand', 'stamina'): (
        'Marathon Cross-Court Artist',
        "This player combines exceptional endurance with effective cross-court forehand patterns. "
        "Their stamina allows them to maintain consistent cross-court pressure throughout extended matches. "
        "They excel at using sustained cross-court exchanges to gradually wear down opponents. "
        "Particularly effective in long matches where their endurance enhances their cross-court consistency."
    ),
    
    ('cross', 'forehand', 'speed'): (
        'Angle-and-Sprint Master',
        "This player excels at creating and exploiting sharp angles with their forehand, using exceptional speed to dominate exchanges."
        "They thrive in dynamic rallies where they can alternate between defensive retrievals and sudden angular attacks."
        "Most dangerous when in a cross-court rally where they are able to pull opponents wide and capitalize on open court spaces."
    ),
    
    ('backhand', 'cross', 'forehand'): (
        'Angular Groundstroke Specialist',
        "This player excels in cross-court exchanges from both wings, constructing points through diagonal patterns and precise shot placement."
        "They excel at creating acute angles and using geometry to gradually open the court."
        "Most effective in baseline battles where their ability to switch directions and control cross-court patterns from either wing wears down opponents."
    ),
    
    ('backhand', 'cross', 'serve'): (
        'Diagonal Backhand Controller',
        "This player orchestrates points through a masterful combination of angled serves and cross-court backhand patterns."
        "They excel at disrupting opponents' rhythm by alternating between wide serves and acute backhand angles."
        "Most potent against players who prefer straight-line exchanges, as their ability to control diagonal spaces forces constant directional adjustments."
    ),
    
    ('cross', 'speed', 'straight'): (
        'Geometric Speed Tactician',
        "This player combines swift movement with a sophisticated understanding of court geometry."
        "They excel at wrong-footing opponents by suddenly transitioning from wide cross-court exchanges to sharp down-the-line winners."
        "Most dangerous when their speed allows them to take the ball early, using quick directional changes to keep opponents off-balance."
    ),

    ('cross', 'forehand', 'straight'): (
        'Directional Forehand Master',
        "This player excels at mixing line and cross-court patterns off their forehand wing. "
        "Their ability to change direction effectively makes their forehand particularly dangerous. "
        "They excel at using directional changes to create opportunities and wrong-foot opponents. "
        "Most effective when able to establish patterns before sudden directional changes."
    ),

    ('cross', 'forehand', 'serve'): (
        'Crosscourt Server-Attacker',
        "This player excels at creating wide angles: a well-placed serve followed by a crossing forehand that opens the court. "
        "They build points by stretching opponents wide, then penetrating the open court with pace and placement or by changing direction to catch defenders off-balance. "
        "They are comfortable constructing points that require both patience and sudden burst aggression. "
    ),

    ('backhand', 'serve', 'speed'): (
        'Serve-Backhand Sprinter',
        "Uses a strong serve to seize control, then uses a compact backhand and elite footspeed to finish points quickly. "
        "Combines aggressive serving with rapid court coverage to pressure opponents into short exchanges. "
        "Most dangerous when tempo is high and against opponents who struggle to recover to wide balls."
    ),

    ('backhand', 'serve', 'stamina'): (
        'Enduring Server-Backhand',
        "Relies on a reliable serve and a durable backhand to sustain long, grinding rallies while keeping opponents on the move. "
        "Maintains intensity through prolonged exchanges and repeatedly applies pressure with consistent depth. "
        "Excels against opponents who fade physically over long matches or in hot conditions."
    ),

    ('cross', 'backhand', 'serve'): (
        'Diagonal Server-Backhand',
        "Opens the court with a well-directed serve and uses a slicing or angled backhand to redirect play diagonally. "
        "Constructs points to create crosscourt openings that set up finishing opportunities. "
        "Most effective versus opponents who leave large diagonal gaps or who struggle with directional variety."
    ),

    ('backhand', 'serve', 'straight'): (
        'Straight-Serving Backhander',
        "Prioritizes straight-line aggression: a penetrating serve followed by a decisive backhand down the line. "
        "Uses pace and precision to attack the opponent’s sideline and shorten points. "
        "Dangerous when timing is sharp and against opponents who over-rotate or open their court too early."
    ),

    ('serve', 'speed', 'stamina'): (
        'Power-Endurance Server',
        "Pairs a strong serve with great movement and the fitness to sustain a high work rate. "
        "Can keep pressure on across multiple long sets while still producing quick, aggressive bursts. "
        "Thrives in physically demanding matches and late-in-match situations where opponents tire."
    ),

    ('cross', 'serve', 'speed'): (
        'Crosscourt Server-Sprinter',
        "Uses angled serving to open the court and then uses speed to exploit crosscourt openings. "
        "Favours diagonal geometry and quick transitions to convert openings into winners. "
        "Works well against static opponents or those who struggle to change direction rapidly."
    ),

    ('serve', 'speed', 'straight'): (
        'Serve & Straight Charger',
        "Drives the ball aggressively on a straight trajectory after the serve, cutting off the court with pace. "
        "Combines explosive movement with a preference for linear winners to force errors. "
        "Especially potent against opponents who give up the center or fail to cover the forehand down-the-line."
    ),

    ('cross', 'serve', 'stamina'): (
        'Durable Crosscourt Server',
        "Maintains a steady, angled serving pattern and relies on endurance to outlast opponents in long rallies. "
        "Methodically opens diagonal channels and patiently constructs points until an opening is created. "
        "Very strong in long matches and on slower surfaces where consistency and placement win out."
    ),

    ('serve', 'stamina', 'straight'): (
        'Endurance Straight Server',
        "Combines a persistent serving strategy with the stamina to sustain pressure through extended matches. "
        "Focuses on vertical court control and finishing with straight-line winners when opportunities arise. "
        "Performs well in long contests and against players who lose intensity over time."
    ),

    ('cross', 'serve', 'straight'): (
        'Versatile Line-and-Angle Server',
        "Mixes straight aggression and diagonal variety after the serve to keep opponents guessing. "
        "Combines directional control with measured aggression to create both immediate and constructed opportunities. "
        "Effective against players who are poor at anticipating varied trajectories and who lack lateral quickness."
    ),

    ('backhand', 'speed', 'stamina'): (
        'Enduring Backhand Sprinter',
        "This player combines a reliable backhand with exceptional speed and stamina, excelling in long, fast-paced rallies. "
        "Their movement allows them to cover the court and set up their backhand repeatedly, while their endurance keeps them effective deep into matches. "
        "They thrive in physically demanding exchanges, using their speed to recover and their stamina to maintain consistency. "
        "Most dangerous when matches become battles of attrition and movement."
    ),

    ('backhand', 'speed', 'straight'): (
        'Linear Backhand Runner',
        "This player uses their speed to set up aggressive down-the-line backhand shots. "
        "Quick movement allows them to take early positions for straight drives, keeping opponents off balance. "
        "They excel at surprising opponents with sudden line attacks after establishing cross-court patterns. "
        "Most effective when able to use their speed to create angles for backhand winners."
    ),

    ('backhand', 'cross', 'speed'): (
        'Diagonal Backhand Sprinter',
        "Combining a strong cross-court backhand with elite speed, this player excels at creating and exploiting wide angles. "
        "Their movement allows them to chase down balls and redirect play diagonally, opening up the court. "
        "They thrive in fast-paced rallies, using their speed to recover and their cross-court skills to pressure opponents. "
        "Most dangerous when able to turn defense into offense with quick directional changes."
    ),

    ('backhand', 'stamina', 'straight'): (
        'Enduring Line Backhander',
        "This player combines physical endurance with a powerful down-the-line backhand. "
        "Their stamina allows them to maintain aggressive line-drive patterns throughout long matches. "
        "They excel at wearing down opponents through consistent pressure up the line, particularly off the backhand wing. "
        "Most dangerous in long matches where their endurance allows them to maintain line-drive accuracy."
    ),

    ('backhand', 'cross', 'stamina'): (
        'Marathon Crosscourt Backhander',
        "This player combines exceptional endurance with effective cross-court backhand patterns. "
        "Their stamina allows them to maintain consistent cross-court pressure throughout extended matches. "
        "They excel at using sustained cross-court exchanges to gradually wear down opponents. "
        "Particularly effective in long matches where their endurance enhances their cross-court consistency."
    ),

    ('backhand', 'cross', 'straight'): (
        'Directional Backhand Master',
        "This player excels at mixing line and cross-court patterns off their backhand wing. "
        "Their ability to change direction effectively makes their backhand particularly dangerous. "
        "They excel at using directional changes to create opportunities and wrong-foot opponents. "
        "Most effective when able to establish patterns before sudden directional changes."
    ),

    ('speed', 'stamina', 'straight'): (
        'Relentless Line Runner',
        "This player combines top-tier speed and stamina with a preference for straight-line attacks. "
        "Their movement and endurance allow them to maintain aggressive patterns up the line throughout long matches. "
        "They excel at wearing down opponents with repeated straight drives and relentless court coverage. "
        "Most effective in physically demanding matches where their fitness and linear aggression shine."
    ),

    ('cross', 'speed', 'stamina'): (
        'Enduring Diagonal Sprinter',
        "This player blends speed and stamina with a focus on cross-court play, excelling in long, wide rallies. "
        "Their movement allows them to chase down balls and maintain pressure with cross-court patterns. "
        "They thrive in matches that require both quick recovery and sustained effort. "
        "Most dangerous when able to use their speed to extend points and their stamina to outlast opponents."
    ),

    ('cross', 'stamina', 'straight'): (
        'Versatile Endurance Hitter',
        "This player combines cross-court consistency, straight-line aggression, and high stamina. "
        "They can switch between angles and linear attacks while maintaining intensity throughout long matches. "
        "They excel at adapting their patterns to exploit opponent weaknesses, using endurance to sustain pressure. "
        "Most effective in matches where tactical variety and fitness are key."
    ),
    
    ('backhand', 'cross', 'dropshot'): (
        'Crafty Backhand Disruptor',
        "This player uses a reliable backhand to set up deceptive cross-court angles and sudden drop shots. "
        "They disrupt the opponent's rhythm by mixing depth with touch, pulling them out of position. "
        "Most effective on varied surfaces where changing pace is crucial."
    ),
    
    ('dropshot', 'forehand', 'serve'): (
        'Aggressive First-Strike Artist',
        "A powerful serve and dominant forehand create immediate pressure, finished with tactical drop shots. "
        "They look to end points quickly but possess the delicate touch to exploit any short reply. "
        "Most effective when their primary weapons are firing accurately."
    ),
    
    ('backhand', 'dropshot', 'serve'): (
        'Unpredictable Serve & Touch Player',
        "A solid serve and backhand provide a stable platform for surprising, well-disguised drop shots. "
        "They keep opponents guessing by blending power from the baseline with sudden changes of pace. "
        "Most effective against players who struggle with forward movement."
    ),
    
    ('dropshot', 'serve', 'speed'): (
        'Blitzing Touch Server',
        "Explosive speed and a strong serve allow this player to rush the net and finish points with drop shot volleys or angled winners. "
        "They use pace to create time for precise touch. "
        "Most effective in fast conditions where their athleticism dominates."
    ),
    
    ('dropshot', 'serve', 'stamina'): (
        'Enduring Drop Shot Specialist',
        "Combines a consistent serve with high stamina to patiently construct points, culminating in draining drop shots. "
        "They wear opponents down physically and mentally with relentless variety. "
        "Most effective in long, grueling matches on slow courts."
    ),
    
    ('dropshot', 'serve', 'straight'): (
        'Linear Serve & Drop Tactician',
        "Uses a penetrating, straight-line serve to pin opponents, following up with decisive drop shots down the line. "
        "Their game is built on precise, direct attacks and sharp changes of pace. "
        "Most effective when targeting an opponent's lateral movement."
    ),
    
    ('cross', 'dropshot', 'serve'): (
        'Wide-Serving Angle Creator',
        "A wide-serving arsenal and cross-court consistency open the court for lethal, angled drop shots. "
        "They use spin and placement to stretch opponents before delivering the finishing touch. "
        "Most effective on courts that reward serve and angle combinations."
    ),
    
    ('dropshot', 'serve', 'volley'): (
        'Classic Serve-Volley Trickster',
        "A pure serve-and-volley style enhanced with deft drop volleys and half-volley drop shots. "
        "They rush the net relentlessly, using touch as both a weapon and a surprise element. "
        "Most effective on fast surfaces where net pressure is paramount."
    ),
    
    ('backhand', 'dropshot', 'forehand'): (
        'Complete Baseline Illusionist',
        "Possesses balanced groundstrokes, using both the forehand and backhand to set up perfectly timed drop shots. "
        "They control baseline rallies with depth before introducing disruptive touch. "
        "Most effective against opponents who prefer a predictable rhythm."
    ),
    
    ('dropshot', 'forehand', 'speed'): (
        'Dynamic Forehand Threat',
        "Blistering speed and a powerful forehand are used to run opponents side-to-side, finished with sudden drop shots. "
        "Their athleticism allows them to create and convert offensive opportunities from anywhere. "
        "Most effective in open-court rallies."
    ),
    
    ('dropshot', 'forehand', 'stamina'): (
        'Iron-Willed Counter-Puncher',
        "Relies on incredible stamina and a rock-solid forehand to extend rallies, waiting for the perfect moment to inject a drop shot. "
        "They win through sheer durability and tactical patience. "
        "Most effective in physical battles and long points."
    ),
    
    ('dropshot', 'forehand', 'straight'): (
        'Direct Forehand Assassin',
        "Aims to hit through opponents with crushing straight-line forehands, using drop shots as a punishing variation down the same line. "
        "Their game is built on aggressive, linear precision. "
        "Most effective when attacking an opponent's weaker side."
    ),
    
    ('cross', 'dropshot', 'forehand'): (
        'Forehand Pattern Weaver',
        "Uses a heavy cross-court forehand to dictate rallies, seamlessly integrating drop shots to break the pattern. "
        "They expertly manipulate width and depth to expose court space. "
        "Most effective when establishing forehand dominance early."
    ),
    
    ('dropshot', 'forehand', 'volley'): (
        'All-Court Touch Master',
        "A potent forehand and confident volley are complemented by exceptional drop shots, both from the baseline and the net. "
        "They transition forward aggressively and finish points with finesse. "
        "Most effective on surfaces that reward all-court play."
    ),
    
    ('backhand', 'dropshot', 'speed'): (
        'Swift Backhand Defender-Slayer',
        "Uses exceptional speed to turn defense into offense, often with a sharp backhand followed by a surprise drop shot. "
        "They can retrieve seemingly lost points and instantly switch to attack. "
        "Most effective against aggressive baseliners."
    ),
    
    ('backhand', 'dropshot', 'stamina'): (
        'Grinding Backhand Technician',
        "A relentless, consistent backhand and high stamina form the foundation for opportunistic drop shots. "
        "They engage in protracted backhand exchanges before disrupting the rally with touch. "
        "Most effective in wearing down one-dimensional opponents."
    ),
    
    ('backhand', 'dropshot', 'straight'): (
        'Precise Backhand Sniper',
        "Prefers direct, straight-line backhand attacks, using the drop shot as a parallel, down-the-line variation. "
        "Their game is marked by clean, linear striking and well-disguised changes of pace. "
        "Most effective when targeting open lanes."
    ),
    
    ('backhand', 'dropshot', 'volley'): (
        'Backhand-Volley Virtuoso',
        "A strong backhand, both as a passing shot and approach, sets up frequent net forays finished with touch volleys and drop shots. "
        "They are comfortable ending points at the net, especially on the backhand side. "
        "Most effective against baseline-bound players."
    ),
    
    ('dropshot', 'speed', 'straight'): (
        'Speed Demon',
        "Relies on explosive speed to chase down balls and hit damaging straight-line winners or drop shots on the run. "
        "Their athleticism allows for aggressive, direct shot-making from defensive positions. "
        "Most effective in fast, chaotic rallies."
    ),
    
    ('dropshot', 'speed', 'stamina'): (
        'Relentless Retrieval Artist',
        "Combines elite speed and stamina to extend every point, using drop shots as a offensive tool from positions of defense. "
        "They simply refuse to lose a point, outlasting and out-thinking opponents. "
        "Most effective in marathon matches under hot conditions."
    ),
    
    ('cross', 'dropshot', 'speed'): (
        'Angelic Speedster',
        "Uses incredible speed to create extreme cross-court angles, finishing with drop shots when opponents are pulled wide. "
        "They cover the court effortlessly and exploit every inch of it. "
        "Most effective on courts with high bounce and wide angles."
    ),
    
    ('dropshot', 'speed', 'volley'): (
        'Acrobatic Net Rusher',
        "Exceptional speed allows them to cover the net with ease, finishing points with both punch volleys and delicate drop volleys. "
        "They are a constant, agile threat to transition forward. "
        "Most effective when following any short ball to the net."
    ),
    
    ('dropshot', 'stamina', 'straight'): (
        'Patient Line Painter',
        "Marries high stamina with straight-line precision, using drop shots to exploit the space created by their consistent depth. "
        "They win through attrition, waiting for the perfect moment to change pace down the line. "
        "Most effective in strategic, point-construction battles."
    ),
    
    ('cross', 'dropshot', 'stamina'): (
        'Cross-Court Marathoner',
        "Engages in lengthy cross-court exchanges thanks to great stamina, using drop shots as a tactical change-up to break the rhythm. "
        "They are the embodiment of consistent, intelligent, and draining tennis. "
        "Most effective in forcing errors through relentless pressure."
    ),
    
    ('dropshot', 'stamina', 'volley'): (
        'Enduring Net Presence',
        "Uses superior stamina to sustain net-rushing tactics over long matches, finishing points with volleys and drop shots. "
        "They maintain their aggressive positioning and touch even in late sets. "
        "Most effective in five-set matches where net pressure is constant."
    ),
    
    ('cross', 'dropshot', 'straight'): (
        'Geometric Disruptor',
        "Masters both cross-court and straight-line patterns, using the drop shot as the disruptive third option in their tactical geometry. "
        "They expertly move opponents around the court before delivering the final blow. "
        "Most effective against players with poor court coverage."
    ),
    
    ('dropshot', 'straight', 'volley'): (
        'Linear Volley Finisher',
        "Prefers direct, straight-line approaches to the net, where they finish points decisively with volleys or drop volleys. "
        "Their game is streamlined, aggressive, and designed to end points at the net. "
        "Most effective on fast, low-bouncing surfaces."
    ),
    
    ('cross', 'dropshot', 'volley'): (
        'Angle-Volley Maestro',
        "Creates sharp cross-court angles to open the court, then advances to finish with volleys or touch drop shots. "
        "They use spin and placement to set up their net game. "
        "Most effective when their first volley is a swing volley into open space."
    ),
    
    ('forehand', 'serve', 'volley'): (
        'Dominant Serve-Forehand Combo',
        "A powerful serve and crushing forehand create easy opportunities to attack the net and finish with volleys. "
        "This classic aggressive style builds points around their primary weapon. "
        "Most effective on fast surfaces where they can take time away."
    ),
    
    ('backhand', 'serve', 'volley'): (
        'Unorthodox Serve-Volleyer',
        "Uses a reliable serve and solid backhand—often as a slice approach—to consistently move forward and finish at net. "
        "They apply pressure by exploiting the backhand side for net approaches. "
        "Most effective against opponents who struggle with low, skidding returns."
    ),
    
    ('serve', 'speed', 'volley'): (
        'Blitzing Serve-Volleyer',
        "Explosive speed complements a big serve, allowing them to cover the net aggressively and put away any volley. "
        "They rush the net with authority, cutting off angles with their athleticism. "
        "Most effective in fast conditions where their first step is lethal."
    ),
    
    ('serve', 'stamina', 'volley'): (
        'Relentless Serve-Volley Machine',
        "Combines a durable serve with exceptional stamina to maintain net-rushing pressure for the entire match. "
        "They outlast opponents in physical, forward-oriented battles. "
        "Most effective in long matches where consistent net aggression pays off."
    ),
    
    ('serve', 'straight', 'volley'): (
        'Precision Serve-Volleyer',
        "Uses accurate, straight-line serves to jam opponents or open the court, following it in for a simple volley finish. "
        "Their game is built on direct, uncomplicated patterns. "
        "Most effective when their serve placement is pinpoint."
    ),

    ('cross', 'serve', 'volley'): (
        'Wide-Angle Serve-Volleyer',
        "Relies on wide serves to pull opponents off the court, creating huge openings for an easy first volley into the empty space. "
        "They master the geometry of the service box. "
        "Most effective on courts with a high-bouncing or slicing wide serve."
    ),
    
    ('backhand', 'forehand', 'volley'): (
        'All-Court Aggressor',
        "Possesses balanced, aggressive groundstrokes from both wings to set up forceful net approaches. "
        "They transition forward behind any short ball and finish confidently. "
        "Most effective against opponents who cannot match their all-court intensity."
    ),
    
    ('forehand', 'speed', 'volley'): (
        'Forehand-Charge Specialist',
        "Uses their forehand to dictate and their speed to close the net instantly, putting away high volleys. "
        "They are constantly looking to turn defense into offense with their forehand and legs. "
        "Most effective in open-court situations."
    ),
    
    ('forehand', 'stamina', 'volley'): (
        'Grinding Attacker',
        "Marries a heavy, consistent forehand with high stamina to gradually break down opponents, finishing points at net. "
        "They can sustain aggressive baseline play before moving forward. "
        "Most effective in physical matches that require persistent pressure."
    ),
    
    ('forehand', 'straight', 'volley'): (
        'Linear Forehand Pressurer',
        "Aims to hit through opponents with direct, straight-line forehands, following the ball to net for a volley put-away. "
        "Their aggression is channeled down precise, predictable, and powerful lines. "
        "Most effective when attacking an opponent's weakness directly."
    ),
    
    ('cross', 'forehand', 'volley'): (
        'Forehand Pattern Volleyer',
        "Uses heavy cross-court forehands to create extreme angles, drawing the opponent wide before approaching to net. "
        "They use spin and width to set up their transition game. "
        "Most effective on clay or high-bouncing hard courts."
    ),
    
    ('backhand', 'speed', 'volley'): (
        'Counter-Punching Volleyer',
        "Uses speed and a reliable backhand to turn defense into instant offense, often approaching the net behind a backhand slice or pass. "
        "They thrive on robbing opponents of time. "
        "Most effective against big hitters by using their pace against them."
    ),
    
    ('backhand', 'stamina', 'volley'): (
        'Dogged Backhand Net Rusher',
        "Relies on a tireless backhand and great stamina to engage in long exchanges before finding the right moment to approach the net. "
        "They wear down opponents with consistency before striking. "
        "Most effective in wars of attrition."
    ),
    
    ('backhand', 'straight', 'volley'): (
        'Backhand-Line Sniper',
        "Prefers to attack with direct, down-the-line backhands, using that shot as their primary approach to net. "
        "Their game is clean, linear, and efficient, especially on the backhand side. "
        "Most effective when exploiting an opponent's forehand corner."
    ),
    
    ('backhand', 'cross', 'volley'): (
        'Slice-and-Dice Specialist',
        "Uses a deep, cross-court backhand slice (especially on approach shots) to skid the ball low, setting up easy volleys. "
        "They disrupt rhythm with spin before closing in. "
        "Most effective on low-bouncing surfaces like grass."
    ),
    
    ('speed', 'stamina', 'volley'): (
        'Perpetual Motion Machine',
        "Combines elite speed and stamina to chase down every ball and consistently end points at the net. "
        "They are an indefatigable, aggressive presence, covering the court like no other. "
        "Most effective in long matches where athleticism is the difference."
    ),
    
    ('speed', 'straight', 'volley'): (
        'Direct Transition Athlete',
        "Uses blistering speed to hit aggressive, straight-line shots and immediately close the net to volley. "
        "Their game is built on directness and explosive forward movement. "
        "Most effective when they can take the ball early and on the rise."
    ),
    
    ('cross', 'speed', 'volley'): (
        'Angle-Generating Speedster',
        "Uses incredible speed to create and recover from extreme cross-court angles, finishing points with volleys at net. "
        "They turn defense into offense by opening the court with width. "
        "Most effective in fast, dynamic rallies."
    ),
    
    ('stamina', 'straight', 'volley'): (
        'Patient Line Attacker',
        "Uses high stamina to construct points with straight-line accuracy, patiently waiting for the right ball to approach and volley. "
        "They win through disciplined, direct shot-making over the long haul. "
        "Most effective in strategic baseline-to-net battles."
    ),
    
    ('cross', 'stamina', 'volley'): (
        'Cross-Court Grinder Volleyer',
        "Engages in lengthy cross-court exchanges thanks to great stamina, using consistency to draw a weak reply before attacking the net. "
        "They blend baseline endurance with opportunistic net play. "
        "Most effective on slow surfaces where they can outlast opponents."
    ),
    
    ('cross', 'straight', 'volley'): (
        'Complete Pattern Volleyer',
        "Masters both cross-court rallies and straight-line attacks to keep opponents guessing, always looking to finish at net. "
        "They have the tactical variety to approach from any angle. "
        "Most effective against players who cannot read their intent."
    ),

    # --- Mental archetypes ---

    ('backhand', 'forehand', 'mental'): (
        'Clutch Baseline General',
        "This player combines reliable groundstrokes from both wings with exceptional composure under pressure. "
        "They elevate their game in critical moments — set points, tiebreaks, and deciding games — where their mental edge allows them to hit cleaner, bolder shots. "
        "Their balanced ground game means they rarely gift free points, and when the stakes rise they become even more dangerous. "
        "Most effective in tight matches where nerve and shot-making quality decide the outcome."
    ),

    ('forehand', 'mental', 'serve'): (
        'Big-Game Server',
        "A powerful serve and heavy forehand are amplified by outstanding mental fortitude in crucial moments. "
        "When the pressure mounts — on set or match points — their serve becomes more precise and their forehand more devastating. "
        "They thrive in the spotlight, frequently producing their best tennis when it matters most. "
        "Most effective in high-stakes encounters where big points demand big shots."
    ),

    ('backhand', 'mental', 'serve'): (
        'Pressure-Proof Serve Machine',
        "Combines a reliable serve and solid backhand with nerves of steel in critical moments. "
        "When opponents expect them to tighten up, they instead raise their level, serving aces and punishing with backhand precision. "
        "Their mental resilience makes them extremely difficult to break in tight sets. "
        "Most effective in tense, close matches where holding serve is paramount."
    ),

    ('mental', 'serve', 'speed'): (
        'Composed Athletic Server',
        "This player's explosive speed and strong serve are paired with outstanding mental composure. "
        "They maintain aggressive court coverage and precise serving even when the match is on the line. "
        "Their ability to stay calm under pressure means their physical gifts remain fully available in clutch moments. "
        "Most effective in fast-paced, high-pressure matches where panic would undo lesser athletes."
    ),

    ('mental', 'serve', 'stamina'): (
        'Enduring Pressure Server',
        "Combines a durable serve with exceptional stamina and mental resilience to dominate in long, tense matches. "
        "When other players fatigue and their nerves fray in the deciding set, this player maintains both physical energy and mental sharpness. "
        "Their ability to sustain high-level serving late in matches makes them a formidable closer. "
        "Most effective in marathon encounters where mental and physical endurance intersect."
    ),

    ('mental', 'serve', 'straight'): (
        'Cool-Headed Line Server',
        "Uses a penetrating serve and down-the-line precision, elevated by exceptional composure on big points. "
        "When the pressure builds, their straight serves and linear attacks become sharper, not shakier. "
        "They thrive on making bold, aggressive choices in critical moments. "
        "Most effective against opponents who expect them to play safe when it counts."
    ),

    ('cross', 'mental', 'serve'): (
        'Angle-Serving Clutch Player',
        "Masters wide-angle serving and cross-court patterns, with the mental strength to execute them flawlessly under pressure. "
        "In tiebreaks and on set points, their geometric precision and nerve combine to produce aces and acute angles. "
        "They are extremely dangerous when the match is tight. "
        "Most effective against opponents who struggle with wide positioning in high-pressure games."
    ),

    ('mental', 'serve', 'volley'): (
        'Ice-Cold Serve-Volleyer',
        "A classic serve-and-volley approach fortified by unshakeable mental composure. "
        "They rush the net with confidence on the biggest points, trusting their touch and reading the game coolly under duress. "
        "Their willingness to attack the net in pressure moments separates them from cautious peers. "
        "Most effective on fast surfaces where their nerve and net skills combine to dominate."
    ),

    ('dropshot', 'mental', 'serve'): (
        'Tactical Pressure Artist',
        "Blends a strong serve and delicate drop shots with the composure to deploy them on the biggest points. "
        "While others play safe under pressure, this player has the nerve to produce unexpected tactical variety. "
        "Their drop shots in clutch moments disrupt opponents who prepare for power. "
        "Most effective against baseline-bound opponents in high-stakes rallies."
    ),

    ('forehand', 'mental', 'speed'): (
        'Clutch Forehand Athlete',
        "Combines a powerful forehand and explosive speed with the mental composure to maintain both under pressure. "
        "In tight situations, their footwork remains sharp and their forehand remains aggressive rather than tentative. "
        "They produce their best attacking tennis when the stakes are highest. "
        "Most effective in fast-paced, decisive moments where physical and mental quality intersect."
    ),

    ('forehand', 'mental', 'stamina'): (
        'Relentless Clutch Forehand',
        "Pairs a heavy forehand and outstanding endurance with the mental strength to sustain aggressive patterns in pressure situations. "
        "Late in long matches, when others tighten up, they maintain their forehand intensity and composure. "
        "Their combination of physical and mental resilience makes them devastating closers. "
        "Most effective in long, tense matches where the final set requires both stamina and nerve."
    ),

    ('forehand', 'mental', 'straight'): (
        'Composed Line Driver',
        "This player hits bold, down-the-line forehands with the mental strength to execute them on the biggest points. "
        "While others default to safer cross-court patterns under pressure, they trust their line-drive accuracy. "
        "Their composure allows them to take calculated risks when it matters most. "
        "Most effective against opponents who expect conservative play in tight moments."
    ),

    ('cross', 'forehand', 'mental'): (
        'Pressure Cross-Court Artist',
        "Combines heavy cross-court forehand patterns with exceptional mental resilience under pressure. "
        "In critical moments, their cross-court consistency becomes even more reliable, suffocating opponents with relentless angles. "
        "They never panic, using their favorite patterns to grind out the toughest points. "
        "Most effective in extended baseline battles where mental and tactical quality decide."
    ),

    ('forehand', 'mental', 'volley'): (
        'Bold Forehand-Volley Closer',
        "This player uses a dominant forehand and confident net play, enhanced by the composure to attack in clutch moments. "
        "On break points and set points, they push forward aggressively rather than retreating to the baseline. "
        "Their mental strength means they take the initiative when others play cautiously. "
        "Most effective on courts that reward attacking, high-pressure tennis."
    ),

    ('dropshot', 'forehand', 'mental'): (
        'Nerve-Holding Touch Attacker',
        "Combines a powerful forehand with delicate drop shots and the nerve to use both at the most critical moments. "
        "Their willingness to vary pace under pressure keeps opponents permanently uncertain. "
        "They are particularly dangerous when producing unexpected drop shots on big points. "
        "Most effective against opponents who tighten up tactically in tense situations."
    ),

    ('backhand', 'mental', 'speed'): (
        'Steel-Nerved Backhand Runner',
        "Elite speed and a reliable backhand are reinforced by exceptional mental composure. "
        "In pressure points, they maintain their court coverage and backhand precision while opponents rush and misfire. "
        "Their ability to stay calm and mobile under duress makes them very difficult to put away. "
        "Most effective in tight rallies where defensive quality and nerve are determinant."
    ),

    ('backhand', 'mental', 'stamina'): (
        'Grinding Mental Fortress',
        "Pairs a consistent backhand and high stamina with outstanding mental resolve. "
        "They wear opponents down physically and then win the big points through superior composure and patience. "
        "In deciding sets of long matches, they are at their most dangerous. "
        "Most effective against opponents who wilt mentally before they do physically."
    ),

    ('backhand', 'mental', 'straight'): (
        'Composed Backhand Sniper',
        "Combines down-the-line backhand precision with the mental fortitude to execute bold shots under pressure. "
        "They hit through the line with confidence when others default to safer cross-court patterns. "
        "Their composure in tight moments makes their straight backhand a decisive weapon. "
        "Most effective when opponents anticipate cautious play on big points."
    ),

    ('backhand', 'cross', 'mental'): (
        'Pressure Cross-Court Defender',
        "Masters cross-court backhand exchanges with the mental strength to sustain them under intense pressure. "
        "In critical games, their cross-court backhand becomes a wall, refusing to yield cheap errors. "
        "They outlast opponents in diagonal exchanges, especially in tense, high-stakes rallies. "
        "Most effective against players who crumble in extended cross-court battles."
    ),

    ('backhand', 'mental', 'volley'): (
        'Composed Backhand Volleyer',
        "Uses a reliable backhand and confident net play, enhanced by exceptional poise under pressure. "
        "They approach the net on big points with conviction, trusting their backhand slice and volley touch. "
        "Their composure at the net in clutch moments is their defining trait. "
        "Most effective against opponents who expect baseline play in tight situations."
    ),

    ('backhand', 'dropshot', 'mental'): (
        'Cool-Headed Backhand Tactician',
        "Combines a solid backhand with clever drop shots and the nerve to deploy them on pressure points. "
        "They add tactical variety when it matters most, keeping opponents guessing in tense rallies. "
        "Their willingness to use touch under pressure reveals supreme confidence in their game. "
        "Most effective against one-dimensional baseliners."
    ),

    ('mental', 'speed', 'stamina'): (
        'Unbreakable Athlete',
        "Combines elite speed, outstanding stamina, and mental fortitude to be the last player standing in every battle. "
        "They simply refuse to lose big points — their fitness means they can chase everything, and their nerve means they stay sharp. "
        "In deciding sets and tiebreaks, they are at their most dominant. "
        "Most effective in marathon matches on slow surfaces where attrition meets pressure."
    ),

    ('mental', 'speed', 'straight'): (
        'Composed Line Sprinter',
        "Uses explosive speed to set up straight-line attacks, with the mental composure to execute under pressure. "
        "On big points, their movement remains sharp and their line drives remain bold. "
        "They take risks with conviction when the match is on the line. "
        "Most effective in fast-paced situations where reactive speed and nerve intersect."
    ),

    ('cross', 'mental', 'speed'): (
        'Calm Angle Sprinter',
        "Combines quick movement with cross-court mastery and exceptional poise in tight moments. "
        "They use their speed to create extreme angles even under pressure, maintaining aggressive positioning. "
        "Their composure means their movement-based game doesn't falter in clutch situations. "
        "Most effective in wide, dynamic rallies on big points."
    ),

    ('mental', 'speed', 'volley'): (
        'Fearless Net Charger',
        "Uses explosive speed and confident net play, backed by the mental strength to rush forward on big points. "
        "While others hesitate to leave the baseline under pressure, they charge the net with conviction. "
        "Their speed and composure at the net make them extremely dangerous closers. "
        "Most effective on fast surfaces in high-pressure moments."
    ),

    ('dropshot', 'mental', 'speed'): (
        'Nerveless Speed Trickster',
        "Combines elite speed with deceiving drop shots and the composure to deploy both on the biggest points. "
        "In pressure situations, they maintain their artistic, varied game rather than defaulting to power. "
        "Their ability to mix pace and position under duress makes them uniquely hard to read. "
        "Most effective against opponents who narrow their tactical range under pressure."
    ),

    ('mental', 'stamina', 'straight'): (
        'Enduring Composed Liner',
        "Pairs physical endurance with down-the-line precision and the mental resolve to sustain both in the biggest moments. "
        "They maintain their aggressive line-drive game deep into deciding sets and tiebreaks. "
        "Their combination of stamina and nerve means they grow stronger as matches become more tense. "
        "Most effective in extended, grinding contests decided in the final stages."
    ),

    ('cross', 'mental', 'stamina'): (
        'Marathon Mental Giant',
        "Combines cross-court consistency with exceptional stamina and unshakeable mental resolve. "
        "They construct points patiently, and when the match enters its decisive phase, their composure remains rock-solid. "
        "Opponents know that winning a tight set against this player requires outlasting both their body and their mind. "
        "Most effective in long matches on slow surfaces where pressure builds gradually."
    ),

    ('mental', 'stamina', 'volley'): (
        'Tireless Pressure Volleyer',
        "Uses high stamina and confident net play, reinforced by mental resilience on the biggest points. "
        "They can sustain net-rushing tactics deep into long matches while maintaining their composure. "
        "In deciding sets, they still have the energy and nerve to attack the net. "
        "Most effective in physically and mentally demanding five-set encounters."
    ),

    ('dropshot', 'mental', 'stamina'): (
        'Patient Mental Craftsman',
        "Combines endurance with tactical drop shots and the composure to use them under maximum pressure. "
        "They extend rallies with stamina, then produce nerve-holding drop shots at the critical moment. "
        "Their patience and mental strength combination makes them maddening opponents in tight situations. "
        "Most effective in long, grinding matches where touch and temperament decide."
    ),

    ('cross', 'mental', 'straight'): (
        'Composed Directional Master',
        "Masters both cross-court and down-the-line patterns with the mental strength to switch direction confidently under pressure. "
        "In clutch moments, they make bold directional choices rather than defaulting to repetitive patterns. "
        "Their tactical variety under pressure keeps opponents permanently uncertain. "
        "Most effective against players who narrow their game in tense situations."
    ),

    ('mental', 'straight', 'volley'): (
        'Pressure Line-and-Volley',
        "Uses direct, straight-line approaches to the net with the mental composure to execute them on big points. "
        "When others retreat to safe baseline positions under pressure, they push forward decisively. "
        "Their combination of directness and nerve produces clean, efficient point-ending on clutch points. "
        "Most effective against baseline-bound opponents in pressure games."
    ),

    ('cross', 'mental', 'volley'): (
        'Clutch Angle Volleyer',
        "Creates cross-court angles to set up net approaches, with the poise to execute in the highest-pressure moments. "
        "Their mental strength means they maintain attacking instincts in tiebreaks and deciding games. "
        "Opponents face a dilemma: this player is most dangerous when the stakes are highest. "
        "Most effective on surfaces that reward aggressive, composed net play."
    ),

    ('dropshot', 'mental', 'straight'): (
        'Clutch Drop-and-Drive',
        "Combines down-the-line precision with tactical drop shots and the nerve to use both on match point. "
        "Their willingness to vary pace and direction under pressure makes them uniquely unpredictable in clutch moments. "
        "They trust their touch and their accuracy equally when the match is on the line. "
        "Most effective against opponents who can only handle one dimension of attack."
    ),

    ('dropshot', 'mental', 'volley'): (
        'Nerveless Touch Artist',
        "Pairs delicate drop shots and confident volleys with the mental resilience to deploy them under maximum pressure. "
        "On set and match points, they produce audacious touch shots that leave opponents flatfooted. "
        "Their composure at the net and around the service line in big moments is extraordinary. "
        "Most effective against power players who expect force, not finesse, on big points."
    ),

    ('cross', 'dropshot', 'mental'): (
        'Calm Pattern Disruptor',
        "Mixes cross-court consistency with well-timed drop shots, maintaining composure to deploy both under pressure. "
        "In tight moments, they are willing to break the rhythm with unexpected touches rather than grinding. "
        "Their mental strength ensures their variety remains a weapon, not a liability, in clutch situations. "
        "Most effective against rhythm-dependent baseliners."
    ),


    # ============================================================
    # New archetypes: IQ, Lift, Slice combinations (166 entries)
    # ============================================================

    # --- IQ combinations ---

    ('backhand', 'cross', 'iq'): (
        'Analytical Cross-Court Defender',
        "Combines a reliable and penetrating backhand with sharp cross-court placement and exceptional tactical "
        "intelligence. Tactical awareness turns raw power and placement into a surgical attack, consistently finding the "
        "right shot at the right moment. Most effective against one-dimensional players who are vulnerable to tactical "
        "adjustments mid-match."
    ),

    ('backhand', 'dropshot', 'iq'): (
        'Cerebral Touch Player',
        "Combines a reliable and penetrating backhand with delicate drop shot touch and exceptional tactical "
        "intelligence. Their tactical mind chooses optimally between raw power plays and specialty shots, keeping "
        "opponents off-balance with unpredictable but intelligent shot selection. Especially dangerous against "
        "deep-positioned baseliners who are vulnerable to intelligent use of short balls."
    ),

    ('backhand', 'forehand', 'iq'): (
        'Intelligent Baseliner',
        "Combines a reliable and penetrating backhand with a heavy and dominant forehand and exceptional tactical "
        "intelligence. The combination of mental resilience and tactical intelligence means they play their best tennis "
        "under pressure, making few unforced errors when it counts. Most effective against one-dimensional players who "
        "are vulnerable to tactical adjustments mid-match."
    ),

    ('backhand', 'iq', 'mental'): (
        'Composed Tactician',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and outstanding mental "
        "composure. The combination of mental resilience and tactical intelligence means they play their best tennis "
        "under pressure, making few unforced errors when it counts. Most effective against one-dimensional players who "
        "are vulnerable to tactical adjustments mid-match."
    ),

    ('backhand', 'iq', 'serve'): (
        'Calculated Server',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and a potent and varied "
        "serve. The combination of mental resilience and tactical intelligence means they play their best tennis under "
        "pressure, making few unforced errors when it counts. Dominant in service games where tactical serving "
        "consistently creates first-strike opportunities."
    ),

    ('backhand', 'iq', 'speed'): (
        'Smart Counter-Puncher',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and elite court coverage. "
        "Their intelligence maximizes natural athleticism and power, ensuring they always channel physical tools toward "
        "the highest-value play. Most effective in long matches where intelligent physical management outlasts opponents "
        "who burn energy chasing the wrong patterns."
    ),

    ('backhand', 'iq', 'stamina'): (
        'Strategic Grinder',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and remarkable physical "
        "endurance. Their intelligence maximizes natural athleticism and power, ensuring they always channel physical "
        "tools toward the highest-value play. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('backhand', 'iq', 'straight'): (
        'Precise Strategist',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and pinpoint down-the-line "
        "accuracy. Tactical awareness turns raw power and placement into a surgical attack, consistently finding the "
        "right shot at the right moment. Most effective against one-dimensional players who are vulnerable to tactical "
        "adjustments mid-match."
    ),

    ('backhand', 'iq', 'volley'): (
        'Net-Savvy Defender',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and polished net skills. "
        "Their tactical mind chooses optimally between raw power plays and specialty shots, keeping opponents "
        "off-balance with unpredictable but intelligent shot selection. Thrives by constructing points that end at the "
        "net, using intelligence to find the right approach moment."
    ),

    ('cross', 'dropshot', 'iq'): (
        'Pattern-Breaking Analyst',
        "Combines sharp cross-court placement with delicate drop shot touch and exceptional tactical intelligence. Court "
        "IQ guides the choice between precise placement and specialty shots, creating layered patterns that steadily "
        "dismantle opponent defenses. Especially dangerous against deep-positioned baseliners who are vulnerable to "
        "intelligent use of short balls."
    ),

    ('cross', 'forehand', 'iq'): (
        'Tactical Aggressor',
        "Combines sharp cross-court placement with a heavy and dominant forehand and exceptional tactical intelligence. "
        "Tactical awareness turns raw power and placement into a surgical attack, consistently finding the right shot at "
        "the right moment. Most effective against one-dimensional players who are vulnerable to tactical adjustments "
        "mid-match."
    ),

    ('cross', 'iq', 'mental'): (
        'Calm Court General',
        "Combines sharp cross-court placement with exceptional tactical intelligence and outstanding mental composure. "
        "Mental strength and precision combine with tactical intelligence to produce an opponent who never beats "
        "themselves and consistently finds narrow windows. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('cross', 'iq', 'serve'): (
        'Serve-Placing Strategist',
        "Combines sharp cross-court placement with exceptional tactical intelligence and a potent and varied serve. "
        "Tactical awareness turns raw power and placement into a surgical attack, consistently finding the right shot at "
        "the right moment. Dominant in service games where tactical serving consistently creates first-strike "
        "opportunities."
    ),

    ('cross', 'iq', 'speed'): (
        'Quick-Thinking Runner',
        "Combines sharp cross-court placement with exceptional tactical intelligence and elite court coverage. "
        "Intelligence transforms court speed and precision into a relentless machine that wears opponents down by always "
        "placing the ball to maximum effect. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('cross', 'iq', 'stamina'): (
        'Reading Grinder',
        "Combines sharp cross-court placement with exceptional tactical intelligence and remarkable physical endurance. "
        "Intelligence transforms court speed and precision into a relentless machine that wears opponents down by always "
        "placing the ball to maximum effect. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('cross', 'iq', 'straight'): (
        'Calculated Shot Placer',
        "Combines sharp cross-court placement with exceptional tactical intelligence and pinpoint down-the-line "
        "accuracy. Mental strength and precision combine with tactical intelligence to produce an opponent who never "
        "beats themselves and consistently finds narrow windows. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('cross', 'iq', 'volley'): (
        'Smart Net Approach Player',
        "Combines sharp cross-court placement with exceptional tactical intelligence and polished net skills. Court IQ "
        "guides the choice between precise placement and specialty shots, creating layered patterns that steadily "
        "dismantle opponent defenses. Thrives by constructing points that end at the net, using intelligence to find the "
        "right approach moment."
    ),

    ('dropshot', 'forehand', 'iq'): (
        'Cunning Forehand Striker',
        "Combines delicate drop shot touch with a heavy and dominant forehand and exceptional tactical intelligence. "
        "Their tactical mind chooses optimally between raw power plays and specialty shots, keeping opponents "
        "off-balance with unpredictable but intelligent shot selection. Especially dangerous against deep-positioned "
        "baseliners who are vulnerable to intelligent use of short balls."
    ),

    ('dropshot', 'iq', 'mental'): (
        'Composed Touch Tactician',
        "Combines delicate drop shot touch with exceptional tactical intelligence and outstanding mental composure. "
        "Tactical awareness maximizes the effectiveness of specialty shots, choosing the right moment for each variation "
        "with surgical precision. Especially dangerous against deep-positioned baseliners who are vulnerable to "
        "intelligent use of short balls."
    ),

    ('dropshot', 'iq', 'serve'): (
        'Tactical Serve & Touch',
        "Combines delicate drop shot touch with exceptional tactical intelligence and a potent and varied serve. Their "
        "tactical mind chooses optimally between raw power plays and specialty shots, keeping opponents off-balance with "
        "unpredictable but intelligent shot selection. Dominant in service games where tactical serving consistently "
        "creates first-strike opportunities."
    ),

    ('dropshot', 'iq', 'speed'): (
        'Anticipating Touch Player',
        "Combines delicate drop shot touch with exceptional tactical intelligence and elite court coverage. Quick "
        "thinking combines with athletic ability and specialty shots to create an opponent who always seems to find "
        "extra time on the ball. Most effective in long matches where intelligent physical management outlasts opponents "
        "who burn energy chasing the wrong patterns."
    ),

    ('dropshot', 'iq', 'stamina'): (
        'Patient Dropshot Schemer',
        "Combines delicate drop shot touch with exceptional tactical intelligence and remarkable physical endurance. "
        "Quick thinking combines with athletic ability and specialty shots to create an opponent who always seems to "
        "find extra time on the ball. Most effective in long matches where intelligent physical management outlasts "
        "opponents who burn energy chasing the wrong patterns."
    ),

    ('dropshot', 'iq', 'straight'): (
        'Linear Touch Analyst',
        "Combines delicate drop shot touch with exceptional tactical intelligence and pinpoint down-the-line accuracy. "
        "Court IQ guides the choice between precise placement and specialty shots, creating layered patterns that "
        "steadily dismantle opponent defenses. Especially dangerous against deep-positioned baseliners who are "
        "vulnerable to intelligent use of short balls."
    ),

    ('dropshot', 'iq', 'volley'): (
        'Cerebral Net Craftsman',
        "Combines delicate drop shot touch with exceptional tactical intelligence and polished net skills. Tactical "
        "awareness maximizes the effectiveness of specialty shots, choosing the right moment for each variation with "
        "surgical precision. Thrives by constructing points that end at the net, using intelligence to find the right "
        "approach moment."
    ),

    ('forehand', 'iq', 'mental'): (
        'Steel-Willed Tactician',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and outstanding mental composure. "
        "The combination of mental resilience and tactical intelligence means they play their best tennis under "
        "pressure, making few unforced errors when it counts. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('forehand', 'iq', 'serve'): (
        'The Thinking Bomber',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and a potent and varied serve. "
        "The combination of mental resilience and tactical intelligence means they play their best tennis under "
        "pressure, making few unforced errors when it counts. Dominant in service games where tactical serving "
        "consistently creates first-strike opportunities."
    ),

    ('forehand', 'iq', 'speed'): (
        'Rapid-Fire Tactician',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and elite court coverage. Their "
        "intelligence maximizes natural athleticism and power, ensuring they always channel physical tools toward the "
        "highest-value play. Most effective in long matches where intelligent physical management outlasts opponents who "
        "burn energy chasing the wrong patterns."
    ),

    ('forehand', 'iq', 'stamina'): (
        'Enduring Strategist',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and remarkable physical "
        "endurance. Their intelligence maximizes natural athleticism and power, ensuring they always channel physical "
        "tools toward the highest-value play. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('forehand', 'iq', 'straight'): (
        'Down-the-Line Genius',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and pinpoint down-the-line "
        "accuracy. Tactical awareness turns raw power and placement into a surgical attack, consistently finding the "
        "right shot at the right moment. Most effective against one-dimensional players who are vulnerable to tactical "
        "adjustments mid-match."
    ),

    ('forehand', 'iq', 'volley'): (
        'Attack-Planning Volleyer',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and polished net skills. Their "
        "tactical mind chooses optimally between raw power plays and specialty shots, keeping opponents off-balance with "
        "unpredictable but intelligent shot selection. Thrives by constructing points that end at the net, using "
        "intelligence to find the right approach moment."
    ),

    ('iq', 'mental', 'serve'): (
        'Mental Giant of Serve',
        "Combines exceptional tactical intelligence with outstanding mental composure and a potent and varied serve. The "
        "combination of mental resilience and tactical intelligence means they play their best tennis under pressure, "
        "making few unforced errors when it counts. Dominant in service games where tactical serving consistently "
        "creates first-strike opportunities."
    ),

    ('iq', 'mental', 'speed'): (
        'Cool & Quick Analyst',
        "Combines exceptional tactical intelligence with outstanding mental composure and elite court coverage. Tactical "
        "intelligence amplifies both physical tools and composure, producing a player who stays calm, moves efficiently, "
        "and thinks two shots ahead. Most effective in long matches where intelligent physical management outlasts "
        "opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'mental', 'stamina'): (
        'Unbreakable Mind',
        "Combines exceptional tactical intelligence with outstanding mental composure and remarkable physical endurance. "
        "Tactical intelligence amplifies both physical tools and composure, producing a player who stays calm, moves "
        "efficiently, and thinks two shots ahead. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'mental', 'straight'): (
        'Composed Line Hitter',
        "Combines exceptional tactical intelligence with outstanding mental composure and pinpoint down-the-line "
        "accuracy. Mental strength and precision combine with tactical intelligence to produce an opponent who never "
        "beats themselves and consistently finds narrow windows. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'mental', 'volley'): (
        'Ice-Cold Net Tactician',
        "Combines exceptional tactical intelligence with outstanding mental composure and polished net skills. Tactical "
        "awareness maximizes the effectiveness of specialty shots, choosing the right moment for each variation with "
        "surgical precision. Thrives by constructing points that end at the net, using intelligence to find the right "
        "approach moment."
    ),

    ('iq', 'serve', 'speed'): (
        'Fast Thinking Server',
        "Combines exceptional tactical intelligence with a potent and varied serve and elite court coverage. Their "
        "intelligence maximizes natural athleticism and power, ensuring they always channel physical tools toward the "
        "highest-value play. Most effective in long matches where intelligent physical management outlasts opponents who "
        "burn energy chasing the wrong patterns."
    ),

    ('iq', 'serve', 'stamina'): (
        'Tireless Serving Strategist',
        "Combines exceptional tactical intelligence with a potent and varied serve and remarkable physical endurance. "
        "Their intelligence maximizes natural athleticism and power, ensuring they always channel physical tools toward "
        "the highest-value play. Most effective in long matches where intelligent physical management outlasts opponents "
        "who burn energy chasing the wrong patterns."
    ),

    ('iq', 'serve', 'straight'): (
        'Straight-Line Server Genius',
        "Combines exceptional tactical intelligence with a potent and varied serve and pinpoint down-the-line accuracy. "
        "Tactical awareness turns raw power and placement into a surgical attack, consistently finding the right shot at "
        "the right moment. Dominant in service games where tactical serving consistently creates first-strike "
        "opportunities."
    ),

    ('iq', 'serve', 'volley'): (
        'Serve & Volley Mastermind',
        "Combines exceptional tactical intelligence with a potent and varied serve and polished net skills. Their "
        "tactical mind chooses optimally between raw power plays and specialty shots, keeping opponents off-balance with "
        "unpredictable but intelligent shot selection. Dominant in service games where tactical serving consistently "
        "creates first-strike opportunities."
    ),

    ('iq', 'speed', 'stamina'): (
        'Perpetual Motion Thinker',
        "Combines exceptional tactical intelligence with elite court coverage and remarkable physical endurance. "
        "Tactical intelligence amplifies both physical tools and composure, producing a player who stays calm, moves "
        "efficiently, and thinks two shots ahead. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'speed', 'straight'): (
        'Quick Linear Thinker',
        "Combines exceptional tactical intelligence with elite court coverage and pinpoint down-the-line accuracy. "
        "Intelligence transforms court speed and precision into a relentless machine that wears opponents down by always "
        "placing the ball to maximum effect. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'speed', 'volley'): (
        'Rushing Net Analyst',
        "Combines exceptional tactical intelligence with elite court coverage and polished net skills. Quick thinking "
        "combines with athletic ability and specialty shots to create an opponent who always seems to find extra time on "
        "the ball. Most effective in long matches where intelligent physical management outlasts opponents who burn "
        "energy chasing the wrong patterns."
    ),

    ('iq', 'stamina', 'straight'): (
        'Patient Line Strategist',
        "Combines exceptional tactical intelligence with remarkable physical endurance and pinpoint down-the-line "
        "accuracy. Intelligence transforms court speed and precision into a relentless machine that wears opponents down "
        "by always placing the ball to maximum effect. Most effective in long matches where intelligent physical "
        "management outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'stamina', 'volley'): (
        'Enduring Net Thinker',
        "Combines exceptional tactical intelligence with remarkable physical endurance and polished net skills. Quick "
        "thinking combines with athletic ability and specialty shots to create an opponent who always seems to find "
        "extra time on the ball. Most effective in long matches where intelligent physical management outlasts opponents "
        "who burn energy chasing the wrong patterns."
    ),

    ('iq', 'straight', 'volley'): (
        'Approach Shot Strategist',
        "Combines exceptional tactical intelligence with pinpoint down-the-line accuracy and polished net skills. Court "
        "IQ guides the choice between precise placement and specialty shots, creating layered patterns that steadily "
        "dismantle opponent defenses. Thrives by constructing points that end at the net, using intelligence to find the "
        "right approach moment."
    ),

    # --- LIFT combinations ---

    ('backhand', 'cross', 'lift'): (
        'Cross-Court Lobber',
        "Combines a reliable and penetrating backhand with sharp cross-court placement and a high-risk topspin lob "
        "weapon. Mixing powerful groundstrokes with precise placement and devastating lobs creates an attack that "
        "operates on multiple levels of risk and reward. Most effective against net-rushing opponents who are vulnerable "
        "to the lob, and against baseliners who don't handle high-bouncing balls well."
    ),

    ('backhand', 'dropshot', 'lift'): (
        'Touch & Lob Specialist',
        "Combines a reliable and penetrating backhand with delicate drop shot touch and a high-risk topspin lob weapon. "
        "The lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. Maximally disruptive against rhythm players ù the combination of lobs and drops constantly "
        "changes the ball's height and depth."
    ),

    ('backhand', 'forehand', 'lift'): (
        'Two-Wing Lobber',
        "Combines a reliable and penetrating backhand with a heavy and dominant forehand and a high-risk topspin lob "
        "weapon. The lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend "
        "against simultaneously. Most effective against net-rushing opponents who are vulnerable to the lob, and against "
        "baseliners who don't handle high-bouncing balls well."
    ),

    ('backhand', 'lift', 'mental'): (
        'Clutch Lobber',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and outstanding mental "
        "composure. The lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend "
        "against simultaneously. Most effective against net-rushing opponents who are vulnerable to the lob, and against "
        "baseliners who don't handle high-bouncing balls well."
    ),

    ('backhand', 'lift', 'serve'): (
        'Serving Lobber',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and a potent and varied serve. "
        "The lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The combination of serving power and lob threat creates a unique game that opponents rarely "
        "face, making preparation difficult."
    ),

    ('backhand', 'lift', 'speed'): (
        'Athletic Lobber',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and elite court coverage. The "
        "topspin lob adds an unpredictable dimension to an already powerful and mobile game, catching opponents "
        "off-guard when they expect conventional aggression. Their physical tools mean even failed lobs rarely cost them "
        "the point, as they recover position quickly enough to stay in the rally."
    ),

    ('backhand', 'lift', 'stamina'): (
        'Tireless Lobber',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and remarkable physical "
        "endurance. The topspin lob adds an unpredictable dimension to an already powerful and mobile game, catching "
        "opponents off-guard when they expect conventional aggression. Their physical tools mean even failed lobs rarely "
        "cost them the point, as they recover position quickly enough to stay in the rally."
    ),

    ('backhand', 'lift', 'straight'): (
        'Linear Lobber',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and pinpoint down-the-line "
        "accuracy. Mixing powerful groundstrokes with precise placement and devastating lobs creates an attack that "
        "operates on multiple levels of risk and reward. Most effective against net-rushing opponents who are vulnerable "
        "to the lob, and against baseliners who don't handle high-bouncing balls well."
    ),

    ('backhand', 'lift', 'volley'): (
        'Lob & Volley Defender',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and polished net skills. The "
        "lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The lob-volley combination creates a vertical dimension to their game that flat-hitting "
        "baseliners struggle to cope with."
    ),

    ('cross', 'dropshot', 'lift'): (
        'Angled Touch Lobber',
        "Combines sharp cross-court placement with delicate drop shot touch and a high-risk topspin lob weapon. The "
        "combination of precision, specialty shots, and lobs creates layers of variation that make every rally a unique "
        "puzzle for the opponent. Maximally disruptive against rhythm players ù the combination of lobs and drops "
        "constantly changes the ball's height and depth."
    ),

    ('cross', 'forehand', 'lift'): (
        'Cross-Court Arc Striker',
        "Combines sharp cross-court placement with a heavy and dominant forehand and a high-risk topspin lob weapon. "
        "Mixing powerful groundstrokes with precise placement and devastating lobs creates an attack that operates on "
        "multiple levels of risk and reward. Most effective against net-rushing opponents who are vulnerable to the lob, "
        "and against baseliners who don't handle high-bouncing balls well."
    ),

    ('cross', 'lift', 'mental'): (
        'Composed Arc Player',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and outstanding mental composure. The "
        "combination of precision, specialty shots, and lobs creates layers of variation that make every rally a unique "
        "puzzle for the opponent. Most effective against net-rushing opponents who are vulnerable to the lob, and "
        "against baseliners who don't handle high-bouncing balls well."
    ),

    ('cross', 'lift', 'serve'): (
        'Serve & Arc Specialist',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and a potent and varied serve. Mixing "
        "powerful groundstrokes with precise placement and devastating lobs creates an attack that operates on multiple "
        "levels of risk and reward. The combination of serving power and lob threat creates a unique game that opponents "
        "rarely face, making preparation difficult."
    ),

    ('cross', 'lift', 'speed'): (
        'Quick Arc Specialist',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and elite court coverage. Court "
        "coverage and precision provide the foundation for safe rallying, while the lob introduces a volatile element "
        "that can end points spectacularly. Their physical tools mean even failed lobs rarely cost them the point, as "
        "they recover position quickly enough to stay in the rally."
    ),

    ('cross', 'lift', 'stamina'): (
        'Relentless Arc Grinder',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and remarkable physical endurance. "
        "Court coverage and precision provide the foundation for safe rallying, while the lob introduces a volatile "
        "element that can end points spectacularly. Their physical tools mean even failed lobs rarely cost them the "
        "point, as they recover position quickly enough to stay in the rally."
    ),

    ('cross', 'lift', 'straight'): (
        'Full-Court Arc Specialist',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and pinpoint down-the-line accuracy. "
        "The combination of precision, specialty shots, and lobs creates layers of variation that make every rally a "
        "unique puzzle for the opponent. Most effective against net-rushing opponents who are vulnerable to the lob, and "
        "against baseliners who don't handle high-bouncing balls well."
    ),

    ('cross', 'lift', 'volley'): (
        'Net-to-Lob Artist',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and polished net skills. The "
        "combination of precision, specialty shots, and lobs creates layers of variation that make every rally a unique "
        "puzzle for the opponent. The lob-volley combination creates a vertical dimension to their game that "
        "flat-hitting baseliners struggle to cope with."
    ),

    ('dropshot', 'forehand', 'lift'): (
        'Forehand Lob & Drop',
        "Combines delicate drop shot touch with a heavy and dominant forehand and a high-risk topspin lob weapon. The "
        "lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. Maximally disruptive against rhythm players ù the combination of lobs and drops constantly "
        "changes the ball's height and depth."
    ),

    ('dropshot', 'lift', 'mental'): (
        'Clutch Touch Lobber',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and outstanding mental composure. With "
        "multiple specialty weapons including the lob, they can keep opponents guessing about what's coming next from "
        "any position on court. Maximally disruptive against rhythm players ù the combination of lobs and drops "
        "constantly changes the ball's height and depth."
    ),

    ('dropshot', 'lift', 'serve'): (
        'Serve & Lob Specialist',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and a potent and varied serve. The lob "
        "adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The combination of serving power and lob threat creates a unique game that opponents rarely "
        "face, making preparation difficult."
    ),

    ('dropshot', 'lift', 'speed'): (
        'Quick Lob & Drop Artist',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and elite court coverage. Athletic "
        "ability provides the platform to execute lobs from any position, while specialty shots offer safe alternatives "
        "when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, as they "
        "recover position quickly enough to stay in the rally."
    ),

    ('dropshot', 'lift', 'stamina'): (
        'Enduring Touch Lobber',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and remarkable physical endurance. "
        "Athletic ability provides the platform to execute lobs from any position, while specialty shots offer safe "
        "alternatives when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, "
        "as they recover position quickly enough to stay in the rally."
    ),

    ('dropshot', 'lift', 'straight'): (
        'Down-the-Line Lob & Drop',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and pinpoint down-the-line accuracy. The "
        "combination of precision, specialty shots, and lobs creates layers of variation that make every rally a unique "
        "puzzle for the opponent. Maximally disruptive against rhythm players ù the combination of lobs and drops "
        "constantly changes the ball's height and depth."
    ),

    ('dropshot', 'lift', 'volley'): (
        'Triple Threat Net Lobber',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and polished net skills. With multiple "
        "specialty weapons including the lob, they can keep opponents guessing about what's coming next from any "
        "position on court. The lob-volley combination creates a vertical dimension to their game that flat-hitting "
        "baseliners struggle to cope with."
    ),

    ('forehand', 'lift', 'mental'): (
        'Mentally Tough Lobber',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and outstanding mental composure. "
        "The lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. Most effective against net-rushing opponents who are vulnerable to the lob, and against "
        "baseliners who don't handle high-bouncing balls well."
    ),

    ('forehand', 'lift', 'serve'): (
        'Power Serve & Lob',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and a potent and varied serve. The "
        "lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The combination of serving power and lob threat creates a unique game that opponents rarely "
        "face, making preparation difficult."
    ),

    ('forehand', 'lift', 'speed'): (
        'Speedy Lob Striker',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and elite court coverage. The "
        "topspin lob adds an unpredictable dimension to an already powerful and mobile game, catching opponents "
        "off-guard when they expect conventional aggression. Their physical tools mean even failed lobs rarely cost them "
        "the point, as they recover position quickly enough to stay in the rally."
    ),

    ('forehand', 'lift', 'stamina'): (
        'Enduring Lob Striker',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and remarkable physical endurance. "
        "The topspin lob adds an unpredictable dimension to an already powerful and mobile game, catching opponents "
        "off-guard when they expect conventional aggression. Their physical tools mean even failed lobs rarely cost them "
        "the point, as they recover position quickly enough to stay in the rally."
    ),

    ('forehand', 'lift', 'straight'): (
        'Linear Lob Striker',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and pinpoint down-the-line accuracy. "
        "Mixing powerful groundstrokes with precise placement and devastating lobs creates an attack that operates on "
        "multiple levels of risk and reward. Most effective against net-rushing opponents who are vulnerable to the lob, "
        "and against baseliners who don't handle high-bouncing balls well."
    ),

    ('forehand', 'lift', 'volley'): (
        'Lob & Rush Attacker',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and polished net skills. The lob "
        "adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The lob-volley combination creates a vertical dimension to their game that flat-hitting "
        "baseliners struggle to cope with."
    ),

    ('lift', 'mental', 'serve'): (
        'Clutch Serving Lobber',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and a potent and varied serve. The "
        "lob adds another layer to an already varied arsenal, giving opponents too many weapons to defend against "
        "simultaneously. The combination of serving power and lob threat creates a unique game that opponents rarely "
        "face, making preparation difficult."
    ),

    ('lift', 'mental', 'speed'): (
        'Cool Quick Lobber',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and elite court coverage. Athletic "
        "ability provides the platform to execute lobs from any position, while specialty shots offer safe alternatives "
        "when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, as they "
        "recover position quickly enough to stay in the rally."
    ),

    ('lift', 'mental', 'stamina'): (
        'Iron-Willed Lobber',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and remarkable physical endurance. "
        "Athletic ability provides the platform to execute lobs from any position, while specialty shots offer safe "
        "alternatives when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, "
        "as they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'mental', 'straight'): (
        'Composed Line Lobber',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and pinpoint down-the-line accuracy. "
        "The combination of precision, specialty shots, and lobs creates layers of variation that make every rally a "
        "unique puzzle for the opponent. Most effective against net-rushing opponents who are vulnerable to the lob, and "
        "against baseliners who don't handle high-bouncing balls well."
    ),

    ('lift', 'mental', 'volley'): (
        'Calm Lob & Volley',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and polished net skills. With "
        "multiple specialty weapons including the lob, they can keep opponents guessing about what's coming next from "
        "any position on court. The lob-volley combination creates a vertical dimension to their game that flat-hitting "
        "baseliners struggle to cope with."
    ),

    ('lift', 'serve', 'speed'): (
        'Fast Serve & Lob Player',
        "Combines a high-risk topspin lob weapon with a potent and varied serve and elite court coverage. The topspin "
        "lob adds an unpredictable dimension to an already powerful and mobile game, catching opponents off-guard when "
        "they expect conventional aggression. Their physical tools mean even failed lobs rarely cost them the point, as "
        "they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'serve', 'stamina'): (
        'Tireless Serve Lobber',
        "Combines a high-risk topspin lob weapon with a potent and varied serve and remarkable physical endurance. The "
        "topspin lob adds an unpredictable dimension to an already powerful and mobile game, catching opponents "
        "off-guard when they expect conventional aggression. Their physical tools mean even failed lobs rarely cost them "
        "the point, as they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'serve', 'straight'): (
        'Straight Serve & Lob',
        "Combines a high-risk topspin lob weapon with a potent and varied serve and pinpoint down-the-line accuracy. "
        "Mixing powerful groundstrokes with precise placement and devastating lobs creates an attack that operates on "
        "multiple levels of risk and reward. The combination of serving power and lob threat creates a unique game that "
        "opponents rarely face, making preparation difficult."
    ),

    ('lift', 'serve', 'volley'): (
        'Serve Lob & Volley',
        "Combines a high-risk topspin lob weapon with a potent and varied serve and polished net skills. The lob adds "
        "another layer to an already varied arsenal, giving opponents too many weapons to defend against simultaneously. "
        "The combination of serving power and lob threat creates a unique game that opponents rarely face, making "
        "preparation difficult."
    ),

    ('lift', 'speed', 'stamina'): (
        'Athletic Moon Baller',
        "Combines a high-risk topspin lob weapon with elite court coverage and remarkable physical endurance. Athletic "
        "ability provides the platform to execute lobs from any position, while specialty shots offer safe alternatives "
        "when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, as they "
        "recover position quickly enough to stay in the rally."
    ),

    ('lift', 'speed', 'straight'): (
        'Quick Line Lobber',
        "Combines a high-risk topspin lob weapon with elite court coverage and pinpoint down-the-line accuracy. Court "
        "coverage and precision provide the foundation for safe rallying, while the lob introduces a volatile element "
        "that can end points spectacularly. Their physical tools mean even failed lobs rarely cost them the point, as "
        "they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'speed', 'volley'): (
        'Fast Lob & Net Player',
        "Combines a high-risk topspin lob weapon with elite court coverage and polished net skills. Athletic ability "
        "provides the platform to execute lobs from any position, while specialty shots offer safe alternatives when the "
        "lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, as they recover "
        "position quickly enough to stay in the rally."
    ),

    ('lift', 'stamina', 'straight'): (
        'Enduring Line Lobber',
        "Combines a high-risk topspin lob weapon with remarkable physical endurance and pinpoint down-the-line accuracy. "
        "Court coverage and precision provide the foundation for safe rallying, while the lob introduces a volatile "
        "element that can end points spectacularly. Their physical tools mean even failed lobs rarely cost them the "
        "point, as they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'stamina', 'volley'): (
        'Tireless Lob & Volleyer',
        "Combines a high-risk topspin lob weapon with remarkable physical endurance and polished net skills. Athletic "
        "ability provides the platform to execute lobs from any position, while specialty shots offer safe alternatives "
        "when the lob isn't viable. Their physical tools mean even failed lobs rarely cost them the point, as they "
        "recover position quickly enough to stay in the rally."
    ),

    ('lift', 'straight', 'volley'): (
        'Linear Lob & Volley',
        "Combines a high-risk topspin lob weapon with pinpoint down-the-line accuracy and polished net skills. The "
        "combination of precision, specialty shots, and lobs creates layers of variation that make every rally a unique "
        "puzzle for the opponent. The lob-volley combination creates a vertical dimension to their game that "
        "flat-hitting baseliners struggle to cope with."
    ),

    # --- SLICE combinations ---

    ('backhand', 'cross', 'slice'): (
        'Cross-Court Slice Artist',
        "Combines a reliable and penetrating backhand with sharp cross-court placement and precise and crafty slice "
        "placement. Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that "
        "amplifies the effectiveness of both styles. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('backhand', 'dropshot', 'slice'): (
        'Touch & Slice Specialist',
        "Combines a reliable and penetrating backhand with delicate drop shot touch and precise and crafty slice "
        "placement. The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies "
        "while maintaining access to finishing weapons. The variety of touch shots ù slices and drops ù makes them a "
        "nightmare for power-dependent players who need pace to generate their own."
    ),

    ('backhand', 'forehand', 'slice'): (
        'Baseline Slicer',
        "Combines a reliable and penetrating backhand with a heavy and dominant forehand and precise and crafty slice "
        "placement. The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies "
        "while maintaining access to finishing weapons. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('backhand', 'mental', 'slice'): (
        'Clutch Slicer',
        "Combines a reliable and penetrating backhand with outstanding mental composure and precise and crafty slice "
        "placement. The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies "
        "while maintaining access to finishing weapons. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('backhand', 'serve', 'slice'): (
        'Serve & Slice Artist',
        "Combines a reliable and penetrating backhand with a potent and varied serve and precise and crafty slice "
        "placement. The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies "
        "while maintaining access to finishing weapons. The serve-and-slice combination is particularly effective on "
        "low-bouncing surfaces where the sliced ball stays low and skids through."
    ),

    ('backhand', 'slice', 'speed'): (
        'Quick Slice Runner',
        "Combines a reliable and penetrating backhand with precise and crafty slice placement and elite court coverage. "
        "The ability to shift between aggressive power tennis and sliced tempo control makes them tactically flexible "
        "and physically draining to play against. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('backhand', 'slice', 'stamina'): (
        'Enduring Slicer',
        "Combines a reliable and penetrating backhand with precise and crafty slice placement and remarkable physical "
        "endurance. The ability to shift between aggressive power tennis and sliced tempo control makes them tactically "
        "flexible and physically draining to play against. Their physical resilience combined with tempo control makes "
        "them especially effective in grueling best-of-five formats."
    ),

    ('backhand', 'slice', 'straight'): (
        'Linear Slice Specialist',
        "Combines a reliable and penetrating backhand with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that "
        "amplifies the effectiveness of both styles. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('backhand', 'slice', 'volley'): (
        'Chip & Charge Defender',
        "Combines a reliable and penetrating backhand with precise and crafty slice placement and polished net skills. "
        "The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The slice approach shot sets up net positions beautifully, making them "
        "especially dangerous on faster surfaces."
    ),

    ('cross', 'dropshot', 'slice'): (
        'Angled Touch Slicer',
        "Combines sharp cross-court placement with delicate drop shot touch and precise and crafty slice placement. "
        "Precision and specialty shots mix with the slice to create endless variation, with every rally trajectory and "
        "pace subtly different from the last. The variety of touch shots ù slices and drops ù makes them a nightmare for "
        "power-dependent players who need pace to generate their own."
    ),

    ('cross', 'forehand', 'slice'): (
        'Cross-Court Tempo Controller',
        "Combines sharp cross-court placement with a heavy and dominant forehand and precise and crafty slice placement. "
        "Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that amplifies the "
        "effectiveness of both styles. Most effective against aggressive hitters who depend on incoming pace, as the "
        "slice denies them the speed they crave."
    ),

    ('cross', 'mental', 'slice'): (
        'Composed Tempo Player',
        "Combines sharp cross-court placement with outstanding mental composure and precise and crafty slice placement. "
        "Precision and specialty shots mix with the slice to create endless variation, with every rally trajectory and "
        "pace subtly different from the last. Most effective against aggressive hitters who depend on incoming pace, as "
        "the slice denies them the speed they crave."
    ),

    ('cross', 'serve', 'slice'): (
        'Serve & Slice Tempoist',
        "Combines sharp cross-court placement with a potent and varied serve and precise and crafty slice placement. "
        "Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that amplifies the "
        "effectiveness of both styles. The serve-and-slice combination is particularly effective on low-bouncing "
        "surfaces where the sliced ball stays low and skids through."
    ),

    ('cross', 'slice', 'speed'): (
        'Quick Tempo Controller',
        "Combines sharp cross-court placement with precise and crafty slice placement and elite court coverage. "
        "Excellent movement and placement combine with slice to create a relentless competitor who controls rallies "
        "through positioning and tempo manipulation. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('cross', 'slice', 'stamina'): (
        'Relentless Tempo Grinder',
        "Combines sharp cross-court placement with precise and crafty slice placement and remarkable physical endurance. "
        "Excellent movement and placement combine with slice to create a relentless competitor who controls rallies "
        "through positioning and tempo manipulation. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('cross', 'slice', 'straight'): (
        'Full-Court Slicer',
        "Combines sharp cross-court placement with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Precision and specialty shots mix with the slice to create endless variation, with every rally "
        "trajectory and pace subtly different from the last. Most effective against aggressive hitters who depend on "
        "incoming pace, as the slice denies them the speed they crave."
    ),

    ('cross', 'slice', 'volley'): (
        'Chip & Approach Player',
        "Combines sharp cross-court placement with precise and crafty slice placement and polished net skills. Precision "
        "and specialty shots mix with the slice to create endless variation, with every rally trajectory and pace subtly "
        "different from the last. The slice approach shot sets up net positions beautifully, making them especially "
        "dangerous on faster surfaces."
    ),

    ('dropshot', 'forehand', 'slice'): (
        'Forehand & Slice Touch',
        "Combines delicate drop shot touch with a heavy and dominant forehand and precise and crafty slice placement. "
        "The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The variety of touch shots ù slices and drops ù makes them a nightmare "
        "for power-dependent players who need pace to generate their own."
    ),

    ('dropshot', 'mental', 'slice'): (
        'Clutch Touch Slicer',
        "Combines delicate drop shot touch with outstanding mental composure and precise and crafty slice placement. The "
        "slice provides a tactical bridge between specialty shots, controlling tempo while setting up opportunities for "
        "more aggressive variations. The variety of touch shots ù slices and drops ù makes them a nightmare for "
        "power-dependent players who need pace to generate their own."
    ),

    ('dropshot', 'serve', 'slice'): (
        'Serve & Touch Slicer',
        "Combines delicate drop shot touch with a potent and varied serve and precise and crafty slice placement. The "
        "slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The serve-and-slice combination is particularly effective on "
        "low-bouncing surfaces where the sliced ball stays low and skids through."
    ),

    ('dropshot', 'slice', 'speed'): (
        'Quick Touch & Slice',
        "Combines delicate drop shot touch with precise and crafty slice placement and elite court coverage. Athletic "
        "ability provides the platform to both attack and temporize, with the slice offering a safe reset option from "
        "any position on court. Their physical resilience combined with tempo control makes them especially effective in "
        "grueling best-of-five formats."
    ),

    ('dropshot', 'slice', 'stamina'): (
        'Patient Touch Slicer',
        "Combines delicate drop shot touch with precise and crafty slice placement and remarkable physical endurance. "
        "Athletic ability provides the platform to both attack and temporize, with the slice offering a safe reset "
        "option from any position on court. Their physical resilience combined with tempo control makes them especially "
        "effective in grueling best-of-five formats."
    ),

    ('dropshot', 'slice', 'straight'): (
        'Down-the-Line Touch Slicer',
        "Combines delicate drop shot touch with precise and crafty slice placement and pinpoint down-the-line accuracy. "
        "Precision and specialty shots mix with the slice to create endless variation, with every rally trajectory and "
        "pace subtly different from the last. The variety of touch shots ù slices and drops ù makes them a nightmare for "
        "power-dependent players who need pace to generate their own."
    ),

    ('dropshot', 'slice', 'volley'): (
        'Triple Touch Specialist',
        "Combines delicate drop shot touch with precise and crafty slice placement and polished net skills. The slice "
        "provides a tactical bridge between specialty shots, controlling tempo while setting up opportunities for more "
        "aggressive variations. The slice approach shot sets up net positions beautifully, making them especially "
        "dangerous on faster surfaces."
    ),

    ('forehand', 'mental', 'slice'): (
        'Composed Slicing Striker',
        "Combines a heavy and dominant forehand with outstanding mental composure and precise and crafty slice "
        "placement. The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies "
        "while maintaining access to finishing weapons. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('forehand', 'serve', 'slice'): (
        'Power Serve & Slice',
        "Combines a heavy and dominant forehand with a potent and varied serve and precise and crafty slice placement. "
        "The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The serve-and-slice combination is particularly effective on "
        "low-bouncing surfaces where the sliced ball stays low and skids through."
    ),

    ('forehand', 'slice', 'speed'): (
        'Speedy Slice Striker',
        "Combines a heavy and dominant forehand with precise and crafty slice placement and elite court coverage. The "
        "ability to shift between aggressive power tennis and sliced tempo control makes them tactically flexible and "
        "physically draining to play against. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('forehand', 'slice', 'stamina'): (
        'Tireless Slice Striker',
        "Combines a heavy and dominant forehand with precise and crafty slice placement and remarkable physical "
        "endurance. The ability to shift between aggressive power tennis and sliced tempo control makes them tactically "
        "flexible and physically draining to play against. Their physical resilience combined with tempo control makes "
        "them especially effective in grueling best-of-five formats."
    ),

    ('forehand', 'slice', 'straight'): (
        'Linear Slice Striker',
        "Combines a heavy and dominant forehand with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that "
        "amplifies the effectiveness of both styles. Most effective against aggressive hitters who depend on incoming "
        "pace, as the slice denies them the speed they crave."
    ),

    ('forehand', 'slice', 'volley'): (
        'Chip & Rush Attacker',
        "Combines a heavy and dominant forehand with precise and crafty slice placement and polished net skills. The "
        "slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The slice approach shot sets up net positions beautifully, making them "
        "especially dangerous on faster surfaces."
    ),

    ('mental', 'serve', 'slice'): (
        'Clutch Serving Slicer',
        "Combines outstanding mental composure with a potent and varied serve and precise and crafty slice placement. "
        "The slice adds tempo control to an already varied game, allowing them to dictate the pace of rallies while "
        "maintaining access to finishing weapons. The serve-and-slice combination is particularly effective on "
        "low-bouncing surfaces where the sliced ball stays low and skids through."
    ),

    ('mental', 'slice', 'speed'): (
        'Cool Quick Slicer',
        "Combines outstanding mental composure with precise and crafty slice placement and elite court coverage. "
        "Athletic ability provides the platform to both attack and temporize, with the slice offering a safe reset "
        "option from any position on court. Their physical resilience combined with tempo control makes them especially "
        "effective in grueling best-of-five formats."
    ),

    ('mental', 'slice', 'stamina'): (
        'Iron-Willed Slicer',
        "Combines outstanding mental composure with precise and crafty slice placement and remarkable physical "
        "endurance. Athletic ability provides the platform to both attack and temporize, with the slice offering a safe "
        "reset option from any position on court. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('mental', 'slice', 'straight'): (
        'Composed Line Slicer',
        "Combines outstanding mental composure with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Precision and specialty shots mix with the slice to create endless variation, with every rally "
        "trajectory and pace subtly different from the last. Most effective against aggressive hitters who depend on "
        "incoming pace, as the slice denies them the speed they crave."
    ),

    ('mental', 'slice', 'volley'): (
        'Calm Chip & Charge',
        "Combines outstanding mental composure with precise and crafty slice placement and polished net skills. The "
        "slice provides a tactical bridge between specialty shots, controlling tempo while setting up opportunities for "
        "more aggressive variations. The slice approach shot sets up net positions beautifully, making them especially "
        "dangerous on faster surfaces."
    ),

    ('serve', 'slice', 'speed'): (
        'Fast Serve & Slice',
        "Combines a potent and varied serve with precise and crafty slice placement and elite court coverage. The "
        "ability to shift between aggressive power tennis and sliced tempo control makes them tactically flexible and "
        "physically draining to play against. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('serve', 'slice', 'stamina'): (
        'Tireless Serve Slicer',
        "Combines a potent and varied serve with precise and crafty slice placement and remarkable physical endurance. "
        "The ability to shift between aggressive power tennis and sliced tempo control makes them tactically flexible "
        "and physically draining to play against. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('serve', 'slice', 'straight'): (
        'Straight Serve & Slice',
        "Combines a potent and varied serve with precise and crafty slice placement and pinpoint down-the-line accuracy. "
        "Precise slice shots disrupt opponent rhythm between power attacks, creating a change of pace that amplifies the "
        "effectiveness of both styles. The serve-and-slice combination is particularly effective on low-bouncing "
        "surfaces where the sliced ball stays low and skids through."
    ),

    ('serve', 'slice', 'volley'): (
        'Classic Serve & Slice',
        "Combines a potent and varied serve with precise and crafty slice placement and polished net skills. The slice "
        "adds tempo control to an already varied game, allowing them to dictate the pace of rallies while maintaining "
        "access to finishing weapons. The serve-and-slice combination is particularly effective on low-bouncing surfaces "
        "where the sliced ball stays low and skids through."
    ),

    ('slice', 'speed', 'stamina'): (
        'Athletic Tempo Grinder',
        "Combines precise and crafty slice placement with elite court coverage and remarkable physical endurance. "
        "Athletic ability provides the platform to both attack and temporize, with the slice offering a safe reset "
        "option from any position on court. Their physical resilience combined with tempo control makes them especially "
        "effective in grueling best-of-five formats."
    ),

    ('slice', 'speed', 'straight'): (
        'Quick Line Slicer',
        "Combines precise and crafty slice placement with elite court coverage and pinpoint down-the-line accuracy. "
        "Excellent movement and placement combine with slice to create a relentless competitor who controls rallies "
        "through positioning and tempo manipulation. Their physical resilience combined with tempo control makes them "
        "especially effective in grueling best-of-five formats."
    ),

    ('slice', 'speed', 'volley'): (
        'Fast Chip & Charge',
        "Combines precise and crafty slice placement with elite court coverage and polished net skills. Athletic ability "
        "provides the platform to both attack and temporize, with the slice offering a safe reset option from any "
        "position on court. Their physical resilience combined with tempo control makes them especially effective in "
        "grueling best-of-five formats."
    ),

    ('slice', 'stamina', 'straight'): (
        'Enduring Line Slicer',
        "Combines precise and crafty slice placement with remarkable physical endurance and pinpoint down-the-line "
        "accuracy. Excellent movement and placement combine with slice to create a relentless competitor who controls "
        "rallies through positioning and tempo manipulation. Their physical resilience combined with tempo control makes "
        "them especially effective in grueling best-of-five formats."
    ),

    ('slice', 'stamina', 'volley'): (
        'Tireless Chip & Charger',
        "Combines precise and crafty slice placement with remarkable physical endurance and polished net skills. "
        "Athletic ability provides the platform to both attack and temporize, with the slice offering a safe reset "
        "option from any position on court. Their physical resilience combined with tempo control makes them especially "
        "effective in grueling best-of-five formats."
    ),

    ('slice', 'straight', 'volley'): (
        'Linear Chip & Charge',
        "Combines precise and crafty slice placement with pinpoint down-the-line accuracy and polished net skills. "
        "Precision and specialty shots mix with the slice to create endless variation, with every rally trajectory and "
        "pace subtly different from the last. The slice approach shot sets up net positions beautifully, making them "
        "especially dangerous on faster surfaces."
    ),

    # --- IQ+LIFT combinations ---

    ('backhand', 'iq', 'lift'): (
        'Cerebral Lob Defender',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and a high-risk topspin lob "
        "weapon. Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate "
        "and making it a calculated weapon rather than a gamble. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('cross', 'iq', 'lift'): (
        'Tactical Arc Placer',
        "Combines sharp cross-court placement with exceptional tactical intelligence and a high-risk topspin lob weapon. "
        "Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate and "
        "making it a calculated weapon rather than a gamble. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('dropshot', 'iq', 'lift'): (
        'Smart Lob & Touch',
        "Combines delicate drop shot touch with exceptional tactical intelligence and a high-risk topspin lob weapon. "
        "Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate and "
        "making it a calculated weapon rather than a gamble. Especially dangerous against deep-positioned baseliners who "
        "are vulnerable to intelligent use of short balls."
    ),

    ('forehand', 'iq', 'lift'): (
        'Intelligent Lob Striker',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and a high-risk topspin lob "
        "weapon. Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate "
        "and making it a calculated weapon rather than a gamble. Most effective against one-dimensional players who are "
        "vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'lift', 'mental'): (
        'Calm Calculated Lobber',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and outstanding mental "
        "composure. Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success "
        "rate and making it a calculated weapon rather than a gamble. Most effective against one-dimensional players who "
        "are vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'lift', 'serve'): (
        'Strategic Serve & Lob',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and a potent and varied serve. "
        "Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate and "
        "making it a calculated weapon rather than a gamble. Dominant in service games where tactical serving "
        "consistently creates first-strike opportunities."
    ),

    ('iq', 'lift', 'speed'): (
        'Quick-Thinking Lobber',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and elite court coverage. Their "
        "intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate and making it "
        "a calculated weapon rather than a gamble. Most effective in long matches where intelligent physical management "
        "outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'lift', 'stamina'): (
        'Patient Tactical Lobber',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and remarkable physical "
        "endurance. Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success "
        "rate and making it a calculated weapon rather than a gamble. Most effective in long matches where intelligent "
        "physical management outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'lift', 'straight'): (
        'Linear Lob Strategist',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and pinpoint down-the-line "
        "accuracy. Their intelligence guides optimal timing for the high-risk lob, dramatically improving its success "
        "rate and making it a calculated weapon rather than a gamble. Most effective against one-dimensional players who "
        "are vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'lift', 'volley'): (
        'Cerebral Lob & Volley',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and polished net skills. Their "
        "intelligence guides optimal timing for the high-risk lob, dramatically improving its success rate and making it "
        "a calculated weapon rather than a gamble. Thrives by constructing points that end at the net, using "
        "intelligence to find the right approach moment."
    ),

    # --- IQ+SLICE combinations ---

    ('backhand', 'iq', 'slice'): (
        'Tactical Backhand Slicer',
        "Combines a reliable and penetrating backhand with exceptional tactical intelligence and precise and crafty "
        "slice placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when "
        "ahead, disrupting rhythm when behind, and neutralizing power when outgunned. Most effective against "
        "one-dimensional players who are vulnerable to tactical adjustments mid-match."
    ),

    ('cross', 'iq', 'slice'): (
        'Strategic Cross-Court Slicer',
        "Combines sharp cross-court placement with exceptional tactical intelligence and precise and crafty slice "
        "placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Most effective against one-dimensional "
        "players who are vulnerable to tactical adjustments mid-match."
    ),

    ('dropshot', 'iq', 'slice'): (
        'Smart Touch & Slice',
        "Combines delicate drop shot touch with exceptional tactical intelligence and precise and crafty slice "
        "placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Especially dangerous against "
        "deep-positioned baseliners who are vulnerable to intelligent use of short balls."
    ),

    ('forehand', 'iq', 'slice'): (
        'Intelligent Slice & Drive',
        "Combines a heavy and dominant forehand with exceptional tactical intelligence and precise and crafty slice "
        "placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Most effective against one-dimensional "
        "players who are vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'mental', 'slice'): (
        'Composed Tactical Slicer',
        "Combines exceptional tactical intelligence with outstanding mental composure and precise and crafty slice "
        "placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Most effective against one-dimensional "
        "players who are vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'serve', 'slice'): (
        'Strategic Serve & Slice',
        "Combines exceptional tactical intelligence with a potent and varied serve and precise and crafty slice "
        "placement. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Dominant in service games where tactical "
        "serving consistently creates first-strike opportunities."
    ),

    ('iq', 'slice', 'speed'): (
        'Quick Tactical Slicer',
        "Combines exceptional tactical intelligence with precise and crafty slice placement and elite court coverage. "
        "Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, disrupting "
        "rhythm when behind, and neutralizing power when outgunned. Most effective in long matches where intelligent "
        "physical management outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'slice', 'stamina'): (
        'Patient Strategic Slicer',
        "Combines exceptional tactical intelligence with precise and crafty slice placement and remarkable physical "
        "endurance. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Most effective in long matches where "
        "intelligent physical management outlasts opponents who burn energy chasing the wrong patterns."
    ),

    ('iq', 'slice', 'straight'): (
        'Calculated Line Slicer',
        "Combines exceptional tactical intelligence with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, "
        "disrupting rhythm when behind, and neutralizing power when outgunned. Most effective against one-dimensional "
        "players who are vulnerable to tactical adjustments mid-match."
    ),

    ('iq', 'slice', 'volley'): (
        'Smart Chip & Charger',
        "Combines exceptional tactical intelligence with precise and crafty slice placement and polished net skills. "
        "Tactical awareness ensures the slice is deployed at optimal moments ù slowing the game when ahead, disrupting "
        "rhythm when behind, and neutralizing power when outgunned. Thrives by constructing points that end at the net, "
        "using intelligence to find the right approach moment."
    ),

    # --- LIFT+SLICE combinations ---

    ('backhand', 'lift', 'slice'): (
        'Backhand Shot Variety',
        "Combines a reliable and penetrating backhand with a high-risk topspin lob weapon and precise and crafty slice "
        "placement. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Most effective against "
        "net-rushing opponents who are vulnerable to the lob, and against baseliners who don't handle high-bouncing "
        "balls well."
    ),

    ('cross', 'lift', 'slice'): (
        'Cross-Court Shot Artist',
        "Combines sharp cross-court placement with a high-risk topspin lob weapon and precise and crafty slice "
        "placement. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Most effective against "
        "net-rushing opponents who are vulnerable to the lob, and against baseliners who don't handle high-bouncing "
        "balls well."
    ),

    ('dropshot', 'lift', 'slice'): (
        'Triple Touch Architect',
        "Combines delicate drop shot touch with a high-risk topspin lob weapon and precise and crafty slice placement. "
        "Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually guessing "
        "about pace and trajectory, making them one of the hardest players to read. Maximally disruptive against rhythm "
        "players ù the combination of lobs and drops constantly changes the ball's height and depth."
    ),

    ('forehand', 'lift', 'slice'): (
        'Forehand Variety Striker',
        "Combines a heavy and dominant forehand with a high-risk topspin lob weapon and precise and crafty slice "
        "placement. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Most effective against "
        "net-rushing opponents who are vulnerable to the lob, and against baseliners who don't handle high-bouncing "
        "balls well."
    ),

    ('lift', 'mental', 'slice'): (
        'Composed Shot Variety',
        "Combines a high-risk topspin lob weapon with outstanding mental composure and precise and crafty slice "
        "placement. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Most effective against "
        "net-rushing opponents who are vulnerable to the lob, and against baseliners who don't handle high-bouncing "
        "balls well."
    ),

    ('lift', 'serve', 'slice'): (
        'Serve & Variety Player',
        "Combines a high-risk topspin lob weapon with a potent and varied serve and precise and crafty slice placement. "
        "Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually guessing "
        "about pace and trajectory, making them one of the hardest players to read. The combination of serving power and "
        "lob threat creates a unique game that opponents rarely face, making preparation difficult."
    ),

    ('lift', 'slice', 'speed'): (
        'Athletic Shot Variety',
        "Combines a high-risk topspin lob weapon with precise and crafty slice placement and elite court coverage. "
        "Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually guessing "
        "about pace and trajectory, making them one of the hardest players to read. Their physical tools mean even "
        "failed lobs rarely cost them the point, as they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'slice', 'stamina'): (
        'Enduring Shot Variety',
        "Combines a high-risk topspin lob weapon with precise and crafty slice placement and remarkable physical "
        "endurance. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Their physical tools mean "
        "even failed lobs rarely cost them the point, as they recover position quickly enough to stay in the rally."
    ),

    ('lift', 'slice', 'straight'): (
        'Linear Shot Variety',
        "Combines a high-risk topspin lob weapon with precise and crafty slice placement and pinpoint down-the-line "
        "accuracy. Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually "
        "guessing about pace and trajectory, making them one of the hardest players to read. Most effective against "
        "net-rushing opponents who are vulnerable to the lob, and against baseliners who don't handle high-bouncing "
        "balls well."
    ),

    ('lift', 'slice', 'volley'): (
        'Net & Shot Variety',
        "Combines a high-risk topspin lob weapon with precise and crafty slice placement and polished net skills. "
        "Outstanding shot variety through both topspin lobs and precise slices keeps opponents perpetually guessing "
        "about pace and trajectory, making them one of the hardest players to read. The lob-volley combination creates a "
        "vertical dimension to their game that flat-hitting baseliners struggle to cope with."
    ),

    # --- IQ+LIFT+SLICE combinations ---

    ('iq', 'lift', 'slice'): (
        'Complete Shot Scientist',
        "Combines exceptional tactical intelligence with a high-risk topspin lob weapon and precise and crafty slice "
        "placement. The intelligence to know when to lob, when to slice, and when to attack normally makes this the most "
        "unpredictable shot-selection profile in the game. Nearly impossible to prepare for, they force opponents to be "
        "ready for everything."
    ),
}


def get_archetype_for_player(player) -> Tuple[str, str, tuple]:
    """
    Determine archetype name, description and key tuple for the given player dict.

    Returns: (name, description, key_tuple)
    """
    skills = player.get('skills', {})
    if not skills:
        return (
            "Balanced Player",
            "A well-rounded player without any extreme strengths or weaknesses. "
            "Comfortable adapting their game to the opponent and conditions; consistent and reliable.",
            tuple()
        )

    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
    top_3 = [s[0].lower() for s in sorted_skills[:3]]
    key = tuple(sorted(top_3))

    if key in ARCTYPE_MAP:
        name, desc = ARCTYPE_MAP[key]
        return name, desc, key
    else:
        return (
            "Balanced Player",
            "A well-rounded player who does not strongly fit any single archetype. "
            "They combine steady technique, tactical awareness, and adaptable physical traits to navigate matches.",
            key,
        )
