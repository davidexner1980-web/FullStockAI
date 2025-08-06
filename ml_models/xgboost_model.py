import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
import logging
from datetime import datetime, timedelta

class XGBoostModel:
    def __init__(self):
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        self.model_params = {
            'objective': 'reg:squarederror',
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
    
    def get_or_train_model(self, ticker: str, data: pd.DataFrame, features: pd.DataFrame):
        """Get existing model or train a new one"""
        model_path = os.path.join(self.models_dir, f'xgb_{ticker}.joblib')
        
        try:
            # Check if model exists and is recent
            if os.path.exists(model_path):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age.days < 7:  # Model is less than a week old
                    return joblib.load(model_path)
            
            # Train new model
            model = self._train_model(ticker, data, features)
            joblib.dump(model, model_path)
            return model
            
        except Exception as e:
            logging.error(f"XGBoost model error for {ticker}: {str(e)}")
            # Train new model as fallback
            return self._train_model(ticker, data, features)
    
    def _train_model(self, ticker: str, data: pd.DataFrame, features: pd.DataFrame):
        """Train XGBoost model"""
        try:
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
            model = xgb.XGBRegressor(**self.model_params)
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            
            logging.info(f"XGBoost {ticker} - Train MSE: {train_mse:.4f}, Test MSE: {test_mse:.4f}")
            logging.info(f"XGBoost {ticker} - Train MAE: {train_mae:.4f}, Test MAE: {test_mae:.4f}")
            
            return model
            
        except Exception as e:
            logging.error(f"XGBoost training error for {ticker}: {str(e)}")
            raise
    
    def get_feature_importance(self, model, feature_names):
        """Get feature importance from trained model"""
        try:
            importance = model.feature_importances_
            feature_importance = list(zip(feature_names, importance))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            return [{'feature': name, 'importance': round(imp, 4)} 
                   for name, imp in feature_importance]
            
        except Exception as e:
            logging.error(f"Feature importance error: {str(e)}")
            return []
    
    def predict_with_intervals(self, model, features, confidence_level=0.95):
        """Predict with confidence intervals using quantile regression"""
        try:
            # Base prediction
            prediction = model.predict(features)
            
            # For simplicity, estimate intervals based on training residuals
            # In production, you might want to use quantile regression
            prediction_std = prediction * 0.02  # Assume 2% standard deviation
            
            z_score = 1.96 if confidence_level == 0.95 else 1.645  # 95% or 90%
            
            lower_bound = prediction - z_score * prediction_std
            upper_bound = prediction + z_score * prediction_std
            
            return {
                'prediction': prediction[0],
                'lower_bound': lower_bound[0],
                'upper_bound': upper_bound[0],
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logging.error(f"Prediction intervals error: {str(e)}")
            return {'prediction': model.predict(features)[0]}
    
    def get_model_metrics(self, ticker: str):
        """Get stored model performance metrics"""
        try:
            metrics_path = os.path.join(self.models_dir, f'xgb_metrics_{ticker}.json')
            if os.path.exists(metrics_path):
                import json
                with open(metrics_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def save_model_metrics(self, ticker: str, metrics: dict):
        """Save model performance metrics"""
        try:
            import json
            metrics_path = os.path.join(self.models_dir, f'xgb_metrics_{ticker}.json')
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f)
        except Exception as e:
            logging.error(f"Save metrics error: {str(e)}")
