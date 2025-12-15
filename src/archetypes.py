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
        "This player excels at creating wide angles: a well-placed serve followed by a forehand that opens the court with crosscourt winners and sharp angles. "
        "They build points by stretching opponents wide, then penetrating the open court with pace and placement or by changing direction to catch defenders off-balance. "
        "Their game blends spin and directional control, using the diagonal geometry to manufacture space for finishing shots, and they are comfortable constructing points that require both patience and sudden burst aggression. "
        "Match plans typically exploit crosscourt exchanges to elicit short replies that the forehand can punish."
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
    
    ('cross', 'backhand', 'volley'): (
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
