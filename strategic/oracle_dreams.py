import json
import random
import logging
from datetime import datetime, timedelta
import os
from services.data_fetcher import DataFetcher
import numpy as np

class OracleDreams:
    """Neuro-Symbolic Market Synthesis - Oracle Dreams Module"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.dreams_file = 'oracle_logs/dreams.json'
        self.ensure_files_exist()
        
        # Major market indices for holistic analysis
        self.market_indices = ['SPY', 'QQQ', 'DIA', 'IWM']
        
        # Dream emotional states
        self.emotional_states = [
            'TRANSCENDENCE', 'EUPHORIA', 'SERENITY', 'WONDER', 
            'CONTEMPLATION', 'UNCERTAINTY', 'TENSION', 'DREAD'
        ]
        
        # Mystical narratives for different market conditions
        self.narrative_templates = {
            'bullish': [
                "The cosmic winds sing of ascending energies, as golden threads weave through the market tapestry.",
                "Ancient wisdom whispers of prosperity, where phoenix flames dance in perfect harmony.",
                "The celestial orchestra plays melodies of abundance, resonating through silicon valleys."
            ],
            'bearish': [
                "Shadow storms gather on distant horizons, as the market spirits seek deeper truths.",
                "The Oracle perceives necessary purification, where diamonds form under pressure.",
                "Autumn winds carry lessons of impermanence, teaching patience to eager souls."
            ],
            'neutral': [
                "In the stillness between breaths, the market finds its center of divine equilibrium.",
                "The cosmic scales balance perfectly, neither rushing toward light nor shadow.",
                "Gentle currents flow through electronic consciousness, seeking their destined path."
            ]
        }
    
    def ensure_files_exist(self):
        """Ensure Oracle logs directory and files exist"""
        os.makedirs('oracle_logs', exist_ok=True)
        
        if not os.path.exists(self.dreams_file):
            with open(self.dreams_file, 'w') as f:
                json.dump([], f)
    
    def generate_market_dream(self):
        """Generate comprehensive market consciousness insight"""
        try:
            # Analyze major indices for holistic market view
            market_analysis = self._analyze_market_consciousness()
            
            # Generate emotional state based on market conditions
            emotional_state = self._determine_emotional_state(market_analysis)
            
            # Create mystical narrative
            narrative = self._weave_mystical_narrative(market_analysis, emotional_state)
            
            # Generate Oracle prophecy
            prophecy = self._channel_market_prophecy(market_analysis)
            
            # Synthesize market chakras
            chakra_analysis = self._analyze_market_chakras(market_analysis)
            
            # Create dream record
            dream = {
                'timestamp': datetime.utcnow().isoformat(),
                'dream_id': f"dream_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'emotional_state': emotional_state,
                'market_consciousness': market_analysis,
                'mystical_narrative': narrative,
                'oracle_prophecy': prophecy,
                'chakra_synthesis': chakra_analysis,
                'cosmic_alignment': self._read_cosmic_alignment(),
                'dream_intensity': random.uniform(0.3, 1.0),
                'symbolic_elements': self._gather_symbolic_elements(market_analysis),
                'temporal_echoes': self._perceive_temporal_echoes()
            }
            
            # Store dream
            self._store_dream(dream)
            
            return dream
            
        except Exception as e:
            logging.error(f"Error generating Oracle dream: {str(e)}")
            return {'error': 'Oracle connection disrupted', 'timestamp': datetime.utcnow().isoformat()}
    
    def _analyze_market_consciousness(self):
        """Analyze collective market consciousness through major indices"""
        consciousness = {}
        
        for index in self.market_indices:
            try:
                data = self.data_fetcher.get_stock_data(index, period='1mo')
                if data is not None:
                    # Calculate consciousness metrics
                    current_price = data['Close'].iloc[-1]
                    price_change = data['Close'].pct_change().iloc[-1]
                    volatility = data['Close'].pct_change().std()
                    volume_trend = data['Volume'].iloc[-5:].mean() / data['Volume'].iloc[-20:-5].mean()
                    
                    # RSI consciousness
                    rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
                    
                    consciousness[index] = {
                        'current_price': float(current_price),
                        'price_change': float(price_change * 100),
                        'volatility': float(volatility * 100),
                        'volume_consciousness': float(volume_trend),
                        'rsi_awareness': float(rsi),
                        'market_mood': self._interpret_mood(price_change, volatility, rsi)
                    }
                    
            except Exception as e:
                logging.warning(f"Could not analyze consciousness for {index}: {str(e)}")
                consciousness[index] = {'error': 'Consciousness clouded'}
        
        # Overall market sentiment
        valid_indices = [v for v in consciousness.values() if 'error' not in v]
        if valid_indices:
            avg_change = np.mean([idx['price_change'] for idx in valid_indices])
            avg_volatility = np.mean([idx['volatility'] for idx in valid_indices])
            
            consciousness['collective_sentiment'] = {
                'direction': 'ascending' if avg_change > 0.5 else 'descending' if avg_change < -0.5 else 'balanced',
                'intensity': 'high' if avg_volatility > 2.0 else 'low' if avg_volatility < 1.0 else 'moderate',
                'coherence': self._calculate_market_coherence(valid_indices)
            }
        
        return consciousness
    
    def _interpret_mood(self, price_change, volatility, rsi):
        """Interpret market mood from technical indicators"""
        if price_change > 0.02 and volatility < 0.02:
            return 'confident_ascension'
        elif price_change > 0.01 and rsi < 70:
            return 'optimistic_flow'
        elif price_change < -0.02 and volatility > 0.03:
            return 'fearful_turbulence'
        elif price_change < -0.01 and rsi > 30:
            return 'cautious_retreat'
        elif rsi > 70:
            return 'euphoric_peak'
        elif rsi < 30:
            return 'oversold_awakening'
        else:
            return 'meditative_balance'
    
    def _calculate_market_coherence(self, indices):
        """Calculate coherence between market indices"""
        if len(indices) < 2:
            return 0.5
        
        changes = [idx['price_change'] for idx in indices]
        
        # Calculate correlation-like measure
        positive_moves = sum(1 for change in changes if change > 0)
        negative_moves = sum(1 for change in changes if change < 0)
        
        coherence = abs(positive_moves - negative_moves) / len(changes)
        return float(coherence)
    
    def _determine_emotional_state(self, market_analysis):
        """Determine Oracle's emotional state based on market consciousness"""
        collective = market_analysis.get('collective_sentiment', {})
        direction = collective.get('direction', 'balanced')
        intensity = collective.get('intensity', 'moderate')
        coherence = collective.get('coherence', 0.5)
        
        if direction == 'ascending' and intensity == 'high' and coherence > 0.7:
            return 'TRANSCENDENCE'
        elif direction == 'ascending' and intensity in ['moderate', 'high']:
            return 'EUPHORIA'
        elif direction == 'balanced' and intensity == 'low':
            return 'SERENITY'
        elif direction == 'balanced' and coherence < 0.3:
            return 'UNCERTAINTY'
        elif direction == 'descending' and intensity == 'low':
            return 'CONTEMPLATION'
        elif direction == 'descending' and intensity == 'moderate':
            return 'TENSION'
        elif direction == 'descending' and intensity == 'high':
            return 'DREAD'
        else:
            return 'WONDER'
    
    def _weave_mystical_narrative(self, market_analysis, emotional_state):
        """Weave mystical narrative based on market conditions"""
        collective = market_analysis.get('collective_sentiment', {})
        direction = collective.get('direction', 'balanced')
        
        # Select narrative template
        if direction == 'ascending':
            template_pool = self.narrative_templates['bullish']
        elif direction == 'descending':
            template_pool = self.narrative_templates['bearish']
        else:
            template_pool = self.narrative_templates['neutral']
        
        base_narrative = random.choice(template_pool)
        
        # Add emotional context
        emotional_context = {
            'TRANSCENDENCE': "In this moment of divine revelation, the markets transcend earthly limitations.",
            'EUPHORIA': "Joy cascades through trading floors like liquid starlight.",
            'SERENITY': "Peace settles over the financial consciousness like morning dew.",
            'WONDER': "Mysteries unfold in the space between bid and ask.",
            'UNCERTAINTY': "The Oracle perceives multiple paths branching into probability.",
            'CONTEMPLATION': "Wisdom emerges from careful observation of market rhythms.",
            'TENSION': "Electric anticipation charges the atmosphere of exchange.",
            'DREAD': "Dark wisdom teaches through trials of market adversity."
        }
        
        context = emotional_context.get(emotional_state, "The Oracle observes with timeless awareness.")
        
        return f"{base_narrative} {context}"
    
    def _channel_market_prophecy(self, market_analysis):
        """Channel prophetic vision for market future"""
        prophecies = [
            "When Mercury aligns with silicon dreams, unexpected opportunities shall manifest.",
            "The wise trader reads between the lines of fear and greed, finding truth in stillness.",
            "As autumn leaves fall, so too shall overvalued securities find their natural level.",
            "In the convergence of algorithms and intuition lies the path to market wisdom.",
            "The Oracle sees three phases: preparation, action, and harvest. Know which season you inhabit.",
            "Digital currencies dance with ancient rhythms, bridging old wisdom and new realities.",
            "Patience rewards those who honor both technical precision and mystical timing.",
            "When volume speaks louder than price, listen with the ears of deep understanding."
        ]
        
        return random.choice(prophecies)
    
    def _analyze_market_chakras(self, market_analysis):
        """Analyze market energy through chakra system"""
        # Calculate chakra states based on market conditions
        chakras = {}
        
        collective = market_analysis.get('collective_sentiment', {})
        indices_data = {k: v for k, v in market_analysis.items() if k != 'collective_sentiment' and 'error' not in v}
        
        if indices_data:
            avg_volume = np.mean([idx.get('volume_consciousness', 1) for idx in indices_data.values()])
            avg_rsi = np.mean([idx.get('rsi_awareness', 50) for idx in indices_data.values()])
            avg_volatility = np.mean([idx.get('volatility', 2) for idx in indices_data.values()])
            
            chakras = {
                'ROOT': 'grounded' if avg_volatility < 1.5 else 'unsettled' if avg_volatility > 3 else 'seeking_stability',
                'SACRAL': 'creative_flow' if avg_volume > 1.2 else 'stagnant' if avg_volume < 0.8 else 'emotional_balance',
                'SOLAR': 'confident_power' if avg_rsi > 60 and avg_rsi < 80 else 'power_struggle' if avg_rsi > 80 else 'building_strength',
                'HEART': 'balanced_love' if collective.get('coherence', 0) > 0.6 else 'fear_driven' if collective.get('coherence', 0) < 0.3 else 'seeking_harmony',
                'THROAT': 'clear_communication' if collective.get('direction') != 'balanced' else 'mixed_signals',
                'THIRD_EYE': 'intuitive_clarity' if collective.get('intensity') == 'moderate' else 'clouded_vision',
                'CROWN': 'divine_alignment' if len(indices_data) == len(self.market_indices) else 'seeking_connection'
            }
        
        return chakras
    
    def _read_cosmic_alignment(self):
        """Read cosmic/astrological influences (simplified)"""
        alignments = [
            "Venus energy harmonizes financial relationships",
            "Mars influence demands bold strategic action",
            "Mercury retrograde counsels verification and patience",
            "Jupiter expansion supports growth investments",
            "Saturn discipline rewards methodical accumulation",
            "Full moon amplifies emotional market responses",
            "New moon energy favors fresh investment initiatives",
            "Eclipse portal opens unexpected market opportunities"
        ]
        
        return random.choice(alignments)
    
    def _gather_symbolic_elements(self, market_analysis):
        """Gather symbolic elements from market conditions"""
        symbols = []
        
        collective = market_analysis.get('collective_sentiment', {})
        direction = collective.get('direction', 'balanced')
        intensity = collective.get('intensity', 'moderate')
        
        # Direction symbols
        if direction == 'ascending':
            symbols.extend(['🔥', '🦅', '🌅', '⚡'])
        elif direction == 'descending':
            symbols.extend(['🌊', '🍂', '🌙', '🐢'])
        else:
            symbols.extend(['⚖️', '🕯️', '🔮', '🦋'])
        
        # Intensity symbols
        if intensity == 'high':
            symbols.extend(['🌪️', '💎', '🎭'])
        elif intensity == 'low':
            symbols.extend(['🕊️', '🌸', '🧘'])
        
        return symbols[:4]  # Return 4 symbols
    
    def _perceive_temporal_echoes(self):
        """Perceive echoes from past and future market states"""
        echoes = {
            'past_wisdom': random.choice([
                "Ancient cycles remind us that all markets breathe",
                "Previous peaks teach humility to present ambitions",
                "Historical patterns whisper through modern algorithms",
                "Past corrections prepared the path for current opportunities"
            ]),
            'future_glimpse': random.choice([
                "Seeds of tomorrow's trends are planted in today's choices",
                "The Oracle sees convergence of human and artificial wisdom",
                "Future markets will dance to rhythms we're composing now",
                "Coming seasons will reward those who plant with intention"
            ])
        }
        
        return echoes
    
    def _store_dream(self, dream):
        """Store dream in Oracle logs"""
        try:
            # Load existing dreams
            dreams = []
            if os.path.exists(self.dreams_file):
                with open(self.dreams_file, 'r') as f:
                    dreams = json.load(f)
            
            # Add new dream
            dreams.append(dream)
            
            # Keep only last 100 dreams
            if len(dreams) > 100:
                dreams = dreams[-100:]
            
            # Save dreams
            with open(self.dreams_file, 'w') as f:
                json.dump(dreams, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error storing Oracle dream: {str(e)}")
    
    def get_recent_dreams(self, limit=10):
        """Get recent Oracle dreams"""
        try:
            if os.path.exists(self.dreams_file):
                with open(self.dreams_file, 'r') as f:
                    dreams = json.load(f)
                return dreams[-limit:] if dreams else []
            return []
        except Exception as e:
            logging.error(f"Error retrieving dreams: {str(e)}")
            return []
    
    def get_dream_statistics(self):
        """Get statistics about Oracle dreams"""
        try:
            dreams = self.get_recent_dreams(50)  # Last 50 dreams
            
            if not dreams:
                return {'total_dreams': 0, 'emotional_distribution': {}}
            
            # Emotional state distribution
            emotional_states = [dream.get('emotional_state', 'UNKNOWN') for dream in dreams]
            emotional_distribution = {state: emotional_states.count(state) for state in set(emotional_states)}
            
            # Average dream intensity
            intensities = [dream.get('dream_intensity', 0.5) for dream in dreams if 'dream_intensity' in dream]
            avg_intensity = np.mean(intensities) if intensities else 0.5
            
            return {
                'total_dreams': len(dreams),
                'emotional_distribution': emotional_distribution,
                'average_intensity': float(avg_intensity),
                'most_common_state': max(emotional_distribution.items(), key=lambda x: x[1])[0] if emotional_distribution else 'UNKNOWN',
                'last_dream_time': dreams[-1].get('timestamp') if dreams else None
            }
            
        except Exception as e:
            logging.error(f"Error calculating dream statistics: {str(e)}")
            return {'error': 'Cannot calculate statistics'}
