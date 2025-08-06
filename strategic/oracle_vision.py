import random
import json
import os
import logging
from datetime import datetime, timedelta
from ml_models.data_fetcher import DataFetcher

class OracleVision:
    """Archetype-based Analysis and Oracle Vision System"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.archetypes = {
            'Phoenix': {
                'symbol': '🔥',
                'element': 'Fire',
                'traits': ['Transformation', 'Rebirth', 'Rising from ashes'],
                'market_interpretation': 'Recovery and transformation after decline',
                'emotional_states': ['ECSTASY', 'WONDER', 'SERENITY'],
                'sectors': ['Technology', 'Biotech', 'Renewable Energy']
            },
            'Titan': {
                'symbol': '⚡',
                'element': 'Earth',
                'traits': ['Strength', 'Dominance', 'Unwavering power'],
                'market_interpretation': 'Market leadership and sustained growth',
                'emotional_states': ['ECSTASY', 'SERENITY', 'CONTEMPLATION'],
                'sectors': ['Large Cap', 'Blue Chip', 'Infrastructure']
            },
            'Serpent': {
                'symbol': '🐍',
                'element': 'Water',
                'traits': ['Hidden knowledge', 'Coiled potential', 'Transformation'],
                'market_interpretation': 'Underlying currents and hidden opportunities',
                'emotional_states': ['WONDER', 'CONTEMPLATION', 'MELANCHOLY'],
                'sectors': ['Healthcare', 'Pharmaceuticals', 'Emerging Markets']
            },
            'Oracle': {
                'symbol': '🔮',
                'element': 'Spirit',
                'traits': ['Wisdom', 'Foresight', 'Divine insight'],
                'market_interpretation': 'Perfect market timing and prophetic insights',
                'emotional_states': ['CONTEMPLATION', 'SERENITY', 'WONDER'],
                'sectors': ['Financial Services', 'Consulting', 'AI/Tech']
            },
            'Storm': {
                'symbol': '⛈️',
                'element': 'Air',
                'traits': ['Chaos', 'Opportunity', 'Destructive creation'],
                'market_interpretation': 'Volatility brings both risk and reward',
                'emotional_states': ['DREAD', 'WONDER', 'MELANCHOLY'],
                'sectors': ['Cyclical', 'Commodities', 'High Beta']
            },
            'Mountain': {
                'symbol': '🏔️',
                'element': 'Earth',
                'traits': ['Stability', 'Endurance', 'Unchanging strength'],
                'market_interpretation': 'Defensive stability in uncertain times',
                'emotional_states': ['SERENITY', 'CONTEMPLATION', 'MELANCHOLY'],
                'sectors': ['Utilities', 'Consumer Staples', 'REITs']
            }
        }
        
        self.emotional_meanings = {
            'ECSTASY': 'Overwhelming positive energy and euphoric market conditions',
            'SERENITY': 'Calm confidence and balanced market harmony',
            'WONDER': 'Curious fascination with emerging market possibilities', 
            'CONTEMPLATION': 'Thoughtful analysis and measured decision-making',
            'MELANCHOLY': 'Bittersweet wisdom gained through market adversity',
            'DREAD': 'Fearful anticipation of challenging market conditions'
        }
        
        # Ensure oracle logs directory exists
        os.makedirs('oracle_logs', exist_ok=True)
    
    def get_vision(self, ticker):
        """Get Oracle Vision for a specific ticker"""
        try:
            # Get market data for analysis
            data = self.data_fetcher.get_stock_data(ticker, period='3m')
            
            if data.empty:
                return self._generate_mystical_fallback(ticker)
            
            # Analyze market conditions
            market_conditions = self._analyze_market_conditions(data)
            
            # Select appropriate archetype
            selected_archetype = self._select_archetype(market_conditions, ticker)
            
            # Determine emotional state
            emotional_state = self._determine_emotional_state(market_conditions, selected_archetype)
            
            # Generate vision narrative
            vision_narrative = self._generate_vision_narrative(ticker, selected_archetype, emotional_state, market_conditions)
            
            # Calculate mystical confidence
            confidence = self._calculate_mystical_confidence(market_conditions)
            
            # Generate ritual suggestions
            ritual_suggestions = self._generate_ritual_suggestions(selected_archetype, emotional_state)
            
            # Create Oracle Vision
            vision = {
                'ticker': ticker,
                'archetype': selected_archetype,
                'archetype_symbol': self.archetypes[selected_archetype]['symbol'],
                'emotional_state': emotional_state,
                'vision': vision_narrative,
                'mystical_elements': {
                    'element': self.archetypes[selected_archetype]['element'],
                    'traits': self.archetypes[selected_archetype]['traits'],
                    'market_meaning': self.archetypes[selected_archetype]['market_interpretation']
                },
                'emotional_meaning': self.emotional_meanings[emotional_state],
                'confidence': confidence,
                'ritual_suggestions': ritual_suggestions,
                'cosmic_timing': self._get_cosmic_timing(),
                'numerology': self._generate_numerology(ticker),
                'vision_timestamp': datetime.now().isoformat()
            }
            
            # Save vision to logs
            self._save_vision_to_logs(vision)
            
            return vision
            
        except Exception as e:
            logging.error(f"Oracle Vision error for {ticker}: {str(e)}")
            return self._generate_mystical_fallback(ticker)
    
    def _analyze_market_conditions(self, data):
        """Analyze market conditions for archetype selection"""
        try:
            conditions = {}
            
            # Price momentum analysis
            recent_change = (data['Close'].iloc[-1] / data['Close'].iloc[-5] - 1) if len(data) >= 5 else 0
            conditions['momentum'] = recent_change
            
            # Volatility analysis
            volatility = data['Close'].pct_change().std()
            conditions['volatility'] = volatility
            
            # Volume analysis
            if 'Volume' in data:
                recent_volume = data['Volume'].tail(5).mean()
                avg_volume = data['Volume'].mean()
                conditions['volume_ratio'] = recent_volume / avg_volume if avg_volume > 0 else 1
            else:
                conditions['volume_ratio'] = 1
            
            # Trend strength
            sma_20 = data['SMA_20'].iloc[-1] if 'SMA_20' in data and not data['SMA_20'].isna().all() else data['Close'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1] if 'SMA_50' in data and not data['SMA_50'].isna().all() else data['Close'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            conditions['trend_strength'] = (current_price - sma_20) / sma_20 if sma_20 > 0 else 0
            conditions['long_trend'] = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
            
            # RSI for overbought/oversold
            if 'RSI' in data and not data['RSI'].isna().all():
                conditions['rsi'] = data['RSI'].iloc[-1]
            else:
                conditions['rsi'] = 50  # Neutral
            
            # Recovery potential (distance from recent low)
            recent_low = data['Close'].tail(20).min()
            conditions['recovery_potential'] = (current_price - recent_low) / recent_low if recent_low > 0 else 0
            
            return conditions
            
        except Exception as e:
            logging.error(f"Market conditions analysis error: {str(e)}")
            return {
                'momentum': 0, 'volatility': 0.02, 'volume_ratio': 1,
                'trend_strength': 0, 'long_trend': 0, 'rsi': 50, 'recovery_potential': 0
            }
    
    def _select_archetype(self, conditions, ticker):
        """Select appropriate archetype based on market conditions"""
        try:
            archetype_scores = {}
            
            # Phoenix: Recovery and transformation
            phoenix_score = 0
            if conditions['recovery_potential'] > 0.1:  # Significant recovery from low
                phoenix_score += 3
            if conditions['momentum'] > 0.05:  # Strong positive momentum
                phoenix_score += 2
            if conditions['volatility'] > 0.03:  # High volatility (transformation)
                phoenix_score += 1
            archetype_scores['Phoenix'] = phoenix_score
            
            # Titan: Strength and dominance
            titan_score = 0
            if conditions['trend_strength'] > 0.05:  # Above moving averages
                titan_score += 3
            if conditions['long_trend'] > 0.02:  # Strong long-term trend
                titan_score += 2
            if conditions['volume_ratio'] > 1.2:  # High volume support
                titan_score += 1
            archetype_scores['Titan'] = titan_score
            
            # Serpent: Hidden potential
            serpent_score = 0
            if 20 < conditions['rsi'] < 40:  # Accumulation zone
                serpent_score += 3
            if conditions['volatility'] < 0.02:  # Low volatility (coiled)
                serpent_score += 2
            if -0.02 < conditions['momentum'] < 0.02:  # Sideways movement
                serpent_score += 1
            archetype_scores['Serpent'] = serpent_score
            
            # Oracle: Perfect timing
            oracle_score = 0
            if 40 < conditions['rsi'] < 60:  # Balanced RSI
                oracle_score += 2
            if abs(conditions['trend_strength']) < 0.03:  # Near moving averages
                oracle_score += 2
            if 0.015 < conditions['volatility'] < 0.025:  # Moderate volatility
                oracle_score += 2
            archetype_scores['Oracle'] = oracle_score
            
            # Storm: Chaos and volatility
            storm_score = 0
            if conditions['volatility'] > 0.04:  # High volatility
                storm_score += 3
            if abs(conditions['momentum']) > 0.1:  # Extreme momentum
                storm_score += 2
            if conditions['volume_ratio'] > 2:  # Very high volume
                storm_score += 1
            archetype_scores['Storm'] = storm_score
            
            # Mountain: Stability
            mountain_score = 0
            if conditions['volatility'] < 0.015:  # Low volatility
                mountain_score += 3
            if abs(conditions['momentum']) < 0.02:  # Low momentum
                mountain_score += 2
            if 0.8 < conditions['volume_ratio'] < 1.2:  # Normal volume
                mountain_score += 1
            archetype_scores['Mountain'] = mountain_score
            
            # Select archetype with highest score (with some randomness for mystique)
            if max(archetype_scores.values()) == 0:
                # If no clear archetype, use Oracle as default
                return 'Oracle'
            
            # Add small random factor for mystical unpredictability
            for archetype in archetype_scores:
                archetype_scores[archetype] += random.uniform(-0.5, 0.5)
            
            selected_archetype = max(archetype_scores, key=archetype_scores.get)
            return selected_archetype
            
        except Exception as e:
            logging.error(f"Archetype selection error: {str(e)}")
            return 'Oracle'
    
    def _determine_emotional_state(self, conditions, archetype):
        """Determine emotional state based on conditions and archetype"""
        try:
            possible_states = self.archetypes[archetype]['emotional_states']
            
            # Determine primary emotional driver
            momentum = conditions['momentum']
            volatility = conditions['volatility']
            rsi = conditions['rsi']
            
            if momentum > 0.08:  # Very strong positive momentum
                preferred_states = ['ECSTASY', 'SERENITY']
            elif momentum > 0.03:  # Moderate positive momentum
                preferred_states = ['SERENITY', 'WONDER']
            elif momentum < -0.08:  # Very negative momentum
                preferred_states = ['DREAD', 'MELANCHOLY']
            elif momentum < -0.03:  # Moderate negative momentum
                preferred_states = ['MELANCHOLY', 'CONTEMPLATION']
            else:  # Neutral momentum
                preferred_states = ['CONTEMPLATION', 'WONDER']
            
            # Adjust for volatility
            if volatility > 0.04:  # High volatility adds uncertainty
                preferred_states.extend(['WONDER', 'DREAD'])
            elif volatility < 0.01:  # Low volatility adds stability
                preferred_states.extend(['SERENITY', 'CONTEMPLATION'])
            
            # Find intersection with archetype's emotional states
            compatible_states = [state for state in preferred_states if state in possible_states]
            
            if compatible_states:
                # Choose most frequent state, or random if tie
                state_counts = {state: preferred_states.count(state) for state in set(compatible_states)}
                return max(state_counts, key=state_counts.get)
            else:
                # Fallback to archetype's primary emotional state
                return possible_states[0]
                
        except Exception as e:
            logging.error(f"Emotional state determination error: {str(e)}")
            return 'CONTEMPLATION'
    
    def _generate_vision_narrative(self, ticker, archetype, emotional_state, conditions):
        """Generate mystical vision narrative"""
        try:
            archetype_data = self.archetypes[archetype]
            symbol = archetype_data['symbol']
            element = archetype_data['element']
            
            # Base narrative templates by archetype
            narratives = {
                'Phoenix': [
                    f"From the ashes of market adversity, {ticker} spreads golden wings {symbol}. The flames of transformation burn away weakness, revealing renewed strength beneath.",
                    f"The Phoenix {symbol} stirs within {ticker}'s price action. Each decline feeds the fire of rebirth, preparing for a magnificent rise from the depths.",
                    f"Ancient fires of renewal dance around {ticker} {symbol}. What appears as destruction is merely the Universe clearing space for unprecedented growth."
                ],
                'Titan': [
                    f"The Titan {symbol} awakens within {ticker}, muscles of market force rippling with unstoppable power. Mountains bow before its advancing presence.",
                    f"Behold the Titan's stride as {ticker} {symbol} claims dominion over lesser securities. Its footsteps shake the foundations of entire sectors.",
                    f"The market trembles as {ticker} channels Titanic energy {symbol}. Competitors scatter like leaves before the hurricane of its ascendance."
                ],
                'Serpent': [
                    f"The Serpent {symbol} coils silently within {ticker}, its wisdom hidden beneath surface ripples. Patient and knowing, it awaits the perfect moment to strike.",
                    f"Ancient serpent knowledge flows through {ticker} {symbol}. What others see as stagnation, the wise recognize as the gathering of immense potential energy.",
                    f"The Serpent's eyes {symbol} gleam within {ticker}'s chart patterns. Hidden currents of opportunity flow beneath the visible market waters."
                ],
                'Oracle': [
                    f"The Oracle's crystal sphere {symbol} reveals {ticker}'s true destiny. Past, present, and future merge in perfect prophetic harmony.",
                    f"Through the mystical lens {symbol}, {ticker}'s path becomes clear. The Oracle speaks: 'All market movements follow ancient patterns of cosmic law.'",
                    f"The Oracle {symbol} sits in meditation with {ticker}, divining the threads of fate that weave through price and time. Wisdom flows like sacred water."
                ],
                'Storm': [
                    f"Thunder crashes as the Storm {symbol} gathers around {ticker}. Lightning illuminates opportunities hidden within the chaos of market turbulence.",
                    f"The Storm Lord {symbol} commands {ticker}'s volatile energies. In the eye of the hurricane, perfect clarity emerges from seeming madness.",
                    f"Winds of change howl through {ticker} {symbol}. The Storm brings both destruction and creation, clearing old patterns to birth new possibilities."
                ],
                'Mountain': [
                    f"The Mountain {symbol} stands eternal, as {ticker} embodies immovable strength. Through market seasons, it remains a beacon of stability.",
                    f"Ancient stone wisdom flows through {ticker} {symbol}. Like the Mountain, it weathers all storms while providing shelter for patient investors.",
                    f"The Mountain spirit {symbol} infuses {ticker} with timeless endurance. Its roots run deep, its peak touches the heavens of prosperity."
                ]
            }
            
            base_narrative = random.choice(narratives[archetype])
            
            # Add emotional state coloring
            emotional_additions = {
                'ECSTASY': " Waves of euphoric energy cascade through every fiber of its being, lifting all who dare to ride its celestial current.",
                'SERENITY': " A profound peace settles over its movements, like morning mist on a sacred lake reflecting infinite possibility.",
                'WONDER': " Curiosity sparkles in its essence, as if the Universe itself whispers secrets of untold potential.",
                'CONTEMPLATION': " Deep thoughtfulness permeates its energy, weighing cosmic scales of risk and reward with ancient wisdom.",
                'MELANCHOLY': " A bittersweet beauty touches its journey, finding strength in vulnerability and wisdom in temporary sorrow.",
                'DREAD': " Shadows gather, yet even in darkness, the spark of eventual triumph refuses to be extinguished."
            }
            
            emotional_addition = emotional_additions.get(emotional_state, "")
            
            # Add market condition insights
            condition_insights = self._generate_condition_insights(conditions, element)
            
            full_narrative = base_narrative + emotional_addition + " " + condition_insights
            
            return full_narrative
            
        except Exception as e:
            logging.error(f"Vision narrative generation error: {str(e)}")
            return f"The cosmic veil obscures clear vision of {ticker}, yet patient observation reveals all truths in time."
    
    def _generate_condition_insights(self, conditions, element):
        """Generate insights based on market conditions and element"""
        try:
            insights = []
            
            if conditions['momentum'] > 0.05:
                insights.append(f"The {element} element surges with upward momentum")
            elif conditions['momentum'] < -0.05:
                insights.append(f"The {element} element retreats to gather strength")
            
            if conditions['volatility'] > 0.03:
                insights.append("while cosmic energies dance in wild patterns")
            elif conditions['volatility'] < 0.015:
                insights.append("as celestial harmony maintains perfect balance")
            
            if conditions['volume_ratio'] > 1.5:
                insights.append("and multitudes of earthly participants join the sacred ritual")
            elif conditions['volume_ratio'] < 0.7:
                insights.append("while the initiated few guard ancient secrets")
            
            return ". ".join(insights) + "." if insights else "The elements whisper of changes yet to unfold."
            
        except Exception as e:
            logging.error(f"Condition insights generation error: {str(e)}")
            return "The cosmic patterns remain mysterious to mortal understanding."
    
    def _calculate_mystical_confidence(self, conditions):
        """Calculate confidence with mystical interpretation"""
        try:
            # Base confidence on data quality and clarity
            base_confidence = 0.7
            
            # Adjust for market clarity
            if conditions['volatility'] < 0.02:  # Low volatility = clearer vision
                base_confidence += 0.1
            elif conditions['volatility'] > 0.04:  # High volatility = unclear vision
                base_confidence -= 0.1
            
            # Adjust for trend strength
            trend_strength = abs(conditions.get('trend_strength', 0))
            if trend_strength > 0.05:  # Strong trend = clearer vision
                base_confidence += 0.1
            elif trend_strength < 0.01:  # Weak trend = unclear vision
                base_confidence -= 0.05
            
            # Add mystical randomness
            mystical_factor = random.uniform(-0.05, 0.15)
            base_confidence += mystical_factor
            
            # Ensure confidence is within bounds
            confidence = max(0.5, min(0.95, base_confidence))
            
            return confidence
            
        except Exception as e:
            logging.error(f"Mystical confidence calculation error: {str(e)}")
            return 0.75
    
    def _generate_ritual_suggestions(self, archetype, emotional_state):
        """Generate ritual suggestions for alignment"""
        try:
            archetype_rituals = {
                'Phoenix': ['Light a candle while reviewing charts', 'Meditate on transformation during market volatility', 'Visualize rising from investment setbacks'],
                'Titan': ['Stand strong during market storms', 'Affirm your investment conviction daily', 'Channel unwavering determination'],
                'Serpent': ['Practice patient observation', 'Study hidden market patterns', 'Trust in the wisdom of timing'],
                'Oracle': ['Seek quiet contemplation before major decisions', 'Record and review your market intuitions', 'Trust your inner wisdom'],
                'Storm': ['Embrace market volatility as opportunity', 'Find calm within chaos', 'Let change be your teacher'],
                'Mountain': ['Maintain steady discipline', 'Focus on long-term stability', 'Let patience be your strength']
            }
            
            emotional_rituals = {
                'ECSTASY': 'Express gratitude for abundance',
                'SERENITY': 'Practice mindful breathing',
                'WONDER': 'Maintain beginner\'s mind',
                'CONTEMPLATION': 'Journal your insights',
                'MELANCHOLY': 'Honor the lessons in loss',
                'DREAD': 'Ground yourself in present reality'
            }
            
            base_rituals = archetype_rituals.get(archetype, ['Seek balance in all things'])
            emotional_ritual = emotional_rituals.get(emotional_state, 'Stay present and aware')
            
            return base_rituals + [emotional_ritual]
            
        except Exception as e:
            logging.error(f"Ritual suggestions generation error: {str(e)}")
            return ['Trust in the natural flow of markets', 'Remain centered and aware']
    
    def _get_cosmic_timing(self):
        """Generate cosmic timing information"""
        try:
            now = datetime.now()
            
            # Simple lunar phase approximation (for mystical element)
            days_since_new_moon = (now.day + 15) % 29
            if days_since_new_moon < 7:
                moon_phase = "Waxing Crescent"
                timing_meaning = "Time for new beginnings and growth"
            elif days_since_new_moon < 14:
                moon_phase = "Waxing Gibbous"
                timing_meaning = "Time for building and accumulation"
            elif days_since_new_moon < 21:
                moon_phase = "Waning Gibbous"
                timing_meaning = "Time for reflection and adjustment"
            else:
                moon_phase = "Waning Crescent"
                timing_meaning = "Time for release and preparation"
            
            # Market timing
            if now.weekday() == 0:  # Monday
                market_timing = "New week energy favors fresh starts"
            elif now.weekday() == 4:  # Friday
                market_timing = "Week's end brings consolidation"
            else:
                market_timing = "Mid-week energies support steady progress"
            
            return {
                'moon_phase': moon_phase,
                'timing_meaning': timing_meaning,
                'market_timing': market_timing,
                'cosmic_number': random.randint(1, 9)
            }
            
        except Exception as e:
            logging.error(f"Cosmic timing generation error: {str(e)}")
            return {
                'moon_phase': 'Unknown',
                'timing_meaning': 'The cosmic cycles continue their eternal dance',
                'market_timing': 'All timing is perfect in the grand design',
                'cosmic_number': 7
            }
    
    def _generate_numerology(self, ticker):
        """Generate numerological interpretation"""
        try:
            # Simple numerology based on ticker letters
            letter_values = {
                'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
                'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
                'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
            }
            
            total = sum(letter_values.get(letter.upper(), 0) for letter in ticker if letter.isalpha())
            
            # Reduce to single digit
            while total > 9:
                total = sum(int(digit) for digit in str(total))
            
            numerology_meanings = {
                1: "Leadership and new beginnings",
                2: "Balance and cooperation",
                3: "Creativity and expansion",
                4: "Stability and foundation",
                5: "Change and adventure",
                6: "Harmony and responsibility",
                7: "Spiritual insight and analysis",
                8: "Material success and power",
                9: "Completion and universal love"
            }
            
            return {
                'number': total,
                'meaning': numerology_meanings.get(total, "Universal mystery")
            }
            
        except Exception as e:
            logging.error(f"Numerology generation error: {str(e)}")
            return {'number': 7, 'meaning': 'Sacred mystery'}
    
    def _save_vision_to_logs(self, vision):
        """Save vision to oracle logs"""
        try:
            log_file = 'oracle_logs/visions.json'
            
            # Load existing visions
            visions = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        visions = json.load(f)
                except json.JSONDecodeError:
                    visions = []
            
            # Add new vision
            visions.append(vision)
            
            # Keep only last 500 visions
            visions = visions[-500:]
            
            # Save updated visions
            with open(log_file, 'w') as f:
                json.dump(visions, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving vision to logs: {str(e)}")
    
    def _generate_mystical_fallback(self, ticker):
        """Generate mystical fallback when data is unavailable"""
        fallback_archetype = random.choice(list(self.archetypes.keys()))
        fallback_emotional_state = random.choice(['CONTEMPLATION', 'WONDER', 'SERENITY'])
        
        return {
            'ticker': ticker,
            'archetype': fallback_archetype,
            'archetype_symbol': self.archetypes[fallback_archetype]['symbol'],
            'emotional_state': fallback_emotional_state,
            'vision': f"The cosmic veil obscures earthly data for {ticker}, yet the {fallback_archetype} {self.archetypes[fallback_archetype]['symbol']} whispers ancient truths through the ethereal realm. When mortal instruments fail, divine insight transcends material limitations.",
            'mystical_elements': self.archetypes[fallback_archetype],
            'emotional_meaning': self.emotional_meanings[fallback_emotional_state],
            'confidence': 0.6,
            'ritual_suggestions': ['Trust in the unseen forces', 'Patience reveals all mysteries'],
            'cosmic_timing': self._get_cosmic_timing(),
            'numerology': self._generate_numerology(ticker),
            'vision_timestamp': datetime.now().isoformat(),
            'note': 'Vision channeled through ethereal realm due to earthly data limitations'
        }
    
    def get_archetype_analysis(self, ticker_list):
        """Get archetype analysis for multiple tickers"""
        try:
            analyses = {}
            archetype_counts = {}
            
            for ticker in ticker_list:
                vision = self.get_vision(ticker)
                archetype = vision['archetype']
                
                analyses[ticker] = {
                    'archetype': archetype,
                    'symbol': vision['archetype_symbol'],
                    'emotional_state': vision['emotional_state']
                }
                
                archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
            
            # Determine dominant archetype
            dominant_archetype = max(archetype_counts, key=archetype_counts.get) if archetype_counts else 'Oracle'
            
            return {
                'individual_analyses': analyses,
                'archetype_distribution': archetype_counts,
                'dominant_archetype': dominant_archetype,
                'portfolio_interpretation': self._interpret_portfolio_archetypes(archetype_counts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Archetype analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _interpret_portfolio_archetypes(self, archetype_counts):
        """Interpret portfolio-level archetype distribution"""
        try:
            total_count = sum(archetype_counts.values())
            if total_count == 0:
                return "The portfolio exists in mystical balance, awaiting cosmic alignment."
            
            interpretations = []
            
            for archetype, count in archetype_counts.items():
                percentage = (count / total_count) * 100
                if percentage > 40:
                    interpretations.append(f"Strong {archetype} energy dominates ({percentage:.0f}%), bringing {self.archetypes[archetype]['market_interpretation'].lower()}")
                elif percentage > 25:
                    interpretations.append(f"Moderate {archetype} influence ({percentage:.0f}%) adds {self.archetypes[archetype]['traits'][0].lower()}")
            
            if len(archetype_counts) >= 4:
                interpretations.append("Diverse archetypal energies create a well-balanced cosmic portfolio")
            elif len(archetype_counts) <= 2:
                interpretations.append("Focused archetypal energy suggests concentrated cosmic purpose")
            
            return ". ".join(interpretations) + "." if interpretations else "The archetypes dance in perfect harmony."
            
        except Exception as e:
            logging.error(f"Portfolio archetype interpretation error: {str(e)}")
            return "The cosmic patterns weave mysterious designs beyond mortal comprehension."
