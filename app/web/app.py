"""
Flask web application for Stock Advisor dashboard.
"""
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path
import sys
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import app modules
from app.portfolio.portfolio import Portfolio
from app.portfolio.valuation import get_portfolio_valuation, get_portfolio_metrics
from app.strategy.signal import get_recent_signals
from app.screener.discover import get_candidates, find_candidates
from app.data.data_fetch import fetch_stock_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("web_app")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock-advisor-secret-key'

# Initialize portfolio
portfolio = Portfolio(name="default")


@app.route('/')
def index():
    """Render main dashboard page."""
    return render_template('index.html', title='Stock Advisor Dashboard')


@app.route('/portfolio')
def portfolio_view():
    """Render portfolio page with current positions and performance."""
    try:
        # Get portfolio data
        portfolio_data = get_portfolio_valuation(portfolio)
        metrics = get_portfolio_metrics(portfolio, period='1mo')
        
        return render_template(
            'portfolio.html',
            title='Portfolio',
            portfolio_data=portfolio_data,
            metrics=metrics
        )
    except Exception as e:
        logger.error(f"Error getting portfolio data: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/signals')
def signals_view():
    """Render signals page with recent trading signals."""
    try:
        # Get recent signals
        signals = get_recent_signals(limit=20)
        
        return render_template(
            'signals.html', 
            title='Trading Signals',
            signals=signals
        )
    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/discovery')
def discovery_view():
    """Render discovery page with stock candidates."""
    try:
        # Get recent candidates
        days = int(request.args.get('days', 7))
        top_n = int(request.args.get('top_n', 20))
        
        candidates = get_candidates(days=days, top_n=top_n)
        
        return render_template(
            'discovery.html',
            title='Stock Discovery',
            candidates=candidates,
            days=days,
            top_n=top_n
        )
    except Exception as e:
        logger.error(f"Error getting discovery candidates: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/run_discovery', methods=['POST'])
def run_discovery():
    """Run a new discovery scan with specified strategy."""
    try:
        strategy = request.form.get('strategy', 'oversold_reversals')
        limit = int(request.form.get('limit', 20))
        min_price = float(request.form.get('min_price', 5))
        max_price = float(request.form.get('max_price', 200))
        
        # Run discovery scan
        results = find_candidates(
            strategy=strategy,
            limit=limit,
            min_price=min_price,
            max_price=max_price
        )
        
        return redirect(url_for('discovery_view'))
    except Exception as e:
        logger.error(f"Error running discovery: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/chart/<ticker>')
def chart_view(ticker):
    """Render stock chart page."""
    try:
        # Fetch stock data
        period = request.args.get('period', '6mo')
        interval = request.args.get('interval', '1d')
        
        # Get stock data
        stock_data = fetch_stock_data(ticker, interval=interval, period=period)
        
        # Convert to dict for JSON serialization
        if not stock_data.empty:
            chart_data = {
                'dates': stock_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
                'prices': stock_data['Close'].tolist(),
                'volumes': stock_data['Volume'].tolist() if 'Volume' in stock_data.columns else []
            }
        else:
            chart_data = {'dates': [], 'prices': [], 'volumes': []}
        
        return render_template(
            'chart.html',
            title=f'{ticker} Chart',
            ticker=ticker,
            chart_data=chart_data,
            period=period,
            interval=interval
        )
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return render_template('error.html', error=str(e))


@app.route('/api/portfolio/data')
def api_portfolio_data():
    """API endpoint for portfolio data."""
    try:
        portfolio_data = get_portfolio_valuation(portfolio)
        return jsonify(portfolio_data)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/metrics')
def api_portfolio_metrics():
    """API endpoint for portfolio metrics."""
    try:
        period = request.args.get('period', '1mo')
        metrics = get_portfolio_metrics(portfolio, period=period)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals')
def api_signals():
    """API endpoint for trading signals."""
    try:
        limit = int(request.args.get('limit', 20))
        signals = get_recent_signals(limit=limit)
        
        # Convert signals to dictionary for JSON serialization
        signals_data = []
        for signal in signals:
            signals_data.append({
                'ticker': signal.ticker,
                'action': signal.action.value,
                'price': signal.price,
                'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'strength': signal.strength.value,
                'reason': signal.reason
            })
        
        return jsonify(signals_data)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/discovery')
def api_discovery():
    """API endpoint for discovery candidates."""
    try:
        days = int(request.args.get('days', 7))
        top_n = int(request.args.get('top_n', 20))
        
        candidates = get_candidates(days=days, top_n=top_n)
        
        # Convert DataFrame to dictionary for JSON serialization
        if not candidates.empty:
            candidates_data = candidates.to_dict(orient='records')
        else:
            candidates_data = []
        
        return jsonify(candidates_data)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
