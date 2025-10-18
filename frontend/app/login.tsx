import { StyleSheet, View, Text, TextInput, TouchableOpacity, Alert, Modal, Image, ActivityIndicator, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import FaceCamera from '@/components/face-camera';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://46.101.175.118:8000/api';

interface UserData {
  id: number;
  name: string;
  surname: string;
  email: string;
  phone: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
}

interface FaceVerificationResult {
  success: boolean;
  verified: boolean;
  message: string;
  user?: {
    user_id: number;
    name: string;
    surname: string;
    email: string;
    phone: string;
    avatar: string;
  };
  confidence?: number;
  distance?: number;
  threshold?: number;
  model?: string;
  error?: string;
}

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

  async function saveUserSession(userData: UserData | FaceVerificationResult['user']) {
    try {
      if (!userData) {
        console.error('No user data provided');
        return;
      }

      // Normalize user data format
      let normalizedUser: UserData;
      
      if ('user_id' in userData) {
        // FaceVerificationResult.user format
        normalizedUser = {
          id: userData.user_id,
          name: userData.name,
          surname: userData.surname,
          email: userData.email,
          phone: userData.phone,
          avatar: userData.avatar,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
      } else {
        // UserData format (already normalized)
        normalizedUser = userData as UserData;
      }
      
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
      Alert.alert('Error', 'Please capture a photo first');
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
      console.log('API URL:', `${API_URL}/faceid/verify`);
      
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
      
      const formData = new FormData();
      // @ts-ignore - FormData accepts blob with filename
      formData.append('file', blob, 'photo.jpg');

      console.log('Sending verification request...');
      const verifyResponse = await fetch(`${API_URL}/faceid/verify`, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', verifyResponse.status);
      
      if (!verifyResponse.ok) {
        const errorText = await verifyResponse.text();
        console.error('Server error:', verifyResponse.status, errorText);
        throw new Error(`Server error: ${verifyResponse.status}`);
      }

      const result: FaceVerificationResult = await verifyResponse.json();
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
      
      let errorMessage = 'Could not connect to the server. Please check your internet connection and try again.';
      
      if (error.message) {
        if (error.message.includes('Network request failed')) {
          errorMessage = 'Network error: Cannot reach the server. Please check if the server is running and your internet connection is active.';
        } else if (error.message.includes('Failed to load photo')) {
          errorMessage = 'Failed to load the captured photo. Please try taking the photo again.';
        } else if (error.message.includes('Photo file is empty')) {
          errorMessage = 'The captured photo is empty. Please try taking the photo again.';
        } else if (error.message.includes('Server error')) {
          errorMessage = 'Server error occurred. Please try again or contact support if the issue persists.';
        }
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
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password: password,
        }),
      });

      if (loginResponse.ok) {
        const userData: UserData = await loginResponse.json();
        
        // Save session
        await saveUserSession(userData);
        
        console.log('Email/password login successful, redirecting...');
        
        // Redirect immediately without Alert
        router.replace('/(tabs)');
      } else {
        const errorData = await loginResponse.json();
        console.error('Login error:', loginResponse.status, errorData);
        
        let errorMessage = 'Login failed. Please try again.';
        
        if (loginResponse.status === 401) {
          errorMessage = 'Invalid email or password. Please check your credentials and try again.';
        } else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Login failed';
        }
        
        Alert.alert('❌ Login Failed', errorMessage);
      }
    } catch (error) {
      console.error('Error during login:', error);
      Alert.alert(
        '🔌 Connection Error',
        'Could not connect to the server. Please check your internet connection and try again.',
        [{ text: 'OK' }]
      );
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
      const formData = new FormData();
      formData.append('name', name.trim());
      formData.append('surname', surname.trim());
      formData.append('email', email.trim().toLowerCase());
      formData.append('phone', phone.trim());
      formData.append('password', password);

      // Add avatar
      const response = await fetch(capturedPhoto);
      const blob = await response.blob();
      // @ts-ignore - FormData accepts blob with filename
      formData.append('avatar', blob, 'avatar.jpg');

      const registerResponse = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        body: formData,
      });

      if (registerResponse.ok) {
        const userData: UserData = await registerResponse.json();
        
        // Clear captured photo to prevent re-triggering
        setCapturedPhoto(null);
        
        // Save session
        await saveUserSession(userData);
        
        console.log('Registration successful, redirecting...');
        
        // Redirect immediately without Alert
        router.replace('/(tabs)');
      } else {
        const errorData = await registerResponse.json();
        console.error('Registration error:', registerResponse.status, errorData);
        
        let errorMessage = 'Could not register. Please try again.';
        
        if (registerResponse.status === 400) {
          if (errorData.detail?.includes('Email')) {
            errorMessage = 'This email is already registered. Please use a different email or try logging in.';
          } else if (errorData.detail?.includes('Phone')) {
            errorMessage = 'This phone number is already registered. Please use a different number.';
          } else {
            errorMessage = errorData.detail || 'This email or phone number is already registered.';
          }
        } else if (registerResponse.status === 422) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join('\n');
          }
        } else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
        
        Alert.alert('❌ Registration Failed', errorMessage);
      }
    } catch (error) {
      console.error('Error during registration:', error);
      Alert.alert(
        '🔌 Connection Error',
        'Could not connect to the server. Please check your internet connection and try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Ionicons name="person-circle" size={60} color="#007AFF" />
          <Text style={styles.title}>
            {mode === 'login' ? 'Login' : 'Register'}
          </Text>
          <Text style={styles.subtitle}>
            {mode === 'login' 
              ? 'Use Face ID to login' 
              : 'Create your account with Face ID'}
          </Text>
        </View>

        <View style={styles.content}>
          {/* Face ID Section */}
          <View style={styles.faceSection}>
            <Text style={styles.sectionTitle}>
              {mode === 'login' ? 'Login with Face ID' : 'Capture your face (required for Face ID)'}
            </Text>
            
            {capturedPhoto ? (
              <View style={styles.photoContainer}>
                <Image source={{ uri: capturedPhoto }} style={styles.photo} />
                <TouchableOpacity 
                  style={styles.retakeButton}
                  onPress={() => setShowCamera(true)}
                  disabled={isLoading}
                >
                  <Ionicons name="camera" size={20} color="white" />
                  <Text style={styles.retakeText}>Retake</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity 
                style={styles.faceButton}
                onPress={() => setShowCamera(true)}
                disabled={isLoading}
              >
                <Ionicons name="camera" size={30} color="#007AFF" />
                <Text style={styles.faceButtonText}>
                  {mode === 'login' ? 'Scan Face to Login' : 'Capture Face'}
                </Text>
              </TouchableOpacity>
            )}

            {mode === 'login' && capturedPhoto && (
              <TouchableOpacity 
                style={styles.verifyButton}
                onPress={handleFaceVerify}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <Ionicons name="checkmark-circle" size={20} color="white" />
                    <Text style={styles.buttonText}>Verify & Login</Text>
                  </>
                )}
              </TouchableOpacity>
            )}
          </View>

          {/* Divider */}
          {mode === 'login' && (
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR</Text>
              <View style={styles.dividerLine} />
            </View>
          )}

          {/* Email/Password Login Section */}
          {mode === 'login' && (
            <>
              <Text style={styles.sectionTitle}>Login with Email & Password</Text>
              <TextInput
                style={styles.input}
                placeholder="Email *"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                editable={!isLoading}
              />
              <TextInput
                style={styles.input}
                placeholder="Password *"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                editable={!isLoading}
              />
              <TouchableOpacity 
                style={styles.submitButton}
                onPress={handleEmailPasswordLogin}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <Ionicons name="log-in" size={20} color="white" />
                    <Text style={styles.buttonText}>Login</Text>
                  </>
                )}
              </TouchableOpacity>
            </>
          )}

          {/* Form Section for Register */}
          {mode === 'register' && (
            <>
              <TextInput
                style={styles.input}
                placeholder="First Name *"
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
                editable={!isLoading}
              />
              <TextInput
                style={styles.input}
                placeholder="Last Name *"
                value={surname}
                onChangeText={setSurname}
                autoCapitalize="words"
                editable={!isLoading}
              />
              <TextInput
                style={styles.input}
                placeholder="Email *"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                editable={!isLoading}
              />
              <TextInput
                style={styles.input}
                placeholder="Phone Number *"
                value={phone}
                onChangeText={setPhone}
                keyboardType="phone-pad"
                editable={!isLoading}
              />
              <TextInput
                style={styles.input}
                placeholder="Password (min 8 characters) *"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                editable={!isLoading}
              />

              {/* Register Button */}
              <TouchableOpacity 
                style={styles.submitButton}
                onPress={handleRegister}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text style={styles.buttonText}>Register</Text>
                )}
              </TouchableOpacity>
            </>
          )}

          {/* Switch Mode */}
          <TouchableOpacity 
            style={styles.switchButton}
            onPress={switchMode}
            disabled={isLoading}
          >
            <Text style={styles.switchText}>
              {mode === 'login' 
                ? "Don't have an account? Register" 
                : 'Already have an account? Login'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

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
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    backgroundColor: 'white',
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  content: {
    padding: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
    textAlign: 'center',
  },
  faceSection: {
    marginBottom: 20,
  },
  faceButton: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    borderRadius: 15,
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  faceButtonText: {
    fontSize: 18,
    color: '#007AFF',
    marginTop: 15,
    fontWeight: '600',
  },
  photoContainer: {
    alignItems: 'center',
  },
  photo: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#ddd',
    borderWidth: 3,
    borderColor: '#007AFF',
  },
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#666',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 25,
    marginTop: 15,
  },
  retakeText: {
    color: 'white',
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
  },
  verifyButton: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 12,
    marginTop: 20,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 30,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#ddd',
  },
  dividerText: {
    marginHorizontal: 15,
    fontSize: 14,
    color: '#999',
    fontWeight: '600',
  },
  input: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 16,
    marginBottom: 15,
    fontSize: 16,
  },
  submitButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 12,
    marginTop: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  switchButton: {
    marginTop: 25,
    alignItems: 'center',
    paddingVertical: 10,
  },
  switchText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

