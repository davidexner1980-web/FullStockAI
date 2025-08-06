import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import logging
from datetime import datetime, timedelta
import json

class RandomForestModel:
    def __init__(self):
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        self.model_params = {
            'n_estimators': 100,
            'max_depth': 15,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42,
            'n_jobs': -1
        }
    
    def get_or_train_model(self, ticker: str, data: pd.DataFrame):
        """Get existing model or train a new one"""
        model_path = os.path.join(self.models_dir, f'rf_{ticker}.joblib')
        
        try:
            # Check if model exists and is recent
            if os.path.exists(model_path):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age.days < 7:  # Model is less than a week old
                    return joblib.load(model_path)
            
            # Train new model
            model = self._train_model(ticker, data)
            joblib.dump(model, model_path)
            return model
            
        except Exception as e:
            logging.error(f"Random Forest model error for {ticker}: {str(e)}")
            # Train new model as fallback
            return self._train_model(ticker, data)
    
    def _train_model(self, ticker: str, data: pd.DataFrame):
        """Train Random Forest model"""
        try:
            # Prepare features
            features = self._prepare_features(data)
            
            # Prepare target variable (next day's closing price)
            target = data['Close'].shift(-1).dropna()
            
            # Align features with target
            features_aligned = features.iloc[:-1]  # Remove last row to match target
            features_aligned = features_aligned.loc[target.index]
            
            if len(features_aligned) != len(target):
                raise ValueError("Feature and target lengths don't match")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features_aligned, target, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Create and train model
            model = RandomForestRegressor(**self.model_params)
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)
            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            logging.info(f"Random Forest {ticker} - Train MSE: {train_mse:.4f}, Test MSE: {test_mse:.4f}")
            logging.info(f"Random Forest {ticker} - Train R²: {train_r2:.4f}, Test R²: {test_r2:.4f}")
            
            # Save metrics
            self._save_model_metrics(ticker, {
                'train_mse': train_mse,
                'test_mse': test_mse,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'feature_importance': self._get_feature_importance(model, features_aligned.columns),
                'training_date': datetime.now().isoformat()
            })
            
            return model
            
        except Exception as e:
            logging.error(f"Random Forest training error for {ticker}: {str(e)}")
            raise
    
    def _prepare_features(self, data: pd.DataFrame):
        """Prepare features for Random Forest model"""
        try:
            features = pd.DataFrame(index=data.index)
            
            # Price-based features
            features['close'] = data['Close']
            features['high'] = data['High']
            features['low'] = data['Low']
            features['open'] = data['Open']
            features['volume'] = data['Volume']
            
            # Returns and volatility
            features['returns'] = data['Close'].pct_change()
            features['volatility_5'] = features['returns'].rolling(5).std()
            features['volatility_20'] = features['returns'].rolling(20).std()
            
            # Moving averages
            for window in [5, 10, 20, 50]:
                features[f'sma_{window}'] = data['Close'].rolling(window).mean()
                features[f'price_to_sma_{window}'] = data['Close'] / features[f'sma_{window}']
            
            # Price momentum
            for period in [5, 10, 20]:
                features[f'momentum_{period}'] = data['Close'] / data['Close'].shift(period) - 1
            
            # Volume features
            features['volume_sma_20'] = data['Volume'].rolling(20).mean()
            features['volume_ratio'] = data['Volume'] / features['volume_sma_20']
            
            # High-Low features
            features['hl_pct'] = (data['High'] - data['Low']) / data['Close']
            features['co_pct'] = (data['Close'] - data['Open']) / data['Open']
            
            # RSI approximation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Band position
            sma_20 = data['Close'].rolling(20).mean()
            std_20 = data['Close'].rolling(20).std()
            features['bb_upper'] = sma_20 + (std_20 * 2)
            features['bb_lower'] = sma_20 - (std_20 * 2)
            features['bb_position'] = (data['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            
            # MACD approximation
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            features['macd'] = ema_12 - ema_26
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            
            # Day of week and month (cyclical encoding)
            features['day_sin'] = np.sin(2 * np.pi * data.index.dayofweek / 7)
            features['day_cos'] = np.cos(2 * np.pi * data.index.dayofweek / 7)
            features['month_sin'] = np.sin(2 * np.pi * data.index.month / 12)
            features['month_cos'] = np.cos(2 * np.pi * data.index.month / 12)
            
            # Remove NaN values
            features = features.dropna()
            
            return features
            
        except Exception as e:
            logging.error(f"Feature preparation error: {str(e)}")
            raise
    
    def _get_feature_importance(self, model, feature_names):
        """Get feature importance from trained model"""
        try:
            importance = model.feature_importances_
            feature_importance = list(zip(feature_names, importance))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            return [{'feature': name, 'importance': round(imp, 4)} 
                   for name, imp in feature_importance[:10]]  # Top 10
            
        except Exception as e:
            logging.error(f"Feature importance error: {str(e)}")
            return []
    
    def get_prediction_intervals(self, model, X, confidence_level=0.95):
        """Calculate prediction intervals using individual tree predictions"""
        try:
            # Get predictions from all trees
            tree_predictions = np.array([tree.predict(X) for tree in model.estimators_])
            
            # Calculate percentiles for confidence intervals
            alpha = 1 - confidence_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            lower_bound = np.percentile(tree_predictions, lower_percentile, axis=0)
            upper_bound = np.percentile(tree_predictions, upper_percentile, axis=0)
            mean_prediction = np.mean(tree_predictions, axis=0)
            
            return {
                'prediction': mean_prediction[0],
                'lower_bound': lower_bound[0],
                'upper_bound': upper_bound[0],
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logging.error(f"Prediction intervals error: {str(e)}")
            return {'prediction': model.predict(X)[0]}
    
    def _save_model_metrics(self, ticker: str, metrics: dict):
        """Save model performance metrics"""
        try:
            metrics_path = os.path.join(self.models_dir, f'rf_metrics_{ticker}.json')
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, default=str)
        except Exception as e:
            logging.error(f"Save RF metrics error: {str(e)}")
    
    def load_model_metrics(self, ticker: str):
        """Load model performance metrics"""
        try:
            metrics_path = os.path.join(self.models_dir, f'rf_metrics_{ticker}.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
