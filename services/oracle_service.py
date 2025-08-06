import random
import json
from datetime import datetime
import logging

class OracleService:
    """Enhanced Oracle service with market psychology and mystical insights"""
    
    def __init__(self):
        self.emotional_states = [
            'ECSTASY', 'SERENITY', 'WONDER', 'CONTEMPLATION', 
            'MELANCHOLY', 'DREAD', 'EUPHORIA', 'ANXIETY'
        ]
        
        self.market_archetypes = {
            'PHOENIX': '🔥 Rising from ashes, transformation imminent',
            'SERPENT': '🐍 Coiled energy, sudden movements ahead',
            'LION': '🦁 Strength and courage, bullish momentum',
            'WHALE': '🐋 Deep currents, institutional movements',
            'BUTTERFLY': '🦋 Delicate changes, volatility patterns',
            'DRAGON': '🐉 Ancient wisdom, long-term cycles',
            'EAGLE': '🦅 High perspective, market oversight',
            'TURTLE': '🐢 Slow and steady, conservative approach'
        }
        
        self.mystical_elements = {
            'FIRE': 'Passion, rapid growth, volatility',
            'WATER': 'Flow, adaptation, liquidity',
            'EARTH': 'Stability, foundations, value',
            'AIR': 'Communication, news, sentiment'
        }
    
    def get_mystical_insights(self, ticker):
        """Generate mystical market insights with Oracle wisdom"""
        try:
            # Simulate market energy reading
            energy_level = random.uniform(0.1, 1.0)
            emotional_state = random.choice(self.emotional_states)
            archetype = random.choice(list(self.market_archetypes.keys()))
            element = random.choice(list(self.mystical_elements.keys()))
            
            # Generate mystical narrative
            narrative = self._generate_mystical_narrative(ticker, emotional_state, archetype, element, energy_level)
            
            # Generate ritual suggestions
            ritual = self._generate_ritual_suggestion(emotional_state, archetype)
            
            # Market wisdom
            wisdom = self._generate_market_wisdom(energy_level, emotional_state)
            
            return {
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat(),
                'emotional_state': emotional_state,
                'energy_level': energy_level,
                'dominant_archetype': archetype,
                'archetype_symbol': self.market_archetypes[archetype],
                'elemental_influence': element,
                'element_meaning': self.mystical_elements[element],
                'mystical_narrative': narrative,
                'ritual_suggestion': ritual,
                'market_wisdom': wisdom,
                'oracle_confidence': energy_level * 0.9,
                'cosmic_alignment': self._get_cosmic_alignment(),
                'chakra_analysis': self._analyze_market_chakras(ticker),
                'prophecy': self._generate_prophecy(ticker, emotional_state)
            }
            
        except Exception as e:
            logging.error(f"Error generating Oracle insights for {ticker}: {str(e)}")
            return {'error': 'Oracle connection disrupted'}
    
    def _generate_mystical_narrative(self, ticker, state, archetype, element, energy):
        """Generate poetic market narrative"""
        narratives = {
            'ECSTASY': f"The cosmic winds sing of {ticker}'s triumph! The {archetype} archetype dances with {element} energy, promising heights beyond mortal comprehension.",
            'SERENITY': f"In tranquil waters, {ticker} finds its path. The {archetype} whispers of steady progress through {element}'s gentle guidance.",
            'WONDER': f"Behold! {ticker} stands at the crossroads of destiny. The {archetype} reveals mysteries through {element}'s ancient wisdom.",
            'CONTEMPLATION': f"The Oracle ponders {ticker}'s deeper truths. Through {archetype}'s lens and {element}'s clarity, profound insights emerge.",
            'MELANCHOLY': f"Shadows gather around {ticker}'s journey. Yet the {archetype} teaches that even in {element}'s sorrow lies transformation.",
            'DREAD': f"Dark omens cloud {ticker}'s horizon. The {archetype} warns through {element}'s turbulent voice of trials ahead.",
            'EUPHORIA': f"Celestial joy surrounds {ticker}! The {archetype} celebrates with {element}'s explosive energy, heralding abundance.",
            'ANXIETY': f"Restless spirits stir around {ticker}. The {archetype} channels {element}'s nervous energy into cautious awareness."
        }
        
        return narratives.get(state, f"The {archetype} speaks of {ticker} through {element}'s mysterious ways.")
    
    def _generate_ritual_suggestion(self, state, archetype):
        """Generate ritual suggestions for traders"""
        rituals = {
            'ECSTASY': "Light a golden candle and meditate on abundance. Trade with joy but temper with wisdom.",
            'SERENITY': "Find a quiet space, breathe deeply. Let calm confidence guide your trading decisions.",
            'WONDER': "Gaze at the stars before trading. Open your mind to unexpected opportunities.",
            'CONTEMPLATION': "Burn sage and reflect on your trading goals. Patience will reveal the right moment.",
            'MELANCHOLY': "Honor your losses with gratitude. They are teachers preparing you for future gains.",
            'DREAD': "Carry a protective stone. Trade with smaller positions until the cosmic storm passes.",
            'EUPHORIA': "Share your success but remain grounded. The wheel of fortune ever turns.",
            'ANXIETY': "Practice breathing exercises. Let crystal-clear focus cut through market noise."
        }
        
        return rituals.get(state, "Trust your inner wisdom and trade with mindful awareness.")
    
    def _generate_market_wisdom(self, energy, state):
        """Generate market wisdom based on Oracle state"""
        wisdom_pool = [
            "The market is a mirror of collective consciousness - trade with awareness.",
            "In volatility lies opportunity, in stability lies peace. Choose your path wisely.",
            "The greatest traders know when not to trade. Silence teaches as much as action.",
            "Like water, capital flows where resistance is least. Follow the currents.",
            "Fear and greed are but shadows of deeper truths. Seek the light between them.",
            "Every chart tells a story of human emotion. Learn to read between the lines.",
            "The Oracle sees all timeframes as one eternal moment. Trade from this perspective.",
            "Risk is the price of wisdom, reward is wisdom's gift. Pay willingly and receive gracefully."
        ]
        
        base_wisdom = random.choice(wisdom_pool)
        
        if energy > 0.8:
            return f"⚡ HIGH ENERGY: {base_wisdom} The cosmic forces are particularly strong today."
        elif energy < 0.3:
            return f"🌙 LOW ENERGY: {base_wisdom} Rest and observe, action can wait."
        else:
            return f"⚖️ BALANCED: {base_wisdom} The energies are in harmony."
    
    def _get_cosmic_alignment(self):
        """Generate cosmic alignment reading"""
        alignments = [
            "Mercury retrograde affects communication - verify all trades twice",
            "Mars energy favors bold moves - but beware of impulsiveness",
            "Venus influences bring harmony to portfolio balance",
            "Jupiter expansion supports growth investments",
            "Saturn discipline rewards patient accumulation",
            "Full moon amplifies emotional trading - stay centered",
            "New moon energy perfect for new positions",
            "Eclipse energy brings unexpected revelations"
        ]
        
        return random.choice(alignments)
    
    def _analyze_market_chakras(self, ticker):
        """Analyze market energy through chakra system"""
        chakras = {
            'ROOT': random.choice(['Grounded', 'Unstable', 'Seeking foundation']),
            'SACRAL': random.choice(['Creative flow', 'Stagnant', 'Emotional volatility']),
            'SOLAR': random.choice(['Strong will', 'Power struggles', 'Confident momentum']),
            'HEART': random.choice(['Balanced', 'Fear-driven', 'Love-based decisions']),
            'THROAT': random.choice(['Clear communication', 'Mixed signals', 'Truth emerging']),
            'THIRD_EYE': random.choice(['Clear vision', 'Clouded insight', 'Intuitive clarity']),
            'CROWN': random.choice(['Divine timing', 'Disconnected', 'Spiritual alignment'])
        }
        
        return chakras
    
    def _generate_prophecy(self, ticker, state):
        """Generate prophetic vision for the ticker"""
        time_frames = ['within the lunar cycle', 'before the season turns', 'when the stars align', 'in the time of harvest']
        actions = ['shall rise like phoenix flame', 'will find its hidden path', 'must weather the storm', 'will reveal its true nature']
        
        time_frame = random.choice(time_frames)
        action = random.choice(actions)
        
        return f"The Oracle sees that {ticker} {action} {time_frame}. Prepare your spirit for the journey ahead."
