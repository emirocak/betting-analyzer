import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  FlatList,
} from 'react-native';

/**
 * NOT: Bu uygulama için backend'de (Python) aşağıdakileri kurman lazım:
 * 
 * 1. Flask API sunucusu (sofascore_api.py ve betting_analyzer.py'yi kullanır)
 * 2. SQLite database (geçmiş iddialar için)
 * 3. Sofascore'dan veri çeken scheduler (her gün güncelleme)
 * 
 * pip install flask requests beautifulsoup4 sqlite3
 */

export default function BettingAnalyzerApp() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [teams, setTeams] = useState([]);
  const [pastBets, setPastBets] = useState([]);
  const [activeTab, setActiveTab] = useState('analyzer'); // analyzer, history

  // Backend URL (bilgisayarında çalışan Python API)
  const API_URL = 'http://192.168.1.100:5000'; // Kendi IP'nizi yazın

  // Analiz yap
  const analyzeMatch = async () => {
    if (!homeTeam.trim() || !awayTeam.trim()) {
      Alert.alert('Hata', 'Lütfen her iki takım adını da girin');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          home_team: homeTeam,
          away_team: awayTeam,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
      } else {
        Alert.alert('Hata', 'Analiz yapılamadı. Takım adlarını kontrol edin.');
      }
    } catch (error) {
      Alert.alert('Hata', `Bağlantı hatası: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Widdraw veya çekiliş olmadan bet ekle
  const saveBet = async () => {
    if (!analysis) {
      Alert.alert('Hata', 'Önce maç analiz edin');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/save-bet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          home_team: homeTeam,
          away_team: awayTeam,
          analysis: analysis,
          date: new Date().toISOString(),
        }),
      });

      if (response.ok) {
        Alert.alert('Başarılı', 'İddia kaydedildi');
        // Formu temizle
        setHomeTeam('');
        setAwayTeam('');
        setAnalysis(null);
      }
    } catch (error) {
      Alert.alert('Hata', `Kaydedilemedi: ${error.message}`);
    }
  };

  // Geçmiş iddiaları yükle
  const loadPastBets = async () => {
    try {
      const response = await fetch(`${API_URL}/bets`);
      if (response.ok) {
        const data = await response.json();
        setPastBets(data);
      }
    } catch (error) {
      console.log('Geçmiş yükleme hatası:', error);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      loadPastBets();
    }
  }, [activeTab]);

  // Analiz ekranı
  const AnalyzerScreen = () => (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>⚽ İDDİA ANALİZÖRÜ</Text>

      <View style={styles.inputSection}>
        <Text style={styles.label}>Ev Sahibi Takımı</Text>
        <TextInput
          style={styles.input}
          placeholder="Örn: Fenerbahçe"
          value={homeTeam}
          onChangeText={setHomeTeam}
          placeholderTextColor="#aaa"
        />

        <Text style={styles.label}>Deplasman Takımı</Text>
        <TextInput
          style={styles.input}
          placeholder="Örn: Galatasaray"
          value={awayTeam}
          onChangeText={setAwayTeam}
          placeholderTextColor="#aaa"
        />

        <TouchableOpacity
          style={[styles.button, loading && { opacity: 0.5 }]}
          onPress={analyzeMatch}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>🔍 Analiz Yap</Text>
          )}
        </TouchableOpacity>
      </View>

      {analysis && (
        <View style={styles.resultsSection}>
          <Text style={styles.subtitle}>📊 SONUÇLAR</Text>

          {/* Maç Sonucu Olasılıkları */}
          <View style={styles.probabilityBox}>
            <Text style={styles.resultTitle}>Maç Sonucu</Text>
            <View style={styles.row}>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>🏠 {homeTeam}</Text>
                <Text style={styles.probability}>
                  {(analysis.home_win_prob * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>🤝 Beraberlik</Text>
                <Text style={styles.probability}>
                  {(analysis.draw_prob * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>✈️ {awayTeam}</Text>
                <Text style={styles.probability}>
                  {(analysis.away_win_prob * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
          </View>

          {/* Gol Analizi */}
          <View style={styles.probabilityBox}>
            <Text style={styles.resultTitle}>Gol Analizi</Text>
            <View style={styles.row}>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>⚽ Üstü 2.5</Text>
                <Text style={styles.probability}>
                  {(analysis.over_2_5_prob * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>🛑 Altı 2.5</Text>
                <Text style={styles.probability}>
                  {((1 - analysis.over_2_5_prob) * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.probabilityItem}>
                <Text style={styles.teamLabel}>🎯 Her İki Gol</Text>
                <Text style={styles.probability}>
                  {(analysis.both_teams_score * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
          </View>

          {/* Detaylı Analiz */}
          <View style={styles.detailedBox}>
            <Text style={styles.resultTitle}>📈 Detaylı Analiz</Text>

            <DetailedStats label="Form" data={analysis.detailed_analysis.form} />
            <DetailedStats label="Gol" data={analysis.detailed_analysis.goals} />
            <DetailedStats label="Savunma" data={analysis.detailed_analysis.defense} />
          </View>

          {/* Tavsiye */}
          <View style={styles.recommendationBox}>
            <Text style={styles.recommTitle}>💡 TAVSİYE</Text>
            <Text style={styles.recommText}>{analysis.recommendation}</Text>
            <Text style={styles.riskText}>
              ⚠️ Risk Seviyesi: {analysis.risk_level}
            </Text>
          </View>

          {/* Kaydet Butonu */}
          <TouchableOpacity style={styles.saveButton} onPress={saveBet}>
            <Text style={styles.buttonText}>💾 İDDİAYI KAYDET</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );

  // Geçmiş ekranı
  const HistoryScreen = () => (
    <View style={styles.container}>
      <Text style={styles.title}>📋 GEÇMİŞ İDDİALAR</Text>

      {pastBets.length === 0 ? (
        <Text style={styles.emptyText}>Henüz kaydedilmiş iddia yok</Text>
      ) : (
        <FlatList
          data={pastBets}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item }) => (
            <View style={styles.betCard}>
              <Text style={styles.betTeams}>
                {item.home_team} vs {item.away_team}
              </Text>
              <Text style={styles.betDate}>
                📅 {new Date(item.date).toLocaleDateString('tr-TR')}
              </Text>
              <View style={styles.betStats}>
                <Text style={styles.betStat}>
                  Ev: {(item.analysis.home_win_prob * 100).toFixed(0)}%
                </Text>
                <Text style={styles.betStat}>
                  Dep: {(item.analysis.away_win_prob * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );

  return (
    <View style={styles.app}>
      {/* Tab Navigation */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'analyzer' && styles.activeTab,
          ]}
          onPress={() => setActiveTab('analyzer')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'analyzer' && styles.activeTabText,
            ]}
          >
            Analiz
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'history' && styles.activeTab]}
          onPress={() => setActiveTab('history')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'history' && styles.activeTabText,
            ]}
          >
            Geçmiş
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'analyzer' ? <AnalyzerScreen /> : <HistoryScreen />}
    </View>
  );
}

// Detaylı istatistikler bileşeni
const DetailedStats = ({ label, data }) => {
  if (!data) return null;

  return (
    <View style={styles.statGroup}>
      <Text style={styles.statGroupTitle}>{label}</Text>
      {Object.entries(data).map(([key, value]) => (
        <View key={key} style={styles.statRow}>
          <Text style={styles.statLabel}>{key}:</Text>
          <Text style={styles.statValue}>
            {typeof value === 'number' ? value.toFixed(2) : String(value)}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  app: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  container: {
    flex: 1,
    padding: 16,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#1e40af',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#1e40af',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#1e40af',
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 12,
    color: '#333',
  },
  inputSection: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    fontSize: 14,
    color: '#333',
  },
  button: {
    backgroundColor: '#1e40af',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  resultsSection: {
    marginBottom: 20,
  },
  probabilityBox: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    color: '#333',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  probabilityItem: {
    flex: 1,
    alignItems: 'center',
  },
  teamLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  probability: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e40af',
  },
  detailedBox: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  statGroup: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  statGroupTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#1e40af',
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  statValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  recommendationBox: {
    backgroundColor: '#fef3c7',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  recommTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
    color: '#b45309',
  },
  recommText: {
    fontSize: 14,
    color: '#78350f',
    marginBottom: 8,
  },
  riskText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#d97706',
  },
  saveButton: {
    backgroundColor: '#10b981',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  betCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  betTeams: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
    color: '#333',
  },
  betDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  betStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  betStat: {
    fontSize: 12,
    color: '#1e40af',
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 20,
  },
});
