import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.

def make_token(scope, cred_name):
    creds = None

    token_path = os.path.join(os.path.dirname(__file__), "credentials" + os.sep + cred_name + "_token.pickle")
    cred_path = os.path.join(os.path.dirname(__file__), "credentials" + os.sep + cred_name + ".json")

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_path, scope)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_document(doc): #Wholesale stolen from Google examples :)
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    docs_token = make_token(scope=SCOPES, cred_name="docs")
    service = build('docs', 'v1', credentials=docs_token)
    return service.documents().get(documentId=doc).execute()


def get_sheet(sheet, range):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    sheets_token = make_token(scope=SCOPES, cred_name="sheets")
    service = build('sheets', 'v4', credentials=sheets_token)
    return service.spreadsheets().values().get(spreadsheetId=sheet, range=range).execute()


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
                    currentSnippet += (line if line.strip() != "|" else "\n")
                elif len(currentSnippet) > 0:
                    snippets.append(currentSnippet)
                    currentSnippet = ""
    return snippets

if __name__ == '__main__':
    print(make_snippet_list_from_doc("16WNStYc5qNLGFOujF8EBywvFtIQWq56hhYwrh9PLp8c"))
    # print(get_sheet("1rmQ0ps140rlztd2CtDCaTaWdel8RO6YxHWB03DmIoU0", "Levels!A1:L16").get('values'))
    pass