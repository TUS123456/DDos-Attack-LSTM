# import pandas as pd
# from sklearn.ensemble import IsolationForest
# from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
# import matplotlib.pyplot as plt

# # Load your traffic data (assuming it's in CSV format)
# data = pd.read_csv(r"C:\Users\tusar\Desktop\sunita-project\DDoSWatch\DDoSWatch\data\traffic-data.csv")  # Update with your actual path
# print(data.head())


# # Assuming the traffic data has a column 'Traffic' with the number of requests per minute
# X = data[['Traffic']].values

# # Assuming you have a 'True_Label' column where 1 = normal, -1 = attack (DDoS)
# y_true = data['True_Label']  # Update with your actual column name for true labels

# # Initialize and fit the Isolation Forest model
# model = IsolationForest(contamination=0.05)  # Adjust contamination level as needed
# model.fit(X)

# # Predict anomalies (-1 for anomaly, 1 for normal)
# data['Anomaly'] = model.predict(X)
# anomalies = data[data['Anomaly'] == -1]

# # Print detected anomalies
# print("Anomalies detected:")
# print(anomalies)

# # Compare predictions with true labels to calculate accuracy
# accuracy = accuracy_score(y_true, data['Anomaly'])
# print(f"Accuracy: {accuracy * 100:.2f}%")

# # Confusion Matrix
# conf_matrix = confusion_matrix(y_true, data['Anomaly'])
# print("Confusion Matrix:")
# print(conf_matrix)

# # Precision, Recall, F1 Score
# print("Classification Report:")
# print(classification_report(y_true, data['Anomaly']))

# # Plot the traffic data and anomalies
# plt.figure(figsize=(10, 6))
# plt.plot(data['Traffic'], label='Traffic Data')
# plt.scatter(anomalies.index, anomalies['Traffic'], color='red', label='Anomalies')
# plt.xlabel('Time')
# plt.ylabel('Traffic')
# plt.legend()
# plt.savefig('anomalies_plot.png')  # Save plot as image


# import json
# import pandas as pd
# from kafka import KafkaConsumer
# from sklearn.preprocessing import MinMaxScaler
# import tensorflow as tf
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
# import numpy as np
# import matplotlib.pyplot as plt
# import os
# import datetime
# import asyncio
# from telegram import Bot

# # ----------------------------- Telegram Setup -----------------------------
# TELEGRAM_TOKEN = "8535450620:AAHyL2blf0u4iyvKlMXmLq_Fzkr04OKieWY"
# CHAT_ID = 5868163209  # Replace with your numeric chat ID
# bot = Bot(token=TELEGRAM_TOKEN)

# # Async function to send Telegram message
# async def send_telegram(message_text):
#     try:
#         await bot.send_message(chat_id=CHAT_ID, text=message_text)
#         print("✅ Telegram message sent")
#     except Exception as e:
#         print(f"❌ Failed to send Telegram message: {e}")

# # ----------------------------- Kafka Consumer Setup -----------------------------
# consumer = KafkaConsumer(
#     'traffic_raw',
#     bootstrap_servers='192.168.29.164:9092',  # Update with your Kafka host
#     auto_offset_reset='earliest',
#     enable_auto_commit=True,
#     group_id='lstm-anomaly-group',
#     value_deserializer=lambda x: json.loads(x.decode('utf-8'))
# )

# # ----------------------------- Settings -----------------------------
# BUFFER_SIZE = 50       # Number of messages to keep in buffer
# TRAINING_SIZE = 20     # Minimum sequences to start training
# timesteps = 5          # Sliding window length for LSTM
# numeric_cols = ['response_time_ms', 'request_size', 'status']

# # ----------------------------- Output folders -----------------------------
# output_folder = r"C:\Users\tusar\Desktop\sunita-project\DDoSWatch\DDoSWatch\data"
# os.makedirs(output_folder, exist_ok=True)
# anomaly_file = os.path.join(output_folder, "realtime_anomalies.json")

# # Initialize JSON file
# with open(anomaly_file, 'w') as f:
#     json.dump([], f)

