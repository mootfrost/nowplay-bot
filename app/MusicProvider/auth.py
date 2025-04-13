import time

import aiohttp


def get_oauth_creds(token, refresh_token, expires_in):
    return {
        'access_token': token,
        'refresh_token': refresh_token,
        'refresh_at': int(time.time()) + expires_in
    }


async def refresh_token(endpoint, refresh_token, creds, proxy=None):
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        'Authorization': 'Basic ' + creds
    }
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    async with aiohttp.ClientSession(proxy=proxy) as session:
        resp = await session.post(endpoint, data=token_data, headers=token_headers)
    resp = await resp.json()
    return resp['access_token'], resp['expires_in']
