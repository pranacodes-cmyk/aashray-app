"""Upload only the independent Aashray first build to an internal DRAFT."""
import os,json,requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

PACKAGE='com.aashray.faith'
c=service_account.Credentials.from_service_account_info(json.loads(os.environ['GOOGLE_PLAY_SERVICE_ACCOUNT_JSON']),scopes=['https://www.googleapis.com/auth/androidpublisher'])
c.refresh(Request())
headers={'Authorization':'Bearer '+c.token}
root=f'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}/edits'
def check(r):
    if not r.ok:
        try: message=r.json().get('error',{}).get('message','Play request failed')
        except Exception: message='Play request failed'
        raise RuntimeError(f'Play [{r.status_code}]: {message}')
    return r.json() if r.content else {}
edit=check(requests.post(root,headers=headers,json={},timeout=60))['id']
base=root+'/'+edit
try:
    existing=check(requests.get(base+'/bundles',headers=headers,timeout=60)).get('bundles',[])
    if existing:raise RuntimeError('First-release safety check: app already has a bundle; do not overwrite.')
    with open('yeshu_app/build/app/outputs/bundle/release/app-release.aab','rb') as f:
        bundle=check(requests.post(f'https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE}/edits/{edit}/bundles?uploadType=media',headers={**headers,'Content-Type':'application/octet-stream'},data=f,timeout=600))
    version=bundle['versionCode']
    check(requests.put(base+'/tracks/internal',headers=headers,json={'track':'internal','releases':[{'name':'Aashray 1.0.0','versionCodes':[str(version)],'status':'draft','releaseNotes':[{'language':'en-IN','text':'First Aashray internal draft for device validation.'}]}]},timeout=60))
    check(requests.post(base+':validate',headers=headers,timeout=60))
    committed = requests.post(base+':commit', headers=headers, params={'changesNotSentForReview':'true'}, timeout=60)
    if committed.status_code == 400 and 'must not be set' in committed.text:
        # Only an internal DRAFT is changed; never silently submit listing edits.
        committed = requests.post(base+':commit', headers=headers, timeout=60)
    check(committed)
    print('Uploaded com.aashray.faith version',version,'to Internal Testing with status draft; not production.')
except Exception:
    requests.delete(base,headers=headers,timeout=60)
    raise