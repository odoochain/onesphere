FROM ghcr.io/masami10/odoo_crack_docker/oneshare_odoo:14.0-3.9

USER root

LABEL org.opencontainers.image.source=https://github.com/ethermeta-org/onesphere

#onesphere addons requirements
COPY ./requirements.txt /

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      phantomjs \
    && pip3 install --upgrade pip \
    && pip3 install -r /requirements.txt \
    && curl https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/bin/mc \
    && chmod +x /usr/bin/mc

COPY ./onesphere /mnt/extra-addons/
COPY ./oneshare_base /mnt/extra-addons/

COPY ./oneshare_base/oneshare_odoo_modify/static/src/img/favicon.ico /usr/lib/python3/dist-packages/odoo/addons/web/static/src/img/favicon.ico

# oneshare base requirements
RUN pip3 install -r /mnt/extra-addons/requirements.txt \
    && rm -f /requirements.txt \
    && rm -f /mnt/extra-addons/requirements.txt \
# 解决生成报告一定需要用户界面的问题
ENV QT_QPA_PLATFORM=offscreen

USER odoo
