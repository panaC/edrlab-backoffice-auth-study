FROM debian:12-slim

ENV container=docker

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        dbus \
        iproute2 \
        openssh-server \
        python3 \
        sudo \
        systemd \
        systemd-sysv \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd \
    && echo "root:root" | chpasswd \
    && mkdir -p /etc/ssh/sshd_config.d \
    && printf '%s\n' \
        'PermitRootLogin yes' \
        'PasswordAuthentication yes' \
        'KbdInteractiveAuthentication no' \
        > /etc/ssh/sshd_config.d/10-lab-default.conf \
    && systemctl enable ssh

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
