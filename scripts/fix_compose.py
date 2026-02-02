#!/usr/bin/env python3
"""Fix docker-compose.prod.yml to add build directive"""

filepath = "/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/docker-compose.prod.yml"

with open(filepath, "r") as f:
    content = f.read()

# The old line we need to replace
old_line = "    image: ${DOCKER_REGISTRY:-}myhibachi-api:${VERSION:-latest}"

# The new section with build directive
new_section = """    build:
      context: .
      dockerfile: Dockerfile
    image: myhibachi-api:latest"""

# Replace
new_content = content.replace(old_line, new_section)

with open(filepath, "w") as f:
    f.write(new_content)

print("SUCCESS: docker-compose.prod.yml updated with build directive")
