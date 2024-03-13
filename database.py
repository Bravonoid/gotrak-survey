from pymongo.mongo_client import MongoClient
import streamlit as st

uri = f'mongodb://{st.secrets["mongo"]["username"]}:{st.secrets["mongo"]["password"]}@ac-sizcvp9-shard-00-00.pugcxfs.mongodb.net:27017,ac-sizcvp9-shard-00-01.pugcxfs.mongodb.net:27017,ac-sizcvp9-shard-00-02.pugcxfs.mongodb.net:27017/?ssl=true&replicaSet=atlas-6bomex-shard-0&authSource=admin&retryWrites=true&w=majority'


@st.cache_resource
def init_connection():
    return MongoClient(uri)


client = init_connection()

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Get the database
db = client.ergonomics

# Get the collection
sample = db.samples
achievment = db.achievment


# Insert many documents into a collection
def insert_update_sample(documents):
    for data in documents:
        for index, row in data.iterrows():
            result = sample.update_one(
                {
                    "Business Unit": row["Business Unit"],
                    "Department": row["Department"],
                    "PEG": row["Potential Exposured Group (PEG)"],
                },
                {
                    "$set": {
                        "Business Unit": row["Business Unit"],
                        "Department": row["Department"],
                        "PEG": row["Potential Exposured Group (PEG)"],
                        "Jumlah Sampel": row["Jumlah Sampel"],
                    }
                },
                upsert=True,
            )
    return result


def insert_update_achievment(documents):
    for data in documents:
        result = achievment.update_one(
            {
                "Business Unit": data["Business Unit"],
                "Department": data["Department"],
                "PEG": data["PEG"],
            },
            {
                "$set": {
                    "Business Unit": data["Business Unit"],
                    "Department": data["Department"],
                    "PEG": data["PEG"],
                    "Total Sample": data["Total Sample"],
                    "Yes": data["Yes"],
                    "No": data["No"],
                    "Percentage": data["Percentage"],
                    "Survey Responses": data["Survey Responses"],
                }
            },
            upsert=True,
        )
    return result


# Get all documents from a collection
def get_all_documents(collection):
    result = collection.find()
    return result
