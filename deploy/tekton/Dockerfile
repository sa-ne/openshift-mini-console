FROM registry.access.redhat.com/ubi8/python-38
USER 0
RUN pip install --upgrade pip && \
  pip install flask && \
  pip install kubernetes && \
  pip install prometheus-flask-exporter
RUN pwd
RUN ls --recursive .
COPY /workspace/output /usr/src/app
USER 1001
WORKDIR /usr/src/app
EXPOSE 5000
ENTRYPOINT ["python", "-m", "flask", "run", "-h", "0.0.0.0"]
