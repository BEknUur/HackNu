import { StyleSheet, View, Text, TouchableOpacity, Alert, Modal, Image, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import FaceCamera from '@/components/face-camera';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://46.101.175.118:8000/api/faceid';

interface UserMatchInfo {
  user_id: number;
  name: string;
  surname: string;
  email: string;
  phone: string;
  avatar: string;
  created_at?: string;
}

interface FaceVerificationResult {
  success: boolean;
  verified: boolean;
  message: string;
  user?: UserMatchInfo;
  confidence?: number;
  distance?: number;
  threshold?: number;
  model?: string;
  error?: string;
}

export default function FaceVerifyScreen() {
  const [showCamera, setShowCamera] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<FaceVerificationResult | null>(null);

  function handleStartVerification() {
    setCapturedPhoto(null);
    setVerificationResult(null);
    setShowCamera(true);
  }

  async function handlePhotoCapture(photoUri: string) {
    setCapturedPhoto(photoUri);
    setShowCamera(false);
    await verifyFace(photoUri);
  }

  async function verifyFace(photoUri: string) {
    setIsVerifying(true);
    
    try {
      const formData = new FormData();
      
      const response = await fetch(photoUri);
      const blob = await response.blob();
      
      formData.append('file', blob, 'photo.jpg');

      const verifyResponse = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      const result: FaceVerificationResult = await verifyResponse.json();
      setVerificationResult(result);

      if (result.success) {
        if (result.verified && result.user) {
          Alert.alert(
            '✅ Verification Successful',
            `Welcome back, ${result.user.name} ${result.user.surname}!\n\nConfidence: ${result.confidence ? (result.confidence * 100).toFixed(1) : 'N/A'}%`,
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert(
            '❌ Verification Failed',
            result.message || 'Face not recognized in our database.',
            [{ text: 'OK' }]
          );
        }
      } else {
        Alert.alert(
          'Error',
          result.message || result.error || 'Verification failed',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error during verification:', error);
      Alert.alert(
        'Connection Error',
        'Could not connect to the server. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsVerifying(false);
    }
  }

  function handleRetake() {
    setCapturedPhoto(null);
    setVerificationResult(null);
    setShowCamera(true);
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="shield-checkmark" size={50} color="#007AFF" />
        <Text style={styles.title}>Face Verification</Text>
        <Text style={styles.subtitle}>Verify your identity using facial recognition</Text>
      </View>

      <View style={styles.content}>
        {!capturedPhoto ? (
          <View style={styles.emptyState}>
            <Ionicons name="scan-outline" size={80} color="#ccc" />
            <Text style={styles.emptyStateText}>
              Click the button below to start face verification
            </Text>
          </View>
        ) : (
          <View style={styles.resultContainer}>
            <Image source={{ uri: capturedPhoto }} style={styles.capturedImage} />
            
            {isVerifying && (
              <View style={styles.verifyingOverlay}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.verifyingText}>Verifying your face...</Text>
              </View>
            )}

            {verificationResult && (
              <View style={styles.resultCard}>
                <View style={[
                  styles.resultBadge,
                  verificationResult.verified ? styles.successBadge : styles.failureBadge
                ]}>
                  <Ionicons 
                    name={verificationResult.verified ? "checkmark-circle" : "close-circle"} 
                    size={20} 
                    color="white" 
                  />
                  <Text style={styles.resultBadgeText}>
                    {verificationResult.verified ? 'VERIFIED' : 'NOT VERIFIED'}
                  </Text>
                </View>

                {verificationResult.verified && verificationResult.user && (
                  <View style={styles.resultDetail}>
                    <Text style={styles.resultLabel}>Matched Person:</Text>
                    <Text style={styles.resultValue}>
                      {verificationResult.user.name} {verificationResult.user.surname}
                    </Text>
                  </View>
                )}

                {verificationResult.confidence && (
                  <View style={styles.resultDetail}>
                    <Text style={styles.resultLabel}>Confidence:</Text>
                    <Text style={styles.resultValue}>
                      {(verificationResult.confidence * 100).toFixed(1)}%
                    </Text>
                  </View>
                )}

                {verificationResult.distance && (
                  <View style={styles.resultDetail}>
                    <Text style={styles.resultLabel}>Distance:</Text>
                    <Text style={styles.resultValue}>
                      {verificationResult.distance.toFixed(4)}
                    </Text>
                  </View>
                )}

                {verificationResult.threshold && (
                  <View style={styles.resultDetail}>
                    <Text style={styles.resultLabel}>Threshold:</Text>
                    <Text style={styles.resultValue}>
                      {verificationResult.threshold.toFixed(4)}
                    </Text>
                  </View>
                )}

                {verificationResult.model && (
                  <View style={styles.resultDetail}>
                    <Text style={styles.resultLabel}>Model:</Text>
                    <Text style={styles.resultValue}>
                      {verificationResult.model}
                    </Text>
                  </View>
                )}
              </View>
            )}
          </View>
        )}
      </View>

      <View style={styles.actions}>
        {capturedPhoto ? (
          <TouchableOpacity 
            style={styles.retakeButton} 
            onPress={handleRetake}
            disabled={isVerifying}
          >
            <Ionicons name="camera" size={20} color="white" />
            <Text style={styles.buttonText}>Try Again</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.startButton} 
            onPress={handleStartVerification}
          >
            <Ionicons name="camera" size={20} color="white" />
            <Text style={styles.buttonText}>Start Verification</Text>
          </TouchableOpacity>
        )}
      </View>

      <Modal
        visible={showCamera}
        animationType="slide"
        presentationStyle="fullScreen"
      >
        <FaceCamera
          onCapture={handlePhotoCapture}
          onClose={() => setShowCamera(false)}
          isVerifying={isVerifying}
        />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: 'white',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#999',
    marginTop: 15,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  resultContainer: {
    flex: 1,
  },
  capturedImage: {
    width: '100%',
    height: 300,
    borderRadius: 10,
    backgroundColor: '#ddd',
  },
  verifyingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 10,
  },
  verifyingText: {
    color: 'white',
    fontSize: 16,
    marginTop: 10,
    fontWeight: '600',
  },
  resultCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginTop: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  successBadge: {
    backgroundColor: '#4CAF50',
  },
  failureBadge: {
    backgroundColor: '#F44336',
  },
  resultBadgeText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 5,
  },
  resultDetail: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  resultLabel: {
    fontSize: 14,
    color: '#666',
  },
  resultValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  actions: {
    padding: 20,
    paddingBottom: 30,
  },
  startButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 8,
  },
  retakeButton: {
    backgroundColor: '#FF9500',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
});