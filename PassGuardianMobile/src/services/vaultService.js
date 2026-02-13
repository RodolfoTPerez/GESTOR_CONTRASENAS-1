import { supabase } from './authService';
import { encryptSecret, decryptSecret } from './cryptoService';

/**
 * Vault Service - Manages encrypted secrets in Supabase
 */
export const VaultService = {
    /**
     * Fetch all secrets for current user
     */
    async fetchSecrets() {
        try {
            const { data, error } = await supabase
                .from('secrets')
                .select('*')
                .eq('deleted', false)
                .order('created_at', { ascending: false });

            if (error) throw error;
            return { success: true, secrets: data || [] };
        } catch (error) {
            console.error('Fetch secrets error:', error);
            return { success: false, error: error.message, secrets: [] };
        }
    },

    /**
     * Fetch single secret by ID
     */
    async getSecret(secretId) {
        try {
            const { data, error } = await supabase
                .from('secrets')
                .select('*')
                .eq('id', secretId)
                .single();

            if (error) throw error;
            return { success: true, secret: data };
        } catch (error) {
            console.error('Get secret error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Decrypt a secret (client-side decryption)
     */
    async decryptSecretData(encryptedSecret, masterPassword, userSalt) {
        try {
            const decrypted = await decryptSecret(encryptedSecret, masterPassword, userSalt);
            return { success: true, password: decrypted };
        } catch (error) {
            console.error('Decrypt error:', error);
            return { success: false, error: 'Failed to decrypt' };
        }
    },

    /**
     * Create new secret
     */
    async createSecret(secretData, masterPassword, userSalt) {
        try {
            // Encrypt the password before sending to Supabase
            const encryptedPassword = await encryptSecret(
                secretData.password,
                masterPassword,
                userSalt
            );

            const { data, error } = await supabase
                .from('secrets')
                .insert([
                    {
                        service: secretData.service,
                        username: secretData.username,
                        secret: encryptedPassword,
                        is_private: secretData.is_private || false,
                        notes: secretData.notes || '',
                    },
                ])
                .select()
                .single();

            if (error) throw error;
            return { success: true, secret: data };
        } catch (error) {
            console.error('Create secret error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Update existing secret
     */
    async updateSecret(secretId, updates, masterPassword, userSalt) {
        try {
            const payload = { ...updates };

            // If password is being updated, encrypt it
            if (updates.password) {
                payload.secret = await encryptSecret(updates.password, masterPassword, userSalt);
                delete payload.password;
            }

            const { data, error } = await supabase
                .from('secrets')
                .update(payload)
                .eq('id', secretId)
                .select()
                .single();

            if (error) throw error;
            return { success: true, secret: data };
        } catch (error) {
            console.error('Update secret error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Soft delete secret
     */
    async deleteSecret(secretId) {
        try {
            const { error } = await supabase
                .from('secrets')
                .update({ deleted: true })
                .eq('id', secretId);

            if (error) throw error;
            return { success: true };
        } catch (error) {
            console.error('Delete secret error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Search secrets by service name
     */
    async searchSecrets(query) {
        try {
            const { data, error } = await supabase
                .from('secrets')
                .select('*')
                .eq('deleted', false)
                .ilike('service', `%${query}%`)
                .order('created_at', { ascending: false });

            if (error) throw error;
            return { success: true, secrets: data || [] };
        } catch (error) {
            console.error('Search secrets error:', error);
            return { success: false, error: error.message, secrets: [] };
        }
    },
};
