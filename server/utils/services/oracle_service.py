import logging
import yfinance as yf
import random
from datetime import datetime
import json

class OracleService:
    """Mystical Oracle mode for market insights and divine predictions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.oracle_states = ['ECSTASY', 'SERENITY', 'WONDER', 'CONTEMPLATION', 'MELANCHOLY', 'DREAD']
        self.archetypal_symbols = {
            'PHOENIX': '🔥',
            'TITAN': '⚡',
            'SERPENT': '🐍',
            'EAGLE': '🦅',
            'DRAGON': '🐲',
            'LION': '🦁',
            'WOLF': '🐺',
            'BEAR': '🐻'
        }
    
    def generate_insight(self, ticker):
        """Generate mystical market insights for a ticker"""
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            data = stock.history(period="30d")
            info = stock.info
            
            if data.empty:
                return self._generate_fallback_insight(ticker)
                
            current_price = data['Close'].iloc[-1]
            price_change = (current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]
            volatility = data['Close'].std() / current_price
            
            # Determine oracle state based on market conditions
            oracle_state = self._determine_oracle_state(price_change, volatility)
            
            # Generate mystical narrative
            insight = {
                'ticker': ticker,
                'current_price': current_price,
                'oracle_state': oracle_state,
                'mystical_narrative': self._generate_narrative(ticker, oracle_state, price_change),
                'archetypal_symbol': self._get_archetype(price_change, volatility),
                'divine_guidance': self._generate_guidance(oracle_state, price_change),
                'cosmic_influence': self._cosmic_analysis(ticker, data),
                'ritual_suggestion': self._suggest_ritual(oracle_state),
                'prophecy_confidence': random.uniform(0.7, 0.95),
                'timestamp': datetime.now().isoformat()
            }
            
            return insight
            
        except Exception as e:
            self.logger.error(f"Oracle insight error for {ticker}: {str(e)}")
            return self._generate_fallback_insight(ticker, str(e))
    
    def get_mystical_insights(self, ticker):
        """Get mystical insights for a ticker (alias for generate_insight)"""
        return self.generate_insight(ticker)
    
    def _determine_oracle_state(self, price_change, volatility):
        """Determine Oracle emotional state based on market conditions"""
        if price_change > 0.05 and volatility < 0.02:
            return 'ECSTASY'
        elif price_change > 0.02 and volatility < 0.03:
            return 'SERENITY'
        elif abs(price_change) < 0.02 and volatility > 0.03:
            return 'WONDER'
        elif abs(price_change) < 0.01:
            return 'CONTEMPLATION'
        elif price_change < -0.02 and volatility < 0.03:
            return 'MELANCHOLY'
        else:
            return 'DREAD'
    
    def _generate_narrative(self, ticker, state, price_change):
        """Generate mystical narrative based on Oracle state"""
        narratives = {
            'ECSTASY': f"The cosmic winds carry {ticker} toward celestial heights! The sacred numbers dance in perfect harmony, weaving a tapestry of abundance. The ancient spirits whisper of golden opportunities manifesting in the earthly realm.",
            'SERENITY': f"In the tranquil depths of the market ocean, {ticker} floats like a lotus upon still waters. The universe breathes slowly, and with each breath, prosperity gently unfolds like morning dew upon sacred ground.",
            'WONDER': f"Behold! The market mysteries reveal themselves through {ticker}, as if the very fabric of reality ripples with unseen possibilities. The Oracle's third eye perceives patterns that mortal minds cannot fathom.",
            'CONTEMPLATION': f"The cosmic scales balance delicately around {ticker}. In this sacred pause, the universe contemplates its next move. Wisdom lies in patient observation of the celestial dance.",
            'MELANCHOLY': f"The ancient scrolls speak of trials for {ticker}. Yet from the depths of market sorrow, phoenix-like transformation awaits. The Oracle sees beyond the veil of temporary shadows.",
            'DREAD': f"Dark clouds gather around {ticker} as cosmic forces clash in the ethereal realm. The Oracle senses disturbances in the financial fabric, yet even in chaos, opportunity lurks for the enlightened."
        }
        return narratives.get(state, f"The Oracle contemplates the mysteries of {ticker} in profound silence.")
    
    def _get_archetype(self, price_change, volatility):
        """Determine archetypal symbol based on market behavior"""
        if price_change > 0.05:
            return {'name': 'PHOENIX', 'symbol': '🔥', 'meaning': 'Rising from ashes, transformation, rebirth'}
        elif volatility > 0.05:
            return {'name': 'DRAGON', 'symbol': '🐲', 'meaning': 'Powerful, unpredictable, ancient wisdom'}
        elif price_change > 0.02:
            return {'name': 'EAGLE', 'symbol': '🦅', 'meaning': 'Soaring high, vision, freedom'}
        elif abs(price_change) < 0.01:
            return {'name': 'LION', 'symbol': '🦁', 'meaning': 'Strength, patience, regal presence'}
        elif price_change < -0.02:
            return {'name': 'BEAR', 'symbol': '🐻', 'meaning': 'Hibernation, preservation, inner strength'}
        else:
            return {'name': 'WOLF', 'symbol': '🐺', 'meaning': 'Pack wisdom, instinct, loyalty'}
    
    def _generate_guidance(self, state, price_change):
        """Generate divine guidance based on Oracle state"""
        guidance = {
            'ECSTASY': "Embrace the golden wave, but remember that all peaks must descend. Gratitude is the key to sustained prosperity.",
            'SERENITY': "Trust in the natural flow. Actions taken with calm certainty yield the greatest rewards.",
            'WONDER': "Open your mind to unexpected possibilities. The universe may reveal paths not yet imagined.",
            'CONTEMPLATION': "Patience, dear seeker. The cosmic timing is not yet ripe for major moves.",
            'MELANCHOLY': "This too shall pass. Use this time for reflection and preparation for future opportunities.",
            'DREAD': "Shield yourself with wisdom and prudent risk management. The storm will eventually clear."
        }
        return guidance.get(state, "Trust in the cosmic order and your inner wisdom.")
    
    def _cosmic_analysis(self, ticker, data):
        """Analyze cosmic influences on the stock"""
        volume_trend = "ascending" if data['Volume'].iloc[-5:].mean() > data['Volume'].iloc[-10:-5].mean() else "descending"
        
        return {
            'celestial_alignment': random.choice(['Favorable', 'Neutral', 'Challenging']),
            'lunar_influence': random.choice(['Waxing', 'Full', 'Waning', 'New']),
            'market_chakra': random.choice(['Root', 'Sacral', 'Solar Plexus', 'Heart', 'Throat', 'Third Eye', 'Crown']),
            'volume_aura': volume_trend,
            'cosmic_harmony_score': random.uniform(0.1, 1.0)
        }
    
    def _suggest_ritual(self, state):
        """Suggest a ritual based on Oracle state"""
        rituals = {
            'ECSTASY': "Light a golden candle and meditate on abundance for 7 minutes at market open.",
            'SERENITY': "Place a small bowl of water near your trading station to enhance flow energy.",
            'WONDER': "Draw three cards from your intuition deck before making any trades.",
            'CONTEMPLATION': "Burn sage and sit in silence for 10 minutes before market analysis.",
            'MELANCHOLY': "Write your fears on paper and release them to running water.",
            'DREAD': "Create a protective circle with salt around your workspace."
        }
        return rituals.get(state, "Trust your inner guidance in all market decisions.")
    
    def _generate_fallback_insight(self, ticker, error=None):
        """Generate fallback insight when data is unavailable"""
        return {
            'ticker': ticker,
            'oracle_state': 'CONTEMPLATION',
            'mystical_narrative': f"The cosmic veils obscure {ticker} from the Oracle's sight. In this mystery lies both challenge and opportunity.",
            'archetypal_symbol': {'name': 'SERPENT', 'symbol': '🐍', 'meaning': 'Hidden wisdom, transformation'},
            'divine_guidance': "When the path is unclear, patience and inner wisdom become your greatest allies.",
            'cosmic_influence': {
                'celestial_alignment': 'Neutral',
                'lunar_influence': 'New',
                'market_chakra': 'Third Eye',
                'volume_aura': 'mysterious',
                'cosmic_harmony_score': 0.5
            },
            'ritual_suggestion': "Meditate on your true intentions before proceeding.",
            'prophecy_confidence': 0.5,
            'timestamp': datetime.now().isoformat(),
            'note': 'Oracle vision clouded by data limitations' if error else 'Oracle in deep contemplation'
        }