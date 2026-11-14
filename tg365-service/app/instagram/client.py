"""Instagram API with Instagram Login — OAuth + Reels publishing (official)."""
import time

import requests

GRAPH = "https://graph.instagram.com"
API_VERSION = "v21.0"


def authorize_url(app_id: str, redirect_uri: str, state: str) -> str:
    from urllib.parse import quote

    scope = "instagram_business_basic,instagram_business_content_publish"
    return (
        "https://www.instagram.com/oauth/authorize"
        f"?client_id={app_id}&redirect_uri={quote(redirect_uri, safe='')}"
        f"&response_type=code&scope={scope}&state={state}"
    )


def exchange_code(app_id: str, app_secret: str, redirect_uri: str, code: str) -> str:
    r = requests.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def long_lived_token(app_secret: str, short_token: str) -> dict:
    r = requests.get(
        f"{GRAPH}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
        timeout=30,
    )
    r.raise_for_status()
    j = r.json()
    return {"token": j["access_token"], "expires_at": int(time.time()) + j.get("expires_in", 5184000)}


def me(token: str) -> dict:
    r = requests.get(
        f"{GRAPH}/me", params={"fields": "user_id,username", "access_token": token}, timeout=30
    )
    r.raise_for_status()
    return r.json()


def refresh_token(token: str, app_secret: str) -> dict:
    r = requests.get(
        f"{GRAPH}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    j = r.json()
    return {"token": j["access_token"], "expires_at": int(time.time()) + j.get("expires_in", 5184000)}


def publish_reel(token: str, ig_user_id: str, video_url: str, caption: str) -> str:
    """Container → wait FINISHED → publish. Returns media_id. (25 posts / 24h cap.)"""
    r = requests.post(
        f"{GRAPH}/{API_VERSION}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
        timeout=60,
    )
    r.raise_for_status()
    creation_id = r.json()["creation_id"]

    deadline = time.time() + 300
    while time.time() < deadline:
        st = requests.get(
            f"{GRAPH}/{API_VERSION}/{creation_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=30,
        ).json()
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(st.get("status", "media container error"))
        time.sleep(5)
    else:
        raise TimeoutError("media container did not finish in 300s")

    r = requests.post(
        f"{GRAPH}/{API_VERSION}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["id"]


def get_permalink(token: str, media_id: str) -> str:
    r = requests.get(
        f"{GRAPH}/{API_VERSION}/{media_id}",
        params={"fields": "permalink", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("permalink", "")
