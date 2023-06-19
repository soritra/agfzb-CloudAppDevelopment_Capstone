FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer="domitien@gmail.com"
LABEL version="1.3"
LABEL description="Docker Image for dealership reviews django-based applications."

ARG DEBIAN_FRONTEND=noninteractive
ARG UID=1000
ARG GID=1000
ARG APP_USR=reviewer

ENV PYTHONBUFFERED=1
ENV PYTHONWRITEBYTECODE=1
ENV UID=${UID}
ENV GID=${GID}
ENV APP_USR=${APP_USR}

RUN apt-get update \
    && apt-get install -y curl nano sudo net-tools python3-pip nginx \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 \
    && adduser --gecos "" --disabled-password "${APP_USR}" \
    && echo "${APP_USR} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers \
    && echo 'export PATH=$PATH:/home/'"${APP_USR}"'/.local/bin' >> /home/${APP_USR}/.bashrc
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*

#ARG TZ=Indian/Antananarivo
#RUN apt-get install libpq-dev postgresql-12 postgresql-contrib

RUN mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak
COPY .config/nginx.index.html /var/www/html/
COPY .config/nginx.default.conf /etc/nginx/sites-available/default

ENV HOME=/home/${APP_USR}
ENV APP=$HOME/app

# Change the workdir.
WORKDIR $APP
RUN chown ${APP_USR} $APP

USER ${APP_USR}

# Install the requirements
COPY server/requirements.txt $APP

RUN pip install --upgrade --no-warn-script-location pip setuptools
RUN pip install --no-warn-script-location -r requirements.txt

# Copy the rest of the files
COPY --chown=${UID}:${GID} server/djangobackend $APP/djangobackend
COPY --chown=${UID}:${GID} server/static $APP/static
COPY --chown=${UID}:${GID} server/db.sqlite3 $APP
COPY --chown=${UID}:${GID} server/manage.py $APP
COPY .config/gunicorn.conf $HOME/.gcorn.conf

# Copy the entrypoint and starting script
COPY --chown=${UID}:${GID} bin/entrypoint.sh $HOME/entrypoint.sh
COPY --chown=${UID}:${GID} bin/start.sh $HOME/start.sh
RUN chmod +x $HOME/entrypoint.sh && chmod +x $HOME/start.sh
#RUN $HOME/entrypoint.sh

ENTRYPOINT ["/home/reviewer/entrypoint.sh"]

CMD ["/home/reviewer/start.sh"]

EXPOSE 80 8000

