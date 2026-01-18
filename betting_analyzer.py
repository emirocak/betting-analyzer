from typing import Dict, List, Tuple
from datetime import datetime
import json

class BettingAnalyzer:
    """
    İstatistikleri analiz edip iddia tahminleri yapan sınıf
    """
    
    def __init__(self):
        self.weights = {
            'recent_form': 0.25,      # Son form % 25
            'h2h': 0.15,               # Head-to-head % 15
            'home_advantage': 0.10,    # Ev sahibi avantajı % 10
            'goal_stats': 0.25,        # Gol istatistikleri % 25
            'defense': 0.15,           # Savunma % 15
            'streak': 0.10             # Seri % 10
        }
    
    def analyze_match(self, home_team: Dict, away_team: Dict, h2h: Dict) -> Dict:
        """
        İki takım arasındaki maçı analiz et
        
        home_team: {form, wins, draws, losses, goals_for, goals_against}
        away_team: aynı yapı
        h2h: head-to-head verisi
        """
        
        analysis = {
            'home_win_prob': 0,
            'draw_prob': 0,
            'away_win_prob': 0,
            'over_2_5_prob': 0,  # 2.5 üstü gol
            'under_2_5_prob': 0,
            'both_teams_score': 0,
            'detailed_analysis': {},
            'recommendation': '',
            'risk_level': 'medium'
        }
        
        # 1. Form analizi
        form_analysis = self._analyze_form(home_team, away_team)
        
        # 2. H2H analizi
        h2h_analysis = self._analyze_h2h(h2h)
        
        # 3. Gol analizi
        goal_analysis = self._analyze_goals(home_team, away_team)
        
        # 4. Savunma analizi
        defense_analysis = self._analyze_defense(home_team, away_team)
        
        # 5. Seri analizi
        streak_analysis = self._analyze_streak(home_team, away_team)
        
        # Ağırlıklı hesaplama
        analysis['home_win_prob'] = (
            form_analysis['home_advantage'] * self.weights['recent_form'] +
            h2h_analysis['home_win'] * self.weights['h2h'] +
            0.55 * self.weights['home_advantage'] +  # Ev sahibi avantajı
            goal_analysis['home_scoring'] * self.weights['goal_stats'] +
            defense_analysis['home_defense'] * self.weights['defense'] +
            streak_analysis['home_streak'] * self.weights['streak']
        )
        
        analysis['away_win_prob'] = (
            form_analysis['away_advantage'] * self.weights['recent_form'] +
            h2h_analysis['away_win'] * self.weights['h2h'] +
            0.45 * self.weights['home_advantage'] +
            goal_analysis['away_scoring'] * self.weights['goal_stats'] +
            defense_analysis['away_defense'] * self.weights['defense'] +
            streak_analysis['away_streak'] * self.weights['streak']
        )
        
        # Beraberlik ihtimali
        analysis['draw_prob'] = 1 - analysis['home_win_prob'] - analysis['away_win_prob']
        analysis['draw_prob'] = max(0, min(1, analysis['draw_prob']))
        
        # Gol over/under
        avg_goals = goal_analysis['expected_goals']
        analysis['over_2_5_prob'] = self._poisson_probability(avg_goals, 2.5)
        analysis['under_2_5_prob'] = 1 - analysis['over_2_5_prob']
        
        # İki takım da gol atacak mı
        analysis['both_teams_score'] = (
            goal_analysis['home_scoring'] * 
            (1 - defense_analysis['away_defense'])
        ) * (
            goal_analysis['away_scoring'] * 
            (1 - defense_analysis['home_defense'])
        )
        
        # Detaylı analiz
        analysis['detailed_analysis'] = {
            'form': form_analysis,
            'h2h': h2h_analysis,
            'goals': goal_analysis,
            'defense': defense_analysis,
            'streak': streak_analysis
        }
        
        # Tavsiye oluştur
        analysis['recommendation'] = self._generate_recommendation(analysis)
        
        # Risk seviyesini hesapla
        analysis['risk_level'] = self._assess_risk(analysis)
        
        return analysis
    
    def _analyze_form(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Son form analizi (0-1 arası)
        """
        home_form = home_team.get('form', [])
        away_form = away_team.get('form', [])
        
        # Form puanı hesapla (W=3, D=1, L=0)
        def form_score(form_list):
            if not form_list:
                return 0.5
            points = sum(3 if r == 'W' else (1 if r == 'D' else 0) for r in form_list)
            return points / (len(form_list) * 3)
        
        home_form_score = form_score(home_form)
        away_form_score = form_score(away_form)
        
        total = home_form_score + away_form_score
        if total == 0:
            total = 1
        
        return {
            'home_advantage': home_form_score / total,
            'away_advantage': away_form_score / total,
            'home_form_string': ''.join(home_form),
            'away_form_string': ''.join(away_form)
        }
    
    def _analyze_h2h(self, h2h: Dict) -> Dict:
        """
        Head-to-head analizi
        """
        if not h2h:
            return {'home_win': 0.5, 'away_win': 0.5, 'draws': 0}
        
        total = h2h['team1_wins'] + h2h['team2_wins'] + h2h['draws']
        if total == 0:
            return {'home_win': 0.5, 'away_win': 0.5, 'draws': 0}
        
        return {
            'home_win': h2h['team1_wins'] / total,
            'away_win': h2h['team2_wins'] / total,
            'draws': h2h['draws'] / total,
            'home_wins': h2h['team1_wins'],
            'away_wins': h2h['team2_wins']
        }
    
    def _analyze_goals(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Gol adetleri analizi
        """
        home_gf = home_team.get('goals_for', 0)
        home_ga = home_team.get('goals_against', 0)
        home_matches = home_team.get('wins', 0) + home_team.get('draws', 0) + home_team.get('losses', 0)
        
        away_gf = away_team.get('goals_for', 0)
        away_ga = away_team.get('goals_against', 0)
        away_matches = away_team.get('wins', 0) + away_team.get('draws', 0) + away_team.get('losses', 0)
        
        # Maç başına ortalama gol
        home_gf_avg = home_gf / max(home_matches, 1)
        away_gf_avg = away_gf / max(away_matches, 1)
        home_ga_avg = home_ga / max(home_matches, 1)
        away_ga_avg = away_ga / max(away_matches, 1)
        
        # Beklenen gol
        expected_home_goals = home_gf_avg * 1.1  # Ev sahibi bonus
        expected_away_goals = away_gf_avg * 0.9
        
        return {
            'home_scoring': min(1, home_gf_avg / 3),  # 3 gol = %100
            'away_scoring': min(1, away_gf_avg / 3),
            'home_gf_avg': home_gf_avg,
            'away_gf_avg': away_gf_avg,
            'expected_goals': expected_home_goals + expected_away_goals
        }
    
    def _analyze_defense(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Savunma kalitesi analizi (0-1, düşük = iyi savunma)
        """
        home_ga = home_team.get('goals_against', 0)
        away_ga = away_team.get('goals_against', 0)
        home_matches = home_team.get('wins', 0) + home_team.get('draws', 0) + home_team.get('losses', 0)
        away_matches = away_team.get('wins', 0) + away_team.get('draws', 0) + away_team.get('losses', 0)
        
        home_ga_avg = home_ga / max(home_matches, 1)
        away_ga_avg = away_ga / max(away_matches, 1)
        
        # 2.5 gol = kötü savunma
        return {
            'home_defense': max(0, min(1, home_ga_avg / 2.5)),
            'away_defense': max(0, min(1, away_ga_avg / 2.5)),
            'home_ga_avg': home_ga_avg,
            'away_ga_avg': away_ga_avg
        }
    
    def _analyze_streak(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Seri analizi (arka arkaya kazanç/kaybı)
        """
        home_form = home_team.get('form', [])
        away_form = away_team.get('form', [])
        
        def current_streak_score(form_list):
            if not form_list:
                return 0.5
            # Son 3 maç
            recent = form_list[:3]
            if all(r == 'W' for r in recent):
                return 0.8
            elif all(r == 'W' or r == 'D' for r in recent):
                return 0.6
            elif all(r == 'L' for r in recent):
                return 0.2
            else:
                return 0.5
        
        return {
            'home_streak': current_streak_score(home_form),
            'away_streak': current_streak_score(away_form)
        }
    
    def _poisson_probability(self, lambda_param: float, k: float) -> float:
        """
        Poisson dağılımı ile gol olasılığını hesapla
        lambda_param: beklenen gol sayısı
        k: hedef gol sayısı
        """
        import math
        
        try:
            e = math.e
            numerator = (lambda_param ** k) * (e ** (-lambda_param))
            denominator = math.factorial(int(k))
            return numerator / denominator
        except:
            return 0.5
    
    def _generate_recommendation(self, analysis: Dict) -> str:
        """
        Analiz sonucundan tavsiye oluştur
        """
        home_prob = analysis['home_win_prob']
        away_prob = analysis['away_win_prob']
        draw_prob = analysis['draw_prob']
        over_prob = analysis['over_2_5_prob']
        
        recommendations = []
        
        # Kazıcı oranlarını kontrol et (gerçek oranlar gerekli)
        if home_prob > 0.55:
            recommendations.append(f"🏠 Ev Sahibi: %{int(home_prob*100)} ({home_prob:.2f} oran)")
        elif away_prob > 0.55:
            recommendations.append(f"✈️ Deplasman: %{int(away_prob*100)} ({away_prob:.2f} oran)")
        elif draw_prob > 0.35:
            recommendations.append(f"🤝 Beraberlik: %{int(draw_prob*100)} ({draw_prob:.2f} oran)")
        
        if over_prob > 0.60:
            recommendations.append(f"⚽ Üstü 2.5: %{int(over_prob*100)}")
        elif over_prob < 0.40:
            recommendations.append(f"🛑 Altı 2.5: %{int((1-over_prob)*100)}")
        
        if analysis['both_teams_score'] > 0.60:
            recommendations.append(f"🎯 Her İki Takım Gol: %{int(analysis['both_teams_score']*100)}")
        
        return " | ".join(recommendations) if recommendations else "Karışık Maç"
    
    def _assess_risk(self, analysis: Dict) -> str:
        """
        Risk seviyesini belirle
        """
        home_prob = analysis['home_win_prob']
        away_prob = analysis['away_win_prob']
        max_prob = max(home_prob, away_prob, analysis['draw_prob'])
        
        if max_prob > 0.65:
            return "LOW"
        elif max_prob > 0.50:
            return "MEDIUM"
        else:
            return "HIGH"


# Örnek kullanım
if __name__ == "__main__":
    analyzer = BettingAnalyzer()
    
    # Örnek veri
    home_team = {
        'form': ['W', 'W', 'D', 'W', 'L'],
        'wins': 4,
        'draws': 1,
        'losses': 1,
        'goals_for': 15,
        'goals_against': 6
    }
    
    away_team = {
        'form': ['W', 'D', 'L', 'W', 'L'],
        'wins': 2,
        'draws': 1,
        'losses': 2,
        'goals_for': 8,
        'goals_against': 10
    }
    
    h2h = {
        'team1_wins': 3,
        'team2_wins': 1,
        'draws': 1,
        'matches': []
    }
    
    print("🎰 BET ANALYZER")
    print("=" * 50)
    
    analysis = analyzer.analyze_match(home_team, away_team, h2h)
    
    print(f"\n📊 Sonuçlar:")
    print(f"Ev Sahibi Kazanma: %{int(analysis['home_win_prob']*100)}")
    print(f"Beraberlik: %{int(analysis['draw_prob']*100)}")
    print(f"Deplasman Kazanma: %{int(analysis['away_win_prob']*100)}")
    print(f"\nGol Analizi:")
    print(f"Üstü 2.5: %{int(analysis['over_2_5_prob']*100)}")
    print(f"Her İki Takım Gol: %{int(analysis['both_teams_score']*100)}")
    print(f"\n💡 Tavsiye: {analysis['recommendation']}")
    print(f"⚠️ Risk: {analysis['risk_level']}")
