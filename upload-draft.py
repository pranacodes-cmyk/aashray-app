"""Upload the independent Aashray build and PUBLISH it on the Internal Testing track (status completed)."""
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
    # versionCode 1 already exists on the app (a manually uploaded 1.0.0 build that
    # contained the startup crash). Ship the fixed build as a higher versionCode;
    # versionCode 1 is burned and never assigned to a track.
    existing=check(requests.get(base+'/bundles',headers=headers,timeout=60)).get('bundles',[])
    existing_codes={b.get('versionCode') for b in existing}
    with open('yeshu_app/build/app/outputs/bundle/release/app-release.aab','rb') as f:
        bundle=check(requests.post(f'https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE}/edits/{edit}/bundles?uploadType=media',headers={**headers,'Content-Type':'application/octet-stream'},data=f,timeout=600))
    version=bundle['versionCode']
    if version in existing_codes:
        raise RuntimeError(f'versionCode {version} already exists on the app; bump the version in pubspec.yaml.')
    def track(status):
        return requests.put(base+'/tracks/internal',headers=headers,json={'track':'internal','releases':[{'name':'Aashray 1.0.6','versionCodes':[str(version)],'status':status,'releaseNotes':[{'language':'en-IN','text':'Cleaner paywall with real UPI app logos and sound-on video, server-controlled Skip, redesigned Settings.'}]}]},timeout=60)
    status='completed'
    r=track(status)
    if r.status_code==400 and 'draft app' in r.text.lower():
        # Play forbids non-draft releases until the app's first setup is finished.
        status='draft'; r=track(status)
        print('PLAY_APP_STILL_DRAFT: Play only allows draft releases until app setup is completed in Play Console.')
    check(r)
    check(requests.post(base+':validate',headers=headers,timeout=60))
    committed = requests.post(base+':commit', headers=headers, params={'changesNotSentForReview':'true'}, timeout=60)
    if committed.status_code == 400 and 'must not be set' in committed.text:
        committed = requests.post(base+':commit', headers=headers, timeout=60)
    check(committed)
    print('Uploaded com.aashray.faith version',version,'to Internal Testing with status',status,'; not production.')
except Exception:
    requests.delete(base,headers=headers,timeout=60)
    raise