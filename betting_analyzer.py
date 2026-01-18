import math
from typing import Dict, List

class BettingAnalyzer:
    """
    İddia analiz motoru
    Form, H2H, gol istatistikleri ve ev avantajını kullanıyor
    """
    
    def __init__(self):
        self.weights = {
            'form': 0.25,
            'h2h': 0.15,
            'home_advantage': 0.10,
            'goals': 0.25,
            'defense': 0.15,
            'streak': 0.10
        }
    
    def analyze_match(self, home_form: Dict, away_form: Dict, h2h: Dict) -> Dict:
        """
        Maç analizi yap
        
        Args:
            home_form: Ev sahibi takımın form verisi
            away_form: Deplasman takımının form verisi
            h2h: İki takım arası geçmiş
        
        Returns:
            Analiz sonuçları (win %, gol tahminleri, tavsiye)
        """
        
        # 1. FORM ANALİZİ
        home_form_score = self._calculate_form_score(home_form)
        away_form_score = self._calculate_form_score(away_form)
        
        # 2. H2H ANALİZİ
        h2h_score = self._calculate_h2h_score(h2h, home_form.get('name', 'Home'))
        
        # 3. GÖL ANALİZİ
        home_gf_avg = home_form.get('goals_for', 0) / max(len(home_form.get('form', [])), 1)
        away_gf_avg = away_form.get('goals_for', 0) / max(len(away_form.get('form', [])), 1)
        home_ga_avg = home_form.get('goals_against', 0) / max(len(home_form.get('form', [])), 1)
        away_ga_avg = away_form.get('goals_against', 0) / max(len(away_form.get('form', [])), 1)
        
        # 4. SERI ANALİZİ (W/D/L)
        home_streak = self._calculate_streak(home_form.get('form', []))
        away_streak = self._calculate_streak(away_form.get('form', []))
        
        # 5. SAVUNMA ANALİZİ
        home_defense_score = self._calculate_defense_score(away_form)
        away_defense_score = self._calculate_defense_score(home_form)
        
        # 6. EV AVANTAJI (ev sahibi takım +0.15 bonus)
        home_advantage_bonus = 0.15
        
        # AĞIRLIKLI HESAPLAMA
        home_win_prob = (
            home_form_score * self.weights['form'] +
            h2h_score * self.weights['h2h'] +
            home_advantage_bonus * self.weights['home_advantage'] +
            (home_gf_avg / (home_gf_avg + away_gf_avg + 1)) * self.weights['goals'] +
            home_defense_score * self.weights['defense'] +
            home_streak * self.weights['streak']
        )
        
        away_win_prob = (
            away_form_score * self.weights['form'] +
            (1 - h2h_score) * self.weights['h2h'] +
            (away_gf_avg / (home_gf_avg + away_gf_avg + 1)) * self.weights['goals'] +
            away_defense_score * self.weights['defense'] +
            away_streak * self.weights['streak']
        )
        
        # Beraberlik olasılığı
        draw_prob = 1 - home_win_prob - away_win_prob
        
        # Negatif değerleri sıfırla
        home_win_prob = max(0, min(1, home_win_prob))
        away_win_prob = max(0, min(1, away_win_prob))
        draw_prob = max(0, min(1, draw_prob))
        
        # NORMALIZASYON (toplam 100% olsun)
        total = home_win_prob + away_win_prob + draw_prob
        if total > 0:
            home_win_prob /= total
            away_win_prob /= total
            draw_prob /= total
        
        # GOL TAHMİNLERİ (Poisson dağılımı)
        expected_home_goals = home_gf_avg
        expected_away_goals = away_gf_avg
        
        over_2_5_prob = self._poisson_over_2_5(expected_home_goals, expected_away_goals)
        both_teams_score = self._both_teams_score_prob(expected_home_goals, expected_away_goals)
        
        # RİSK SEVİYESİ
        risk_level = self._calculate_risk_level(
            home_win_prob, away_win_prob, draw_prob,
            home_form_score, away_form_score
        )
        
        # TAVSİYE
        recommendation = self._generate_recommendation(
            home_win_prob, away_win_prob, draw_prob,
            over_2_5_prob, both_teams_score,
            home_form_score, away_form_score
        )
        
        return {
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'over_2_5_prob': over_2_5_prob,
            'under_2_5_prob': 1 - over_2_5_prob,
            'both_teams_score': both_teams_score,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'detailed_analysis': {
                'form': {
                    'home_form_score': home_form_score,
                    'away_form_score': away_form_score,
                    'home_recent': home_form.get('form', []),
                    'away_recent': away_form.get('form', [])
                },
                'h2h': {
                    'home_wins': h2h.get('team1_wins', 0),
                    'away_wins': h2h.get('team2_wins', 0),
                    'draws': h2h.get('draws', 0)
                },
                'goals': {
                    'home_scoring': home_gf_avg,
                    'away_scoring': away_gf_avg,
                    'home_gf_avg': home_gf_avg,
                    'away_gf_avg': away_gf_avg,
                    'expected_goals': f"Home: {expected_home_goals:.2f}, Away: {expected_away_goals:.2f}"
                },
                'defense': {
                    'home_ga_avg': home_ga_avg,
                    'away_ga_avg': away_ga_avg
                }
            }
        }
    
    def _calculate_form_score(self, form_data: Dict) -> float:
        """Form puanını hesapla (0-1 arası)"""
        if not form_data:
            return 0.5
        
        wins = form_data.get('wins', 0)
        draws = form_data.get('draws', 0)
        losses = form_data.get('losses', 0)
        
        total = wins + draws + losses
        if total == 0:
            return 0.5
        
        # Win = 3 puan, Draw = 1 puan, Loss = 0 puan
        points = (wins * 3) + (draws * 1)
        max_points = total * 3
        
        return points / max_points if max_points > 0 else 0.5
    
    def _calculate_h2h_score(self, h2h: Dict, home_team_name: str = None) -> float:
        """H2H skoru (ev sahibi için)"""
        if not h2h or not h2h.get('matches'):
            return 0.5
        
        home_wins = h2h.get('team1_wins', 0)
        away_wins = h2h.get('team2_wins', 0)
        draws = h2h.get('draws', 0)
        
        total = home_wins + away_wins + draws
        if total == 0:
            return 0.5
        
        # Ev sahibi için skor
        home_points = (home_wins * 3) + (draws * 1)
        max_points = total * 3
        
        return home_points / max_points if max_points > 0 else 0.5
    
    def _calculate_defense_score(self, opponent_form: Dict) -> float:
        """Savunma skoru (rakibin gol atmama oranına göre)"""
        if not opponent_form:
            return 0.5
        
        goals_for = opponent_form.get('goals_for', 0)
        matches = len(opponent_form.get('form', []))
        
        if matches == 0:
            return 0.5
        
        avg_goals = goals_for / matches
        # Daha az gol = daha iyi savunma
        # 3+ gol = 0.3 skor, 0 gol = 0.9 skor
        return max(0.2, 1 - (avg_goals / 3))
    
    def _calculate_streak(self, form_list: List[str]) -> float:
        """Son formu hesapla (son 3 maç)"""
        if not form_list:
            return 0.5
        
        recent = form_list[:3]  # Son 3 maç
        wins = recent.count('W')
        draws = recent.count('D')
        losses = recent.count('L')
        
        points = (wins * 3) + (draws * 1)
        max_points = len(recent) * 3
        
        return points / max_points if max_points > 0 else 0.5
    
    def _poisson_over_2_5(self, home_goals: float, away_goals: float) -> float:
        """Poisson dağılımı ile Üstü 2.5 olasılığı"""
        try:
            expected_total = home_goals + away_goals
            
            # 0, 1, 2 gol olasılıkları
            prob_0 = math.exp(-expected_total)
            prob_1 = expected_total * math.exp(-expected_total)
            prob_2 = (expected_total ** 2 / 2) * math.exp(-expected_total)
            
            prob_under_2_5 = prob_0 + prob_1 + prob_2
            return max(0.1, min(0.9, 1 - prob_under_2_5))
        except:
            return 0.5
    
    def _both_teams_score_prob(self, home_goals: float, away_goals: float) -> float:
        """Her iki takım gol attığı olasılığı"""
        try:
            # Basit formül: her takımın gol atma olasılığı
            home_scores = 1 - math.exp(-home_goals)
            away_scores = 1 - math.exp(-away_goals)
            
            return max(0.1, min(0.9, home_scores * away_scores))
        except:
            return 0.5
    
    def _calculate_risk_level(self, home_prob: float, away_prob: float, 
                             draw_prob: float, home_form: float, away_form: float) -> str:
        """Risk seviyesi belirle"""
        
        # En yüksek olasılık
        max_prob = max(home_prob, away_prob, draw_prob)
        
        # Form farkı
        form_diff = abs(home_form - away_form)
        
        if max_prob >= 0.65 and form_diff >= 0.2:
            return "LOW"
        elif max_prob >= 0.55 and form_diff >= 0.15:
            return "MEDIUM"
        elif max_prob >= 0.45:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _generate_recommendation(self, home_prob: float, away_prob: float, draw_prob: float,
                                over_prob: float, both_score: float,
                                home_form: float, away_form: float) -> str:
        """Tavsiye oluştur"""
        
        recommendations = []
        
        # En yüksek olasılığı bul
        max_prob = max(home_prob, away_prob, draw_prob)
        
        if home_prob == max_prob and home_prob >= 0.50:
            recommendations.append(f"🏠 Ev sahibi favorit ({int(home_prob*100)}%)")
        elif away_prob == max_prob and away_prob >= 0.50:
            recommendations.append(f"✈️ Deplasman takımı güçlü ({int(away_prob*100)}%)")
        elif draw_prob == max_prob and draw_prob >= 0.40:
            recommendations.append(f"🤝 Beraberlik muhtemel ({int(draw_prob*100)}%)")
        
        # Gol analizi
        if over_prob >= 0.60:
            recommendations.append("⚽ Üstü 2.5 gol bekleniyor")
        elif over_prob <= 0.40:
            recommendations.append("🛑 Altı 2.5 gol bekleniyor")
        
        if both_score >= 0.65:
            recommendations.append("🎯 Her iki takım gol atacak")
        
        # Form farkı
        if home_form > away_form + 0.15:
            recommendations.append("📈 Ev sahibi formu daha iyi")
        elif away_form > home_form + 0.15:
            recommendations.append("📈 Deplasman takımı formu daha iyi")
        
        return " | ".join(recommendations) if recommendations else "🤔 Belirsiz maç"
