FROM nginx:alpine

RUN apk add --no-cache openssh sudo python3 \
    && addgroup -g 1000 ansible \
    && adduser -D -u 1000 -G ansible -s /bin/sh ansible \
    && mkdir -p /home/ansible/.ssh \
    && chown -R ansible:ansible /home/ansible \
    && chmod 700 /home/ansible/.ssh \
    && printf 'ansible ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/ansible \
    && chmod 440 /etc/sudoers.d/ansible \
    && printf '\nPasswordAuthentication no\nPubkeyAuthentication yes\nPermitRootLogin no\n' >> /etc/ssh/sshd_config

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 22 80

CMD ["sh", "-c", "ssh-keygen -A && /usr/sbin/sshd && exec nginx -g 'daemon off;'"]
