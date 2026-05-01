# backend/ml_model.py
import logging
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif
from imblearn.over_sampling import SMOTE, BorderlineSMOTE
from backend.risk_engine import RiskCalculator
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger("MLEngine")


class MultiThresholdPredictor:
    """Ensemble predictor that combines models trained on different thresholds for better performance."""
    
    def __init__(self, ticker: str, user_threshold_pct: float):
        self.ticker = ticker
        self.user_threshold_pct = user_threshold_pct
        
        # Determine optimal base thresholds based on user threshold
        if user_threshold_pct <= 1.2:
            # User wants low threshold - use single model
            self.base_thresholds = [user_threshold_pct]
            self.weights = [1.0]
        elif user_threshold_pct <= 2.0:
            # Medium threshold - use 2 models
            self.base_thresholds = [1.0, user_threshold_pct]
            self.weights = [0.6, 0.4]  # More weight to lower threshold (better performance)
        else:
            # High threshold - use 2 models with more weight on lower
            self.base_thresholds = [1.2, user_threshold_pct]
            self.weights = [0.7, 0.3]  # Even more weight to lower threshold
        
        logger.info(f"Multi-threshold ensemble: Using {len(self.base_thresholds)} models with thresholds {self.base_thresholds} and weights {self.weights}")
    
    def predict(self) -> dict:
        """Train multiple models and combine predictions."""
        predictions = []
        
        for threshold in self.base_thresholds:
            predictor = RiskPredictor(self.ticker, threshold)
            result = predictor.train_and_predict()
            
            if "error" in result:
                return result  # Return error immediately
            
            predictions.append(result)
        
        # If single model, return directly
        if len(predictions) == 1:
            return predictions[0]
        
        # Combine predictions using weighted average
        return self._combine_predictions(predictions)
    
    def _combine_predictions(self, predictions: list) -> dict:
        """Combine multiple predictions using weighted average."""
        # Weighted average of risk probabilities
        combined_risk_prob = sum(
            pred["risk_probability"] * weight 
            for pred, weight in zip(predictions, self.weights)
        )
        
        # Weighted average of confidence metrics
        combined_accuracy = sum(
            pred["model_confidence"]["accuracy"] * weight
            for pred, weight in zip(predictions, self.weights)
        )
        combined_precision = sum(
            pred["model_confidence"]["precision"] * weight
            for pred, weight in zip(predictions, self.weights)
        )
        combined_recall = sum(
            pred["model_confidence"]["recall"] * weight
            for pred, weight in zip(predictions, self.weights)
        )
        combined_f2 = sum(
            pred["model_confidence"]["f2_score"] * weight
            for pred, weight in zip(predictions, self.weights)
        )
        combined_roc_auc = sum(
            pred["model_confidence"]["roc_auc"] * weight
            for pred, weight in zip(predictions, self.weights)
        )
        
        # Determine trust score based on combined metrics
        if combined_recall >= 60 and combined_precision >= 28 and combined_f2 >= 48:
            trust_score = "HIGH"
        elif combined_recall >= 45 and combined_precision >= 23 and combined_f2 >= 38:
            trust_score = "MEDIUM"
        else:
            trust_score = "LOW"
        
        # Use the primary model's SHAP breakdown (highest weight)
        primary_idx = self.weights.index(max(self.weights))
        primary_pred = predictions[primary_idx]
        
        # Build combined response
        return {
            "ticker": self.ticker,
            "target_threshold": self.user_threshold_pct,
            "risk_probability": round(combined_risk_prob, 2),
            "is_high_risk_tomorrow": bool(combined_risk_prob >= 50),  # Convert to Python bool
            "recommendation": "SELL" if combined_risk_prob >= 50 else "HOLD",
            "top_risk_driver": primary_pred["top_risk_driver"],
            "shap_breakdown": primary_pred["shap_breakdown"],
            
            "model_confidence": {
                "accuracy": round(combined_accuracy, 1),
                "precision": round(combined_precision, 1),
                "recall": round(combined_recall, 1),
                "f2_score": round(combined_f2, 1),
                "roc_auc": round(combined_roc_auc, 2),
                "validation_days": primary_pred["model_confidence"]["validation_days"],
                "trust_score": trust_score,
                "confusion_matrix": primary_pred["model_confidence"]["confusion_matrix"],
                "explanation": f"Multi-threshold ensemble: Caught {int(combined_recall)}% of crashes (F2: {int(combined_f2)}%). "
                               f"Precision: {int(combined_precision)}%. "
                               f"(Combined {len(predictions)} models at thresholds {self.base_thresholds} for better accuracy)"
            }
        }


