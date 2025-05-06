from flask import Blueprint, render_template, request
import pandas as pd
import io
from models.clospan_models import run_clospan

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/', methods=['GET', 'POST'])
def index():
    patterns = None
    error = None

    print("Starting request processing...")

    if request.method == 'POST':
        print("POST request received")
        if 'file' not in request.files or 'minsup' not in request.form:
            error = "Vui lòng tải lên file CSV và nhập minsup."
            print("Error: Missing file or minsup")
        else:
            file = request.files['file']
            minsup = request.form['minsup']
            print(f"File: {file.filename}, Minsup: {minsup}")

            if file.filename == '':
                error = "Chưa chọn file CSV."
                print("Error: No file selected")
            elif not file.filename.endswith('.csv'):
                error = "File phải có định dạng CSV."
                print("Error: File not CSV")
            else:
                try:
                    minsup = float(minsup)
                    print(f"Parsed minsup: {minsup}")
                    if minsup <= 0:
                        error = "Minsup phải lớn hơn 0."
                        print("Error: Minsup <= 0")
                    else:
                        file_content = file.read().decode('utf-8')
                        df = pd.read_csv(io.StringIO(file_content))
                        print(f"Dataframe loaded with {len(df)} rows, columns: {df.columns.tolist()}")

                        required_columns = ['user_id', 'order_id', 'product_name', 'timestamp']
                        if not all(col in df.columns for col in required_columns):
                            error = "File CSV thiếu một hoặc nhiều cột cần thiết."
                            print(f"Error: Missing required columns, found: {df.columns.tolist()}")
                        else:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                            if df['timestamp'].isnull().any():
                                error = "Một số giá trị timestamp không hợp lệ."
                                print("Error: Invalid timestamp values")
                            else:
                                # Xác định số lượng user_id duy nhất
                                unique_users = df['user_id'].nunique()
                                print(f"Number of unique users: {unique_users}")
                                
                                if unique_users == 1:
                                    print("Processing single user data...")
                                    # Xử lý trường hợp 1 người dùng: coi mỗi order là một sequence độc lập
                                    df = df.sort_values(by=['order_id', 'timestamp'])
                                    sequences = []
                                    for order_id, group in df.groupby('order_id'):
                                        sequence = [tuple(group['product_name'].tolist())]
                                        sequences.append(sequence)
                                    print(f"Generated {len(sequences)} sequences from single user's orders")
                                else:
                                    print("Processing multiple users data...")
                                    # Xử lý trường hợp nhiều người dùng (như code cũ)
                                    df = df.sort_values(by=['user_id', 'timestamp'])
                                    df_grouped = df.groupby(['user_id', 'order_id', 'timestamp'])['product_name'].apply(list).reset_index()
                                    sequences_df = df_grouped.groupby('user_id').apply(lambda x: x[['order_id', 'timestamp', 'product_name']].to_dict('records')).reset_index()
                                    sequences_df.columns = ['user_id', 'orders']

                                    sequences = []
                                    for _, row in sequences_df.iterrows():
                                        user_sequence = [order['product_name'] for order in row['orders']]
                                        sequences.append(user_sequence)
                                
                                print("Sequences generated:")
                                for i, seq in enumerate(sequences):
                                    print(f"Sequence {i}: {seq}")

                                if not sequences:
                                    print("No sequences generated!")
                                else:
                                    patterns = run_clospan(sequences, int(minsup))
                                    print(f"Patterns found: {len(patterns)}")
                                    if patterns:
                                        print("Closed Sequential Patterns:")
                                        for pattern, support in patterns.items():
                                            print(f"[Pattern]: {' → '.join([', '.join(itemset) for itemset in pattern])} -> Support: {support}")
                                    else:
                                        print(f"No patterns found with minsup = {int(minsup)}")

                except ValueError:
                    error = "Minsup phải là số."
                    print("Error: Minsup not a number")
                except Exception as e:
                    error = f"Lỗi: {str(e)}"
                    print(f"Exception: {str(e)}")

    print("Rendering template...")
    return render_template('index.html', patterns=patterns, error=error)