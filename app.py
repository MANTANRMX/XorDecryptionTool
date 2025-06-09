import os
import base64
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

def xor_decrypt(data: bytes, key: bytes) -> bytes:
    """XOR decrypt data with the given key"""
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def decrypt(encoded: str, key: str = "UTF-8") -> str:
    """Decode base64 and XOR decrypt with key"""
    try:
        decoded = base64.b64decode(encoded)
        decrypted = xor_decrypt(decoded, key.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

@app.route('/')
def index():
    """Main page with the decryption interface"""
    return render_template('index.html')

@app.route('/decrypt', methods=['POST'])
def decrypt_string():
    """API endpoint to decrypt the provided string"""
    try:
        data = request.get_json()
        if not data or 'encrypted_string' not in data:
            return jsonify({'error': 'Missing encrypted_string parameter'}), 400
        
        encrypted_string = data['encrypted_string'].strip()
        if not encrypted_string:
            return jsonify({'error': 'Encrypted string cannot be empty'}), 400
        
        # Perform 16 iterations of decryption
        results = []
        current_string = encrypted_string
        
        for i in range(16):
            try:
                current_string = decrypt(current_string)
                results.append({
                    'iteration': i + 1,
                    'result': current_string
                })
            except ValueError as e:
                # If decryption fails at any step, return partial results with error
                return jsonify({
                    'results': results,
                    'error': f'Decryption failed at iteration {i + 1}: {str(e)}',
                    'partial': True
                }), 200
            except Exception as e:
                return jsonify({
                    'results': results,
                    'error': f'Unexpected error at iteration {i + 1}: {str(e)}',
                    'partial': True
                }), 200
        
        return jsonify({
            'results': results,
            'success': True
        })
        
    except Exception as e:
        app.logger.error(f"Error in decrypt_string: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