# # ----------------------------- Build LSTM Autoencoder -----------------------------
# def build_autoencoder(input_dim):
#     model = Sequential([
#         LSTM(16, activation='relu', return_sequences=True, input_shape=(timesteps, input_dim)),
#         LSTM(8, activation='relu', return_sequences=False),
#         RepeatVector(timesteps),
#         LSTM(8, activation='relu', return_sequences=True),
#         LSTM(16, activation='relu', return_sequences=True),
#         TimeDistributed(Dense(input_dim))
#     ])
#     model.compile(optimizer='adam', loss='mse')
#     return model

# # ----------------------------- Variables -----------------------------
# buffer = []
# model_trained = False
# threshold = None
# scaler = MinMaxScaler()

# # ----------------------------- Real-time Plot -----------------------------
# plt.ion()  # Enable interactive mode
# fig, ax = plt.subplots(figsize=(12, 6))

# print("🚀 Waiting for Kafka data...")

# # Create an event loop for async Telegram notifications
# loop = asyncio.get_event_loop()

# # ----------------------------- Main Streaming Loop -----------------------------
# for message in consumer:
#     log = message.value
#     buffer.append(log)

#     if len(buffer) > BUFFER_SIZE:
#         buffer = buffer[-BUFFER_SIZE:]

#     df = pd.DataFrame(buffer)

#     # Ensure numeric fields exist
#     if not all(col in df.columns for col in numeric_cols):
#         continue

#     df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

#     # Normalize numeric data
#     normalized_data = scaler.fit_transform(df[numeric_cols])

#     # Create sequences for LSTM
#     sequence = []
#     for i in range(len(normalized_data) - timesteps):
#         sequence.append(normalized_data[i:i + timesteps])
#     sequence = np.array(sequence)

#     # Train LSTM if not trained yet
#     if not model_trained and len(sequence) >= TRAINING_SIZE:
#         print("\n🧠 Training LSTM model...")
#         model = build_autoencoder(len(numeric_cols))
#         history = model.fit(sequence, sequence, epochs=20, batch_size=16, verbose=0)

#         # Compute reconstruction error threshold
#         recon = model.predict(sequence)
#         mse = np.mean(np.power(sequence - recon, 2), axis=(1, 2))
#         threshold = np.percentile(mse, 95)
#         print(f"✅ Model trained! Threshold set to: {threshold}")
#         model_trained = True

#     # Detect anomalies
#     if model_trained and len(sequence) > 0:
#         recon = model.predict(sequence)
#         mse = np.mean(np.power(sequence - recon, 2), axis=(1, 2))
#         anomaly_flags = mse > threshold

#         last_record = df.tail(1)[['timestamp','client_ip','method','path','status','response_time_ms']].to_dict(orient='records')[0]

#         if anomaly_flags[-1]:
#             print(f"\n⚠️ Anomaly detected at {datetime.datetime.now()}")
#             print(last_record)

#             # Append anomaly to JSON file
#             with open(anomaly_file, 'r+') as f:
#                 data = json.load(f)
#                 data.append(last_record)
#                 f.seek(0)
#                 json.dump(data, f, indent=4)

#             # Send Telegram message asynchronously
#             message_text = f"⚠️ Anomaly Detected!\nTime: {datetime.datetime.now()}\nDetails:\n{json.dumps(last_record, indent=2)}"
#             loop.run_until_complete(send_telegram(message_text))

#         else:
#             print(f"✅ Normal record: {last_record}")

#         # ----------------------------- Real-time plot -----------------------------
#         ax.clear()
#         ax.plot(df.index, df['response_time_ms'], label="Response Time", marker='o')
#         anomalies_index = np.where(anomaly_flags)[0]
#         if len(anomalies_index) > 0:
#             ax.scatter(anomalies_index, df.iloc[anomalies_index]['response_time_ms'],
#                        color="red", label="Anomaly", s=100)
#         ax.set_title("Real-Time LSTM Traffic Anomaly Detection")
#         ax.set_xlabel("Event Index")
#         ax.set_ylabel("Response Time (ms)")
#         ax.legend()
#         plt.pause(0.1)  # Small pause to update plot


import json
import pandas as pd
from kafka import KafkaConsumer
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
import numpy as np
import matplotlib.pyplot as plt
import os
import datetime
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# ========================= LOAD ENV =========================
load_dotenv()

# ========================= TELEGRAM =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram(message_text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message_text)
        print("✅ Telegram message sent")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ========================= KAFKA =========================
