import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';

export default function App() {
    return (
        <View style={styles.container}>
            <StatusBar style="light" />
            <Text style={styles.logo}>🛡️</Text>
            <Text style={styles.title}>PASSGUARDIAN</Text>
            <Text style={styles.subtitle}>Mobile App v1.0</Text>
            <Text style={styles.message}>
                ✅ La aplicación está funcionando correctamente!
            </Text>
            <Text style={styles.info}>
                Esta es una versión de prueba básica.
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
    },
    logo: {
        fontSize: 80,
        marginBottom: 20,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#fff',
        letterSpacing: 3,
        marginBottom: 10,
    },
    subtitle: {
        fontSize: 14,
        color: '#3b82f6',
        letterSpacing: 2,
        marginBottom: 40,
    },
    message: {
        fontSize: 18,
        color: '#10b981',
        textAlign: 'center',
        marginBottom: 20,
    },
    info: {
        fontSize: 14,
        color: '#94a3b8',
        textAlign: 'center',
    },
});
