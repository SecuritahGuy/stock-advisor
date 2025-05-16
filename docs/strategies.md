# Trading Strategies

Stock Advisor implements several trading strategies based on technical indicators. This document explains how each strategy works and how to configure it.

## 1. Moving Average Crossover with RSI Filter

### Overview

This strategy combines trend-following signals from moving average crossovers with momentum confirmation from the Relative Strength Index (RSI).

### Mathematical Rules

- **Buy Signal**: 
  - Fast MA crosses above Slow MA (golden cross)
  - AND RSI is above oversold threshold (>30) but below overbought (<70)
  
- **Sell Signal**:
  - Fast MA crosses below Slow MA (death cross)
  - OR RSI exceeds overbought threshold (>70)

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fast_ma` | 50 | Fast moving average period |
| `slow_ma` | 200 | Slow moving average period |
| `rsi_period` | 14 | RSI calculation period |
| `rsi_oversold` | 30 | RSI level considered oversold |
| `rsi_overbought` | 70 | RSI level considered overbought |

### Example Usage

```bash
python backtest.py --ticker SPY --strategy ma_crossover --fast-ma 50 --slow-ma 200 --rsi-period 14
```

## 2. Bollinger Bands Mean Reversion/Breakout

### Overview

This strategy uses Bollinger Bands to identify potential mean reversion opportunities (price returning to the middle band) or breakout signals (strong momentum beyond bands).

### Mathematical Rules

**Mean Reversion Mode**:
- **Buy Signal**: Price touches or crosses below the lower band AND RSI is oversold (<30)
- **Sell Signal**: Price touches or crosses above the middle band OR above upper band

**Breakout Mode**:
- **Buy Signal**: Price crosses above the upper band with increasing volume
- **Sell Signal**: Price crosses below the middle band OR below the lower band with increasing volume

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bb_length` | 20 | Bollinger Bands calculation period |
| `bb_std` | 2.0 | Standard deviation multiplier for bands |
| `rsi_period` | 14 | RSI calculation period |
| `breakout` | False | Enable breakout mode instead of mean reversion |

### Example Usage

```bash
# Mean reversion strategy
python test_bbands.py AAPL --bb-length 20 --rsi-period 14

# Breakout strategy
python test_bbands.py MSFT --breakout --bb-length 20
```

## 3. MACD + Stochastic Momentum

### Overview

This strategy combines MACD (Moving Average Convergence Divergence) for trend detection with Stochastic Oscillator for momentum confirmation and entry/exit timing.

### Mathematical Rules

- **Buy Signal**:
  - MACD line crosses above Signal line
  - AND Stochastic %K crosses above %D while both are below oversold threshold
  
- **Sell Signal**:
  - MACD line crosses below Signal line
  - OR Stochastic %K crosses below %D while both are above overbought threshold

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `macd_fast` | 12 | MACD fast period |
| `macd_slow` | 26 | MACD slow period |
| `macd_signal` | 9 | MACD signal line period |
| `stoch_k` | 14 | Stochastic %K period |
| `stoch_d` | 3 | Stochastic %D period |
| `stoch_smooth` | 3 | Stochastic smoothing |
| `stoch_oversold` | 20 | Stochastic oversold threshold |
| `stoch_overbought` | 80 | Stochastic overbought threshold |

### Example Usage

```bash
python test_macd_stoch.py SPY --macd-fast 12 --macd-slow 26 --macd-signal 9 --stoch-k 14 --stoch-d 3
```

## Creating Your Own Strategy

You can extend the Stock Advisor framework with your own strategy by:

1. Creating a new class in `app/strategy/` that inherits from `BaseStrategy`
2. Implementing the required methods: `calculate_indicators()` and `generate_signals()`
3. Registering your strategy in the strategy factory

See the existing strategy implementations for examples.