consumer = KafkaConsumer(
    os.getenv("KAFKA_TOPIC"),
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    auto_offset_reset=os.getenv("KAFKA_OFFSET_RESET"),
    enable_auto_commit=os.getenv("KAFKA_AUTO_COMMIT") == "true",
    group_id=os.getenv("KAFKA_GROUP_ID"),
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

# ========================= SETTINGS =========================
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE"))
TRAINING_SIZE = int(os.getenv("TRAINING_SIZE"))
timesteps = int(os.getenv("TIMESTEPS"))

numeric_cols = ["response_time_ms", "request_size", "status"]

# ========================= OUTPUT =========================
output_folder = os.getenv("OUTPUT_FOLDER")
anomaly_file = os.path.join(output_folder, os.getenv("ANOMALY_FILE_NAME"))

os.makedirs(output_folder, exist_ok=True)

with open(anomaly_file, "w") as f:
    json.dump([], f)

# ========================= MODEL =========================
def build_autoencoder(input_dim):
    model = Sequential([
        LSTM(16, activation="relu", return_sequences=True,
             input_shape=(timesteps, input_dim)),
        LSTM(8, activation="relu", return_sequences=False),
        RepeatVector(timesteps),
        LSTM(8, activation="relu", return_sequences=True),
        LSTM(16, activation="relu", return_sequences=True),
        TimeDistributed(Dense(input_dim))
    ])
    model.compile(optimizer="adam", loss="mse")
    return model

# ========================= VARIABLES =========================
buffer = []
model_trained = False
threshold = None
scaler = MinMaxScaler()

plt.ion()
fig, ax = plt.subplots(figsize=(12, 6))

loop = asyncio.get_event_loop()

print("🚀 Waiting for Kafka data...")

# ========================= MAIN LOOP =========================
for message in consumer:
    log = message.value
    buffer.append(log)

    if len(buffer) > BUFFER_SIZE:
        buffer = buffer[-BUFFER_SIZE:]

    df = pd.DataFrame(buffer)

    if not all(col in df.columns for col in numeric_cols):
        continue

    df[numeric_cols] = df[numeric_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    normalized_data = scaler.fit_transform(df[numeric_cols])

    sequences = []
    for i in range(len(normalized_data) - timesteps):
        sequences.append(normalized_data[i:i + timesteps])

    sequences = np.array(sequences)

    # -------- TRAIN --------
    if not model_trained and len(sequences) >= TRAINING_SIZE:
        print("🧠 Training LSTM...")
        model = build_autoencoder(len(numeric_cols))
        model.fit(sequences, sequences, epochs=20, batch_size=16, verbose=0)

        recon = model.predict(sequences)
        mse = np.mean(np.power(sequences - recon, 2), axis=(1, 2))
        threshold = np.percentile(mse, 95)

        model_trained = True
        print(f"✅ Model trained | Threshold: {threshold}")

    # -------- DETECT --------
    if model_trained and len(sequences) > 0:
        recon = model.predict(sequences)
        mse = np.mean(np.power(sequences - recon, 2), axis=(1, 2))
        anomaly_flags = mse > threshold

        last_record = df.tail(1)[
            ["timestamp", "client_ip", "method", "path",
             "status", "response_time_ms"]
        ].to_dict(orient="records")[0]

        if anomaly_flags[-1]:
            print("⚠️ ANOMALY DETECTED")
            print(last_record)

            with open(anomaly_file, "r+") as f:
                data = json.load(f)
                data.append(last_record)
                f.seek(0)
                json.dump(data, f, indent=4)

            msg = (
                f"⚠️ Anomaly Detected\n"
                f"Time: {datetime.datetime.now()}\n\n"
                f"{json.dumps(last_record, indent=2)}"
            )
            loop.run_until_complete(send_telegram(msg))
        else:
            print("✅ Normal traffic")

        # -------- PLOT --------
        ax.clear()
        ax.plot(df.index, df["response_time_ms"], marker="o", label="Response Time")

        anomaly_idx = np.where(anomaly_flags)[0]
        if len(anomaly_idx) > 0:
            ax.scatter(
                anomaly_idx,
                df.iloc[anomaly_idx]["response_time_ms"],
                color="red",
                s=100,
                label="Anomaly"
            )

        ax.set_title("Real-Time LSTM Traffic Anomaly Detection")
        ax.set_xlabel("Event Index")
        ax.set_ylabel("Response Time (ms)")
        ax.legend()
        plt.pause(0.1)