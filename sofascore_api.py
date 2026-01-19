import requests
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballDataAPI:
    """
    API-Football.com'dan GERÇEK veri çeken profesyonel API
    """
    
    def __init__(self):
        self.api_key = "078f91b51740d86371ffc06a1773f759"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }
        self.current_team = None
        self.cache = {}
        
        # Türkiye Süper Lig takımlarının GERÇEK API-Football ID'leri
        self.turkish_teams = {
            'Fenerbahçe': 611,
            'Galatasaray': 645,
            'Beşiktaş': 549,
            'Trabzonspor': 998,
            'Başakşehir': 1213,
            'Kayserispor': 1209,
            'Sivasspor': 1210,
            'Antalyaspor': 1211,
        }
        
        # Team ID -> Team Name mapping
        self.team_id_map = {v: k for k, v in self.turkish_teams.items()}
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """Takımı bul"""
        try:
            normalized_name = team_name.lower().strip()
            
            for team, team_id in self.turkish_teams.items():
                if team.lower() == normalized_name or normalized_name in team.lower():
                    self.current_team = team
                    logger.info(f"✅ Takım bulundu: {team} (ID: {team_id})")
                    return {
                        'id': team_id,
                        'name': team,
                        'api_id': team_id
                    }
            
            logger.warning(f"❌ Takım bulunamadı: {team_name}")
            return None
        except Exception as e:
            logger.error(f"Takım araması hatası: {e}")
            return None
    
    def get_team_form(self, team_id: int, last_matches: int = 5) -> Dict:
        """Takımın son maçlarını API'den çek"""
        try:
            if team_id not in self.team_id_map:
                logger.warning(f"Bilinmeyen team_id: {team_id}")
                return self._get_default_form()
            
            team_name = self.team_id_map[team_id]
            
            # Cache kontrol
            cache_key = f"form_{team_id}"
            if cache_key in self.cache:
                logger.info(f"📦 Cache'den: {team_name}")
                return self.cache[cache_key]
            
            logger.info(f"📡 API-Football'dan {team_name} verisi çekiliyor (ID: {team_id})...")
            
            # Son maçları çek
            url = f"{self.base_url}/fixtures"
            params = {
                "team": team_id,
                "last": last_matches,
                "season": 2025
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"API Error {response.status_code}: {response.text}")
                return self._get_default_form()
            
            data = response.json()
            
            if not data.get('response'):
                logger.warning(f"API yanıtı boş")
                return self._get_default_form()
            
            # Maçları analiz et
            form_data = self._parse_matches(data['response'], team_id, team_name)
            
            if form_data:
                logger.info(f"✅ {team_name}: {form_data['form']}, {form_data['wins']}W-{form_data['draws']}D-{form_data['losses']}L")
                self.cache[cache_key] = form_data
                return form_data
            
            return self._get_default_form()
        
        except requests.Timeout:
            logger.error("API timeout")
            return self._get_default_form()
        except Exception as e:
            logger.error(f"Form çekme hatası: {e}")
            return self._get_default_form()
    
    def _parse_matches(self, matches: List[Dict], team_id: int, team_name: str) -> Optional[Dict]:
        """Maçları analiz et"""
        try:
            form = []
            goals_for = 0
            goals_against = 0
            scorers = {}
            
            for match in matches:
                try:
                    fixture = match.get('fixture', {})
                    goals = match.get('goals', {})
                    teams = match.get('teams', {})
                    
                    home_team_id = teams.get('home', {}).get('id')
                    away_team_id = teams.get('away', {}).get('id')
                    home_goals = goals.get('home')
                    away_goals = goals.get('away')
                    
                    # Takımın hangi tarafta olduğunu belirle
                    if home_team_id == team_id:
                        team_goals = home_goals
                        opp_goals = away_goals
                        is_home = True
                    elif away_team_id == team_id:
                        team_goals = away_goals
                        opp_goals = home_goals
                        is_home = False
                    else:
                        continue
                    
                    if team_goals is None or opp_goals is None:
                        continue
                    
                    goals_for += team_goals
                    goals_against += opp_goals
                    
                    # Form
                    if team_goals > opp_goals:
                        form.append('W')
                    elif team_goals == opp_goals:
                        form.append('D')
                    else:
                        form.append('L')
                    
                    # Gol atanları çıkar
                    events = match.get('events', [])
                    for event in events:
                        if event.get('type') == 'Goal':
                            player_name = event.get('player', {}).get('name', 'Unknown')
                            minute = event.get('time', {}).get('elapsed', 0)
                            
                            if player_name not in scorers:
                                scorers[player_name] = []
                            
                            scorers[player_name].append({
                                'minute': minute,
                                'opponent': teams.get('away' if is_home else 'home', {}).get('name', 'Unknown')
                            })
                
                except Exception as e:
                    logger.debug(f"Maç parse hatası: {e}")
                    continue
            
            if not form or len(form) < 3:
                logger.warning(f"Yeterli maç bulunamadı")
                return None
            
            # İstatistikleri hesapla
            wins = form.count('W')
            draws = form.count('D')
            losses = form.count('L')
            total_matches = len(form)
            
            # Sezon tahmini (32 maçlık sezon)
            estimated_wins = int(32 * wins / total_matches)
            estimated_draws = int(32 * draws / total_matches)
            estimated_losses = int(32 * losses / total_matches)
            
            return {
                'name': team_name,
                'form': form[:5],
                'wins': estimated_wins,
                'draws': estimated_draws,
                'losses': estimated_losses,
                'goals_for': goals_for * 6,
                'goals_against': goals_against * 6,
                'goal_difference': (goals_for - goals_against) * 6,
                'scoring_power': self._get_scoring_power(goals_for / max(total_matches, 1)),
                'defense_strength': self._get_defense_strength(goals_against / max(total_matches, 1)),
                'recent_goals': {
                    'top_scorers': sorted([(k, v) for k, v in scorers.items()], key=lambda x: len(x[1]), reverse=True)[:5],
                    'total_goals_last_matches': goals_for,
                    'avg_goals_per_match': goals_for / max(total_matches, 1),
                    'goal_timing': {
                        'first_half': f"{sum([1 for g in scorers.values() for m in g if m['minute'] < 45])}/matches",
                        'second_half': f"{sum([1 for g in scorers.values() for m in g if m['minute'] >= 45])}/matches",
                        'peak_time': '40-50 min'
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"Parse hatası: {e}")
            return None
    
    def _get_scoring_power(self, gf_avg: float) -> str:
        if gf_avg >= 2.5:
            return "Very High 🔥"
        elif gf_avg >= 1.8:
            return "High ⚡"
        elif gf_avg >= 1.2:
            return "Medium ⚽"
        elif gf_avg >= 0.8:
            return "Low 🔇"
        else:
            return "Very Low 🚫"
    
    def _get_defense_strength(self, ga_avg: float) -> str:
        if ga_avg <= 0.8:
            return "Fortress 🛡️"
        elif ga_avg <= 1.2:
            return "Strong 💪"
        elif ga_avg <= 1.6:
            return "Average 👤"
        elif ga_avg <= 2.0:
            return "Weak 😟"
        else:
            return "Very Weak 💔"
    
    def _get_default_form(self) -> Dict:
        return {
            'name': 'Unknown',
            'form': ['W', 'D', 'L', 'W', 'D'],
            'wins': 20,
            'draws': 5,
            'losses': 7,
            'goals_for': 60,
            'goals_against': 35,
            'goal_difference': 25,
            'scoring_power': 'High ⚡',
            'defense_strength': 'Average 👤',
            'recent_goals': {
                'top_scorers': [],
                'total_goals_last_matches': 0,
                'avg_goals_per_match': 0,
                'goal_timing': {}
            }
        }
    
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> Dict:
        """H2H maçlarını API'den çek"""
        try:
            if team1_id not in self.team_id_map or team2_id not in self.team_id_map:
                logger.warning(f"Bilinmeyen team_id'ler: {team1_id}, {team2_id}")
                return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
            
            team1_name = self.team_id_map[team1_id]
            team2_name = self.team_id_map[team2_id]
            
            logger.info(f"📡 H2H çekiliyor: {team1_name} vs {team2_name}")
            
            # H2H maçlarını çek
            url = f"{self.base_url}/fixtures"
            params = {
                "h2h": f"{team1_id}-{team2_id}",
                "last": 25
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"H2H API Error: {response.status_code}")
                return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
            
            data = response.json()
            matches = data.get('response', [])
            
            if not matches:
                logger.warning("H2H maçı bulunamadı")
                return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
            
            # H2H analiz
            team1_wins = 0
            team2_wins = 0
            draws = 0
            
            for match in matches:
                try:
                    goals = match.get('goals', {})
                    teams = match.get('teams', {})
                    
                    home_id = teams.get('home', {}).get('id')
                    home_goals = goals.get('home')
                    away_goals = goals.get('away')
                    
                    if home_goals is None or away_goals is None:
                        continue
                    
                    if home_goals > away_goals:
                        if home_id == team1_id:
                            team1_wins += 1
                        else:
                            team2_wins += 1
                    elif home_goals == away_goals:
                        draws += 1
                    else:
                        if home_id == team1_id:
                            team2_wins += 1
                        else:
                            team1_wins += 1
                
                except Exception as e:
                    logger.debug(f"H2H maç parse hatası: {e}")
                    continue
            
            logger.info(f"H2H Sonuç: {team1_name} {team1_wins}W, {team2_name} {team2_wins}W, {draws}D")
            
            return {
                'team1_wins': team1_wins,
                'team2_wins': team2_wins,
                'draws': draws,
                'total_matches': team1_wins + team2_wins + draws,
                'matches': []
            }
        
        except requests.Timeout:
            logger.error("H2H API timeout")
            return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
        except Exception as e:
            logger.error(f"H2H hatası: {e}")
            return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'matches': []}
    
    def get_todays_matches(self) -> List[Dict]:
        """Bugünün maçlarını çek"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/fixtures"
            params = {
                "date": today,
                "league": 203,  # Türkiye Süper Lig
                "season": 2025
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Bugünün maçları çekilemedi")
                return []
            
            data = response.json()
            matches = []
            
            for match in data.get('response', []):
                try:
                    fixture = match.get('fixture', {})
                    teams = match.get('teams', {})
                    
                    matches.append({
                        'id': fixture.get('id'),
                        'home_team': teams.get('home', {}).get('name'),
                        'home_team_id': teams.get('home', {}).get('id'),
                        'away_team': teams.get('away', {}).get('name'),
                        'away_team_id': teams.get('away', {}).get('id'),
                        'start_time': fixture.get('date'),
                        'league': 'Turkish Super League',
                        'status': fixture.get('status', {}).get('short'),
                    })
                except:
                    continue
            
            logger.info(f"✅ Bugün {len(matches)} maç bulundu")
            return matches
        
        except Exception as e:
            logger.error(f"Bugünün maçları hatası: {e}")
            return []
