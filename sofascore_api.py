import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FootballDataAPI:
    """
    Football-Data.org API wrapper
    Süper Lig ve Avrupa maçlarını çekebiliyor
    """
    
    def __init__(self, api_token='16a1f2ff9ac9490a8a31b3847722856e'):
        self.base_url = "https://api.football-data.org/v4"
        self.api_token = api_token
        self.headers = {
            'X-Auth-Token': api_token,
            'User-Agent': 'BettingAnalyzer/1.0'
        }
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """Takım ID'sini bul"""
        try:
            url = f"{self.base_url}/teams"
            params = {'name': team_name}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                teams = data.get('teams', [])
                if teams:
                    return teams[0]
            return None
        except Exception as e:
            print(f"❌ Takım araması hatası: {e}")
            return None
    
    def get_team_form(self, team_id: int, last_matches: int = 5) -> Dict:
        """Takımın son maçlarını ve formunu al"""
        try:
            url = f"{self.base_url}/teams/{team_id}/matches"
            params = {'limit': last_matches, 'status': 'FINISHED'}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                form_data = {
                    'form': [],
                    'wins': 0,
                    'draws': 0,
                    'losses': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'goal_difference': 0,
                    'last_matches': []
                }
                
                for match in matches:
                    status = match.get('status')
                    if status != 'FINISHED':
                        continue
                    
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    home_score = match.get('score', {}).get('fullTime', {}).get('home', 0)
                    away_score = match.get('score', {}).get('fullTime', {}).get('away', 0)
                    
                    is_home = home_team.get('id') == team_id
                    
                    if is_home:
                        team_goals = home_score
                        opponent_goals = away_score
                        opponent_name = away_team.get('name')
                    else:
                        team_goals = away_score
                        opponent_goals = home_score
                        opponent_name = home_team.get('name')
                    
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
                        'opponent': opponent_name,
                        'home': is_home,
                        'score': f"{team_goals}-{opponent_goals}",
                        'date': match.get('utcDate')
                    })
                
                form_data['goal_difference'] = form_data['goals_for'] - form_data['goals_against']
                
                return form_data
            
            return {
                'form': [],
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
            }
        
        except Exception as e:
            print(f"❌ Form hatası: {e}")
            return {
                'form': [],
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
            }
    
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> Dict:
        """İki takım arasındaki son maçlar"""
        try:
            url = f"{self.base_url}/teams/{team1_id}/matches"
            params = {'limit': 50, 'status': 'FINISHED'}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                all_matches = data.get('matches', [])
                
                h2h_matches = []
                for match in all_matches:
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    
                    if (home_team.get('id') == team2_id or away_team.get('id') == team2_id):
                        h2h_matches.append(match)
                    
                    if len(h2h_matches) >= limit:
                        break
                
                h2h = {
                    'team1_wins': 0,
                    'team2_wins': 0,
                    'draws': 0,
                    'matches': []
                }
                
                for match in h2h_matches:
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    home_score = match.get('score', {}).get('fullTime', {}).get('home', 0)
                    away_score = match.get('score', {}).get('fullTime', {}).get('away', 0)
                    
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
                        'date': match.get('utcDate'),
                        'home': home_team.get('name'),
                        'away': away_team.get('name'),
                        'score': f"{home_score}-{away_score}",
                        'winner': 'home' if home_score > away_score else ('away' if away_score > home_score else 'draw')
                    })
                
                return h2h
        
        except Exception as e:
            print(f"❌ H2H hatası: {e}")
        
        return {
            'team1_wins': 0,
            'team2_wins': 0,
            'draws': 0,
            'matches': []
        }
    
    def get_todays_matches(self) -> List[Dict]:
        """Bugünün maçlarını getir (tüm ligler)"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/matches"
            params = {
                'dateFrom': today,
                'dateTo': tomorrow,
                'status': 'SCHEDULED'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                # İstediğimiz ligleri filtrele
                target_league_codes = ['SA', 'CL', 'EL', 'EC', 'PD', 'PL', 'BL1', 'FL1']
                
                filtered_matches = [
                    m for m in matches 
                    if m.get('competition', {}).get('code') in target_league_codes
                ]
                
                # Saate göre sırala
                filtered_matches.sort(key=lambda x: x.get('utcDate', ''))
                
                result = []
                for match in filtered_matches:
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    competition = match.get('competition', {})
                    
                    match_info = {
                        'id': match.get('id'),
                        'home_team': home_team.get('name'),
                        'home_team_id': home_team.get('id'),
                        'away_team': away_team.get('name'),
                        'away_team_id': away_team.get('id'),
                        'start_time': match.get('utcDate'),
                        'league': competition.get('name'),
                        'status': match.get('status'),
                    }
                    result.append(match_info)
                
                return result
            
            return []
        
        except Exception as e:
            print(f"❌ Bugün maçları hatası: {e}")
            return []


# Örnek kullanım
if __name__ == "__main__":
    api = FootballDataAPI()
    
    print("⚽ FOOTBALL-DATA API WRAPPER")
    print("=" * 50)
    
    # Bugünün maçlarını al
    print("\n📅 Bugünün Maçları:")
    matches = api.get_todays_matches()
    print(f"Toplam: {len(matches)} maç")
    
    for match in matches[:3]:
        print(f"\n{match['league']}")
        print(f"{match['home_team']} vs {match['away_team']}")
        print(f"Saat: {match['start_time']}")
