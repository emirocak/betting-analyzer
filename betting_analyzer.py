import math
from typing import Dict, List

class BettingAnalyzer:
    """Detaylı ve kapsamlı analiz motoru"""
    
    def analyze_match(self, home_form: Dict, away_form: Dict, h2h: Dict) -> Dict:
        """Maç analizi yap - Tüm detaylarla"""
        
        # ==================== ADIM 1: VERİ HAZIRLA ====================
        home_team_name = home_form.get('name', 'Home Team')
        away_team_name = away_form.get('name', 'Away Team')
        
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
        
        home_total = home_wins + home_draws + home_losses
        away_total = away_wins + away_draws + away_losses
        
        # ==================== ADIM 2: FORM ANALİZİ ====================
        home_form_score = self._calculate_form_score(home_wins, home_draws, home_losses)
        away_form_score = self._calculate_form_score(away_wins, away_draws, away_losses)
        
        home_recent_form = self._analyze_recent_form(home_form_list)
        away_recent_form = self._analyze_recent_form(away_form_list)
        
        # ==================== ADIM 3: GÖL ANALİZİ ====================
        home_gf_avg = home_gf / max(home_total, 1)
        away_gf_avg = away_gf / max(away_total, 1)
        home_ga_avg = home_ga / max(home_total, 1)
        away_ga_avg = away_ga / max(away_total, 1)
        
        home_scoring_power = self._calculate_scoring_power(home_gf_avg)
        away_scoring_power = self._calculate_scoring_power(away_gf_avg)
        home_defense_strength = self._calculate_defense_strength(home_ga_avg)
        away_defense_strength = self._calculate_defense_strength(away_ga_avg)
        
        # ==================== ADIM 4: H2H ANALİZİ ====================
        h2h_home_wins = h2h.get('team1_wins', 0)
        h2h_away_wins = h2h.get('team2_wins', 0)
        h2h_draws = h2h.get('draws', 0)
        h2h_total = h2h_home_wins + h2h_away_wins + h2h_draws
        
        h2h_analysis = self._analyze_h2h(h2h_home_wins, h2h_away_wins, h2h_draws)
        
        # ==================== ADIM 5: MAÇIN TAHMİNİ ====================
        win_probabilities = self._calculate_win_probabilities(
            home_form_score, away_form_score,
            home_gf_avg, away_gf_avg,
            home_ga_avg, away_ga_avg,
            h2h_home_wins, h2h_away_wins, h2h_draws,
            home_recent_form, away_recent_form
        )
        
        home_win_prob = win_probabilities['home']
        draw_prob = win_probabilities['draw']
        away_win_prob = win_probabilities['away']
        
        # ==================== ADIM 6: GÖL TAHMINLERI ====================
        expected_home_goals = home_gf_avg
        expected_away_goals = away_gf_avg
        expected_total = expected_home_goals + expected_away_goals
        
        over_2_5_prob = self._calculate_over_2_5(expected_total)
        under_2_5_prob = 1 - over_2_5_prob
        both_teams_score_prob = self._calculate_both_teams_score(expected_home_goals, expected_away_goals)
        over_1_5_prob = self._calculate_over_x(expected_total, 1.5)
        
        # ==================== ADIM 7: RİSK DEĞERLENDİRMESİ ====================
        max_prob = max(home_win_prob, away_win_prob, draw_prob)
        form_difference = abs(home_form_score - away_form_score)
        
        if max_prob >= 0.65 and form_difference >= 0.20:
            risk_level = "LOW"
            confidence = "Very High"
        elif max_prob >= 0.58 and form_difference >= 0.15:
            risk_level = "LOW"
            confidence = "High"
        elif max_prob >= 0.50:
            risk_level = "MEDIUM"
            confidence = "Medium"
        elif max_prob >= 0.45:
            risk_level = "MEDIUM-HIGH"
            confidence = "Low"
        else:
            risk_level = "HIGH"
            confidence = "Very Low"
        
        # ==================== ADIM 8: TAVSİYELER ====================
        recommendations = self._generate_detailed_recommendations(
            home_win_prob, away_win_prob, draw_prob,
            over_2_5_prob, both_teams_score_prob,
            home_form_score, away_form_score,
            home_gf_avg, away_gf_avg,
            h2h_analysis
        )
        
        # ==================== ADIM 9: SONUÇ ====================
        return {
            'match_info': {
                'home_team': home_team_name,
                'away_team': away_team_name,
                'timestamp': None
            },
            
            # Kazanma Olasılıkları
            'win_probabilities': {
                'home_win': round(home_win_prob * 100, 1),
                'draw': round(draw_prob * 100, 1),
                'away_win': round(away_win_prob * 100, 1),
                'home_win_prob': home_win_prob,
                'draw_prob': draw_prob,
                'away_win_prob': away_win_prob,
            },
            
            # Gol Tahminleri
            'goal_predictions': {
                'over_2_5': round(over_2_5_prob * 100, 1),
                'under_2_5': round(under_2_5_prob * 100, 1),
                'over_1_5': round(over_1_5_prob * 100, 1),
                'both_teams_score': round(both_teams_score_prob * 100, 1),
                'expected_home_goals': round(expected_home_goals, 2),
                'expected_away_goals': round(expected_away_goals, 2),
                'expected_total': round(expected_total, 2),
            },
            
            # Form Analizi
            'form_analysis': {
                'home': {
                    'score': round(home_form_score * 100, 1),
                    'recent_form': ''.join(home_form_list[:5]),
                    'wins': home_wins,
                    'draws': home_draws,
                    'losses': home_losses,
                    'gf': home_gf,
                    'ga': home_ga,
                    'goal_difference': home_gf - home_ga,
                    'gf_avg': round(home_gf_avg, 2),
                    'ga_avg': round(home_ga_avg, 2),
                    'scoring_power': home_scoring_power,
                    'defense_strength': home_defense_strength,
                    'trend': home_recent_form['trend']
                },
                'away': {
                    'score': round(away_form_score * 100, 1),
                    'recent_form': ''.join(away_form_list[:5]),
                    'wins': away_wins,
                    'draws': away_draws,
                    'losses': away_losses,
                    'gf': away_gf,
                    'ga': away_ga,
                    'goal_difference': away_gf - away_ga,
                    'gf_avg': round(away_gf_avg, 2),
                    'ga_avg': round(away_ga_avg, 2),
                    'scoring_power': away_scoring_power,
                    'defense_strength': away_defense_strength,
                    'trend': away_recent_form['trend']
                }
            },
            
            # H2H Analizi
            'h2h_analysis': {
                'home_wins': h2h_home_wins,
                'away_wins': h2h_away_wins,
                'draws': h2h_draws,
                'total_matches': h2h_total,
                'home_win_rate': round(h2h_home_wins / max(h2h_total, 1) * 100, 1),
                'away_win_rate': round(h2h_away_wins / max(h2h_total, 1) * 100, 1),
                'draw_rate': round(h2h_draws / max(h2h_total, 1) * 100, 1),
                'advantage': h2h_analysis['advantage'],
                'summary': h2h_analysis['summary']
            },
            
            # Risk & Confidence
            'assessment': {
                'risk_level': risk_level,
                'confidence': confidence,
                'form_difference': round(form_difference * 100, 1),
                'betting_clarity': 'Clear' if form_difference > 0.20 else 'Moderate' if form_difference > 0.10 else 'Unclear',
            },
            
            # Tavsiyeler
            'recommendations': {
                'main': recommendations['main'],
                'gol_tavsiyesi': recommendations['gol'],
                'ozel_oyunlar': recommendations['special'],
                'uyari': recommendations['warning']
            },
            
            # Detaylı Analiz
            'detailed_analysis': {
                'ev_avantaji': 'Strong (Ev sahibi önemli avantaj)',
                'form_momentum': home_recent_form['description'],
                'deplasman_guc': away_recent_form['description'],
                'taktik_analiz': self._get_tactical_analysis(home_form_score, away_form_score, home_gf_avg, away_gf_avg)
            }
        }
    
    # ==================== YARDIMCI FONKSİYONLAR ====================
    
    def _calculate_form_score(self, wins: int, draws: int, losses: int) -> float:
        """Form puanı hesapla (0-1)"""
        total = wins + draws + losses
        if total == 0:
            return 0.5
        points = wins * 3 + draws * 1
        max_points = total * 3
        return points / max_points
    
    def _analyze_recent_form(self, form_list: List[str]) -> Dict:
        """Son formu analiz et"""
        if not form_list:
            return {'trend': 'Unknown', 'description': 'No data', 'strength': 0.5}
        
        recent = form_list[:3]
        wins = recent.count('W')
        draws = recent.count('D')
        losses = recent.count('L')
        
        if wins == 3:
            return {'trend': 'Excellent ⬆️', 'description': 'Çok iyi form, 3 ardı ardına galibiyet', 'strength': 0.9}
        elif wins == 2:
            return {'trend': 'Good ↗️', 'description': 'İyi form, son 3 maçta 2 galibiyet', 'strength': 0.75}
        elif wins == 1 and losses == 0:
            return {'trend': 'Stable →', 'description': 'Stabil form, beraberlikli galibiyetler', 'strength': 0.6}
        elif wins == 1:
            return {'trend': 'Mixed ↔️', 'description': 'Değişken form, karışık sonuçlar', 'strength': 0.5}
        else:
            return {'trend': 'Poor ↘️', 'description': 'Kötü form, son 3 maçta 2+ yenilgi', 'strength': 0.3}
    
    def _calculate_scoring_power(self, gf_avg: float) -> str:
        """Gol atma gücü"""
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
    
    def _calculate_defense_strength(self, ga_avg: float) -> str:
        """Savunma gücü"""
        if ga_avg <= 0.6:
            return "Fortress 🛡️"
        elif ga_avg <= 1.0:
            return "Strong 💪"
        elif ga_avg <= 1.4:
            return "Average 👤"
        elif ga_avg <= 1.8:
            return "Weak 😟"
        else:
            return "Very Weak 💔"
    
    def _analyze_h2h(self, home_wins: int, away_wins: int, draws: int) -> Dict:
        """H2H analizi"""
        total = home_wins + away_wins + draws
        if total == 0:
            return {'advantage': 'Even', 'summary': 'Geçmiş maç yok'}
        
        home_dominance = home_wins - away_wins
        
        if home_dominance > 2:
            return {'advantage': f'Home +{home_dominance}', 'summary': f'Ev sahibi tarihsel avantaj ({home_wins}W-{away_wins}L)'}
        elif home_dominance > 0:
            return {'advantage': f'Home +{home_dominance}', 'summary': f'Ev sahibi hafif avantaj ({home_wins}W-{away_wins}L)'}
        elif home_dominance == 0:
            return {'advantage': 'Balanced', 'summary': f'Dengeli maçlar ({home_wins}W-{away_wins}L)'}
        else:
            return {'advantage': f'Away +{abs(home_dominance)}', 'summary': f'Deplasman üstünlüğü ({away_wins}L-{home_wins}W)'}
    
    def _calculate_win_probabilities(self, home_form: float, away_form: float,
                                     home_gf: float, away_gf: float,
                                     home_ga: float, away_ga: float,
                                     h2h_home: int, h2h_away: int, h2h_draws: int,
                                     home_recent: Dict, away_recent: Dict) -> Dict:
        """Kazanma olasılıklarını hesapla"""
        
        # Ağırlıklı hesaplama
        weights = {
            'form': 0.25,
            'goals': 0.25,
            'defense': 0.15,
            'h2h': 0.15,
            'home_advantage': 0.10,
            'trend': 0.10
        }
        
        # Base score
        home_score = 0.5 + 0.10  # Ev avantajı
        
        # Form etkisi
        home_score += (home_form - away_form) * weights['form']
        
        # Gol etkisi
        goal_ratio = home_gf / (home_gf + away_gf + 0.1)
        home_score += (goal_ratio - 0.5) * weights['goals']
        
        # Savunma etkisi
        defense_ratio = (1 - away_ga / 3) / (2 - (home_ga / 3 + away_ga / 3))
        home_score += (defense_ratio - 0.5) * weights['defense']
        
        # H2H etkisi
        h2h_total = h2h_home + h2h_away + h2h_draws
        if h2h_total > 0:
            h2h_home_rate = h2h_home / h2h_total
            home_score += (h2h_home_rate - 0.5) * weights['h2h']
        
        # Trend etkisi
        home_score += (home_recent['strength'] - away_recent['strength']) * weights['trend']
        
        # Normalize
        home_prob = max(0.15, min(0.85, home_score))
        
        # Beraberlik
        form_diff = abs(home_form - away_form)
        draw_prob = (1 - form_diff) * 0.25
        
        # Final
        away_prob = 1 - home_prob - draw_prob
        
        # Total normalize
        total = home_prob + away_prob + draw_prob
        return {
            'home': home_prob / total,
            'draw': draw_prob / total,
            'away': away_prob / total
        }
    
    def _calculate_over_2_5(self, expected_total: float) -> float:
        """Üstü 2.5 olasılığı"""
        prob_0 = math.exp(-expected_total)
        prob_1 = expected_total * math.exp(-expected_total)
        prob_2 = (expected_total ** 2 / 2) * math.exp(-expected_total)
        return max(0.1, min(0.9, 1 - (prob_0 + prob_1 + prob_2)))
    
    def _calculate_over_x(self, expected_total: float, x: float) -> float:
        """Üstü X olasılığı"""
        prob = 0
        for i in range(int(x) + 1):
            try:
                prob += (expected_total ** i / math.factorial(i)) * math.exp(-expected_total)
            except:
                pass
        return max(0.1, min(0.9, 1 - prob))
    
    def _calculate_both_teams_score(self, home_goals: float, away_goals: float) -> float:
        """Her iki takım gol atma olasılığı"""
        try:
            home_scores = 1 - math.exp(-home_goals)
            away_scores = 1 - math.exp(-away_goals)
            return home_scores * away_scores
        except:
            return 0.5
    
    def _generate_detailed_recommendations(self, home_prob: float, away_prob: float, draw_prob: float,
                                          over_2_5: float, both_score: float,
                                          home_form: float, away_form: float,
                                          home_gf: float, away_gf: float,
                                          h2h_analysis: Dict) -> Dict:
        """Detaylı tavsiyeler oluştur"""
        recs = []
        gol = []
        special = []
        warning = []
        
        # Ana tahmin
        max_prob = max(home_prob, away_prob, draw_prob)
        
        if home_prob == max_prob and home_prob > 0.50:
            recs.append(f"🏠 EV SAHİBİ FAVORIT: {int(home_prob*100)}%")
            if home_prob > 0.65:
                special.append(f"💎 1X (Ev avantajı + beraberlik seçeneği) güvenli seçenek")
        elif away_prob == max_prob and away_prob > 0.50:
            recs.append(f"✈️ DEPLASMAN GÜÇLÜ: {int(away_prob*100)}%")
            if away_prob > 0.65:
                special.append(f"💎 X2 (Deplasman haritası) güvenli seçenek")
        elif draw_prob > 0.35:
            recs.append(f"🤝 BERABERLIK MUHTEMEL: {int(draw_prob*100)}%")
        
        # Gol analizi
        if over_2_5 > 0.70:
            gol.append("⚽ ÜSTÜ 2.5 GÖL: YÜKSEK İHTİMAL")
            if both_score > 0.65:
                special.append("🎯 İKİ TARAF GOLE GİDECEK: Çok güçlü sinyal")
        elif over_2_5 > 0.55:
            gol.append("⚽ Üstü 2.5 gol oynanabilir")
        elif over_2_5 < 0.35:
            gol.append("🛑 ALTI 2.5 GÖL: Savunma-ağırlıklı maç")
        else:
            gol.append("⚽ Belirsiz gol tahmini")
        
        # Uyarılar
        if abs(home_prob - away_prob) < 0.05:
            warning.append("⚠️ ÇOK YAKIN MAÇLAR: Her şey mümkün")
        
        if home_form < 0.40 and away_form < 0.40:
            warning.append("⚠️ KÖTÜ FORM: Her iki takımda düşük form")
        
        if home_gf < 0.8 and away_gf < 0.8:
            warning.append("⚠️ AZ GÖL ATMA: Düşük gol beklentisi")
        
        return {
            'main': ' | '.join(recs) if recs else '🤔 Belirsiz',
            'gol': ' | '.join(gol) if gol else 'Gol tahmini belirsiz',
            'special': ' | '.join(special) if special else 'Özel oyun: Değerlendir',
            'warning': ' | '.join(warning) if warning else 'Uyarı: Yok'
        }
    
    def _get_tactical_analysis(self, home_form: float, away_form: float,
                              home_gf: float, away_gf: float) -> str:
        """Taktik analizi"""
        if home_form > 0.65 and home_gf > 1.8:
            return "Ev sahibi hızlı ve etkili oynuyor"
        elif away_form > 0.65 and away_gf > 1.5:
            return "Deplasman takımı disiplinli ve tehlikeli"
        elif home_form > away_form + 0.15:
            return "Ev sahibi baskı yapacak, kaçan pozisyonlar açıklanabilir"
        else:
            return "Dengeli taktik mücadelesi bekleniyor"
