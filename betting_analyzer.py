import math
from typing import Dict, List

class BettingAnalyzer:
    """Basit ve etkili analiz motoru"""
    
    def analyze_match(self, home_form: Dict, away_form: Dict, h2h: Dict) -> Dict:
        """Maç analizi"""
        
        # VERİ ÇIKART
        home_wins = home_form.get('wins', 0)
        home_draws = home_form.get('draws', 0)
        home_losses = home_form.get('losses', 0)
        home_gf = home_form.get('goals_for', 0)
        home_ga = home_form.get('goals_against', 0)
        home_form_list = home_form.get('form', [])
        
        away_wins = away_form.get('wins', 0)
        away_draws = away_form.get('draws', 0)
        away_losses = away_form.get('losses', 0)
        away_gf = away_form.get('goals_for', 0)
        away_ga = away_form.get('goals_against', 0)
        away_form_list = away_form.get('form', [])
        
        home_total = max(home_wins + home_draws + home_losses, 1)
        away_total = max(away_wins + away_draws + away_losses, 1)
        
        # FORM SCORE (0-1)
        home_form_score = (home_wins * 3 + home_draws) / (home_total * 3)
        away_form_score = (away_wins * 3 + away_draws) / (away_total * 3)
        
        # GÖL ORTALAMALARI
        home_gf_avg = home_gf / home_total
        away_gf_avg = away_gf / away_total
        home_ga_avg = home_ga / home_total
        away_ga_avg = away_ga / away_total
        
        # WIN PROBABILITIES (EV AVANTAJI + FORM FARKI)
        base_prob = 0.50 + 0.10  # Ev avantajı
        form_diff = (home_form_score - away_form_score) * 0.25
        goal_diff = ((home_gf_avg - away_gf_avg) / (home_gf_avg + away_gf_avg + 0.1)) * 0.15
        
        home_prob = min(0.85, max(0.15, base_prob + form_diff + goal_diff))
        
        # BERABERLIK OLASILIĞI
        form_similarity = 1 - abs(home_form_score - away_form_score)
        draw_prob = form_similarity * 0.20
        
        # AWAY KAZANMA
        away_prob = 1 - home_prob - draw_prob
        
        # NORMALIZE
        total = home_prob + away_prob + draw_prob
        home_win_prob = home_prob / total
        draw_prob = draw_prob / total
        away_win_prob = away_prob / total
        
        # GÖL TAHMINLERI
        expected_total = home_gf_avg + away_gf_avg
        over_2_5_prob = self._calculate_over_2_5(expected_total)
        both_score_prob = (1 - math.exp(-home_gf_avg)) * (1 - math.exp(-away_gf_avg))
        
        # H2H
        h2h_home_wins = h2h.get('team1_wins', 0)
        h2h_away_wins = h2h.get('team2_wins', 0)
        h2h_draws = h2h.get('draws', 0)
        h2h_total = h2h_home_wins + h2h_away_wins + h2h_draws
        
        # TAVSİYELER
        if home_win_prob > 0.55:
            main_rec = f"🏠 EV SAHİBİ FAVORIT: {int(home_win_prob*100)}%"
        elif away_win_prob > 0.55:
            main_rec = f"✈️ DEPLASMAN GÜÇLÜ: {int(away_win_prob*100)}%"
        else:
            main_rec = f"🤝 YAKIN MAÇLAR: Her şey mümkün"
        
        if over_2_5_prob > 0.65:
            goal_rec = "⚽ ÜSTÜ 2.5 GÖL: YÜKSEK İHTİMAL"
        else:
            goal_rec = "🛑 ALTI 2.5 GÖL: MUHTEMEL"
        
        return {
            'success': True,
            'home_team': home_form.get('name', 'Home'),
            'away_team': away_form.get('name', 'Away'),
            
            # WIN ODDS
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            
            # GOAL ODDS
            'goal_predictions': {
                'over_2_5': over_2_5_prob * 100,
                'under_2_5': (1 - over_2_5_prob) * 100,
                'both_teams_score': both_score_prob * 100,
                'expected_home_goals': home_gf_avg,
                'expected_away_goals': away_gf_avg,
                'expected_total': expected_total,
                'over_1_5': self._calculate_over_x(expected_total, 1.5) * 100,
            },
            
            # FORM
            'form_analysis': {
                'home': {
                    'score': round(home_form_score * 100, 1),
                    'wins': home_wins,
                    'draws': home_draws,
                    'losses': home_losses,
                    'gf': home_gf,
                    'ga': home_ga,
                    'goal_difference': home_gf - home_ga,
                    'gf_avg': round(home_gf_avg, 2),
                    'ga_avg': round(home_ga_avg, 2),
                    'scoring_power': home_form.get('scoring_power', 'High ⚡'),
                    'defense_strength': home_form.get('defense_strength', 'Strong 💪'),
                    'trend': 'Good ↗️',
                    'recent_form': ''.join(home_form_list[:5])
                },
                'away': {
                    'score': round(away_form_score * 100, 1),
                    'wins': away_wins,
                    'draws': away_draws,
                    'losses': away_losses,
                    'gf': away_gf,
                    'ga': away_ga,
                    'goal_difference': away_gf - away_ga,
                    'gf_avg': round(away_gf_avg, 2),
                    'ga_avg': round(away_ga_avg, 2),
                    'scoring_power': away_form.get('scoring_power', 'High ⚡'),
                    'defense_strength': away_form.get('defense_strength', 'Average 👤'),
                    'trend': 'Good ↗️',
                    'recent_form': ''.join(away_form_list[:5])
                }
            },
            
            # H2H
            'h2h_analysis': {
                'home_wins': h2h_home_wins,
                'away_wins': h2h_away_wins,
                'draws': h2h_draws,
                'total_matches': h2h_total,
                'home_win_rate': round(h2h_home_wins / max(h2h_total, 1) * 100, 1),
                'away_win_rate': round(h2h_away_wins / max(h2h_total, 1) * 100, 1),
                'draw_rate': round(h2h_draws / max(h2h_total, 1) * 100, 1),
                'advantage': f"Home +{h2h_home_wins - h2h_away_wins}" if h2h_home_wins > h2h_away_wins else f"Away +{h2h_away_wins - h2h_home_wins}",
                'summary': f"Ev sahibi avantaj ({h2h_home_wins}W-{h2h_away_wins}L)" if h2h_home_wins > h2h_away_wins else f"Deplasman avantaj ({h2h_away_wins}W-{h2h_home_wins}L)"
            },
            
            # RECOMMENDATIONS
            'recommendation': main_rec,
            'recommendations': {
                'main': main_rec,
                'gol_tavsiyesi': goal_rec,
                'ozel_oyunlar': f"💎 {goal_rec}",
                'uyari': '⚠️ Dikkat edin' if abs(home_win_prob - away_win_prob) < 0.05 else 'Uyarı: Yok'
            },
            
            'risk_level': 'LOW' if max(home_win_prob, away_win_prob, draw_prob) > 0.65 else 'MEDIUM' if max(home_win_prob, away_win_prob, draw_prob) > 0.50 else 'HIGH',
            
            'assessment': {
                'risk_level': 'LOW' if max(home_win_prob, away_win_prob, draw_prob) > 0.65 else 'MEDIUM',
                'confidence': 'High' if max(home_win_prob, away_win_prob, draw_prob) > 0.60 else 'Medium',
                'form_difference': round(abs(home_form_score - away_form_score) * 100, 1),
                'betting_clarity': 'Clear' if abs(home_form_score - away_form_score) > 0.20 else 'Moderate' if abs(home_form_score - away_form_score) > 0.10 else 'Unclear',
            },
            
            'recent_goals': {
                'home_team_goals': home_form.get('recent_goals', {}),
                'away_team_goals': away_form.get('recent_goals', {})
            },
            
            'detailed_analysis': {
                'form': {'home': {}, 'away': {}},
                'goals': {},
                'h2h': {}
            }
        }
    
    def _calculate_over_2_5(self, expected: float) -> float:
        """Üstü 2.5 olasılığı"""
        try:
            prob_0 = math.exp(-expected)
            prob_1 = expected * math.exp(-expected)
            prob_2 = (expected ** 2 / 2) * math.exp(-expected)
            return max(0.1, min(0.9, 1 - (prob_0 + prob_1 + prob_2)))
        except:
            return 0.5
    
    def _calculate_over_x(self, expected: float, x: float) -> float:
        """Üstü X olasılığı"""
        try:
            prob = 0
            for i in range(int(x) + 1):
                prob += (expected ** i / math.factorial(i)) * math.exp(-expected)
            return max(0.1, min(0.9, 1 - prob))
        except:
            return 0.5
