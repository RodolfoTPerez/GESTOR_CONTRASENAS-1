// Supabase Configuration
// IMPORTANT: Replace with your actual Supabase credentials

export const SUPABASE_URL = 'https://iymgmlxlvjsqxiwdznac.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5bWdtbHhsdmpzcXhpd2R6bmFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc0NTU0NDAsImV4cCI6MjA1MzAzMTQ0MH0.2FiHqHCxiPqvd96jqKXJXiD4n8S_Tj-HziNP9mqpBpA';

// App Configuration
export const APP_CONFIG = {
    APP_NAME: 'PassGuardian',
    VERSION: '1.0.0',
    CIPHER_ALGORITHM: 'AES-GCM',
    KEY_DERIVATION: 'PBKDF2',
    PBKDF2_ITERATIONS: 100000,
    SALT_LENGTH: 16,
    IV_LENGTH: 12,
    TAG_LENGTH: 16
};
