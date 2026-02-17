import logging
from src.runtime.docker_mgr import docker_mgr

logger = logging.getLogger(__name__)

class ProxyManager:
    def get_active_urls(self):
        """
        Scans running containers and returns active URLs
        """
        containers = docker_mgr.list_containers()
        urls = []
        for c in containers:
            # Check for Traefik labels
            if "traefik.enable" in c.labels:
                name = c.name
                # Construct URL from rule label usually: Host(`xyz.thukha.online`)
                for key, value in c.labels.items():
                    if "rule" in key and "Host" in value:
                        # Extract domain roughly
                        domain = value.split("`")[1]
                        urls.append(f"🌍 {name}: http://{domain}")
        
        if not urls:
            return "No active web apps found."
        return "\n".join(urls)

proxy_mgr = ProxyManager()