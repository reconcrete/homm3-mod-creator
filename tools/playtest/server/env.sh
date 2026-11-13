# Shared settings for the play-test scripts on the Linux test machine (sourced, not run).
export VCMI_ROOT="$HOME/Projects/vcmi"
export XDG_DATA_HOME="$VCMI_ROOT/home/share"     # game data, mods, maps, saves: home/share/vcmi
export XDG_CONFIG_HOME="$VCMI_ROOT/home/config"  # settings.json, modSettings.json: home/config/vcmi
export XDG_CACHE_HOME="$VCMI_ROOT/home/cache"    # logs: home/cache/vcmi
export DISPLAY=:50
export SDL_AUDIODRIVER=dummy
SHOTS="$VCMI_ROOT/shots"
