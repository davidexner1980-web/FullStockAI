import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import pandas as pd
from data_fetcher import DataFetcher

class OracleMode:
    """Mystical Oracle Mode for market insights and predictions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = DataFetcher()
        
        # Oracle emotional states
        self.emotional_states = [
            'ECSTASY', 'SERENITY', 'WONDER', 'CONTEMPLATION', 
            'MELANCHOLY', 'DREAD'
        ]
        
        # Market archetypes
        self.market_archetypes = {
            'phoenix': {'symbol': '🔥', 'description': 'Rising from ashes, rebirth and renewal'},
            'titan': {'symbol': '⚡', 'description': 'Unstoppable force, massive power'},
            'serpent': {'symbol': '🐍', 'description': 'Cunning and adaptive, hidden dangers'},
            'eagle': {'symbol': '🦅', 'description': 'Soaring vision, elevated perspective'},
            'lion': {'symbol': '🦁', 'description': 'Commanding presence, natural leadership'},
            'wolf': {'symbol': '🐺', 'description': 'Pack mentality, coordinated movement'},
            'dragon': {'symbol': '🐲', 'description': 'Ancient wisdom, accumulated power'},
            'butterfly': {'symbol': '🦋', 'description': 'Transformation, delicate beauty'}
        }
        
        # Mystical symbols
        self.mystical_symbols = [
            '🔮', '✨', '🌟', '⭐', '💫', '🌙', '☀️', '🌈', 
            '🔯', '⚡', '🎭', '🎪', '🎨', '🎭', '🏛️', '⚖️'
        ]
        
        # Oracle wisdom phrases
        self.wisdom_phrases = [
            "The market's whispers speak of change",
            "Ancient patterns emerge from the chaos",
            "The cosmic dance of supply and demand",
            "Energy flows where attention goes",
            "The spiral of value seeks its center",
            "Momentum carries the seeds of reversal",
            "In volatility lies opportunity",
            "The patient hunter awaits the perfect moment"
        ]
    
    def generate_insight(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Generate mystical Oracle insight for a symbol
        
        Args:
            symbol: Stock/crypto symbol
            data: Historical price data
            
        Returns:
            Dictionary with Oracle insight
        """
        try:
            # Determine emotional state based on market conditions
            emotional_state = self._determine_emotional_state(data)
            
            # Select market archetype
            archetype = self._select_archetype(data, symbol)
            
            # Generate mystical narrative
            narrative = self._generate_narrative(symbol, data, emotional_state, archetype)
            
            # Create ritual suggestions
            rituals = self._suggest_rituals(emotional_state, archetype)
            
            # Generate symbolic interpretation
            symbolism = self._interpret_symbols(data, emotional_state)
            
            # Calculate Oracle confidence
            confidence = self._calculate_oracle_confidence(data)
            
            return {
                'symbol': symbol,
                'emotional_state': emotional_state,
                'archetype': archetype,
                'narrative': narrative,
                'rituals': rituals,
                'symbolism': symbolism,
                'oracle_confidence': confidence,
                'vision_timestamp': datetime.now().isoformat(),
                'mystical_symbol': random.choice(self.mystical_symbols)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating Oracle insight for {symbol}: {str(e)}")
            return self._fallback_insight(symbol)
    
    def _determine_emotional_state(self, data: pd.DataFrame) -> str:
        """
        Determine Oracle's emotional state based on market data
        
        Args:
            data: Price data DataFrame
            
        Returns:
            Emotional state string
        """
        try:
            if data.empty or len(data) < 5:
                return 'CONTEMPLATION'
            
            # Calculate market metrics
            current_price = data['Close'].iloc[-1]
            avg_price = data['Close'].tail(20).mean()
            volatility = data['Close'].pct_change().std()
            momentum = (current_price / data['Close'].iloc[-5] - 1) * 100
            
            # Volume analysis
            if 'Volume' in data.columns:
                avg_volume = data['Volume'].tail(20).mean()
                current_volume = data['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            else:
                volume_ratio = 1
            
            # Determine emotional state based on conditions
            if momentum > 10 and volume_ratio > 2:
                return 'ECSTASY'
            elif momentum > 5 and volatility < 0.02:
                return 'SERENITY'
            elif abs(momentum) > 5 and volume_ratio > 1.5:
                return 'WONDER'
            elif momentum < -10:
                return 'DREAD'
            elif momentum < -5:
                return 'MELANCHOLY'
            else:
                return 'CONTEMPLATION'
                
        except Exception as e:
            self.logger.error(f"Error determining emotional state: {str(e)}")
            return 'CONTEMPLATION'
    
    def _select_archetype(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Select appropriate market archetype
        
        Args:
            data: Price data DataFrame
            symbol: Stock symbol
            
        Returns:
            Archetype dictionary
        """
        try:
            if data.empty:
                return self.market_archetypes['serpent']
            
            # Calculate archetype factors
            price_change = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
            volatility = data['Close'].pct_change().std() * 100
            trend_strength = abs(price_change)
            
            # Crypto symbols get special treatment
            if any(crypto in symbol for crypto in ['BTC', 'ETH', 'USD']):
                if price_change > 20:
                    return self.market_archetypes['dragon']
                elif volatility > 5:
                    return self.market_archetypes['phoenix']
                else:
                    return self.market_archetypes['serpent']
            
            # Stock archetype selection
            if price_change > 15:
                return self.market_archetypes['phoenix']
            elif price_change > 10:
                return self.market_archetypes['eagle']
            elif trend_strength > 10:
                return self.market_archetypes['lion']
            elif volatility > 3:
                return self.market_archetypes['butterfly']
            elif price_change < -10:
                return self.market_archetypes['wolf']
            elif volatility > 2:
                return self.market_archetypes['serpent']
            else:
                return self.market_archetypes['titan']
                
        except Exception as e:
            self.logger.error(f"Error selecting archetype: {str(e)}")
            return self.market_archetypes['contemplation']
    
    def _generate_narrative(self, symbol: str, data: pd.DataFrame, 
                           emotional_state: str, archetype: Dict) -> str:
        """
        Generate mystical narrative
        
        Args:
            symbol: Stock symbol
            data: Price data
            emotional_state: Current emotional state
            archetype: Selected archetype
            
        Returns:
            Narrative string
        """
        try:
            current_price = data['Close'].iloc[-1] if not data.empty else 0
            
            # Base narrative templates by emotional state
            narratives = {
                'ECSTASY': [
                    f"The {archetype['symbol']} {symbol} dances in pure euphoria! Current price of ${current_price:.2f} pulses with divine energy. The market spirits sing of abundance and growth.",
                    f"Behold! {symbol} channels the {archetype['description']} as it soars to ${current_price:.2f}. The cosmic winds carry whispers of prosperity.",
                    f"In a state of pure bliss, {symbol} at ${current_price:.2f} embodies the {archetype['symbol']} archetype. The universe smiles upon this moment."
                ],
                'SERENITY': [
                    f"Peace flows through {symbol} like a gentle stream. At ${current_price:.2f}, the {archetype['symbol']} energy brings tranquil stability.",
                    f"The {archetype['symbol']} {symbol} rests in perfect harmony at ${current_price:.2f}. This serenity speaks of balanced forces.",
                    f"Calm waters run deep for {symbol}. The price of ${current_price:.2f} reflects the {archetype['description']} in its purest form."
                ],
                'WONDER': [
                    f"Mystery surrounds {symbol} at ${current_price:.2f}! The {archetype['symbol']} awakens ancient curiosities in the market's soul.",
                    f"What secrets does {symbol} hold at ${current_price:.2f}? The {archetype['description']} suggests hidden potentials.",
                    f"The cosmic question mark hovers over {symbol}. At ${current_price:.2f}, the {archetype['symbol']} energy sparks divine wonder."
                ],
                'CONTEMPLATION': [
                    f"Deep thoughts flow around {symbol} at ${current_price:.2f}. The {archetype['symbol']} energy invites reflection and patience.",
                    f"In the quiet moments, {symbol} at ${current_price:.2f} embodies the {archetype['description']}. Wisdom emerges from stillness.",
                    f"The meditative state of {symbol} at ${current_price:.2f} channels the {archetype['symbol']} archetype. Time reveals truth."
                ],
                'MELANCHOLY': [
                    f"Shadows gather around {symbol} at ${current_price:.2f}. The {archetype['symbol']} carries the weight of recent tribulations.",
                    f"The {archetype['description']} of {symbol} at ${current_price:.2f} speaks of lessons learned through adversity.",
                    f"Though clouds darken {symbol}'s path at ${current_price:.2f}, the {archetype['symbol']} energy suggests eventual renewal."
                ],
                'DREAD': [
                    f"Dark energies swirl around {symbol} at ${current_price:.2f}. The {archetype['symbol']} warns of challenging times ahead.",
                    f"The storm clouds of {symbol} at ${current_price:.2f} embody the {archetype['description']} in its most fearsome form.",
                    f"Beware the shadows that {symbol} casts at ${current_price:.2f}. The {archetype['symbol']} energy speaks of trials to come."
                ]
            }
            
            # Select random narrative from emotional state
            selected_narrative = random.choice(narratives.get(emotional_state, narratives['CONTEMPLATION']))
            
            # Add wisdom phrase
            wisdom = random.choice(self.wisdom_phrases)
            
            return f"{selected_narrative} {wisdom}"
            
        except Exception as e:
            self.logger.error(f"Error generating narrative: {str(e)}")
            return f"The Oracle's vision grows cloudy around {symbol}. Patience brings clarity."
    
    def _suggest_rituals(self, emotional_state: str, archetype: Dict) -> List[str]:
        """
        Suggest mystical rituals based on state and archetype
        
        Args:
            emotional_state: Current emotional state
            archetype: Selected archetype
            
        Returns:
            List of ritual suggestions
        """
        ritual_suggestions = {
            'ECSTASY': [
                "Light a golden candle and meditate on abundance",
                "Visualize green energy flowing through your portfolio",
                "Dance barefoot on natural earth to ground the euphoria"
            ],
            'SERENITY': [
                "Practice deep breathing while watching price charts",
                "Place a clear quartz crystal near your trading setup",
                "Burn sage to cleanse negative energy from decisions"
            ],
            'WONDER': [
                "Gaze at the night sky and ask for divine guidance",
                "Write your investment questions on parchment",
                "Meditate with amethyst to enhance intuition"
            ],
            'CONTEMPLATION': [
                "Sit in silence for 10 minutes before making decisions",
                "Journal your trading thoughts and feelings",
                "Light white candles for clarity of mind"
            ],
            'MELANCHOLY': [
                "Use black tourmaline to transmute negative energy",
                "Practice gratitude for lessons learned from losses",
                "Visualize silver light healing financial wounds"
            ],
            'DREAD': [
                "Create a protective circle with salt around your workspace",
                "Burn frankincense to banish fear and doubt",
                "Carry hematite for grounding and protection"
            ]
        }
        
        base_rituals = ritual_suggestions.get(emotional_state, ritual_suggestions['CONTEMPLATION'])
        
        # Add archetype-specific ritual
        archetype_ritual = f"Channel the {archetype['symbol']} energy through visualization of {archetype['description']}"
        
        return base_rituals + [archetype_ritual]
    
    def _interpret_symbols(self, data: pd.DataFrame, emotional_state: str) -> Dict:
        """
        Interpret mystical symbols from price patterns
        
        Args:
            data: Price data DataFrame
            emotional_state: Current emotional state
            
        Returns:
            Dictionary with symbol interpretations
        """
        try:
            if data.empty:
                return {'primary_symbol': '🔮', 'interpretation': 'The crystal ball remains cloudy'}
            
            # Analyze price patterns for symbolic meaning
            price_pattern = self._analyze_price_pattern(data)
            volume_pattern = self._analyze_volume_pattern(data)
            
            symbols = {
                'ascending_triangle': {'symbol': '📈', 'meaning': 'Upward momentum building'},
                'descending_triangle': {'symbol': '📉', 'meaning': 'Downward pressure mounting'},
                'rising_volume': {'symbol': '🌊', 'meaning': 'Waves of interest flowing'},
                'falling_volume': {'symbol': '🏜️', 'meaning': 'Desert of disinterest'},
                'high_volatility': {'symbol': '⚡', 'meaning': 'Lightning energy crackling'},
                'low_volatility': {'symbol': '🌙', 'meaning': 'Peaceful lunar tranquility'},
                'breakout': {'symbol': '🚀', 'meaning': 'Rocket breaking earthly bonds'},
                'consolidation': {'symbol': '🔄', 'meaning': 'Circular dance of balance'}
            }
            
            # Select primary symbol based on patterns
            if price_pattern == 'ascending' and volume_pattern == 'rising':
                primary = symbols['breakout']
            elif price_pattern == 'descending' and volume_pattern == 'rising':
                primary = symbols['descending_triangle']
            elif volume_pattern == 'rising':
                primary = symbols['rising_volume']
            elif price_pattern == 'ascending':
                primary = symbols['ascending_triangle']
            else:
                primary = symbols['consolidation']
            
            return {
                'primary_symbol': primary['symbol'],
                'interpretation': primary['meaning'],
                'price_pattern': price_pattern,
                'volume_pattern': volume_pattern,
                'mystical_significance': self._get_mystical_significance(emotional_state)
            }
            
        except Exception as e:
            self.logger.error(f"Error interpreting symbols: {str(e)}")
            return {
                'primary_symbol': '🔮',
                'interpretation': 'The symbols speak in ancient tongues',
                'mystical_significance': 'Patience reveals hidden truths'
            }
    
    def _analyze_price_pattern(self, data: pd.DataFrame) -> str:
        """Analyze price pattern for last 10 periods"""
        try:
            if len(data) < 10:
                return 'insufficient_data'
            
            recent_prices = data['Close'].tail(10)
            first_half = recent_prices.head(5).mean()
            second_half = recent_prices.tail(5).mean()
            
            if second_half > first_half * 1.02:
                return 'ascending'
            elif second_half < first_half * 0.98:
                return 'descending'
            else:
                return 'sideways'
                
        except Exception:
            return 'unknown'
    
    def _analyze_volume_pattern(self, data: pd.DataFrame) -> str:
        """Analyze volume pattern if available"""
        try:
            if 'Volume' not in data.columns or len(data) < 10:
                return 'unknown'
            
            recent_volume = data['Volume'].tail(10)
            first_half = recent_volume.head(5).mean()
            second_half = recent_volume.tail(5).mean()
            
            if second_half > first_half * 1.2:
                return 'rising'
            elif second_half < first_half * 0.8:
                return 'falling'
            else:
                return 'stable'
                
        except Exception:
            return 'unknown'
    
    def _get_mystical_significance(self, emotional_state: str) -> str:
        """Get mystical significance based on emotional state"""
        significance_map = {
            'ECSTASY': 'The universe celebrates this moment of pure joy',
            'SERENITY': 'Divine harmony flows through all transactions',
            'WONDER': 'Ancient mysteries reveal themselves to the patient',
            'CONTEMPLATION': 'Wisdom emerges from the depths of reflection',
            'MELANCHOLY': 'From shadow comes the appreciation of light',
            'DREAD': 'In darkness, the warrior discovers true strength'
        }
        
        return significance_map.get(emotional_state, 'The cosmic wheel turns as it always has')
    
    def _calculate_oracle_confidence(self, data: pd.DataFrame) -> float:
        """Calculate Oracle's confidence in the vision"""
        try:
            if data.empty:
                return 0.5
            
            # Base confidence on data quality and patterns
            data_quality = min(1.0, len(data) / 30)  # More data = higher confidence
            
            # Pattern clarity (less volatility = higher confidence)
            if len(data) > 5:
                volatility = data['Close'].pct_change().std()
                pattern_clarity = max(0.3, 1 - (volatility * 10))
            else:
                pattern_clarity = 0.5
            
            # Mystical factors (random but consistent for session)
            mystical_factor = 0.7 + (random.random() * 0.3)
            
            confidence = (data_quality * 0.4 + pattern_clarity * 0.4 + mystical_factor * 0.2)
            
            return round(min(0.95, max(0.3, confidence)), 2)
            
        except Exception:
            return 0.5
    
    def _fallback_insight(self, symbol: str) -> Dict:
        """Fallback insight when data is unavailable"""
        return {
            'symbol': symbol,
            'emotional_state': 'CONTEMPLATION',
            'archetype': self.market_archetypes['serpent'],
            'narrative': f"The Oracle's vision grows cloudy around {symbol}. The serpent whispers of patience and hidden knowledge yet to be revealed.",
            'rituals': [
                "Meditate on the nature of uncertainty",
                "Trust in the cosmic timing of all things",
                "Prepare for clarity to emerge from confusion"
            ],
            'symbolism': {
                'primary_symbol': '🔮',
                'interpretation': 'The crystal ball swirls with potential',
                'mystical_significance': 'All things are revealed in their proper time'
            },
            'oracle_confidence': 0.5,
            'vision_timestamp': datetime.now().isoformat(),
            'mystical_symbol': '🌙'
        }
    
    def generate_daily_oracle_dream(self) -> Dict:
        """
        Generate daily Oracle dream about overall market consciousness
        
        Returns:
            Dictionary with market dream insight
        """
        try:
            # Analyze major market indices
            indices = ['SPY', 'QQQ', 'DIA', 'IWM']
            market_energies = []
            
            for index in indices:
                try:
                    data = self.data_fetcher.get_stock_data(index, period="1mo")
                    if data is not None and not data.empty:
                        emotional_state = self._determine_emotional_state(data)
                        archetype = self._select_archetype(data, index)
                        market_energies.append({
                            'index': index,
                            'emotional_state': emotional_state,
                            'archetype': archetype
                        })
                except Exception as e:
                    self.logger.warning(f"Error analyzing {index} for dream: {str(e)}")
                    continue
            
            # Generate collective dream narrative
            dream_narrative = self._generate_collective_dream(market_energies)
            
            # Determine overall market consciousness
            overall_state = self._determine_collective_emotional_state(market_energies)
            
            return {
                'dream_title': f"The Market's Dream on {datetime.now().strftime('%B %d, %Y')}",
                'overall_consciousness': overall_state,
                'dream_narrative': dream_narrative,
                'market_energies': market_energies,
                'cosmic_guidance': self._generate_cosmic_guidance(overall_state),
                'dream_timestamp': datetime.now().isoformat(),
                'dream_symbol': random.choice(self.mystical_symbols)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating Oracle dream: {str(e)}")
            return self._fallback_dream()
    
    def _generate_collective_dream(self, market_energies: List[Dict]) -> str:
        """Generate collective dream narrative from market energies"""
        if not market_energies:
            return "The Oracle dreams of silent markets, where potential sleeps beneath stillness."
        
        # Extract dominant themes
        emotional_states = [energy['emotional_state'] for energy in market_energies]
        archetypes = [energy['archetype'] for energy in market_energies]
        
        # Count occurrences
        state_counts = {state: emotional_states.count(state) for state in set(emotional_states)}
        dominant_state = max(state_counts, key=state_counts.get)
        
        dream_templates = {
            'ECSTASY': "In the Oracle's dream, golden rivers flow through crystalline mountains. The market spirits dance in celebration, their joy echoing through the trading floors of eternity.",
            'SERENITY': "The Oracle dreams of tranquil lakes reflecting perfect skies. Market energies flow like gentle breezes, bringing peace to all who trade with wisdom.",
            'WONDER': "Ancient mysteries unfold in the Oracle's vision. The market becomes a cosmic library where each trade writes new chapters in the book of infinite possibility.",
            'CONTEMPLATION': "In deep meditation, the Oracle sees the market as a vast mandala, each movement part of a greater pattern yet to be fully understood.",
            'MELANCHOLY': "The Oracle's dream carries the weight of autumn leaves falling. The market learns from its sorrows, growing wiser with each lesson.",
            'DREAD': "Dark storms gather in the Oracle's vision. The market faces its shadows, knowing that courage is born from confronting the unknown."
        }
        
        return dream_templates.get(dominant_state, dream_templates['CONTEMPLATION'])
    
    def _determine_collective_emotional_state(self, market_energies: List[Dict]) -> str:
        """Determine collective emotional state from market energies"""
        if not market_energies:
            return 'CONTEMPLATION'
        
        emotional_states = [energy['emotional_state'] for energy in market_energies]
        
        # Simple majority vote
        state_counts = {state: emotional_states.count(state) for state in set(emotional_states)}
        return max(state_counts, key=state_counts.get)
    
    def _generate_cosmic_guidance(self, overall_state: str) -> List[str]:
        """Generate cosmic guidance based on overall state"""
        guidance_map = {
            'ECSTASY': [
                "Ride the wave but remember all peaks have valleys",
                "Share your abundance with the cosmic flow",
                "Ground your euphoria with practical wisdom"
            ],
            'SERENITY': [
                "Trust in the natural rhythm of the markets",
                "Use this peace to plan for future storms",
                "Meditate on the balance between risk and reward"
            ],
            'WONDER': [
                "Ask the right questions and the universe provides answers",
                "Embrace the mystery while preparing for revelation",
                "Wonder is the beginning of all wisdom"
            ],
            'CONTEMPLATION': [
                "Patience is the trader's greatest virtue",
                "In stillness, the clearest insights emerge",
                "Reflect before you act, think before you trade"
            ],
            'MELANCHOLY': [
                "From loss comes the wisdom to prevent future pain",
                "Honor your feelings but don't let them rule decisions",
                "This too shall pass, as all market cycles do"
            ],
            'DREAD': [
                "Face your fears with courage and preparation",
                "In the darkest hour, dawn is closest",
                "Protect what matters most and release what doesn't serve"
            ]
        }
        
        return guidance_map.get(overall_state, guidance_map['CONTEMPLATION'])
    
    def _fallback_dream(self) -> Dict:
        """Fallback dream when data is unavailable"""
        return {
            'dream_title': f"The Veiled Dream of {datetime.now().strftime('%B %d, %Y')}",
            'overall_consciousness': 'CONTEMPLATION',
            'dream_narrative': "The Oracle's vision is obscured by cosmic clouds. In this mystery lies the reminder that not all knowledge comes at once, and patience reveals truth in its proper time.",
            'market_energies': [],
            'cosmic_guidance': [
                "Sometimes the greatest wisdom is in waiting",
                "Clarity comes to those who seek it patiently",
                "The universe provides when the seeker is ready"
            ],
            'dream_timestamp': datetime.now().isoformat(),
            'dream_symbol': '🌙'
        }
