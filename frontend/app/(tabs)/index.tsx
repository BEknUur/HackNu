import { Image } from 'expo-image';
import { Platform, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useState, useEffect } from 'react';
import { useRouter } from 'expo-router';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors } from '@/constants/theme';
import { Link } from 'expo-router';

interface UserData {
  id: number;
  name: string;
  surname: string;
  email: string;
  phone: string;
  avatar?: string;
}

export default function HomeScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    loadUser();
  }, []);

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

  function handleLogout() {
    // On web, Alert.alert doesn't work, so use confirm
    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to logout?')) {
        if (typeof localStorage !== 'undefined') {
          localStorage.removeItem('user');
        }
        router.replace('/login');
      }
    } else {
      Alert.alert(
        'Logout',
        'Are you sure you want to logout?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Logout', 
            style: 'destructive',
            onPress: () => {
              if (typeof localStorage !== 'undefined') {
                localStorage.removeItem('user');
              }
              router.replace('/login');
            }
          }
        ]
      );
    }
  }

  const features = [
    {
      title: 'Live Chat',
      description: 'Real-time AI conversations',
      icon: 'message.fill',
      href: '/live-chat',
      gradient: ['#667eea', '#764ba2']
    },
    {
      title: 'Face Verification',
      description: 'Secure biometric authentication',
      icon: 'person.crop.circle.fill',
      href: '/face-verify',
      gradient: ['#f093fb', '#f5576c']
    },
    {
      title: 'Explore',
      description: 'Discover new features',
      icon: 'paperplane.fill',
      href: '/explore',
      gradient: ['#4facfe', '#00f2fe']
    }
  ];

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Header Section */}
      <ThemedView style={styles.header}>
        <LinearGradient
          colors={isDark ? ['#1a1a1a', '#2d2d2d'] : ['#667eea', '#764ba2']}
          style={styles.headerGradient}
        >
          <ThemedText style={styles.welcomeText}>
            Welcome, {user ? `${user.name} ${user.surname}` : 'Guest'}
          </ThemedText>
          <ThemedText style={styles.subtitleText}>
            Your AI-powered platform for innovation
          </ThemedText>
          {user && (
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <IconSymbol name="arrow.right.square.fill" size={20} color="white" />
              <ThemedText style={styles.logoutText}>Logout</ThemedText>
            </TouchableOpacity>
          )}
        </LinearGradient>
      </ThemedView>

      {/* Quick Actions */}
      <ThemedView style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Quick Actions</ThemedText>
        <ThemedView style={styles.quickActions}>
          {features.map((feature, index) => (
            <Link key={index} href={feature.href} asChild>
              <TouchableOpacity style={styles.featureCard}>
                <LinearGradient
                  colors={feature.gradient}
                  style={styles.cardGradient}
                >
                  <IconSymbol 
                    name={feature.icon} 
                    size={32} 
                    color="white" 
                  />
                  <ThemedText style={styles.cardTitle}>
                    {feature.title}
                  </ThemedText>
                  <ThemedText style={styles.cardDescription}>
                    {feature.description}
                  </ThemedText>
                </LinearGradient>
              </TouchableOpacity>
            </Link>
          ))}
        </ThemedView>
      </ThemedView>

      {/* Stats Section */}
      <ThemedView style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Platform Stats</ThemedText>
        <ThemedView style={styles.statsContainer}>
          <ThemedView style={styles.statCard}>
            <ThemedText style={styles.statNumber}>1.2K+</ThemedText>
            <ThemedText style={styles.statLabel}>Active Users</ThemedText>
          </ThemedView>
          <ThemedView style={styles.statCard}>
            <ThemedText style={styles.statNumber}>99.9%</ThemedText>
            <ThemedText style={styles.statLabel}>Uptime</ThemedText>
          </ThemedView>
          <ThemedView style={styles.statCard}>
            <ThemedText style={styles.statNumber}>24/7</ThemedText>
            <ThemedText style={styles.statLabel}>Support</ThemedText>
          </ThemedView>
        </ThemedView>
      </ThemedView>

      {/* Recent Activity */}
      <ThemedView style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Recent Activity</ThemedText>
        <ThemedView style={styles.activityCard}>
          <IconSymbol name="clock.fill" size={20} color={Colors[colorScheme ?? 'light'].tint} />
          <ThemedView style={styles.activityContent}>
            <ThemedText style={styles.activityTitle}>System Updated</ThemedText>
            <ThemedText style={styles.activityTime}>2 minutes ago</ThemedText>
          </ThemedView>
        </ThemedView>
        <ThemedView style={styles.activityCard}>
          <IconSymbol name="checkmark.circle.fill" size={20} color="#4CAF50" />
          <ThemedView style={styles.activityContent}>
            <ThemedText style={styles.activityTitle}>Face ID Verified</ThemedText>
            <ThemedText style={styles.activityTime}>5 minutes ago</ThemedText>
          </ThemedView>
        </ThemedView>
      </ThemedView>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 100, // Space for floating nav bar
  },
  header: {
    marginHorizontal: 16,
    marginTop: 20,
    borderRadius: 20,
    overflow: 'hidden',
  },
  headerGradient: {
    padding: 24,
    alignItems: 'center',
  },
  welcomeText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  subtitleText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    marginTop: 16,
  },
  logoutText: {
    color: 'white',
    marginLeft: 8,
    fontWeight: '600',
    fontSize: 14,
  },
  section: {
    marginHorizontal: 16,
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  featureCard: {
    flex: 1,
    minWidth: '30%',
    borderRadius: 16,
    overflow: 'hidden',
  },
  cardGradient: {
    padding: 16,
    alignItems: 'center',
    minHeight: 120,
    justifyContent: 'center',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 8,
    textAlign: 'center',
  },
  cardDescription: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#667eea',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  activityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(102, 126, 234, 0.05)',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  activityContent: {
    marginLeft: 12,
    flex: 1,
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  activityTime: {
    fontSize: 12,
    opacity: 0.6,
    marginTop: 2,
  },
});
