from flask import Blueprint, render_template, request
import pandas as pd
import io
from models.clospan_models import run_clospan

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/', methods=['GET', 'POST'])
def index():
    patterns = None
    error = None

    if request.method == 'POST':
        if 'file' not in request.files or 'minsup' not in request.form:
            error = "Vui lòng tải lên file CSV và nhập minsup."
        else:
            file = request.files['file']
            minsup = request.form['minsup']

            if file.filename == '':
                error = "Chưa chọn file CSV."
            elif not file.filename.endswith('.csv'):
                error = "File phải có định dạng CSV."
            else:
                try:
                    minsup = float(minsup)
                    if minsup <= 0:
                        error = "Minsup phải lớn hơn 0."
                    else:
                        file_content = file.read().decode('utf-8')
                        df = pd.read_csv(io.StringIO(file_content))

                        required_columns = ['user_id', 'order_id', 'product_name', 'timestamp']
                        if not all(col in df.columns for col in required_columns):
                            error = "File CSV thiếu một hoặc nhiều cột cần thiết."
                        else:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                            if df['timestamp'].isnull().any():
                                error = "Một số giá trị timestamp không hợp lệ."
                            else:
                                df = df.sort_values(by=['user_id', 'timestamp'])
                                df_grouped = df.groupby(['user_id', 'order_id', 'timestamp'])['product_name'].apply(list).reset_index()
                                sequences_df = df_grouped.groupby('user_id').apply(
                                    lambda x: x[['order_id', 'timestamp', 'product_name']].to_dict('records')
                                ).reset_index()
                                sequences_df.columns = ['user_id', 'orders']

                                sequences = []
                                for _, row in sequences_df.iterrows():
                                    user_sequence = [order['product_name'] for order in row['orders']]
                                    sequences.append(user_sequence)

                                if not sequences:
                                    error = "Không thể tạo chuỗi từ dữ liệu được cung cấp."
                                else:
                                    patterns = run_clospan(sequences, int(minsup))
                                    if not patterns:
                                        error = f"Không tìm thấy mẫu nào với minsup = {int(minsup)}."

                except ValueError:
                    error = "Minsup phải là số."
                except Exception as e:
                    error = f"Lỗi: {str(e)}"

    return render_template('index.html', patterns=patterns, error=error)
