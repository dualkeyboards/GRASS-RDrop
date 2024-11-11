# _includes/core.py
import asyncio
import random
import ssl
import json
import time
import uuid
import websockets
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from websockets.exceptions import ConnectionClosedError
from python_socks._errors import ProxyConnectionError
from loguru import logger
from _includes.proxies_manager import update_file, get_proxy_name #import
from _includes.errors_handler import handle_generic_error

async def connect_to_wss(proxy_url, device_id, user_id, stats, removed_proxies, retry_counts):
    user_agent = UserAgent()
    random_user_agent = user_agent.random

    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 5)
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy.wynd.network:4444/", "wss://proxy.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy.wynd.network"

            # Determine proxy type
            protocol = proxy_url.split("://")[0]
            if protocol in ["socks4", "socks5", "http"]:
                try:
                    proxy = Proxy.from_url(proxy_url)
                except Exception as e:
                    logger.error(f"Error creating proxy object: {e}")
                    retur
            else:
                logger.error(f"Unsupported proxy type: {protocol}")
                return

            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                stats['active_connections'] += 1

                async def send_ping():
                    while True:
                        try:
                            if websocket.closed:
                                break
                            send_message = json.dumps({"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.log("PING", f"PINGING to: {proxy_ip}")
                            await websocket.send(send_message)# Inside the while loop in `connect_to_wss`, where we send a ping:
                            stats['pings'] += 1  # Increment the ping count
                            update_file("proxies_ping.txt", proxy_url)  # Update ping file
                            await asyncio.sleep(10)
                        except ConnectionClosedError:
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.error(f"Connection closed unexpectedly during PING to {proxy_ip}")
                            break

                await asyncio.sleep(1)
                ping_task = asyncio.create_task(send_ping())

                while True:
                    try:
                        response = await websocket.recv()
                        message = json.loads(response)
                        proxy_ip = get_proxy_name(proxy_url)
                        if message.get("action") == "AUTH":
                            logger.log("AUTHENTICATION", f"AUTHENTICATION request from: {proxy_ip}")
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "desktop",
                                    "version": "4.28.2",
                                }
                            }
                            logger.log("AUTHENTICATION", f"AUTHENTICATION reply to: {proxy_ip}")
                            await websocket.send(json.dumps(auth_response))
                            update_file("proxies_auth.txt", proxy_url)  # Update auth file

                        elif message.get("action") == "PONG":
                            logger.log("PONG", f"PONG received from - {proxy_ip}")
                            # Inside the while loop in `connect_to_wss`, where we receive a pong:
                            stats['pongs'] += 1  # Increment the pong count
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            await websocket.send(json.dumps(pong_response))
                            update_file("proxies_pong.txt", proxy_url)  # Update pong file
                    except ConnectionClosedError:
                        proxy_ip = get_proxy_name(proxy_url)
                        logger.error(f"Connection closed while receiving data")
                        break
                    except OSError as e:
                        if "WinError 121" in str(e):
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.error(f"Semaphore timeout expired - {proxy_ip}. Retrying connection...")
                            await asyncio.sleep(10)
                            break

        except ConnectionClosedError as e:
            proxy_ip = get_proxy_name(proxy_url)
            stats['active_connections'] -= 1  # Decrement on any close
            close_reason = str(e.reason)
            logger.error(f"Connection closed ({close_reason}) - {proxy_ip}")

            # Retry logic if needed:
            if close_reason in ("Ping timeout", "WebSocket connection is closed: code = 1006 (connection closed abnormally [socket error = Connection reset by peer])"):

                if retry_counts.get(proxy_url, 0) < 2:
                    retry_counts[proxy_url] = retry_counts.get(proxy_url, 0) + 1
                    logger.warning(f"Retrying proxy {proxy_ip}, attempt {retry_counts[proxy_url]} / 2")
                    await asyncio.sleep(5)  # Wait before retrying
                    break  # Break inner loop to retry connection
                else:
                    logger.warning(f"Removing proxy {proxy_ip} after multiple retries.")
                    removed_proxies[0] += 1
                    break

            else: #don't retry
                break  # Only break inner loop, retry managed earlier

        except Exception as e:
            await handle_generic_error(proxy_url, removed_proxies, retry_counts, e)  # Pass retry_counts
            if retry_counts.get(proxy_url,0) < 2:
                await asyncio.sleep(5)
                continue #retry
            break