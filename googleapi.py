import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def get_document(doc): #Wholesale stolen from Google examples :)
    creds = None

    if os.path.exists('credentials' + os.sep + 'token.pickle'):
        with open('credentials' + os.sep + 'token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials' + os.sep + 'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('credentials' + os.sep + 'token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('docs', 'v1', credentials=creds)

    return service.documents().get(documentId=doc).execute()

def make_snippet_list_from_doc(doc):
    lyric_doc = get_document(doc)
    currentSnippet = ""
    snippets = []

    for l in lyric_doc.get('body')['content']:
        if l is not None:
            par = l.get('paragraph')
            if par is not None:
                ele = par.get('elements')
                line = ele[0]['textRun']['content']
                if line != '\n':
                    currentSnippet += line
                elif len(currentSnippet) > 0:
                    snippets.append(currentSnippet)
                    currentSnippet = ""
    return snippets

if __name__ == '__main__':
    print(make_snippet_list_from_doc("16WNStYc5qNLGFOujF8EBywvFtIQWq56hhYwrh9PLp8c"))
    pass