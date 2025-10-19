import { StyleSheet, View, Text, TextInput, TouchableOpacity, Alert, Modal, Image, ActivityIndicator, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import FaceCamera from '@/components/face-camera';
import ZamanLogo from '@/components/zaman-logo';
import { Ionicons } from '@expo/vector-icons';
import { ZamanColors } from '@/constants/theme';
import { loginUser, registerUser, verifyFaceID, type UserData } from '@/lib/api-client';

export default function LoginScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [showCamera, setShowCamera] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Form fields
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  
  const resetForm = () => {
    setName('');
    setSurname('');
    setEmail('');
    setPhone('');
    setPassword('');
    setCapturedPhoto(null);
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    resetForm();
  };

  async function handlePhotoCapture(photoUri: string) {
    setCapturedPhoto(photoUri);
    setShowCamera(false);
  }

  async function saveUserSession(userData: UserData | any) {
    try {
      if (!userData) {
        console.error('No user data provided');
        return;
      }
      
      // Normalize user data - handle both 'id' and 'user_id' formats
      const normalizedUser = {
        id: userData.id || userData.user_id,
        name: userData.name,
        surname: userData.surname,
        email: userData.email,
        phone: userData.phone,
        avatar: userData.avatar,
        created_at: userData.created_at || new Date().toISOString(),
        updated_at: userData.updated_at || new Date().toISOString(),
      };
      
      console.log('Saving normalized user to localStorage:', normalizedUser);
      
      const userJson = JSON.stringify(normalizedUser);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('user', userJson);
      }
    } catch (error) {
      console.error('Error saving user session:', error);
    }
  }

  function validateEmail(email: string): boolean {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email.trim());
  }

  async function handleFaceVerify() {
    if (!capturedPhoto) {
      Alert.alert('❌ Error', 'Please capture a photo first');
      return;
    }

    // Prevent duplicate calls
    if (isLoading) {
      console.log('Verification already in progress, skipping...');
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('Starting face verification...');
      console.log('Photo URI:', capturedPhoto);
      
      // Fetch the photo from the URI
      const response = await fetch(capturedPhoto);
      if (!response.ok) {
        throw new Error('Failed to load photo from URI');
      }
      
      const blob = await response.blob();
      console.log('Blob created, size:', blob.size, 'type:', blob.type);
      
      if (blob.size === 0) {
        throw new Error('Photo file is empty');
      }

      console.log('Sending verification request...');
      const result = await verifyFaceID(blob);
      console.log('Verification result:', result);

      if (result.success && result.verified && result.user) {
        // Clear captured photo immediately to prevent re-triggering
        setCapturedPhoto(null);
        
        // Save session
        await saveUserSession(result.user);
        
        console.log('Login successful, redirecting...');
        
        // Redirect immediately without Alert
        router.replace('/(tabs)');
      } else if (result.success && !result.verified) {
        Alert.alert(
          '❌ Face Not Recognized',
          result.message || 'No matching face found. Please try again or register if you don\'t have an account.',
          [{ text: 'OK' }]
        );
      } else if (result.error) {
        let errorMsg = 'Error processing your photo.';
        if (result.error.toLowerCase().includes('face')) {
          errorMsg = 'Could not detect a face in the photo. Please ensure your face is clearly visible and try again.';
        }
        Alert.alert('❌ Verification Error', errorMsg, [{ text: 'OK' }]);
      } else {
        Alert.alert(
          '❌ Login Failed',
          result.message || 'Face verification failed. Please try again.',
          [{ text: 'OK' }]
        );
      }
    } catch (error: any) {
      console.error('Error during face verification:', error);
      
      let errorMessage = error.message || 'Could not connect to the server. Please check your internet connection and try again.';
      
      if (error.message?.includes('Failed to load photo')) {
        errorMessage = 'Failed to load the captured photo. Please try taking the photo again.';
      } else if (error.message?.includes('Photo file is empty')) {
        errorMessage = 'The captured photo is empty. Please try taking the photo again.';
      }
      
      Alert.alert(
        '🔌 Connection Error',
        errorMessage,
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleEmailPasswordLogin() {
    // Validate fields
    if (!email.trim() || !password.trim()) {
      Alert.alert('❌ Validation Error', 'Please enter both email and password');
      return;
    }

    if (!validateEmail(email)) {
      Alert.alert('❌ Invalid Email', 'Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      const userData = await loginUser({
        email: email.trim(),
        password: password,
      });
      
      // Save session
      await saveUserSession(userData);
      
      console.log('Email/password login successful, redirecting...');
      
      // Redirect immediately without Alert
      router.replace('/(tabs)');
      
    } catch (error: any) {
      console.error('Error during login:', error);
      
      const errorMessage = error.message || 'Login failed. Please try again.';
      Alert.alert('❌ Login Failed', errorMessage, [{ text: 'OK' }]);
      
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRegister() {
    // Validate fields
    if (!name.trim() || !surname.trim() || !email.trim() || !phone.trim() || !password.trim()) {
      Alert.alert('❌ Validation Error', 'Please fill in all required fields');
      return;
    }

    if (!validateEmail(email)) {
      Alert.alert('❌ Invalid Email', 'Please enter a valid email address');
      return;
    }

    if (password.length < 8) {
      Alert.alert('❌ Invalid Password', 'Password must be at least 8 characters long');
      return;
    }

    if (!capturedPhoto) {
      Alert.alert('❌ Photo Required', 'Please capture your face photo for Face ID registration');
      return;
    }

    setIsLoading(true);

    try {
      // Fetch the photo from URI and convert to blob
      const response = await fetch(capturedPhoto);
      if (!response.ok) {
        throw new Error('Failed to load captured photo');
      }
      const blob = await response.blob();

      // Register user
      const userData = await registerUser({
        name: name.trim(),
        surname: surname.trim(),
        email: email.trim(),
        phone: phone.trim(),
        password: password,
        avatar: blob,
      });
      
      // Clear captured photo to prevent re-triggering
      setCapturedPhoto(null);
      
      // Save session
      await saveUserSession(userData);
      
      console.log('Registration successful, redirecting...');
      
      // Redirect immediately without Alert
      router.replace('/(tabs)');
      
    } catch (error: any) {
      console.error('Error during registration:', error);
      
      const errorMessage = error.message || 'Registration failed. Please try again.';
      Alert.alert('❌ Registration Failed', errorMessage, [{ text: 'OK' }]);
      
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.keyboardView} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Minimal Header */}
          <View style={styles.header}>
            <View style={styles.logoMark}>
              <ZamanLogo size={90} withAccent />
            </View>
            <Text style={styles.appName}>ZAMAN</Text>
            <Text style={styles.tagline}>
              {mode === 'login' ? 'Welcome back' : 'Get started'}
            </Text>
          </View>

          {/* Content */}
          <View style={styles.content}>
            {/* Face ID Section */}
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>
                {mode === 'login' ? 'Face ID' : 'Face ID (Required)'}
              </Text>
              
              {capturedPhoto ? (
                <View style={styles.photoContainer}>
                  <Image source={{ uri: capturedPhoto }} style={styles.photo} />
                  <TouchableOpacity 
                    style={styles.linkButton}
                    onPress={() => setShowCamera(true)}
                    disabled={isLoading}
                  >
                    <Text style={styles.linkText}>Retake</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity 
                  style={styles.captureButton}
                  onPress={() => setShowCamera(true)}
                  disabled={isLoading}
                >
                  <Ionicons name="camera-outline" size={24} color={ZamanColors.persianGreen} />
                  <Text style={styles.captureButtonText}>
                    {mode === 'login' ? 'Scan face' : 'Capture face'}
                  </Text>
                </TouchableOpacity>
              )}

              {mode === 'login' && capturedPhoto && (
                <TouchableOpacity 
                  style={styles.primaryButton}
                  onPress={handleFaceVerify}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color={ZamanColors.black} />
                  ) : (
                    <Text style={styles.primaryButtonText}>Verify & Login</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>

            {/* Divider */}
            {mode === 'login' && (
              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>or</Text>
                <View style={styles.dividerLine} />
              </View>
            )}

            {/* Email/Password Login */}
            {mode === 'login' && (
              <View style={styles.section}>
                <Text style={styles.sectionLabel}>Email & Password</Text>
                
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  editable={!isLoading}
                />
                
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  editable={!isLoading}
                />
                
                <TouchableOpacity 
                  style={styles.primaryButton}
                  onPress={handleEmailPasswordLogin}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color={ZamanColors.black} />
                  ) : (
                    <Text style={styles.primaryButtonText}>Login</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* Register Form */}
            {mode === 'register' && (
              <View style={styles.section}>
                <Text style={styles.sectionLabel}>Personal Information</Text>
                
                <TextInput
                  style={styles.input}
                  placeholder="First name"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={name}
                  onChangeText={setName}
                  autoCapitalize="words"
                  editable={!isLoading}
                />
                
                <TextInput
                  style={styles.input}
                  placeholder="Last name"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={surname}
                  onChangeText={setSurname}
                  autoCapitalize="words"
                  editable={!isLoading}
                />
                
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  editable={!isLoading}
                />
                
                <TextInput
                  style={styles.input}
                  placeholder="Phone"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={phone}
                  onChangeText={setPhone}
                  keyboardType="phone-pad"
                  editable={!isLoading}
                />
                
                <TextInput
                  style={styles.input}
                  placeholder="Password (min 8 characters)"
                  placeholderTextColor={ZamanColors.gray[400]}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  editable={!isLoading}
                />

                <TouchableOpacity 
                  style={styles.primaryButton}
                  onPress={handleRegister}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color={ZamanColors.black} />
                  ) : (
                    <Text style={styles.primaryButtonText}>Create Account</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* Switch Mode */}
            <TouchableOpacity 
              style={styles.switchButton}
              onPress={switchMode}
              disabled={isLoading}
            >
              <Text style={styles.switchText}>
                {mode === 'login' 
                  ? "Don't have an account? " 
                  : 'Already have an account? '}
              </Text>
              <Text style={styles.switchTextBold}>
                {mode === 'login' ? 'Sign up' : 'Sign in'}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Camera Modal */}
      <Modal
        visible={showCamera}
        animationType="slide"
        presentationStyle="fullScreen"
      >
        <FaceCamera
          onCapture={handlePhotoCapture}
          onClose={() => setShowCamera(false)}
          isVerifying={false}
        />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: ZamanColors.white,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 80 : 60,
    paddingBottom: 40,
    paddingHorizontal: 32,
    alignItems: 'center',
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
    marginBottom: 8,
  },
  tagline: {
    fontSize: 15,
    color: ZamanColors.gray[500],
    fontWeight: '400',
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
    marginBottom: 16,
  },
  captureButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    borderRadius: 12,
    paddingVertical: 20,
    gap: 12,
  },
  captureButtonText: {
    fontSize: 16,
    color: ZamanColors.persianGreen,
    fontWeight: '500',
  },
  photoContainer: {
    alignItems: 'center',
    gap: 16,
  },
  photo: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: ZamanColors.gray[100],
    borderWidth: 2,
    borderColor: ZamanColors.persianGreen,
  },
  linkButton: {
    paddingVertical: 8,
  },
  linkText: {
    fontSize: 15,
    color: ZamanColors.persianGreen,
    fontWeight: '500',
  },
  input: {
    backgroundColor: ZamanColors.white,
    borderWidth: 1,
    borderColor: ZamanColors.gray[300],
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 16,
    fontSize: 16,
    color: ZamanColors.black,
    marginBottom: 12,
  },
  primaryButton: {
    backgroundColor: ZamanColors.solar,
    borderRadius: 12,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: ZamanColors.black,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 32,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: ZamanColors.gray[200],
  },
  dividerText: {
    marginHorizontal: 16,
    fontSize: 13,
    color: ZamanColors.gray[400],
    fontWeight: '400',
  },
  switchButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 32,
    paddingVertical: 16,
  },
  switchText: {
    fontSize: 15,
    color: ZamanColors.gray[600],
  },
  switchTextBold: {
    fontSize: 15,
    color: ZamanColors.persianGreen,
    fontWeight: '600',
  },
});

