import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
import logging
from datetime import datetime, timedelta
import json

# Using a lightweight LSTM implementation since we can't import tensorflow
class SimpleLSTM:
    """Simplified LSTM-like implementation using numpy"""
    def __init__(self, input_size=1, hidden_size=50, output_size=1, num_layers=2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        
        # Initialize weights randomly
        self.W_f = np.random.randn(hidden_size, input_size + hidden_size) * 0.01
        self.W_i = np.random.randn(hidden_size, input_size + hidden_size) * 0.01
        self.W_o = np.random.randn(hidden_size, input_size + hidden_size) * 0.01
        self.W_c = np.random.randn(hidden_size, input_size + hidden_size) * 0.01
        self.W_y = np.random.randn(output_size, hidden_size) * 0.01
        
        # Bias terms
        self.b_f = np.zeros((hidden_size, 1))
        self.b_i = np.zeros((hidden_size, 1))
        self.b_o = np.zeros((hidden_size, 1))
        self.b_c = np.zeros((hidden_size, 1))
        self.b_y = np.zeros((output_size, 1))
        
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def tanh(self, x):
        return np.tanh(np.clip(x, -250, 250))
    
    def forward(self, X):
        """Forward pass through LSTM"""
        seq_len = X.shape[0]
        
        # Initialize hidden and cell states
        h = np.zeros((self.hidden_size, 1))
        c = np.zeros((self.hidden_size, 1))
        
        outputs = []
        
        for t in range(seq_len):
            x_t = X[t].reshape(-1, 1)
            
            # Concatenate input and hidden state
            combined = np.vstack([x_t, h])
            
            # Forget gate
            f_t = self.sigmoid(np.dot(self.W_f, combined) + self.b_f)
            
            # Input gate
            i_t = self.sigmoid(np.dot(self.W_i, combined) + self.b_i)
            
            # Candidate values
            c_tilde = self.tanh(np.dot(self.W_c, combined) + self.b_c)
            
            # Update cell state
            c = f_t * c + i_t * c_tilde
            
            # Output gate
            o_t = self.sigmoid(np.dot(self.W_o, combined) + self.b_o)
            
            # Update hidden state
            h = o_t * self.tanh(c)
            
            outputs.append(h.copy())
        
        # Final output
        output = np.dot(self.W_y, h) + self.b_y
        return output.flatten()[0]
    
    def predict(self, X):
        """Predict using the LSTM"""
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        
        predictions = []
        for i in range(X.shape[0]):
            pred = self.forward(X[i])
            predictions.append(pred)
        
        return np.array(predictions)
    
    def fit(self, X, y, epochs=50, learning_rate=0.001):
        """Simple training using gradient approximation"""
        # Simplified training - just adjust weights based on error
        for epoch in range(epochs):
            total_loss = 0
            for i in range(len(X)):
                pred = self.forward(X[i])
                error = y[i] - pred
                total_loss += error ** 2
                
                # Simple weight adjustment (pseudo gradient descent)
                adjustment = learning_rate * error * 0.01
                self.W_y += adjustment
            
            if epoch % 10 == 0:
                logging.debug(f"LSTM Epoch {epoch}, Loss: {total_loss/len(X):.6f}")

class LSTMModel:
    def __init__(self):
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        self.sequence_length = 60  # Use 60 days to predict next day
        
    def get_or_train_model(self, ticker: str, data: pd.DataFrame):
        """Get existing model or train a new one"""
        model_path = os.path.join(self.models_dir, f'lstm_{ticker}.joblib')
        scaler_path = os.path.join(self.models_dir, f'scaler_{ticker}.joblib')
        
        try:
            # Check if model exists and is recent
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age.days < 7:  # Model is less than a week old
                    model = joblib.load(model_path)
                    scaler = joblib.load(scaler_path)
                    return model, scaler
            
            # Train new model
            model, scaler = self._train_model(ticker, data)
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            return model, scaler
            
        except Exception as e:
            logging.error(f"LSTM model error for {ticker}: {str(e)}")
            # Train new model as fallback
            return self._train_model(ticker, data)
    
    def _train_model(self, ticker: str, data: pd.DataFrame):
        """Train LSTM model"""
        try:
            # Prepare data
            prices = data['Close'].values.reshape(-1, 1)
            
            # Scale the data
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(prices)
            
            # Create sequences
            X, y = self._create_sequences(scaled_data, self.sequence_length)
            
            if len(X) < 10:
                raise ValueError("Not enough data to create sequences")
            
            # Split data
            split_point = int(len(X) * 0.8)
            X_train, X_test = X[:split_point], X[split_point:]
            y_train, y_test = y[:split_point], y[split_point:]
            
            # Create and train model
            model = SimpleLSTM(input_size=1, hidden_size=50)
            
            # Train the model
            model.fit(X_train, y_train, epochs=50)
            
            # Evaluate
            train_pred = model.predict(X_train.reshape(len(X_train), self.sequence_length))
            test_pred = model.predict(X_test.reshape(len(X_test), self.sequence_length))
            
            # Calculate metrics
            train_mse = mean_squared_error(y_train, train_pred)
            test_mse = mean_squared_error(y_test, test_pred)
            
            logging.info(f"LSTM {ticker} - Train MSE: {train_mse:.6f}, Test MSE: {test_mse:.6f}")
            
            # Save metrics
            self._save_model_metrics(ticker, {
                'train_mse': train_mse,
                'test_mse': test_mse,
                'training_date': datetime.now().isoformat()
            })
            
            return model, scaler
            
        except Exception as e:
            logging.error(f"LSTM training error for {ticker}: {str(e)}")
            raise
    
    def _create_sequences(self, data, seq_length):
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(seq_length, len(data)):
            X.append(data[i-seq_length:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)
    
    def prepare_prediction_sequence(self, data: pd.DataFrame, scaler):
        """Prepare sequence for prediction"""
        try:
            prices = data['Close'].values[-self.sequence_length:].reshape(-1, 1)
            scaled_prices = scaler.transform(prices)
            return scaled_prices.reshape(1, self.sequence_length, 1)
        except Exception as e:
            logging.error(f"Sequence preparation error: {str(e)}")
            raise
    
    def calculate_confidence(self, ticker: str):
        """Calculate confidence based on recent model performance"""
        try:
            metrics = self._load_model_metrics(ticker)
            if metrics and 'test_mse' in metrics:
                # Convert MSE to confidence (lower MSE = higher confidence)
                mse = metrics['test_mse']
                confidence = 1 / (1 + mse * 1000)  # Scale factor
                return min(max(confidence, 0.3), 0.9)  # Clamp between 0.3 and 0.9
            return 0.75  # Default confidence
        except:
            return 0.75
    
    def _save_model_metrics(self, ticker: str, metrics: dict):
        """Save model performance metrics"""
        try:
            metrics_path = os.path.join(self.models_dir, f'lstm_metrics_{ticker}.json')
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f)
        except Exception as e:
            logging.error(f"Save LSTM metrics error: {str(e)}")
    
    def _load_model_metrics(self, ticker: str):
        """Load model performance metrics"""
        try:
            metrics_path = os.path.join(self.models_dir, f'lstm_metrics_{ticker}.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
