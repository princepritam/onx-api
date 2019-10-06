import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use the application default credentials
cred = credentials.Certificate('./admin_sdk.json')
firebase_admin.initialize_app(cred, {
  'projectId': 'onx-app',
})

db = firestore.client()