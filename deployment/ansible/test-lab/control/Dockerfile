FROM debian:12-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ansible \
        ca-certificates \
        curl \
        git \
        openssh-client \
        rsync \
        sshpass \
    && rm -rf /var/lib/apt/lists/*

COPY run-lab.sh /usr/local/bin/run-lab.sh
RUN chmod +x /usr/local/bin/run-lab.sh

CMD ["/usr/local/bin/run-lab.sh"]
