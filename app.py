from flask import Flask
from controllers.analysis_controller import analysis_bp
import os

app = Flask(__name__, template_folder='views')  
app.config['UPLOAD_FOLDER'] = 'uploads'

app.register_blueprint(analysis_bp)

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
    