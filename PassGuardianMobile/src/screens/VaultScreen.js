import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    TouchableOpacity,
    StyleSheet,
    TextInput,
    RefreshControl,
    Alert,
} from 'react-native';
import { VaultService } from '../services/vaultService';
import { AuthService } from '../services/authService';
import * as Clipboard from 'expo-clipboard';

export default function VaultScreen({ route, navigation }) {
    const { masterPassword, userEmail } = route.params;
    const [secrets, setSecrets] = useState([]);
    const [filteredSecrets, setFilteredSecrets] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [userSalt, setUserSalt] = useState(null);

    useEffect(() => {
        loadSecrets();
        loadUserProfile();
    }, []);

    useEffect(() => {
        if (searchQuery) {
            const filtered = secrets.filter((s) =>
                s.service.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredSecrets(filtered);
        } else {
            setFilteredSecrets(secrets);
        }
    }, [searchQuery, secrets]);

    const loadUserProfile = async () => {
        // Load user's salt from Supabase (you'll need to store this during signup)
        // For now, we'll use a derived value
        const salt = userEmail; // Simplified - in production, fetch from users table
        setUserSalt(salt);
    };

    const loadSecrets = async () => {
        setRefreshing(true);
        const result = await VaultService.fetchSecrets();
        if (result.success) {
            setSecrets(result.secrets);
        } else {
            Alert.alert('Error', 'Failed to load secrets');
        }
        setRefreshing(false);
    };

    const handleCopyPassword = async (encryptedSecret) => {
        try {
            const result = await VaultService.decryptSecretData(
                encryptedSecret,
                masterPassword,
                userSalt
            );

            if (result.success) {
                await Clipboard.setStringAsync(result.password);
                Alert.alert('Success', 'Password copied to clipboard!');
            } else {
                Alert.alert('Error', 'Failed to decrypt password');
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to copy password');
        }
    };

    const handleSignOut = async () {
        const result = await AuthService.signOut();
        if (result.success) {
            navigation.replace('Login');
        }
    };

    const renderSecretItem = ({ item }) => {
        const isPrivate = item.is_private;
        return (
            <TouchableOpacity
                style={styles.secretCard}
                onPress={() =>
                    navigation.navigate('SecretDetail', {
                        secret: item,
                        masterPassword,
                        userSalt,
                    })
                }
            >
                <View style={styles.secretHeader}>
                    <Text style={styles.secretIcon}>{isPrivate ? '🔒' : '🔑'}</Text>
                    <View style={styles.secretInfo}>
                        <Text style={styles.secretService}>{item.service}</Text>
                        <Text style={styles.secretUsername}>{item.username}</Text>
                    </View>
                </View>

                <TouchableOpacity
                    style={styles.copyButton}
                    onPress={() => handleCopyPassword(item.secret)}
                >
                    <Text style={styles.copyButtonText}>📋 COPY</Text>
                </TouchableOpacity>
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.headerTitle}>🛡️ VAULT</Text>
                    <Text style={styles.headerSubtitle}>{secrets.length} credentials</Text>
                </View>
                <TouchableOpacity onPress={handleSignOut}>
                    <Text style={styles.signOutButton}>⏏️</Text>
                </TouchableOpacity>
            </View>

            {/* Search Bar */}
            <View style={styles.searchContainer}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="🔍 Search credentials..."
                    placeholderTextColor="#64748b"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                />
            </View>

            {/* Secrets List */}
            <FlatList
                data={filteredSecrets}
                renderItem={renderSecretItem}
                keyExtractor={(item) => item.id.toString()}
                contentContainerStyle={styles.listContainer}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={loadSecrets}
                        tintColor="#3b82f6"
                    />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>🔐</Text>
                        <Text style={styles.emptyTitle}>No credentials yet</Text>
                        <Text style={styles.emptySubtitle}>
                            Add your first credential to get started
                        </Text>
                    </View>
                }
            />

            {/* Add Button */}
            <TouchableOpacity
                style={styles.fab}
                onPress={() =>
                    navigation.navigate('AddSecret', { masterPassword, userSalt })
                }
            >
                <Text style={styles.fabText}>+</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 24,
        paddingTop: 60,
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(59, 130, 246, 0.3)',
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: '900',
        color: '#fff',
        letterSpacing: 2,
    },
    headerSubtitle: {
        fontSize: 12,
        color: '#64748b',
        marginTop: 4,
    },
    signOutButton: {
        fontSize: 28,
    },
    searchContainer: {
        padding: 16,
    },
    searchInput: {
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.3)',
        borderRadius: 12,
        padding: 16,
        color: '#e2e8f0',
        fontSize: 16,
    },
    listContainer: {
        padding: 16,
        paddingBottom: 80,
    },
    secretCard: {
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.2)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 12,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    secretHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
    },
    secretIcon: {
        fontSize: 24,
        marginRight: 16,
    },
    secretInfo: {
        flex: 1,
    },
    secretService: {
        fontSize: 16,
        fontWeight: '700',
        color: '#e2e8f0',
        marginBottom: 4,
    },
    secretUsername: {
        fontSize: 14,
        color: '#94a3b8',
    },
    copyButton: {
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderWidth: 1,
        borderColor: '#3b82f6',
        borderRadius: 8,
        paddingHorizontal: 16,
        paddingVertical: 8,
    },
    copyButtonText: {
        color: '#3b82f6',
        fontSize: 12,
        fontWeight: '800',
        letterSpacing: 1,
    },
    emptyContainer: {
        alignItems: 'center',
        marginTop: 80,
    },
    emptyText: {
        fontSize: 64,
        marginBottom: 16,
    },
    emptyTitle: {
        fontSize: 20,
        fontWeight: '700',
        color: '#e2e8f0',
        marginBottom: 8,
    },
    emptySubtitle: {
        fontSize: 14,
        color: '#64748b',
        textAlign: 'center',
    },
    fab: {
        position: 'absolute',
        bottom: 24,
        right: 24,
        width: 64,
        height: 64,
        borderRadius: 32,
        backgroundColor: '#3b82f6',
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#3b82f6',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.5,
        shadowRadius: 16,
        elevation: 8,
    },
    fabText: {
        fontSize: 32,
        color: '#fff',
        fontWeight: '300',
    },
});
