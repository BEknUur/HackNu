import { View, Text, Platform, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useState, useEffect } from 'react';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Link } from 'expo-router';
import { ZamanColors } from '@/constants/theme';
import ZamanLogo from '@/components/zaman-logo';

interface UserData {
  id: number;
  name: string;
  surname: string;
  email: string;
  phone: string;
  avatar?: string;
}

export default function HomeScreen() {
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
          const userData = JSON.parse(userJson);
          console.log('Loaded user from localStorage:', userData);
          
          // Validate user data has required fields
          if (userData && userData.id) {
            setUser(userData);
          } else {
            console.error('Invalid user data in localStorage:', userData);
            // Redirect to login if invalid
            router.replace('/login');
          }
        } else {
          console.log('No user found in localStorage, redirecting to login');
          // Redirect to login if no user
          router.replace('/login');
        }
      }
    } catch (error) {
      console.error('Error loading user:', error);
      // Redirect to login on error
      router.replace('/login');
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
      icon: 'chatbubbles',
      href: '/live-chat' as const,
      bgColor: ZamanColors.cloud
    },
    {
      title: 'Wallet',
      description: 'Manage your transactions',
      icon: 'wallet',
      href: '/transactions' as const,
      bgColor: ZamanColors.cloud
    },
    {
      title: 'Financial Analysis',
      description: 'AI-powered insights',
      icon: 'analytics',
      href: '/financial-analysis' as const,
      bgColor: ZamanColors.cloud
    },
    {
      title: 'Explore',
      description: 'Discover new features',
      icon: 'compass',
      href: '/explore' as const,
      bgColor: ZamanColors.cloud
    }
  ];

  return (
    <View style={styles.container}>
      {/* Logout Button - Top Right */}
      {user && (
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      )}

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Minimal Header */}
        <View style={styles.header}>
          <View style={styles.logoMark}>
            <ZamanLogo size={90} withAccent />
          </View>
          <Text style={styles.appName}>ZAMAN</Text>
          <Text style={styles.welcomeText}>
            Welcome, {user ? `${user.name} ${user.surname}` : 'Beknur Ualikhanuly'}
          </Text>
          <Text style={styles.subtitleText}>
            Your AI-powered platform for innovation
          </Text>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {/* Quick Actions */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Quick Actions</Text>
            <View style={styles.quickActions}>
              {features.map((feature, index) => (
                <Link key={index} href={feature.href} asChild>
                  <TouchableOpacity style={styles.featureCard}>
                    <View style={styles.iconContainer}>
                      <Ionicons 
                        name={feature.icon as any} 
                        size={28} 
                        color={ZamanColors.white}
                      />
                    </View>
                    <Text style={styles.cardTitle}>
                      {feature.title}
                    </Text>
                    <Text style={styles.cardDescription}>
                      {feature.description}
                    </Text>
                  </TouchableOpacity>
                </Link>
              ))}
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: ZamanColors.white,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    flexGrow: 1,
    paddingBottom: 100,
  },
  logoutButton: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 60 : 40,
    right: 24,
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 12,
    zIndex: 100,
  },
  logoutText: {
    color: ZamanColors.persianGreen,
    fontWeight: '500',
    fontSize: 15,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 80 : 60,
    paddingBottom: 50,
    paddingHorizontal: 32,
    alignItems: 'center',
    backgroundColor: ZamanColors.white,
  },
  logoMark: {
    marginBottom: 20,
    alignItems: 'center',
  },
  appName: {
    fontSize: 32,
    fontWeight: '300',
    letterSpacing: 8,
    color: ZamanColors.black,
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 20,
    fontWeight: '600',
    color: ZamanColors.black,
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitleText: {
    fontSize: 15,
    color: ZamanColors.gray[500],
    fontWeight: '400',
    textAlign: 'center',
    marginBottom: 24,
  },
  content: {
    paddingHorizontal: 32,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 40,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: ZamanColors.gray[600],
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 20,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  featureCard: {
    width: '47%',
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    minHeight: 180,
    justifyContent: 'center',
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: ZamanColors.persianGreen,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: ZamanColors.black,
    marginBottom: 8,
    textAlign: 'center',
  },
  cardDescription: {
    fontSize: 13,
    color: ZamanColors.gray[500],
    textAlign: 'center',
    lineHeight: 18,
  },
});
