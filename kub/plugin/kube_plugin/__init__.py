from fabric.api import run,sudo,put

def get_docker():
  run("wget -O get_docker.sh https://get.docker.com")
  sudo("sh ./get_docker.sh")

