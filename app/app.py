import requests
import os
import logging
from fastapi import FastAPI, HTTPException, Request

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Replace with your qBittorrent Web UI credentials and URL
QB_SERVER = os.getenv('QB_SERVER')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
DUMMY_TRACKER_PART = os.getenv('DUMMY_TRACKER_PART')
REAL_TRACKER_PART = os.getenv('REAL_TRACKER_PART')
INDEXER_NAME = os.getenv('INDEXER_NAME')

# Remove " (Prowlarr)" suffix if present in the environment variable
if INDEXER_NAME.endswith(" (Prowlarr)"):
    INDEXER_NAME = INDEXER_NAME[:-11]

logger.info(f"qBittorrent server: {QB_SERVER}")

# Login to qBittorrent Web API


def qb_login():
    """Login to qBittorrent Web API."""
    login_url = f'{QB_SERVER}/api/v2/auth/login'
    data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    session = requests.Session()
    response = session.post(login_url, data=data)
    if response.ok and response.text == "Ok.":
        return session
    else:
        logger.error("Login failed.")
        return None


def get_torrent_by_hash(session, torrent_hash):
    """Retrieve information about a specific torrent using its hash."""
    url = f'{QB_SERVER}/api/v2/torrents/info?hashes={torrent_hash}'
    response = session.get(url)
    if response.ok:
        torrents = response.json()
        if torrents:
            return torrents[0]
        else:
            return None
    else:
        logger.error(f"Failed to get torrent with hash {torrent_hash}")
        return None


def get_trackers(session, torrent_hash):
    """Retrieve the list of trackers for a specific torrent."""
    url = f'{QB_SERVER}/api/v2/torrents/trackers?hash={torrent_hash}'
    response = session.get(url)
    if response.ok:
        return response.json()
    else:
        logger.error(f"Failed to get trackers for torrent {torrent_hash}.")
        return []


def edit_tracker(session, torrent_hash, old_tracker, new_tracker):
    """Edit a tracker for a specific torrent."""
    url = f'{QB_SERVER}/api/v2/torrents/editTracker'
    data = {
        'hash': torrent_hash,
        'origUrl': old_tracker,
        'newUrl': new_tracker
    }
    response = session.post(url, data=data)
    if response.ok:
        logger.info(f"Tracker updated for torrent {torrent_hash}")
    else:
        logger.error(f"Failed to update tracker for torrent {torrent_hash}")


@app.post('/update_tracker')
async def webhook(request: Request):
    """Receive and process webhook"""

    """Generic webhook receiver to process dynamic data"""
    # Parse the incoming JSON data
    data = await request.json()

    # Allow testing the webhook
    if data['eventType'] == 'Test':
        logger.info("Test event received")
        return HTTPException(status_code=200, detail="Test event received")

    # Skip events that are coming from Prowlarr acting as a proxy
    if data["instanceName"] == "Prowlarr" and data["source"] != "Prowlarr":
        logger.info("Skipping event from Prowlarr acting as a proxy")
        return HTTPException(status_code=200, detail="Prowlarr acting as a proxy")

    torrent_hash = data['downloadId']

    # Only process events for the specified indexer
    indexer = data['release']['indexer']

    logger.info(f"Indexer: {indexer}")
    logger.info(f"Indexer name: {INDEXER_NAME}")

    if indexer != INDEXER_NAME:
        logger.info(f"Skipping event from {indexer}")
        return HTTPException(status_code=200, detail="Changing tracker skipped")

    if not torrent_hash:
        logger.error("Missing download ID (torrent hash)")
        raise HTTPException(
            status_code=400, detail="Missing download ID (torrent hash)")

    # Login to qBittorrent
    session = qb_login()
    if not session:
        raise HTTPException(status_code=500, detail="qBittorrent login failed")

    # Retrieve torrent by hash
    edit_torrent = get_torrent_by_hash(session, torrent_hash)
    if not edit_torrent:
        logger.error(f"No matching torrent found for hash: {torrent_hash}")
        raise HTTPException(status_code=404, detail="Torrent not found")

    # Retrieve the list of trackers for the matched torrent
    trackers = get_trackers(session, torrent_hash)
    if not trackers:
        logger.error(f"No trackers found for torrent {torrent_hash}")
        raise HTTPException(
            status_code=404, detail="No trackers found for the torrent")

    # Find the tracker that contains the portion to replace (one or more)
    for tracker in trackers:
        tracker_url = tracker['url']
        if DUMMY_TRACKER_PART in tracker_url:
            # Replace only the part of the tracker URL
            new_tracker_url = tracker_url.replace(
                DUMMY_TRACKER_PART, REAL_TRACKER_PART)

            # Update the tracker with the modified URL
            edit_tracker(session, torrent_hash, tracker_url, new_tracker_url)
            logger.info(f"Tracker updated for torrent {edit_torrent['name']}")

    return {"message": "Tracker updated", "torrent": edit_torrent['name']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level="debug")
