import docker
import time
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("🐳 Docker Manager Connected")
            # Traefik Network ကို Auto ရှာမယ်
            self.network_name = self._get_traefik_network()
            
            # 🔥 NEW: စစချင်း Run တာနဲ့ အမှိုက်ရှင်းမယ် (Disk Space သက်သာအောင်)
            self.prune_resources()
            
        except Exception as e:
            logger.error(f"❌ Docker Connection Failed: {e}")
            self.client = None
            self.network_name = "ironman_net"

    def _get_traefik_network(self):
        """Traefik Container ဘယ် Network သုံးနေလဲ လှမ်းချောင်းကြည့်မယ့် Function"""
        try:
            traefik_container = self.client.containers.get("ironman-traefik")
            networks = traefik_container.attrs['NetworkSettings']['Networks']
            if networks:
                net_name = list(networks.keys())[0]
                logger.info(f"🌐 Connected to Traefik Bridge: {net_name}")
                return net_name
        except docker.errors.NotFound:
            logger.warning("⚠️ Traefik Container not found! Using default 'ironman_net'.")
        except Exception as e:
            logger.warning(f"⚠️ Error detecting network: {e}")
        return "ironman_net"

    def prune_resources(self):
        """
        🔥 AUTO-PRUNE SYSTEM: 
        မလိုတဲ့ Container, Network, Image တွေကို ရှင်းထုတ်ပြီး VPS Storage ကို ကာကွယ်မယ်။
        """
        if not self.client: return
        try:
            logger.info("🧹 Auto-Pruning Docker Resources...")
            # Stopped Containers တွေကို ဖျက်မယ်
            self.client.containers.prune()
            # Dangling Images (နာမည်မရှိတဲ့ Image အဟောင်းတွေ) ကို ဖျက်မယ်
            self.client.images.prune(filters={'dangling': True})
            # မသုံးတဲ့ Network တွေ ဖျက်မယ်
            self.client.networks.prune()
            logger.info("✨ Docker System Cleaned.")
        except Exception as e:
            logger.warning(f"⚠️ Prune Warning: {e}")

    def start_container(self, image: str, name: str, port: int, command: str = None, env: dict = None):
        if not self.client:
            return "❌ Docker Client not available."

        try:
            # 1. Clean up old container
            try:
                old = self.client.containers.get(name)
                # 🔥 Memory Saver: အဟောင်းကို Stop လုပ်ရုံမကဘူး Remove ပါလုပ်မယ်
                old.remove(force=True)
                logger.info(f"♻️ Removed old container: {name}")
            except docker.errors.NotFound:
                pass

            # 2. Labels for Traefik
            labels = {
                "traefik.enable": "true",
                f"traefik.http.routers.{name}.rule": f"Host(`{name}.thukha.online`)",
                f"traefik.http.services.{name}.loadbalancer.server.port": str(port),
                "traefik.docker.network": self.network_name
            }

            logger.info(f"🚀 Starting container {name} on network '{self.network_name}'...")
            
            # 3. Run Container (Limit Memory to avoid VPS Freeze)
            container = self.client.containers.run(
                image=image,
                name=name,
                command=command,
                detach=True,
                environment=env or {},
                labels=labels,
                network=self.network_name,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 3},
                # 🔥 VPS Protection: Container တစ်ခုကို RAM 512MB ထက် ပိုမပေးဘူး
                mem_limit="512m" 
            )
            
            return f"✅ Container Started: {name} (ID: {container.short_id})\n🌍 URL: http://{name}.thukha.online"

        except Exception as e:
            logger.error(f"🔥 Docker Run Error: {e}")
            return f"❌ Failed to start container: {e}"

    def list_containers(self):
        if not self.client: return []
        return self.client.containers.list()

    def stop_container(self, name):
        try:
            container = self.client.containers.get(name)
            container.stop()
            container.remove()
            return f"🛑 Stopped {name}"
        except Exception as e:
            return f"⚠️ Error stopping {name}: {e}"

docker_mgr = DockerManager()