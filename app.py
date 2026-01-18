import os
from os.path import join, dirname
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
from sofascore_api import FootballDataAPI
from betting_analyzer import BettingAnalyzer
import logging

app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize modules
api = FootballDataAPI()
analyzer = BettingAnalyzer()

# Cloud'da çalışmak için database yolu
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/betting_data.db'  # Cloud'da geçici storage
else:
    DB_PATH = 'betting_data.db'  # Local

def init_db():
    """SQLite veritabanını başlat"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            analysis TEXT NOT NULL,
            date TEXT NOT NULL,
            result TEXT,
            notes TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams_cache (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT UNIQUE,
            team_data TEXT,
            last_updated TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# API Endpoints

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Maç analizi yap
    İstek: { "home_team": "Fenerbahçe", "away_team": "Galatasaray" }
    """
    try:
        data = request.json
        home_team_name = data.get('home_team')
        away_team_name = data.get('away_team')
        
        if not home_team_name or not away_team_name:
            return jsonify({'error': 'Takım adları gerekli'}), 400
        
        logger.info(f"Analyzing: {home_team_name} vs {away_team_name}")
        
        # Takımları bul
        home_team_data = api.search_team(home_team_name)
        away_team_data = api.search_team(away_team_name)
        
        if not home_team_data or not away_team_data:
            return jsonify({'error': 'Takım bulunamadı'}), 404
        
        home_team_id = home_team_data['id']
        away_team_id = away_team_data['id']
        
        # Form verilerini al
        home_form = api.get_team_form(home_team_id, 5)
        away_form = api.get_team_form(away_team_id, 5)
        
        # H2H al
        h2h = api.get_head_to_head(home_team_id, away_team_id, 5)
        
        # Analiz yap
        analysis = analyzer.analyze_match(home_form, away_form, h2h)
        
        # Response oluştur
        response = {
            'home_team': home_team_name,
            'away_team': away_team_name,
            'home_win_prob': analysis['home_win_prob'],
            'draw_prob': analysis['draw_prob'],
            'away_win_prob': analysis['away_win_prob'],
            'over_2_5_prob': analysis['over_2_5_prob'],
            'under_2_5_prob': analysis['under_2_5_prob'],
            'both_teams_score': analysis['both_teams_score'],
            'recommendation': analysis['recommendation'],
            'risk_level': analysis['risk_level'],
            'detailed_analysis': {
                'form': analysis['detailed_analysis']['form'],
                'h2h': analysis['detailed_analysis']['h2h'],
                'goals': {
                    'home_scoring': analysis['detailed_analysis']['goals']['home_scoring'],
                    'away_scoring': analysis['detailed_analysis']['goals']['away_scoring'],
                    'home_gf_avg': analysis['detailed_analysis']['goals']['home_gf_avg'],
                    'away_gf_avg': analysis['detailed_analysis']['goals']['away_gf_avg'],
                    'expected_goals': analysis['detailed_analysis']['goals']['expected_goals']
                },
                'defense': analysis['detailed_analysis']['defense']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Analiz hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/save-bet', methods=['POST'])
def save_bet():
    """
    Yapılan iddiaları kaydet
    """
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO bets (home_team, away_team, analysis, date)
            VALUES (?, ?, ?, ?)
        ''', (
            data['home_team'],
            data['away_team'],
            json.dumps(data['analysis']),
            data['date']
        ))
        
        conn.commit()
        bet_id = c.lastrowid
        conn.close()
        
        logger.info(f"Bet saved: ID {bet_id}")
        return jsonify({'success': True, 'bet_id': bet_id})
    
    except Exception as e:
        logger.error(f"Bet save error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/bets', methods=['GET'])
def get_bets():
    """
    Tüm kaydedilmiş iddiaları getir
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM bets ORDER BY date DESC')
        rows = c.fetchall()
        
        bets = []
        for row in rows:
            bet = dict(row)
            bet['analysis'] = json.loads(bet['analysis'])
            bets.append(bet)
        
        conn.close()
        return jsonify(bets)
    
    except Exception as e:
        logger.error(f"Get bets error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/bets/<int:bet_id>', methods=['GET'])
def get_bet(bet_id):
    """
    Belirli bir iddianın detaylarını getir
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM bets WHERE id = ?', (bet_id,))
        row = c.fetchone()
        
        conn.close()
        
        if not row:
            return jsonify({'error': 'Iddia bulunamadı'}), 404
        
        bet = dict(row)
        bet['analysis'] = json.loads(bet['analysis'])
        
        return jsonify(bet)
    
    except Exception as e:
        logger.error(f"Get bet error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/bets/<int:bet_id>/result', methods=['PUT'])
def update_bet_result(bet_id):
    """
    İddianın sonucunu güncelle
    İstek: { "result": "win/loss/pending", "notes": "açıklama" }
    """
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            UPDATE bets 
            SET result = ?, notes = ?
            WHERE id = ?
        ''', (data.get('result'), data.get('notes'), bet_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Bet {bet_id} result updated: {data.get('result')}")
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Update bet error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    İstatistiksel özet (win rate vs)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                COUNT(*) as total_bets,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result IS NULL THEN 1 ELSE 0 END) as pending
            FROM bets
        ''')
        
        row = c.fetchone()
        conn.close()
        
        stats = {
            'total_bets': row[0] or 0,
            'wins': row[1] or 0,
            'losses': row[2] or 0,
            'pending': row[3] or 0,
        }
        
        if stats['total_bets'] > 0:
            stats['win_rate'] = stats['wins'] / stats['total_bets'] * 100
        else:
            stats['win_rate'] = 0
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/teams/search', methods=['GET'])
def search_teams():
    """
    Takım arama (autocomplete için)
    """
    try:
        query = request.args.get('q', '')
        
        if len(query) < 2:
            return jsonify([])
        
        team = api.search_team(query)
        
        if team:
            return jsonify([{
                'id': team['id'],
                'name': team['name']
            }])
        
        return jsonify([])
    
    except Exception as e:
        logger.error(f"Team search error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Sunucunun sağlık kontrolü
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/matches/today', methods=['GET'])
def get_todays_matches():
    """
    Bugünün maçlarını getir (Süper Lig ve Avrupa)
    """
    try:
        matches = api.get_todays_matches()
        
        return jsonify({
            'success': True,
            'matches': matches,
            'count': len(matches)
        })
    
    except Exception as e:
        logger.error(f"Today's matches error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Hata yönetimi
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint bulunamadı'}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Sunucu hatası'}), 500


if __name__ == '__main__':
    # Veritabanını başlat
    init_db()
    
    # Port'u environment variable'dan al
    port = int(os.environ.get('PORT', 5000))
    
    # Sunucuyu başlat
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )
