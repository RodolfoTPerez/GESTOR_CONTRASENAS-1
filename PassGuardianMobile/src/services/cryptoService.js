import * as Crypto from 'expo-crypto';
import { encode as base64Encode, decode as base64Decode } from 'base-64';
import { APP_CONFIG } from '../config/config';

/**
 * Crypto Service - AES-GCM Encryption/Decryption
 * COMPATIBLE with Python desktop version (AES-256-GCM + PBKDF2)
 */

/**
 * Derive encryption key from master password using PBKDF2
 * Compatible with Python: hashlib.pbkdf2_hmac('sha256', password, salt, iterations)
 */
async function deriveKey(masterPassword, salt) {
    const passwordBuffer = new TextEncoder().encode(masterPassword);
    const saltBuffer = typeof salt === 'string' ?
        base64DecodeToArrayBuffer(salt) :
        salt;

    // Import password as key material
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        passwordBuffer,
        { name: 'PBKDF2' },
        false,
        ['deriveBits', 'deriveKey']
    );

    // Derive 256-bit key using PBKDF2
    const key = await crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: saltBuffer,
            iterations: APP_CONFIG.PBKDF2_ITERATIONS,
            hash: 'SHA-256',
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
    );

    return key;
}

/**
 * Encrypt data using AES-GCM
 * Format: base64(iv + tag + ciphertext)
 */
export async function encryptSecret(plaintext, masterPassword, salt) {
    try {
        const key = await deriveKey(masterPassword, salt);

        // Generate random IV (12 bytes for GCM)
        const iv = crypto.getRandomValues(new Uint8Array(APP_CONFIG.IV_LENGTH));

        // Encrypt
        const plaintextBuffer = new TextEncoder().encode(plaintext);
        const ciphertextWithTag = await crypto.subtle.encrypt(
            {
                name: 'AES-GCM',
                iv: iv,
                tagLength: APP_CONFIG.TAG_LENGTH * 8, // 128 bits
            },
            key,
            plaintextBuffer
        );

        // Combine: IV + Ciphertext+Tag
        const combined = new Uint8Array(
            iv.length + ciphertextWithTag.byteLength
        );
        combined.set(iv, 0);
        combined.set(new Uint8Array(ciphertextWithTag), iv.length);

        // Return as base64
        return arrayBufferToBase64(combined);
    } catch (error) {
        console.error('Encryption error:', error);
        throw new Error('Failed to encrypt data');
    }
}

/**
 * Decrypt data using AES-GCM
 */
export async function decryptSecret(encryptedData, masterPassword, salt) {
    try {
        const key = await deriveKey(masterPassword, salt);

        // Decode from base64
        const combined = base64DecodeToArrayBuffer(encryptedData);

        // Extract IV and ciphertext+tag
        const iv = combined.slice(0, APP_CONFIG.IV_LENGTH);
        const ciphertextWithTag = combined.slice(APP_CONFIG.IV_LENGTH);

        // Decrypt
        const plaintextBuffer = await crypto.subtle.decrypt(
            {
                name: 'AES-GCM',
                iv: iv,
                tagLength: APP_CONFIG.TAG_LENGTH * 8,
            },
            key,
            ciphertextWithTag
        );

        // Decode to string
        return new TextDecoder().decode(plaintextBuffer);
    } catch (error) {
        console.error('Decryption error:', error);
        throw new Error('Failed to decrypt data - wrong password or corrupted data');
    }
}

/**
 * Generate random salt for key derivation
 */
export function generateSalt() {
    const salt = crypto.getRandomValues(new Uint8Array(APP_CONFIG.SALT_LENGTH));
    return arrayBufferToBase64(salt);
}

/**
 * Generate strong password
 */
export function generatePassword(length = 16, options = {}) {
    const {
        uppercase = true,
        lowercase = true,
        numbers = true,
        symbols = true,
    } = options;

    let chars = '';
    if (uppercase) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (lowercase) chars += 'abcdefghijklmnopqrstuvwxyz';
    if (numbers) chars += '0123456789';
    if (symbols) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';

    let password = '';
    const randomValues = crypto.getRandomValues(new Uint8Array(length));

    for (let i = 0; i < length; i++) {
        password += chars[randomValues[i] % chars.length];
    }

    return password;
}

// Helper functions
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return base64Encode(binary);
}

function base64DecodeToArrayBuffer(base64) {
    const binary = base64Decode(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}