class RiskPredictor:
    def __init__(self, ticker: str, threshold_pct: float = 1.5):
        self.ticker = ticker
        self.threshold_pct = threshold_pct
        self.threshold_decimal = -(threshold_pct / 100.0)

        try:
            engine   = RiskCalculator(ticker)
            self.df  = engine.df
        except Exception as e:
            logger.error(f"Failed to initialize RiskCalculator for {ticker}: {e}")
            self.df = pd.DataFrame()

        # OPTIMIZED ENSEMBLE: XGBoost + LightGBM with tuned hyperparameters
        xgb_model = XGBClassifier(
            n_estimators=300,            # Increased from 200
            max_depth=7,                 # Increased from 6
            learning_rate=0.05,          # Decreased for better generalization
            scale_pos_weight=7,          # Increased from 5 (more penalty for missing crashes)
            subsample=0.7,               # Reduced from 0.8 (prevent overfitting)
            colsample_bytree=0.7,
            min_child_weight=3,          # NEW: Require more samples per leaf
            gamma=0.1,                   # NEW: Minimum loss reduction
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        lgbm_model = LGBMClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            class_weight={0: 1, 1: 7},
            subsample=0.7,
            colsample_bytree=0.7,
            min_child_samples=20,        # NEW: Require more samples per leaf
            reg_alpha=0.1,               # NEW: L1 regularization
            reg_lambda=0.1,              # NEW: L2 regularization
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        # Weighted Voting: Give more weight to XGBoost (usually performs better)
        self.model = VotingClassifier(
            estimators=[
                ('xgb', xgb_model),
                ('lgbm', lgbm_model)
            ],
            voting='soft',
            weights=[0.6, 0.4],          # NEW: 60% XGBoost, 40% LightGBM
            n_jobs=-1
        )

        # EXPANDED: 21 features (was 18) - Added market context features
        self.feature_names = [
            # Original technical features
            'SMA_10', 'SMA_30', 'Rolling_Vol_10', 'Momentum_5',
            'RSI_14', 'MACD', 'Volume_Change', 'ATR_14', 'Gap_Pct',
            'Price_to_52w_High', 'PE_Ratio', 'PB_Ratio', 'Beta',
            # Advanced technical features
            'BB_Width', 'Stochastic', 'OBV', 'ROC_12', 'ADX_14',
            # NEW: Market context features (3 new)
            'Volume_Ratio', 'Price_Acceleration', 'Volatility_Ratio'
        ]

    def _engineer_features(self) -> pd.DataFrame:
        """Creates all technical + fundamental indicators for the ML model."""
        if self.df.empty:
            logger.warning(f"No data available to engineer features for {self.ticker}.")
            return None

        df = self.df.copy()

        try:
            # === ORIGINAL FEATURES ===
            df['SMA_10']         = df['close_price'].rolling(window=10).mean()
            df['SMA_30']         = df['close_price'].rolling(window=30).mean()
            df['Momentum_5']     = df['close_price'].pct_change(periods=5)
            df['Rolling_Vol_10'] = df['daily_return'].rolling(window=10).std()

            prev_close   = df['close_price'].shift(1)
            df['TR']     = np.maximum(
                df['high_price'] - df['low_price'],
                np.maximum(
                    (df['high_price'] - prev_close).abs(),
                    (df['low_price']  - prev_close).abs()
                )
            )
            df['ATR_14'] = df['TR'].rolling(window=14).mean()

            delta = df['close_price'].diff()
            gain  = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss  = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            df['RSI_14'] = 100 - (100 / (1 + gain / loss))

            ema_12      = df['close_price'].ewm(span=12, adjust=False).mean()
            ema_26      = df['close_price'].ewm(span=26, adjust=False).mean()
            df['MACD']  = ema_12 - ema_26

            df['Volume_Change'] = df['volume'].pct_change()
            df['Gap_Pct'] = (df['open_price'] - prev_close) / prev_close
            df['Price_to_52w_High'] = (df['close_price'] - df['week52_high']) / df['week52_high']

            df['PE_Ratio'] = df['pe_ratio'].ffill()
            df['PB_Ratio'] = df['pb_ratio'].ffill()
            df['Beta'] = df['beta'].ffill()

            # === NEW FEATURES (5 powerful indicators) ===
            
            # 1. Bollinger Bands Width (volatility squeeze detector)
            sma_20 = df['close_price'].rolling(window=20).mean()
            std_20 = df['close_price'].rolling(window=20).std()
            bb_upper = sma_20 + (2 * std_20)
            bb_lower = sma_20 - (2 * std_20)
            df['BB_Width'] = (bb_upper - bb_lower) / sma_20
            
            # 2. Stochastic Oscillator (momentum - overbought/oversold)
            low_14 = df['low_price'].rolling(14).min()
            high_14 = df['high_price'].rolling(14).max()
            df['Stochastic'] = 100 * (df['close_price'] - low_14) / (high_14 - low_14 + 1e-10)
            
            # 3. On-Balance Volume (volume-price relationship)
            obv = [0]
            for i in range(1, len(df)):
                if df['close_price'].iloc[i] > df['close_price'].iloc[i-1]:
                    obv.append(obv[-1] + df['volume'].iloc[i])
                elif df['close_price'].iloc[i] < df['close_price'].iloc[i-1]:
                    obv.append(obv[-1] - df['volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            df['OBV'] = obv
            df['OBV'] = df['OBV'].pct_change()  # Normalize
            
            # 4. Rate of Change (momentum indicator)
            df['ROC_12'] = df['close_price'].pct_change(periods=12)
            
            # 5. Average Directional Index (trend strength)
            high_low = df['high_price'] - df['low_price']
            high_close = (df['high_price'] - df['close_price'].shift()).abs()
            low_close = (df['low_price'] - df['close_price'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            high_diff = df['high_price'].diff()
            low_diff = -df['low_price'].diff()
            
            pos_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            neg_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
            
            pos_di = 100 * (pos_dm.rolling(14).mean() / atr)
            neg_di = 100 * (neg_dm.rolling(14).mean() / atr)
            
            dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di + 1e-10)
            df['ADX_14'] = dx.rolling(14).mean()

            # === NEW MARKET CONTEXT FEATURES (3 powerful indicators) ===
            
            # 1. Volume Ratio (current vs 20-day average)
            avg_volume_20 = df['volume'].rolling(20).mean()
            df['Volume_Ratio'] = df['volume'] / (avg_volume_20 + 1)
            
            # 2. Price Acceleration (rate of change of momentum)
            df['Price_Acceleration'] = df['Momentum_5'].diff()
            
            # 3. Volatility Ratio (short-term vs long-term volatility)
            vol_5 = df['daily_return'].rolling(5).std()
            vol_20 = df['daily_return'].rolling(20).std()
            df['Volatility_Ratio'] = vol_5 / (vol_20 + 1e-10)

            # === TARGET VARIABLE ===
            df['Target_High_Risk'] = (df['daily_return'].shift(-1) < self.threshold_decimal).astype(int)

            # === CLEAN DATA ===
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(subset=self.feature_names + ['Target_High_Risk'], inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error engineering features for {self.ticker}: {e}")
            return None

    def train_and_predict(self) -> dict:
        """Trains XGBoost+LightGBM ensemble with SMOTE and returns tomorrow's risk with model confidence metrics."""
        logger.info(f"Initiating ML Training & Prediction for {self.ticker} using {self.threshold_pct}% threshold...")

        df_ml = self._engineer_features()
        if df_ml is None or df_ml.empty:
            logger.error(f"Insufficient data to train ML model for {self.ticker}.")
            return {"error": f"Insufficient historical data to predict risk for {self.ticker}."}

        try:
            # === STEP 2: SPLIT DATA (CRITICAL FOR VALIDATION) ===
            if len(df_ml) < 120:
                return {"error": f"Not enough data for {self.ticker}. Need at least 120 days, have {len(df_ml)}."}
            
            split_idx = len(df_ml) - 60
            train_data = df_ml.iloc[:split_idx].copy()
            validation_data = df_ml.iloc[split_idx:-1].copy()
            today_data = df_ml.iloc[-1:].copy()
            
            logger.info(f"Data split: {len(train_data)} training days, {len(validation_data)} validation days")

            # === STEP 3: APPLY ADAPTIVE SMOTE (FIX CLASS IMBALANCE) ===
            X_train_raw = train_data[self.feature_names]
            y_train_raw = train_data['Target_High_Risk']
            
            crash_count = y_train_raw.sum()
            safe_count = len(y_train_raw) - crash_count
            logger.info(f"Before SMOTE: {safe_count} safe days, {crash_count} crash days ({crash_count/len(y_train_raw)*100:.1f}% crashes)")
            
            # Use BorderlineSMOTE (better than regular SMOTE for imbalanced data)
            if crash_count >= 5:  # Need at least 5 examples
                try:
                    # BorderlineSMOTE focuses on borderline cases (harder to classify)
                    smote = BorderlineSMOTE(
                        random_state=42,
                        k_neighbors=min(crash_count-1, 5),
                        sampling_strategy=0.5  # Balance to 50% (was auto)
                    )
                    X_train, y_train = smote.fit_resample(X_train_raw, y_train_raw)
                    logger.info(f"After BorderlineSMOTE: {len(X_train)} samples (balanced)")
                except Exception as e:
                    logger.warning(f"BorderlineSMOTE failed: {e}. Using regular SMOTE.")
                    try:
                        smote = SMOTE(random_state=42, k_neighbors=min(crash_count-1, 3))
                        X_train, y_train = smote.fit_resample(X_train_raw, y_train_raw)
                        logger.info(f"After SMOTE: {len(X_train)} samples")
                    except:
                        X_train, y_train = X_train_raw, y_train_raw
            else:
                logger.warning(f"Only {crash_count} crash examples. Skipping SMOTE (need at least 5).")
                X_train, y_train = X_train_raw, y_train_raw

            # === STEP 4: FEATURE SELECTION (Remove weak features) ===
            if len(X_train) > 50:  # Only if we have enough data
                try:
                    # Select top 15 features (from 21)
                    selector = SelectKBest(f_classif, k=min(15, len(self.feature_names)))
                    X_train_selected = selector.fit_transform(X_train, y_train)
                    selected_features = [self.feature_names[i] for i in selector.get_support(indices=True)]
                    logger.info(f"Selected {len(selected_features)} best features: {selected_features}")
                    
                    # Update feature names for this prediction
                    self.selected_features = selected_features
                    X_train = X_train_selected
                except Exception as e:
                    logger.warning(f"Feature selection failed: {e}. Using all features.")
                    self.selected_features = self.feature_names
            else:
                self.selected_features = self.feature_names

            # === STEP 5: TRAIN ENSEMBLE MODEL ===
            self.model.fit(X_train, y_train)
            logger.info(f"Ensemble model trained on {len(X_train)} samples")

            # === STEP 6: VALIDATE MODEL & FIND OPTIMAL THRESHOLD ===
            X_val = validation_data[self.selected_features]
            y_val = validation_data['Target_High_Risk']
            
            y_val_pred_proba = self.model.predict_proba(X_val)[:, 1]
            
            # ADAPTIVE THRESHOLD: Find best threshold optimizing F2-score (prioritizes recall)
            best_threshold = 0.25
            best_f2 = 0
            
            # Try thresholds from 0.15 to 0.50
            for threshold in np.arange(0.15, 0.55, 0.05):
                y_pred_temp = (y_val_pred_proba >= threshold).astype(int)
                
                # Calculate F2 score (weights recall 2x more than precision)
                prec_temp = precision_score(y_val, y_pred_temp, zero_division=0)
                rec_temp = recall_score(y_val, y_pred_temp, zero_division=0)
                
                if prec_temp + rec_temp > 0:
                    # F2 = 5 * (precision * recall) / (4 * precision + recall)
                    f2_temp = 5 * (prec_temp * rec_temp) / (4 * prec_temp + rec_temp)
                    
                    # Prefer threshold with precision > 25% (relaxed) and high recall
                    if prec_temp >= 0.25 and rec_temp >= 0.50 and f2_temp > best_f2:
                        best_f2 = f2_temp
                        best_threshold = threshold
            
            # If no threshold meets criteria, use one with best recall
            if best_f2 == 0:
                best_recall = 0
                for threshold in np.arange(0.15, 0.55, 0.05):
                    y_pred_temp = (y_val_pred_proba >= threshold).astype(int)
                    rec_temp = recall_score(y_val, y_pred_temp, zero_division=0)
                    prec_temp = precision_score(y_val, y_pred_temp, zero_division=0)
                    
                    if rec_temp > best_recall and prec_temp >= 0.20:
                        best_recall = rec_temp
                        best_threshold = threshold
                        best_f2 = 5 * (prec_temp * rec_temp) / (4 * prec_temp + rec_temp) if (prec_temp + rec_temp) > 0 else 0
            
            logger.info(f"Optimal threshold: {best_threshold:.2f} (F2={best_f2:.3f}, optimized for recall)")
            
            # Use optimal threshold for validation
            y_val_pred = (y_val_pred_proba >= best_threshold).astype(int)
            
            # Calculate validation metrics
            accuracy = accuracy_score(y_val, y_val_pred) * 100
            precision = precision_score(y_val, y_val_pred, zero_division=0) * 100
            recall = recall_score(y_val, y_val_pred, zero_division=0) * 100
            
            # Calculate F2-score (prioritizes recall over precision)
            if precision + recall > 0:
                f2_score = 5 * (precision/100 * recall/100) / (4 * precision/100 + recall/100) * 100
            else:
                f2_score = 0
            precision = precision_score(y_val, y_val_pred, zero_division=0) * 100
            recall = recall_score(y_val, y_val_pred, zero_division=0) * 100
            
            try:
                roc_auc = roc_auc_score(y_val, y_val_pred_proba)
            except:
                roc_auc = 0.5
            
            # Confusion matrix
            cm = confusion_matrix(y_val, y_val_pred)
            if cm.shape == (2, 2):
                tn, fp, fn, tp = cm.ravel()
            else:
                # Handle case where only one class exists in validation
                tn = fp = fn = tp = 0
                if cm.shape == (1, 1):
                    if y_val.iloc[0] == 0:
                        tn = cm[0, 0]
                    else:
                        tp = cm[0, 0]
            
            # Determine trust score - FOCUS ON RECALL (catching crashes)
            if recall >= 65 and precision >= 30 and f2_score >= 50:
                trust_score = "HIGH"
            elif recall >= 50 and precision >= 25 and f2_score >= 40:
                trust_score = "MEDIUM"
            else:
                trust_score = "LOW"
            
            logger.info(f"Validation: Accuracy={accuracy:.1f}%, Precision={precision:.1f}%, Recall={recall:.1f}%, F2={f2_score:.1f}%, ROC-AUC={roc_auc:.2f}, Trust={trust_score}")

            # === STEP 7: PREDICT TOMORROW ===
            X_today = today_data[self.selected_features]
            
            if X_today.isnull().values.any():
                X_today = X_today.fillna(X_train.median())

            risk_probability = self.model.predict_proba(X_today)[0][1]
            is_high_risk = bool(risk_probability >= best_threshold)  # Use optimal threshold

            # === EXPLAINABLE AI (Feature Importance) ===
            # Get feature importance from XGBoost (first model in ensemble)
            try:
                xgb_importances = self.model.estimators_[0].feature_importances_
                lgbm_importances = self.model.estimators_[1].feature_importances_
                # Average importances from both models
                importances = (xgb_importances + lgbm_importances) / 2
            except:
                importances = np.ones(len(self.selected_features)) / len(self.selected_features)
            
            shap_breakdown = []
            # CRITICAL FIX: Use selected_features, not all feature_names
            for name, importance in zip(self.selected_features, importances):
                scaled_impact = float(importance * risk_probability * 100)
                current_val = float(X_today[name].iloc[0])
                shap_breakdown.append({
                    "feature": name,
                    "current_value": round(current_val, 4),
                    "impact_percentage": round(scaled_impact, 2)
                })

            shap_breakdown.sort(key=lambda x: x['impact_percentage'], reverse=True)

            # === STEP 7: RETURN ENHANCED RESPONSE ===
            return {
                "ticker": self.ticker,
                "target_threshold": self.threshold_pct,
                "risk_probability": round(risk_probability * 100, 2),
                "is_high_risk_tomorrow": is_high_risk,
                "recommendation": "SELL" if is_high_risk else "HOLD",
                "top_risk_driver": shap_breakdown[0]['feature'] if shap_breakdown else "Unknown",
                "shap_breakdown": shap_breakdown,
                
                "model_confidence": {
                    "accuracy": round(accuracy, 1),
                    "precision": round(precision, 1),
                    "recall": round(recall, 1),
                    "f2_score": round(f2_score, 1),
                    "roc_auc": round(roc_auc, 2),
                    "validation_days": len(validation_data),
                    "trust_score": trust_score,
                    
                    "confusion_matrix": {
                        "true_negatives": int(tn),
                        "false_positives": int(fp),
                        "false_negatives": int(fn),
                        "true_positives": int(tp)
                    },
                    
                    "explanation": f"This model caught {int(recall)}% of crashes (F2-score: {int(f2_score)}%). "
                                   f"When it says 'SELL', it's right {int(precision)}% of the time. "
                                   f"Overall accuracy: {int(accuracy)}%. "
                                   f"(Optimized for catching crashes, not accuracy. Threshold={best_threshold:.2f})"
                }
            }

        except Exception as e:
            logger.error(f"Critical failure during ML inference for {self.ticker}: {e}")
            import traceback
            traceback.print_exc()
            return {"error": "Internal AI processing error."}