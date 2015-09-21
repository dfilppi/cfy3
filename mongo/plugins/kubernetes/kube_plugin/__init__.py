from fabric.api import run,sudo,put

def get_docker():
  run("wget -O get_docker.sh https://get.docker.com")
  sudo("sh ./get_docker.sh")


# Overrides one dict with another in place.  First dict serves
# as defaults, second for overrides.  Overrides can never be
# subtractive, just additive or replacements
def override(d1,d2):
  assert d1 and isinstance(d1,dict),"invalid dictionary"
  assert d2 and isinstance(d2,dict),"invalid dictionary"

  #handle mods
  def o1(d1,d2):
    for k in d1:
      if k in d2:
        if isinstance(d1[k], dict):
          override(d1[k],d2[k])
        else:
          d1[k]=d2[k]   

  #handle additions
  def o2(d1,d2):
    for k in d2:
      if k not in d1:
        d1[k]=d2[k] 
      else:
        if isinstance(d1[k], dict):
          o2(d1[k],d2[k])
  o1(d1,d2)
  o2(d1,d2)

