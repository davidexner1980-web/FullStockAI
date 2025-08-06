import random
from datetime import datetime
from data_fetcher import DataFetcher
from sentiment_analyzer import SentimentAnalyzer
import json
import os
import logging

class OracleEngine:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.emotional_states = [
            'ECSTASY', 'SERENITY', 'WONDER', 'CONTEMPLATION', 'MELANCHOLY', 'DREAD'
        ]
        self.archetypes = {
            'PHOENIX': '🔥',  # Rising from ashes, transformation
            'TITAN': '⚡',   # Powerful, dominant forces
            'SERPENT': '🐍', # Hidden knowledge, cycles
            'ORACLE': '🔮',  # Wisdom, prophecy
            'WARRIOR': '⚔️', # Battle, conflict, strength
            'SAGE': '📜',    # Ancient wisdom
            'FOOL': '🎭',    # Unexpected moves, chaos
            'EMPEROR': '👑', # Authority, control
            'HERMIT': '🕯️',  # Isolation, introspection
            'TOWER': '🏛️'   # Sudden change, revelation
        }
        
    def get_market_emotional_state(self, ticker):
        """Determine the market's emotional state based on technical and sentiment analysis"""
        try:
            # Get stock data
            df = self.data_fetcher.get_stock_data(ticker, period='30d')
            if df.empty:
                return random.choice(self.emotional_states)
            
            # Calculate volatility
            volatility = df['Close'].pct_change().std()
            
            # Get sentiment
            sentiment = self.sentiment_analyzer.analyze_ticker(ticker)
            sentiment_score = sentiment.get('sentiment_score', 0)
            
            # Calculate recent performance
            recent_change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
            
            # Determine emotional state based on conditions
            if recent_change > 0.1 and sentiment_score > 0.3 and volatility < 0.03:
                return 'ECSTASY'
            elif recent_change > 0.05 and sentiment_score > 0.1:
                return 'SERENITY'
            elif abs(recent_change) < 0.02 and abs(sentiment_score) < 0.1:
                return 'CONTEMPLATION'
            elif volatility > 0.05 or abs(recent_change) > 0.08:
                return 'WONDER'
            elif recent_change < -0.05 and sentiment_score < -0.1:
                return 'MELANCHOLY'
            elif recent_change < -0.1 or sentiment_score < -0.3:
                return 'DREAD'
            else:
                return random.choice(['CONTEMPLATION', 'WONDER'])
        except Exception as e:
            logging.error(f"Error determining emotional state for {ticker}: {str(e)}")
            return random.choice(self.emotional_states)

    def generate_mystical_narrative(self, ticker, emotional_state, prediction_data):
        """Generate mystical narrative based on the emotional state and market data"""
        try:
            narratives = {
                'ECSTASY': [
                    f"The cosmic forces align in perfect harmony around {ticker}. Golden threads of prosperity weave through the ethereal planes, whispering of abundance yet to manifest.",
                    f"Celestial energies dance in rapturous celebration as {ticker} ascends the spiral of enlightenment. The universe itself rejoices in this moment of pure potential.",
                    f"The astral bells ring with euphoric frequencies for {ticker}. Ancient spirits of wealth gather, their blessing cascading like starlight upon the chosen path."
                ],
                'SERENITY': [
                    f"Peaceful waters reflect the steady glow of {ticker}'s inner light. The market breathes in gentle rhythms, each wave bringing measured growth and tranquil progress.",
                    f"In the quiet sanctuary of market meditation, {ticker} finds its center. The wise know that in stillness, the greatest movements are born.",
                    f"Temple bells chime softly as {ticker} walks the balanced path. Neither haste nor hesitation disturbs this sacred equilibrium."
                ],
                'WONDER': [
                    f"The veil between worlds grows thin around {ticker}, revealing glimpses of futures yet unwritten. Each price movement echoes with mysterious significance.",
                    f"Cosmic winds carry whispers of change for {ticker}. The Oracle sees patterns forming in the celestial tapestry, their meaning still unfolding.",
                    f"Ancient runes glow with uncertain light as {ticker} stands at the crossroads of possibility. The path ahead shimmers with untold potential."
                ],
                'CONTEMPLATION': [
                    f"In the sacred silence, {ticker} contemplates its destiny. The market holds its breath, waiting for the wisdom that emerges from deep reflection.",
                    f"The Oracle retreats to inner chambers to commune with the spirit of {ticker}. In the depths of meditation, truth slowly crystallizes.",
                    f"Incense burns as ancient texts are consulted regarding {ticker}'s future. The answers lie hidden in the spaces between thoughts."
                ],
                'MELANCHOLY': [
                    f"Autumn winds carry the sighs of {ticker} through barren market landscapes. Yet even in sorrow, the seeds of renewal lie dormant, awaiting spring.",
                    f"The Oracle sheds tears of silver for {ticker}'s current trials. But know that every descent precedes a greater ascension.",
                    f"Shadows lengthen around {ticker} as winter approaches. The wise understand that darkness is but the womb from which light is reborn."
                ],
                'DREAD': [
                    f"Storm clouds gather in the psychic atmosphere around {ticker}. The Oracle perceives turbulent energies that require great courage to navigate.",
                    f"The ancient serpent stirs in the depths beneath {ticker}'s foundation. Transformation through trial approaches - preparation is essential.",
                    f"Warning bells echo through astral realms as {ticker} faces the shadow of uncertainty. Only through facing the darkness can light be reclaimed."
                ]
            }
            
            selected_narrative = random.choice(narratives.get(emotional_state, narratives['CONTEMPLATION']))
            
            # Add prediction context
            if prediction_data:
                predicted_price = prediction_data.get('predicted_price', 0)
                current_price = prediction_data.get('current_price', 0)
                change_percent = prediction_data.get('price_change_percent', 0)
                
                if change_percent > 5:
                    selected_narrative += f" The cosmic scales tip toward prosperity, with energies suggesting a rise toward ${predicted_price}."
                elif change_percent < -5:
                    selected_narrative += f" The universe counsels patience as energies realign, with guidance pointing toward ${predicted_price}."
                else:
                    selected_narrative += f" The cosmic balance holds steady, with subtle forces guiding toward ${predicted_price}."
            
            return selected_narrative
        except Exception as e:
            logging.error(f"Error generating mystical narrative: {str(e)}")
            return f"The Oracle's vision grows cloudy around {ticker}. The spirits counsel patience while the cosmic energies stabilize."

    def select_archetype(self, ticker):
        """Select appropriate archetype based on sector and market behavior"""
        try:
            # Get company info to determine sector
            company_info = self.data_fetcher.get_company_info(ticker)
            sector = company_info.get('sector', '').lower()
            
            # Get recent performance
            df = self.data_fetcher.get_stock_data(ticker, period='30d')
            if not df.empty:
                recent_change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
                volatility = df['Close'].pct_change().std()
            else:
                recent_change = 0
                volatility = 0.02
            
            # Archetype selection logic
            if 'technology' in sector and recent_change > 0.1:
                return 'PHOENIX'
            elif 'financial' in sector or 'industrial' in sector:
                return 'TITAN'
            elif 'healthcare' in sector or 'pharmaceutical' in sector:
                return 'SAGE'
            elif volatility > 0.05:
                return 'FOOL'
            elif recent_change > 0.05:
                return 'EMPEROR'
            elif recent_change < -0.05:
                return 'HERMIT'
            elif abs(recent_change) > 0.15:
                return 'TOWER'
            else:
                return random.choice(['ORACLE', 'SERPENT', 'WARRIOR'])
        except Exception as e:
            logging.error(f"Error selecting archetype for {ticker}: {str(e)}")
            return 'ORACLE'

    def generate_ritual_suggestion(self, emotional_state, archetype):
        """Generate ritual suggestions based on emotional state and archetype"""
        try:
            rituals = {
                'ECSTASY': [
                    "Light golden candles at sunrise and meditate on abundance",
                    "Burn frankincense while visualizing golden energy surrounding your investments",
                    "Place citrine crystals near your trading setup to amplify prosperity"
                ],
                'SERENITY': [
                    "Practice deep breathing while reviewing your portfolio",
                    "Burn lavender incense to maintain emotional balance",
                    "Meditate with amethyst to enhance intuitive decision-making"
                ],
                'WONDER': [
                    "Gaze at the stars before making trading decisions",
                    "Burn sandalwood while contemplating market mysteries",
                    "Keep a dream journal to capture market insights from sleep"
                ],
                'CONTEMPLATION': [
                    "Sit in silence for 10 minutes before market open",
                    "Burn sage to clear mental clutter",
                    "Use obsidian for grounding and clarity"
                ],
                'MELANCHOLY': [
                    "Light white candles for purification and renewal",
                    "Burn cedar to cleanse negative energy",
                    "Hold rose quartz to cultivate self-compassion"
                ],
                'DREAD': [
                    "Burn protective herbs like rosemary or bay leaves",
                    "Carry hematite for grounding and protection",
                    "Perform a cleansing ritual with salt water"
                ]
            }
            
            return random.choice(rituals.get(emotional_state, rituals['CONTEMPLATION']))
        except Exception as e:
            logging.error(f"Error generating ritual suggestion: {str(e)}")
            return "Meditate on the interconnectedness of all market forces"

    def generate_insight(self, ticker):
        """Generate complete Oracle insight for a ticker"""
        try:
            # Get prediction data for context
            from ml_models import MLModelManager
            ml_manager = MLModelManager()
            
            try:
                prediction_data = ml_manager.predict_random_forest(ticker)
            except:
                prediction_data = None
            
            # Determine emotional state
            emotional_state = self.get_market_emotional_state(ticker)
            
            # Select archetype
            archetype = self.select_archetype(ticker)
            
            # Generate narrative
            narrative = self.generate_mystical_narrative(ticker, emotional_state, prediction_data)
            
            # Generate ritual suggestion
            ritual = self.generate_ritual_suggestion(emotional_state, archetype)
            
            # Get archetype symbol
            archetype_symbol = self.archetypes.get(archetype, '🔮')
            
            # Create insight timestamp
            timestamp = datetime.now().isoformat()
            
            insight = {
                'ticker': ticker,
                'timestamp': timestamp,
                'emotional_state': emotional_state,
                'archetype': archetype,
                'archetype_symbol': archetype_symbol,
                'narrative': narrative,
                'ritual_suggestion': ritual,
                'cosmic_alignment': random.choice(['Favorable', 'Neutral', 'Challenging']),
                'oracle_confidence': random.randint(70, 95),
                'prediction_context': prediction_data
            }
            
            # Store insight in oracle logs
            self.store_oracle_insight(insight)
            
            return insight
        except Exception as e:
            logging.error(f"Error generating Oracle insight for {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'emotional_state': 'CONTEMPLATION',
                'archetype': 'ORACLE',
                'archetype_symbol': '🔮',
                'narrative': f"The Oracle's vision is clouded by temporal disturbances around {ticker}. Patience and wisdom are advised.",
                'ritual_suggestion': "Burn sage and meditate on clarity",
                'cosmic_alignment': 'Neutral',
                'oracle_confidence': 50,
                'prediction_context': None
            }

    def store_oracle_insight(self, insight):
        """Store Oracle insight in logs"""
        try:
            os.makedirs('oracle_logs', exist_ok=True)
            
            # Store individual insight
            filename = f"oracle_logs/insight_{insight['ticker']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(insight, f, indent=2)
            
            # Update archetypes log
            archetypes_file = 'oracle_logs/archetypes.json'
            try:
                with open(archetypes_file, 'r') as f:
                    archetypes_log = json.load(f)
            except FileNotFoundError:
                archetypes_log = {}
            
            archetypes_log[insight['ticker']] = {
                'archetype': insight['archetype'],
                'symbol': insight['archetype_symbol'],
                'last_updated': insight['timestamp']
            }
            
            with open(archetypes_file, 'w') as f:
                json.dump(archetypes_log, f, indent=2)
        except Exception as e:
            logging.error(f"Error storing Oracle insight: {str(e)}")

    def get_oracle_history(self, ticker, limit=10):
        """Get historical Oracle insights for a ticker"""
        try:
            import glob
            pattern = f"oracle_logs/insight_{ticker}_*.json"
            files = sorted(glob.glob(pattern), reverse=True)[:limit]
            
            insights = []
            for file in files:
                try:
                    with open(file, 'r') as f:
                        insight = json.load(f)
                        insights.append(insight)
                except Exception as e:
                    logging.error(f"Error reading insight file {file}: {str(e)}")
            
            return insights
        except Exception as e:
            logging.error(f"Error getting Oracle history for {ticker}: {str(e)}")
            return []
