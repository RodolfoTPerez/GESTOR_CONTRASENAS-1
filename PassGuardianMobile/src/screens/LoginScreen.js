import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    Alert,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
} from 'react-native';
import { AuthService } from '../services/authService';
import { generateSalt } from '../services/cryptoService';

export default function LoginScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [isSignUp, setIsSignUp] = useState(false);
    const [username, setUsername] = useState('');

    const handleAuth = async () => {
        if (!email || !password) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }

        setLoading(true);

        try {
            let result;
            if (isSignUp) {
                if (!username) {
                    Alert.alert('Error', 'Please enter a username');
                    setLoading(false);
                    return;
                }
                result = await AuthService.signUp(email, password, username);
            } else {
                result = await AuthService.signIn(email, password);
            }

            if (result.success) {
                // Navigate to main app
                navigation.replace('Vault', {
                    masterPassword: password,
                    userEmail: email,
                });
            } else {
                Alert.alert('Error', result.error || 'Authentication failed');
            }
        } catch (error) {
            Alert.alert('Error', error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.container}
        >
            <View style={styles.content}>
                {/* Logo/Title */}
                <View style={styles.header}>
                    <Text style={styles.logoIcon}>🛡️</Text>
                    <Text style={styles.title}>PASSGUARDIAN</Text>
                    <Text style={styles.subtitle}>AI SECURITY SYSTEM</Text>
                </View>

                {/* Form */}
                <View style={styles.formContainer}>
                    {isSignUp && (
                        <View style={styles.inputContainer}>
                            <Text style={styles.label}>USERNAME</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="Enter username"
                                placeholderTextColor="#64748b"
                                value={username}
                                onChangeText={setUsername}
                                autoCapitalize="none"
                            />
                        </View>
                    )}

                    <View style={styles.inputContainer}>
                        <Text style={styles.label}>EMAIL</Text>
                        <TextInput
                            style={styles.input}
                            placeholder="Enter email"
                            placeholderTextColor="#64748b"
                            value={email}
                            onChangeText={setEmail}
                            keyboardType="email-address"
                            autoCapitalize="none"
                        />
                    </View>

                    <View style={styles.inputContainer}>
                        <Text style={styles.label}>MASTER PASSWORD</Text>
                        <TextInput
                            style={styles.input}
                            placeholder="Enter master password"
                            placeholderTextColor="#64748b"
                            value={password}
                            onChangeText={setPassword}
                            secureTextEntry
                        />
                    </View>

                    {/* Submit Button */}
                    <TouchableOpacity
                        style={[styles.button, loading && styles.buttonDisabled]}
                        onPress={handleAuth}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <Text style={styles.buttonText}>
                                {isSignUp ? 'CREATE ACCOUNT' : 'SIGN IN'}
                            </Text>
                        )}
                    </TouchableOpacity>

                    {/* Toggle Sign Up/Sign In */}
                    <TouchableOpacity
                        style={styles.toggleButton}
                        onPress={() => setIsSignUp(!isSignUp)}
                    >
                        <Text style={styles.toggleText}>
                            {isSignUp
                                ? 'Already have an account? Sign In'
                                : "Don't have an account? Sign Up"}
                        </Text>
                    </TouchableOpacity>
                </View>

                {/* Footer */}
                <Text style={styles.footer}>
                    🔒 End-to-end encrypted • Zero-knowledge architecture
                </Text>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a', // Dark Navy base
    },
    content: {
        flex: 1,
        justifyContent: 'center',
        padding: 24,
    },
    header: {
        alignItems: 'center',
        marginBottom: 48,
    },
    logoIcon: {
        fontSize: 64,
        marginBottom: 16,
    },
    title: {
        fontSize: 32,
        fontWeight: '900',
        color: '#fff',
        letterSpacing: 3,
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 12,
        fontWeight: '700',
        color: '#3b82f6', // Electric Blue
        letterSpacing: 2,
    },
    formContainer: {
        width: '100%',
    },
    inputContainer: {
        marginBottom: 20,
    },
    label: {
        fontSize: 11,
        fontWeight: '800',
        color: '#94a3b8',
        letterSpacing: 1.5,
        marginBottom: 8,
    },
    input: {
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.3)',
        borderRadius: 12,
        padding: 16,
        color: '#e2e8f0',
        fontSize: 16,
    },
    button: {
        backgroundColor: '#3b82f6', // Electric Blue
        borderRadius: 12,
        padding: 18,
        alignItems: 'center',
        marginTop: 12,
        shadowColor: '#3b82f6',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 12,
        elevation: 8,
    },
    buttonDisabled: {
        opacity: 0.6,
    },
    buttonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '800',
        letterSpacing: 1.5,
    },
    toggleButton: {
        marginTop: 24,
        alignItems: 'center',
    },
    toggleText: {
        color: '#64748b',
        fontSize: 14,
    },
    footer: {
        textAlign: 'center',
        color: '#64748b',
        fontSize: 12,
        marginTop: 32,
    },
});
