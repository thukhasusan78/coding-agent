import docker
import time
import logging
import os
import tarfile
import io
from config.settings import settings

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("🐳 Docker Manager Connected")
            self.network_name = self._get_traefik_network()
            self.prune_resources()
        except Exception as e:
            logger.error(f"❌ Docker Connection Failed: {e}")
            self.client = None
            self.network_name = "ironman_net"

    def _get_traefik_network(self):
        try:
            traefik = self.client.containers.get("ironman-traefik")
            networks = traefik.attrs['NetworkSettings']['Networks']
            return list(networks.keys())[0] if networks else "ironman_net"
        except:
            return "ironman_net"

    def prune_resources(self):
        if not self.client: return
        try:
            self.client.containers.prune()
            self.client.images.prune(filters={'dangling': True})
        except: pass

    # 🔥 Helper: Folder တစ်ခုလုံးကို Tar ဖိုင်ပြောင်းပြီး Stream လုပ်မယ်
    def _create_archive(self, src_path):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w|') as tar:
            # Folder အောက်က ဖိုင်တွေကိုပဲ ယူမယ် (Root အနေနဲ့)
            arcname_root = os.path.basename(src_path)
            tar.add(src_path, arcname=".") 
        stream.seek(0)
        return stream

    def start_container(self, image: str, name: str, port: int, command: str = None, env: dict = None, code_path: str = None):
        if not self.client: return "❌ Docker Client Missing"

        try:
            # 1. Kill Old
            try:
                old = self.client.containers.get(name)
                old.remove(force=True)
                logger.info(f"♻️ Old container removed: {name}")
            except: pass

            labels = {
                "traefik.enable": "true",
                f"traefik.http.routers.{name}.rule": f"Host(`{name}.thukha.online`)",
                f"traefik.http.services.{name}.loadbalancer.server.port": str(port),
                "traefik.docker.network": self.network_name
            }

            # 2. Start Container (Sleep Mode - Code ထည့်ဖို့ စောင့်ခိုင်းမယ်)
            # 🔥 Code မရောက်ခင် App မ Run အောင် 'tail -f /dev/null' နဲ့ အရင်မောင်းထားမယ်
            logger.info(f"🚀 Initializing container {name}...")
            container = self.client.containers.run(
                image=image,
                name=name,
                command="tail -f /dev/null", # Keep alive command
                detach=True,
                environment=env or {},
                labels=labels,
                network=self.network_name,
                mem_limit="512m",
                working_dir="/app"
            )

            # 3. Inject Code (Code တွေကို Container ထဲ လှမ်းပို့မယ်)
            if code_path and os.path.exists(code_path):
                logger.info(f"📦 Injecting code from {code_path}...")
                archive = self._create_archive(code_path)
                # /app folder ထဲကို ဖြည်ချမယ်
                container.put_archive("/app", archive)
            
            # 4. Execute Actual Command (App ကို တကယ် Run မယ်)
            if command:
                logger.info(f"⚡ Executing start command: {command}")
                # Detached mode နဲ့ run မယ်
                container.exec_run(
                    f"bash -c '{command}'", 
                    detach=True
                )

            return f"✅ Container Deployed: {name}\n🌍 URL: http://{name}.thukha.online"

        except Exception as e:
            logger.error(f"🔥 Docker Error: {e}")
            return f"❌ Deployment Error: {e}"

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