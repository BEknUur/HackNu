import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
  Alert,
} from 'react-native';
import { ZamanColors } from '@/constants/theme';
import { getFinancialAnalysis, FinancialAnalysisResponse } from '@/lib/api-client';

interface UserData {
  id: number;
  name: string;
  surname: string;
  email: string;
}

export default function FinancialAnalysisScreen() {
  const [user, setUser] = useState<UserData | null>(null);
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [monthsBack, setMonthsBack] = useState(6);
  const [isInsightsExpanded, setIsInsightsExpanded] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    if (user) {
      loadAnalysis();
    }
  }, [user, monthsBack]);

  function loadUser() {
    try {
      if (typeof localStorage !== 'undefined') {
        const userJson = localStorage.getItem('user');
        if (userJson) {
          setUser(JSON.parse(userJson));
        }
      }
    } catch (error) {
      console.error('Error loading user:', error);
    }
  }

  async function loadAnalysis() {
    if (!user) return;

    try {
      setLoading(true);
      const analysisData = await getFinancialAnalysis(user.id, monthsBack);
      setAnalysis(analysisData);
    } catch (error) {
      console.error('Error loading analysis:', error);
      if (Platform.OS === 'web') {
        alert(`Error: ${error instanceof Error ? error.message : 'Failed to load analysis'}`);
      } else {
        Alert.alert('Error', error instanceof Error ? error.message : 'Failed to load analysis');
      }
    } finally {
      setLoading(false);
    }
  }

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAnalysis();
    setRefreshing(false);
  }, [user, monthsBack]);

  function getHealthColor(score: number): string {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#8BC34A';
    if (score >= 40) return '#FF9800';
    return '#F44336';
  }

  function getHealthIcon(status: string): any {
    switch (status) {
      case 'Excellent':
        return 'trophy';
      case 'Good':
        return 'checkmark-circle';
      case 'Fair':
        return 'warning';
      default:
        return 'alert-circle';
    }
  }

  function formatCurrency(amount: number, currency: string = 'KZT'): string {
    return `${amount.toFixed(2)} ${currency}`;
  }

  function formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  function renderFormattedInsights(text: string) {
    const lines = text.split('\n');
    const elements: React.ReactElement[] = [];
    let key = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (!line) {
        // Skip empty lines but add small spacing
        elements.push(<View key={`space-${key++}`} style={{ height: 8 }} />);
        continue;
      }

      // Section headers (starting with **)
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '');
        elements.push(
          <View key={`section-${key++}`} style={styles.insightSection}>
            <View style={styles.insightSectionHeader}>
              <View style={styles.insightSectionDot} />
              <Text style={styles.insightSectionTitle}>{title}</Text>
            </View>
          </View>
        );
        continue;
      }

      // Numbered items (1. 2. 3. etc)
      const numberedMatch = line.match(/^(\d+)\.\s*\*\*(.*?)\*\*\s*(.*)/);
      if (numberedMatch) {
        const [, number, title, description] = numberedMatch;
        elements.push(
          <View key={`numbered-${key++}`} style={styles.insightNumberedItem}>
            <View style={styles.insightNumberBadge}>
              <Text style={styles.insightNumberText}>{number}</Text>
            </View>
            <View style={styles.insightNumberedContent}>
              <Text style={styles.insightNumberedTitle}>{title}</Text>
              {description && (
                <Text style={styles.insightNumberedDescription}>{description}</Text>
              )}
            </View>
          </View>
        );
        continue;
      }

      // Bullet points (starting with • or *)
      if (line.startsWith('•') || line.startsWith('*')) {
        const bulletText = line.substring(1).trim();
        
        // Check if it has bold text
        const boldMatch = bulletText.match(/\*\*(.*?)\*\*\s*(.*)/);
        if (boldMatch) {
          const [, boldPart, regularPart] = boldMatch;
          elements.push(
            <View key={`bullet-${key++}`} style={styles.insightBulletItem}>
              <View style={styles.insightBulletDot} />
              <View style={styles.insightBulletContent}>
                <Text style={styles.insightBulletTextBold}>{boldPart}</Text>
                {regularPart && (
                  <Text style={styles.insightBulletText}> {regularPart}</Text>
                )}
              </View>
            </View>
          );
        } else {
          elements.push(
            <View key={`bullet-${key++}`} style={styles.insightBulletItem}>
              <View style={styles.insightBulletDot} />
              <Text style={styles.insightBulletText}>{bulletText}</Text>
            </View>
          );
        }
        continue;
      }

      // Subheadings with **
      const subheadMatch = line.match(/^\*\*(.+?)\*\*:?\s*(.*)/);
      if (subheadMatch) {
        const [, heading, rest] = subheadMatch;
        elements.push(
          <View key={`subhead-${key++}`} style={styles.insightSubheading}>
            <Text style={styles.insightSubheadingText}>{heading}:</Text>
            {rest && <Text style={styles.insightNormalText}> {rest}</Text>}
          </View>
        );
        continue;
      }

      // Regular paragraph
      elements.push(
        <Text key={`para-${key++}`} style={styles.insightNormalText}>
          {line}
        </Text>
      );
    }

    return <View>{elements}</View>;
  }

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color={ZamanColors.persianGreen} />
        <Text style={styles.loadingText}>Analyzing your finances</Text>
        <View style={styles.loadingDots}>
          <View style={[styles.dot, styles.dot1]} />
          <View style={[styles.dot, styles.dot2]} />
          <View style={[styles.dot, styles.dot3]} />
        </View>
      </View>
    );
  }

  if (!analysis) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <Text style={styles.emptyStateText}>No data yet</Text>
        <Text style={styles.emptyStateSubtext}>Start making transactions to see your analysis</Text>
      </View>
    );
  }

  const { financial_data, ai_insights } = analysis;
  const healthScore = financial_data.financial_health.health_score;
  const healthColor = getHealthColor(healthScore);

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={onRefresh}
            tintColor={ZamanColors.persianGreen}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <View style={styles.heroContent}>
            <Text style={styles.heroGreeting}>Your Financial Story</Text>
            <Text style={styles.heroSubtitle}>Last {monthsBack} months of insights</Text>
            
            {/* Period Selector */}
            <View style={styles.periodSelector}>
              {[3, 6, 12].map((months) => (
                <TouchableOpacity
                  key={months}
                  style={[
                    styles.periodChip,
                    monthsBack === months && styles.periodChipActive,
                  ]}
                  onPress={() => setMonthsBack(months)}
                  activeOpacity={0.8}
                >
                  <Text
                    style={[
                      styles.periodChipText,
                      monthsBack === months && styles.periodChipTextActive,
                    ]}
                  >
                    {months} months
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Main Health Score */}
            <View style={styles.scoreContainer}>
              <Text style={styles.scoreLabel}>Health Score</Text>
              <Text style={styles.scoreValue}>{healthScore.toFixed(0)}</Text>
              <View style={styles.scoreBar}>
                <View style={[styles.scoreBarFill, { width: `${healthScore}%`, backgroundColor: healthColor }]} />
              </View>
              <Text style={styles.scoreStatus}>{financial_data.financial_health.financial_status}</Text>
            </View>
          </View>
        </View>

        {/* Key Metrics */}
        <View style={styles.metricsSection}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Monthly Income</Text>
            <Text style={styles.metricValue}>
              {formatCurrency(financial_data.income_analysis.average_monthly_income)}
            </Text>
            <Text style={styles.metricChange}>Average</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Monthly Spending</Text>
            <Text style={[styles.metricValue, { color: '#E63946' }]}>
              {formatCurrency(financial_data.spending_breakdown.average_monthly_spending)}
            </Text>
            <Text style={styles.metricChange}>Average</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Monthly Savings</Text>
            <Text style={[styles.metricValue, { color: '#06D6A0' }]}>
              {formatCurrency(financial_data.financial_health.average_monthly_savings)}
            </Text>
            <Text style={styles.metricChange}>
              {formatPercentage(financial_data.financial_health.savings_rate_percentage)} rate
            </Text>
          </View>
        </View>

        {/* Account Balances */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Total Balance</Text>
          <View style={styles.balanceCard}>
            {Object.entries(financial_data.accounts_summary.total_balance_by_currency).map(
              ([currency, balance]) => (
                <View key={currency} style={styles.balanceRow}>
                  <View style={styles.currencyBadge}>
                    <Text style={styles.currencyBadgeText}>{currency}</Text>
                  </View>
                  <Text style={styles.balanceValue}>{formatCurrency(balance, '')}</Text>
                </View>
              )
            )}
            <View style={styles.balanceMeta}>
              <Text style={styles.balanceMetaText}>
                {financial_data.accounts_summary.total_accounts} accounts
              </Text>
            </View>
          </View>
        </View>

        {/* Spending Breakdown */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Spending Breakdown</Text>
          <View style={styles.spendingCard}>
            {Object.entries(financial_data.spending_breakdown.by_category)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([category, amount], index) => {
                const total = financial_data.spending_breakdown.total_spending;
                const percentage = (amount / total) * 100;
                const colors = ['#0D8377', '#E63946', '#F77F00', '#06D6A0', '#118AB2'];
                return (
                  <View key={category} style={styles.spendingRow}>
                    <View style={styles.spendingLeft}>
                      <View style={[styles.spendingDot, { backgroundColor: colors[index % colors.length] }]} />
                      <Text style={styles.spendingLabel}>{category}</Text>
                    </View>
                    <View style={styles.spendingRight}>
                      <Text style={styles.spendingPercent}>{formatPercentage(percentage)}</Text>
                      <Text style={styles.spendingAmount}>{formatCurrency(amount)}</Text>
                    </View>
                  </View>
                );
              })}
          </View>
        </View>

        {/* AI Insights */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.insightsHeader}
            onPress={() => setIsInsightsExpanded(!isInsightsExpanded)}
            activeOpacity={0.9}
          >
            <View>
              <Text style={styles.insightsHeaderTitle}>AI Insights</Text>
              <Text style={styles.insightsHeaderSubtitle}>
                {isInsightsExpanded ? 'Tap to collapse' : 'Tap to expand'}
              </Text>
            </View>
            <View style={[styles.expandIndicator, isInsightsExpanded && styles.expandIndicatorActive]} />
          </TouchableOpacity>

          {isInsightsExpanded && (
            <View style={styles.insightsContent}>
              {renderFormattedInsights(ai_insights)}
            </View>
          )}
        </View>

        {/* Action Items */}
        {(financial_data.recommendations_data.needs_budget_adjustment ||
          financial_data.recommendations_data.needs_savings_increase ||
          financial_data.recommendations_data.has_negative_cash_flow ||
          financial_data.recommendations_data.spending_is_volatile) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recommended Actions</Text>
            <View style={styles.actionsCard}>
              {financial_data.recommendations_data.has_negative_cash_flow && (
                <View style={[styles.actionRow, styles.actionCritical]}>
                  <Text style={styles.actionText}>Review your cash flow</Text>
                  <Text style={styles.actionPriority}>High Priority</Text>
                </View>
              )}
              {financial_data.recommendations_data.needs_savings_increase && (
                <View style={styles.actionRow}>
                  <Text style={styles.actionText}>Increase your savings rate</Text>
                  <Text style={styles.actionPriority}>Medium</Text>
                </View>
              )}
              {financial_data.recommendations_data.needs_budget_adjustment && (
                <View style={styles.actionRow}>
                  <Text style={styles.actionText}>Adjust your budget</Text>
                  <Text style={styles.actionPriority}>Medium</Text>
                </View>
              )}
              {financial_data.recommendations_data.spending_is_volatile && (
                <View style={styles.actionRow}>
                  <Text style={styles.actionText}>Stabilize spending patterns</Text>
                  <Text style={styles.actionPriority}>Low</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Updated {new Date(financial_data.generated_at).toLocaleDateString()}
          </Text>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 60,
  },
  
  // Loading State
  loadingText: {
    marginTop: 20,
    fontSize: 20,
    fontWeight: '600',
    color: '#1A1A1A',
    letterSpacing: -0.3,
  },
  loadingDots: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: ZamanColors.persianGreen,
  },
  dot1: { opacity: 0.4 },
  dot2: { opacity: 0.7 },
  dot3: { opacity: 1.0 },
  
  // Empty State
  emptyStateText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  emptyStateSubtext: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
  },
  
  // Hero Section
  heroSection: {
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 40,
    paddingHorizontal: 24,
    backgroundColor: '#FFFFFF',
  },
  heroContent: {
    alignItems: 'center',
  },
  heroGreeting: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.5,
    textAlign: 'center',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  
  // Period Selector
  periodSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  periodChip: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  periodChipActive: {
    backgroundColor: '#0D8377',
    borderColor: '#0D8377',
  },
  periodChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  periodChipTextActive: {
    color: '#FFFFFF',
  },
  
  // Score Container
  scoreContainer: {
    alignItems: 'center',
    width: '100%',
  },
  scoreLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  scoreValue: {
    fontSize: 72,
    fontWeight: '800',
    color: '#1A1A1A',
    letterSpacing: -2,
    marginBottom: 16,
  },
  scoreBar: {
    width: '100%',
    height: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 12,
  },
  scoreBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  scoreStatus: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  
  // Metrics Section
  metricsSection: {
    paddingHorizontal: 24,
    paddingVertical: 24,
    gap: 16,
  },
  metricCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  metricLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 32,
    fontWeight: '800',
    color: '#1A1A1A',
    letterSpacing: -1,
    marginBottom: 4,
  },
  metricChange: {
    fontSize: 14,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  
  // Section Styles
  section: {
    paddingHorizontal: 24,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 1.2,
  },
  
  // Balance Card
  balanceCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  currencyBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  currencyBadgeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
    letterSpacing: 0.5,
  },
  balanceValue: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1A1A1A',
    letterSpacing: -1,
  },
  balanceMeta: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  balanceMetaText: {
    fontSize: 13,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  
  // Spending Card
  spendingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    gap: 16,
  },
  spendingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  spendingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  spendingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  spendingLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#374151',
    textTransform: 'capitalize',
  },
  spendingRight: {
    alignItems: 'flex-end',
  },
  spendingPercent: {
    fontSize: 18,
    fontWeight: '800',
    color: '#1A1A1A',
    letterSpacing: -0.5,
  },
  spendingAmount: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 2,
  },
  
  // AI Insights
  insightsHeader: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 12,
  },
  insightsHeaderTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  insightsHeaderSubtitle: {
    fontSize: 13,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  expandIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    transform: [{ rotate: '0deg' }],
  },
  expandIndicatorActive: {
    backgroundColor: '#0D8377',
    transform: [{ rotate: '45deg' }],
  },
  insightsContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  
  // Formatted Insights
  insightSection: {
    marginTop: 20,
    marginBottom: 12,
  },
  insightSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  insightSectionDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#0D8377',
    marginRight: 10,
  },
  insightSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.2,
  },
  insightNumberedItem: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  insightNumberBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  insightNumberText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
  },
  insightNumberedContent: {
    flex: 1,
  },
  insightNumberedTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A1A',
    marginBottom: 4,
    lineHeight: 22,
  },
  insightNumberedDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 22,
  },
  insightBulletItem: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  insightBulletDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#9CA3AF',
    marginRight: 12,
    marginTop: 9,
  },
  insightBulletContent: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  insightBulletText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 22,
    flex: 1,
  },
  insightBulletTextBold: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
    lineHeight: 22,
  },
  insightSubheading: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
    marginTop: 8,
  },
  insightSubheadingText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A1A',
    lineHeight: 22,
  },
  insightNormalText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 22,
    marginBottom: 10,
  },
  
  // Actions Card
  actionsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    gap: 12,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#0D8377',
  },
  actionCritical: {
    backgroundColor: '#FEF2F2',
    borderLeftColor: '#DC2626',
  },
  actionText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A1A',
    flex: 1,
  },
  actionPriority: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  
  // Footer
  footer: {
    paddingHorizontal: 24,
    paddingVertical: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 13,
    color: '#9CA3AF',
    fontWeight: '500',
  },
});

