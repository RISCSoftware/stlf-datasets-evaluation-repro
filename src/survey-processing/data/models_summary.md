🔍 Summary of Load Forecasting Modeling Approaches
1. Pure Univariate Models

    Approach: Use only the historical load time series to predict future values.
    Common Models: (Bi)LSTM, GRU, TCN, SVR, GBT, ARIMA.
    Note: Most models inherently support this baseline.

2. Feature Compression + Univariate Models

    Approach:
        Compress time series features (e.g., with Autoencoders (AE) or 1D CNNs).
        Feed compressed representations into univariate models.
    Goal: Dimensionality reduction before forecasting.

3. Multidimensional Feature Compression + Multivariate Models

    Approach:
        Extract features via CNN, functional PCA (fPCA), or similar methods.
        Features often handpicked by domain experts.
        Then forecast using multivariate models.
    Motivation: Leverage multiple relevant features beyond just the target series.

4. Pretrained Deep Models + Explainable Wrapper

    Approach:
        Use powerful pretrained architectures (e.g., xLSTMs, TOTEM, momentFM).
        Wrap them with interpretable models like Gradient Boosted Trees (GBT) or Symbolic Regression (SymReg).
    Goal: Combine performance and interpretability.
    Note: Currently xLSTM/SymReg not in active use yet, but under consideration.

5. Signal Decomposition + Multivariate Model

    Approach:
        Decompose the input signal (e.g., via Empirical Mode Decomposition (EMD) or Loess smoothing).
        Model each component or recombined components using multivariate models.

6. Multivariate Decomposition (e.g., MEMD) + Loess

    Approach:
        Decompose multiple time series via Multivariate EMD (MEMD).
        Apply Loess (or similar smoother) afterward for component-wise modeling.

7. Embedding-based Forecasting

    Approach:
        Use pretrained or learned embeddings from historical data.
        Feed those embeddings into forecasting models.
    Example: Embeddings from transformers or encoders used as features.

8. Wavelet Decomposition + Forecasting Models

    Approach:
        Apply wavelet transform to extract time-frequency components.
        Model wavelet subcomponents individually or collectively.

⚙️ Model Combinations & Hybrids

    Frequently used combinations:
        CNN-LSTM, LSTM-AM (Attention Mechanism), etc.
        Combining spatial feature extractors (CNNs) with temporal models (LSTM, TCN).

📌 Remarks

    Model types used most frequently: (Bi)LSTM, GRU, CNN, TCN, SVR, GBT, Attention Mechanisms (AM).
    Under exploration: xLSTMs and symbolic regression (SymReg).
    Trend: Increasing use of explainable AI (XAI) techniques alongside black-box models.
