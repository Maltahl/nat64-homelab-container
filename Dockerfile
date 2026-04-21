FROM ubuntu:24.04
RUN apt-get update && apt-get install -y tayga iproute2 iptables python3 && rm -rf /var/lib/apt/lists/*
COPY start.sh /start.sh
COPY pref64-ra.py /pref64-ra.py
RUN chmod +x /start.sh
CMD ["/start.sh"]
