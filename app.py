
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

import io
import os
import sys
import traceback

import nltk
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models import InferSent

import sqlite3

V = 1
MODEL_PATH = '../encoder/infersent%s.pkl' % V
params_model = {'bsize': 64, 'word_emb_dim': 300, 'enc_lstm_dim': 2048,
                'pool_type': 'max', 'dpout_model': 0.0, 'version': V}
infersent = InferSent(params_model)
infersent.load_state_dict(torch.load(MODEL_PATH))
W2V_PATH = '../GloVe/glove.840B.300d.txt'
infersent.set_w2v_path(W2V_PATH)

infersent.build_vocab_k_words(K=100000) #100k most common words loaded up in model vocab 

PORT = "5000"
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def adapt_array(arr):
    """
    http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


# Converts np.array to TEXT when inserting
#sqlite3.register_adapter(np.ndarray, adapt_array)

# Converts TEXT to np.array when selecting
#sqlite3.register_converter("array", convert_array)

def get_cosine_similarity(feature_vec_1, feature_vec_2):    
    return cosine_similarity(feature_vec_1.reshape(1, -1), feature_vec_2.reshape(1, -1))[0][0]

@app.route("/questions", methods=["POST"])
@cross_origin()
def questions(): 
    with sqlite3.connect("database.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES) as con:
        data = [request.json["fa1"]]
        friend_code = request.json["friend_code"]
        embeddings = infersent.encode(data, tokenize=True)
        cursor = con.cursor()

        print(friend_code, embeddings.shape)
        print("type on insert is", type(embeddings), embeddings[0])
        try: 
            print('tables:', cursor.fetchall())
            cursor.execute("INSERT INTO embeddings (uid, data) VALUES (?, ?)", (friend_code, adapt_array(embeddings)))
            return jsonify(success=True), 201
        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return jsonify(success=False), 500

@app.route("/matches", methods=["POST"])
@cross_origin()
def matches(): 

    with sqlite3.connect("database.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES) as con:
        friend_code = request.json["friend_code"]
        cursor = con.cursor()

        try: 
            matched_friends = []

            cursor.execute("SELECT * FROM embeddings WHERE NOT uid = ?", (friend_code,))
            
            # can optimize with numpy commands later

            results = cursor.fetchall()

            cursor.execute("SELECT * FROM embeddings WHERE uid = ?", (friend_code,))
            current_embedding = cursor.fetchone()[0]

            print("current embedding", convert_array(current_embedding))

            cosine_similarities = []
            for row in results:
                uid, data = row
                print("data", data)
                sim = get_cosine_similarity(convert_array(current_embedding), convert_array(data))
                cosine_similarities.append((uid, sim))

            sorted_matches = sorted(cosine_similarities, key=lambda x : x[1], reverse=True)

            print(f"Finding matches for {friend_code}: friend {sorted_matches[0][0]} has similarity {sorted_matches[0][1]}")
            top_match = map(lambda x: x[1], sorted_matches[:3])    
            return jsonify(uid=top_match), 200

        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
            return jsonify(success=False), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

