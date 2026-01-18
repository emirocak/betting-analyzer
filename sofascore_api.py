import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SofascoreAPI:
    """
    Sofascore'dan istatistik çeken API wrapper
    Resmi API değil ama çalıştığı sürece sorun yok (kişisel kullanım için)
    """
    
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """
        Takım ID'sini bul
        Örnek: search_team("Fenerbahçe")
        """
        try:
            url = f"{self.base_url}/search/team"
            params = {'q': team_name}
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                if results.get('results'):
                    return results['results'][0]
            return None
        except Exception as e:
            print(f"❌ Takım araması hatası: {e}")
            return None
    
    def get_team_matches(self, team_id: int, limit: int = 5) -> List[Dict]:
        """
        Takımın son maçlarını al
        """
        try:
            url = f"{self.base_url}/team/{team_id}/events/last/{limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('events', [])
            return []
        except Exception as e:
            print(f"❌ Maç listesi hatası: {e}")
            return []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """
        Maçın detaylı istatistiklerini al
        - Gol dakikaları
        - Gol atan oyuncular
        - Tüm maç olayları
        - İstatistikler
        """
        try:
            url = f"{self.base_url}/event/{match_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Maç detayları hatası: {e}")
            return None
    
    def parse_goals(self, match_data: Dict) -> List[Dict]:
        """
        Maç verisinden gol bilgilerini çıkar
        """
        goals = []
        
        if not match_data:
            return goals
        
        # Maç olaylarını tara
        events = match_data.get('event', {}).get('events', [])
        
        for event in events:
            # Gol olaylarını bul (type: 16 = goal)
            if event.get('type') == 16:
                goal_info = {
                    'minute': event.get('minute'),
                    'second': event.get('second'),
                    'player_name': event.get('player', {}).get('name'),
                    'player_id': event.get('player', {}).get('id'),
                    'team': event.get('team', {}).get('name'),
                    'team_id': event.get('team', {}).get('id'),
                    'assist_player': None,
                    'assist_id': None,
                }
                
                # Asist bilgisini kontrol et
                if event.get('assist'):
                    goal_info['assist_player'] = event.get('assist', {}).get('name')
                    goal_info['assist_id'] = event.get('assist', {}).get('id')
                
                # Penaltı mı kontrol et
                if event.get('isOwnGoal'):
                    goal_info['own_goal'] = True
                
                goals.append(goal_info)
        
        return goals
    
    def parse_statistics(self, match_data: Dict) -> Dict:
        """
        Maç istatistiklerini parse et
        """
        stats = {
            'home_team': {},
            'away_team': {}
        }
        
        if not match_data:
            return stats
        
        match_info = match_data.get('event', {})
        
        # İstatistikleri al
        statistics = match_info.get('statistics', [])
        
        for stat_group in statistics:
            group_name = stat_group.get('groupName', '')
            
            for stat in stat_group.get('statistics', []):
                stat_type = stat.get('name')
                home_value = stat.get('home')
                away_value = stat.get('away')
                
                stats['home_team'][stat_type] = home_value
                stats['away_team'][stat_type] = away_value
        
        return stats
    
    def get_team_form(self, team_id: int, last_matches: int = 5) -> Dict:
        """
        Takımın formunu hesapla (son N maç)
        """
        matches = self.get_team_matches(team_id, last_matches)
        
        form_data = {
            'form': [],  # W, D, L
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'last_matches': []
        }
        
        for match in matches:
            home_team = match.get('homeTeam', {})
            away_team = match.get('awayTeam', {})
            home_score = match.get('homeScore', {}).get('current', 0)
            away_score = match.get('awayScore', {}).get('current', 0)
            status = match.get('status')
            
            # Eğer bu takım maçını kontrol et
            is_home = home_team.get('id') == team_id
            
            if status == 'finished':
                if is_home:
                    team_goals = home_score
                    opponent_goals = away_score
                else:
                    team_goals = away_score
                    opponent_goals = home_score
                
                form_data['goals_for'] += team_goals
                form_data['goals_against'] += opponent_goals
                
                if team_goals > opponent_goals:
                    form_data['wins'] += 1
                    form_data['form'].append('W')
                elif team_goals == opponent_goals:
                    form_data['draws'] += 1
                    form_data['form'].append('D')
                else:
                    form_data['losses'] += 1
                    form_data['form'].append('L')
                
                form_data['last_matches'].append({
                    'opponent': away_team.get('name') if is_home else home_team.get('name'),
                    'home': is_home,
                    'score': f"{team_goals}-{opponent_goals}",
                    'date': match.get('startTimestamp')
                })
        
        form_data['goal_difference'] = form_data['goals_for'] - form_data['goals_against']
        
        return form_data
    
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> Dict:
        """
        İki takım arasındaki son maçlar
        """
        try:
            url = f"{self.base_url}/team/{team1_id}/events/last/100"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                all_matches = response.json().get('events', [])
                h2h_matches = [
                    m for m in all_matches 
                    if (m.get('homeTeam', {}).get('id') == team2_id or 
                        m.get('awayTeam', {}).get('id') == team2_id)
                ][:limit]
                
                h2h = {
                    'team1_wins': 0,
                    'team2_wins': 0,
                    'draws': 0,
                    'matches': []
                }
                
                for match in h2h_matches:
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    home_score = match.get('homeScore', {}).get('current', 0)
                    away_score = match.get('awayScore', {}).get('current', 0)
                    
                    is_home = home_team.get('id') == team1_id
                    
                    if home_score > away_score:
                        if is_home:
                            h2h['team1_wins'] += 1
                        else:
                            h2h['team2_wins'] += 1
                    elif home_score < away_score:
                        if is_home:
                            h2h['team2_wins'] += 1
                        else:
                            h2h['team1_wins'] += 1
                    else:
                        h2h['draws'] += 1
                    
                    h2h['matches'].append({
                        'date': match.get('startTimestamp'),
                        'home': home_team.get('name'),
                        'away': away_team.get('name'),
                        'score': f"{home_score}-{away_score}",
                        'winner': 'home' if home_score > away_score else ('away' if away_score > home_score else 'draw')
                    })
                
                return h2h
        except Exception as e:
            print(f"❌ H2H hatası: {e}")
        
        return None
    
    def get_todays_matches(self):
        """
        Bugünün maçlarını getir (Süper Lig ve Avrupa)
        """
        try:
            from datetime import datetime
            
            # Bugünün tarihini al
            today = datetime.now().strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/sport/football/events"
            params = {
                'date': today,
                'status': 'notstarted'  # Henüz başlamamış maçlar
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('events', [])
                
                # Süper Lig ve Avrupa maçlarını filtrele
                filtered_matches = self._filter_league_matches(matches)
                
                return filtered_matches
            
            return []
        
        except Exception as e:
            print(f"❌ Bugün maçları hatası: {e}")
            return []
    
    def _filter_league_matches(self, matches):
        """
        Süper Lig ve Avrupa maçlarını filtrele
        """
        filtered = []
        
        # Aranan ligler
        target_leagues = [
            'Super Lig',           # Türkiye
            'Champions League',    # Avrupa
            'Europa League',       # Avrupa
            'Conference League',   # Avrupa
            'La Liga',            # İspanya
            'Premier League',      # İngiltere
            'Serie A',            # İtalya
            'Bundesliga',         # Almanya
            'Ligue 1',            # Fransa
        ]
        
        for match in matches:
            tournament = match.get('tournament', {})
            league_name = tournament.get('name', '')
            
            # Eğer hedef liglerden biriyse ekle
            if any(league in league_name for league in target_leagues):
                home_team = match.get('homeTeam', {})
                away_team = match.get('awayTeam', {})
                
                match_info = {
                    'id': match.get('id'),
                    'home_team': home_team.get('name'),
                    'home_team_id': home_team.get('id'),
                    'away_team': away_team.get('name'),
                    'away_team_id': away_team.get('id'),
                    'start_time': match.get('startTimestamp'),
                    'league': league_name,
                    'status': match.get('status'),
                }
                
                filtered.append(match_info)
        
        # Saate göre sırala
        filtered.sort(key=lambda x: x['start_time'] if x['start_time'] else 0)
        
        return filtered


# Örnek kullanım
if __name__ == "__main__":
    api = SofascoreAPI()
    
    print("⚽ SOFASCORE API WRAPPER")
    print("=" * 50)
    
    # Fenerbahçe'yi bul
    print("\n🔍 Fenerbahçe'yi aranıyor...")
    fenerbahce = api.search_team("Fenerbahçe")
    if fenerbahce:
        fb_id = fenerbahce['id']
        print(f"✅ Fenerbahçe ID: {fb_id}")
        
        # Son maçlarını al
        print("\n📊 Fenerbahçe'nin Son 5 Maçı:")
        form = api.get_team_form(fb_id, 5)
        print(f"Form: {' '.join(form['form'])}")
        print(f"Kazanç/Beraberlik/Kaybı: {form['wins']}W-{form['draws']}D-{form['losses']}L")
        print(f"Atılan/Yenen: {form['goals_for']}/{form['goals_against']}")
        
        # Galatasaray'ı bul
        print("\n🔍 Galatasaray'ı aranıyor...")
        galatasaray = api.search_team("Galatasaray")
        if galatasaray:
            gs_id = galatasaray['id']
            print(f"✅ Galatasaray ID: {gs_id}")
            
            # H2H
            print(f"\n🔄 Fenerbahçe vs Galatasaray (Son 5):")
            h2h = api.get_head_to_head(fb_id, gs_id, 5)
            if h2h:
                print(f"Fenerbahçe: {h2h['team1_wins']}W")
                print(f"Galatasaray: {h2h['team2_wins']}W")
                print(f"Beraberlikler: {h2h['draws']}")
    
    # Maç detaylarını al (örnek maç ID'si)
    print("\n📋 Maç Detayları Örneği:")
    # Bu bölüm belirli bir maç ID'si ile çalışır
    
    def get_todays_matches(self):
        """
        Bugünün maçlarını getir (Süper Lig ve Avrupa)
        """
        try:
            from datetime import datetime, timedelta
            
            # Bugünün tarihini al
            today = datetime.now().strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/sport/football/events"
            params = {
                'date': today,
                'status': 'notstarted'  # Henüz başlamamış maçlar
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('events', [])
                
                # Süper Lig ve Avrupa maçlarını filtrele
                filtered_matches = self._filter_league_matches(matches)
                
                return filtered_matches
            
            return []
        
        except Exception as e:
            print(f"❌ Bugün maçları hatası: {e}")
            return []
    
    def _filter_league_matches(self, matches):
        """
        Süper Lig ve Avrupa maçlarını filtrele
        """
        filtered = []
        
        # Aranan ligler
        target_leagues = [
            'Super Lig',           # Türkiye
            'Champions League',    # Avrupa
            'Europa League',       # Avrupa
            'Conference League',   # Avrupa
            'La Liga',            # İspanya
            'Premier League',      # İngiltere
            'Serie A',            # İtalya
            'Bundesliga',         # Almanya
            'Ligue 1',            # Fransa
        ]
        
        for match in matches:
            tournament = match.get('tournament', {})
            league_name = tournament.get('name', '')
            
            # Eğer hedef liglerden biriyse ekle
            if any(league in league_name for league in target_leagues):
                home_team = match.get('homeTeam', {})
                away_team = match.get('awayTeam', {})
                
                match_info = {
                    'id': match.get('id'),
                    'home_team': home_team.get('name'),
                    'home_team_id': home_team.get('id'),
                    'away_team': away_team.get('name'),
                    'away_team_id': away_team.get('id'),
                    'start_time': match.get('startTimestamp'),
                    'league': league_name,
                    'status': match.get('status'),
                }
                
                filtered.append(match_info)
        
        # Saate göre sırala
        filtered.sort(key=lambda x: x['start_time'])
        
        return filtered