import { StyleSheet, View, Text, TouchableOpacity, Alert, Modal, Image, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import FaceCamera from '@/components/face-camera';
import { Ionicons } from '@expo/vector-icons';
import { config } from '@/lib/config';

const API_URL = `${config.backendURL}${config.endpoints.faceid}`;

interface VerificationResult {
  success: boolean;
  message: string;
  result?: {
    verified: boolean;
    confidence: number;
    matched_person?: string;
    distance: number;
    threshold: number;
    model: string;
    detector_backend: string;
    similarity_metric: string;
  };
  error?: string;
}

export default function FaceVerifyScreen() {
  const [showCamera, setShowCamera] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [registeredCount, setRegisteredCount] = useState<number | null>(null);
  const [matchedPersonImage, setMatchedPersonImage] = useState<string | null>(null);

  // Load registered faces count on mount
  useState(() => {
    fetchRegisteredCount();
  });

  async function fetchRegisteredCount() {
    try {
      const response = await fetch(`${API_URL}/registered-count`);
      const data = await response.json();
      if (data.success) {
        setRegisteredCount(data.count);
      }
    } catch (error) {
      console.error('Error fetching registered count:', error);
    }
  }

  function handleStartVerification() {
    setCapturedPhoto(null);
    setVerificationResult(null);
    setMatchedPersonImage(null);
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
      // Create form data
      const formData = new FormData();
      
      // Convert image URI to blob for upload
      const response = await fetch(photoUri);
      const blob = await response.blob();
      
      // @ts-ignore - FormData append handles File/Blob
      formData.append('file', blob, 'photo.jpg');

      // Send to backend
      const verifyResponse = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      const result: VerificationResult = await verifyResponse.json();
      setVerificationResult(result);

      // Load matched person's image if verified
      if (result.success && result.result?.verified && result.result.matched_person) {
        try {
          const imageUrl = `${API_URL}/image/${result.result.matched_person}`;
          setMatchedPersonImage(imageUrl);
        } catch (error) {
          console.error('Error loading matched person image:', error);
        }
      }

      // Show result
      if (result.success && result.result) {
        if (result.result.verified) {
          Alert.alert(
            '✅ Verification Successful',
            `Welcome back, ${result.result.matched_person}!\n\nConfidence: ${(result.result.confidence * 100).toFixed(1)}%`,
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert(
            '❌ Verification Failed',
            `Face not recognized in our database.\n\nPlease try again or register your face first.`,
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
    setMatchedPersonImage(null);
    setShowCamera(true);
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="shield-checkmark" size={60} color="#007AFF" />
        <Text style={styles.title}>Face Verification</Text>
        <Text style={styles.subtitle}>
          Verify your identity using facial recognition
        </Text>
        {registeredCount !== null && (
          <Text style={styles.registeredCount}>
            {registeredCount} face{registeredCount !== 1 ? 's' : ''} registered in database
          </Text>
        )}
      </View>

      {/* Content */}
      <View style={styles.content}>
        {!capturedPhoto ? (
          <View style={styles.emptyState}>
            <Ionicons name="scan-outline" size={100} color="#ccc" />
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

            {verificationResult && verificationResult.result && (
              <View style={styles.resultCard}>
                <View style={[
                  styles.resultBadge,
                  verificationResult.result.verified ? styles.successBadge : styles.failureBadge
                ]}>
                  <Ionicons 
                    name={verificationResult.result.verified ? "checkmark-circle" : "close-circle"} 
                    size={24} 
                    color="white" 
                  />
                  <Text style={styles.resultBadgeText}>
                    {verificationResult.result.verified ? 'VERIFIED' : 'NOT VERIFIED'}
                  </Text>
                </View>

                {verificationResult.result.verified && verificationResult.result.matched_person && (
                  <>
                    <View style={styles.resultDetail}>
                      <Text style={styles.resultLabel}>Matched Person:</Text>
                      <Text style={styles.resultValue}>{verificationResult.result.matched_person}</Text>
                    </View>
                    
                    {matchedPersonImage && (
                      <View style={styles.matchedImageContainer}>
                        <Text style={styles.matchedImageLabel}>Registered Photo:</Text>
                        <Image 
                          source={{ uri: matchedPersonImage }} 
                          style={styles.matchedPersonImage}
                          resizeMode="cover"
                        />
                      </View>
                    )}
                  </>
                )}

                <View style={styles.resultDetail}>
                  <Text style={styles.resultLabel}>Confidence:</Text>
                  <Text style={styles.resultValue}>
                    {(verificationResult.result.confidence * 100).toFixed(1)}%
                  </Text>
                </View>

                <View style={styles.resultDetail}>
                  <Text style={styles.resultLabel}>Distance:</Text>
                  <Text style={styles.resultValue}>
                    {verificationResult.result.distance.toFixed(4)}
                  </Text>
                </View>
              </View>
            )}
          </View>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {capturedPhoto ? (
          <TouchableOpacity 
            style={styles.retakeButton} 
            onPress={handleRetake}
            disabled={isVerifying}
          >
            <Ionicons name="camera" size={24} color="white" />
            <Text style={styles.buttonText}>Try Again</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.startButton} 
            onPress={handleStartVerification}
          >
            <Ionicons name="camera" size={24} color="white" />
            <Text style={styles.buttonText}>Start Verification</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Camera Modal */}
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
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 15,
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  registeredCount: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 10,
    fontWeight: '600',
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
    marginTop: 20,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  resultContainer: {
    flex: 1,
  },
  capturedImage: {
    width: '100%',
    height: 400,
    borderRadius: 15,
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
    borderRadius: 15,
  },
  verifyingText: {
    color: 'white',
    fontSize: 16,
    marginTop: 15,
    fontWeight: '600',
  },
  resultCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  resultBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    marginBottom: 15,
  },
  successBadge: {
    backgroundColor: '#4CAF50',
  },
  failureBadge: {
    backgroundColor: '#F44336',
  },
  resultBadgeText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  resultDetail: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
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
  matchedImageContainer: {
    marginTop: 15,
    alignItems: 'center',
  },
  matchedImageLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 10,
  },
  matchedPersonImage: {
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 3,
    borderColor: '#4CAF50',
  },
  actions: {
    padding: 20,
    paddingBottom: 40,
  },
  startButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 12,
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  retakeButton: {
    backgroundColor: '#FF9500',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 12,
    shadowColor: '#FF9500',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});

